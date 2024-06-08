import asyncio
from asyncio import Future

from prompt_toolkit.application import get_app
from prompt_toolkit.layout import (
    HSplit,
    Float,
    FloatContainer,
    Container,
    AnyContainer,
    DynamicContainer,
)
from prompt_toolkit.widgets import Dialog, Label, Box, Frame

from tspace.client.logging import log
from tspace.client.models import Sector
from tspace.client.ui.button import Button
from tspace.client.ui.draw import AnimatedPlanetApproach
from tspace.client.ui.starfield import Starfield


def dyn_container():
    return getattr(dyn_container, "blah", None)


class WarpDialog(Dialog):
    def __init__(self, sector_id: int):
        self._dims = get_app().output.get_size()
        self._starfield = Starfield()
        self.body = HSplit(
            children=[self._starfield],
            width=int(self._dims.columns / 2),
            height=int(self._dims.rows / 2),
        )
        dyn_container.blah = self.body
        self.ok_btn = Button(text="OK", disabled=True, handler=self._on_ok)
        super().__init__(
            body=DynamicContainer(dyn_container),
            title=f"Warping to {sector_id}",
            buttons=[self.ok_btn],
            modal=True,
        )
        self._sector_future = Future()
        self.future = Future()

    def set_next_sector(self, sector: Sector):
        self._sector_future.set_result(sector)

    def _on_ok(self):
        self.future.set_result(None)

    async def show(self):
        async def speed_up():
            for _ in range(4):
                self._starfield.speed *= 2.5
                await asyncio.sleep(0.5)
            next_sector = await self._sector_future

            has_port = bool(next_sector.ports)
            has_planet = bool(next_sector.planets)
            has_something = has_planet or has_port

            self.body = HSplit(
                children=[
                    AnimatedPlanetApproach(
                        3,
                        port=has_port,
                        planet=has_planet,
                    )
                ],
                width=int(self._dims.columns / 2),
                height=int(self._dims.rows / 2),
            )
            if has_something:
                await asyncio.sleep(3)
            # for _ in range(3):
            #     self._starfield.speed /= 2.5
            #     await asyncio.sleep(0.5)
            self.ok_btn.disabled = False

        asyncio.create_task(speed_up())
        return await show_dialog_as_float(self)

    async def wait_till_done(self):
        await self.future


async def show_dialog_as_float(dialog):
    "Coroutine."
    float_ = Float(content=dialog)
    app = get_app()
    root_container = app.layout.container
    root_container.floats.insert(0, float_)

    try:
        focused_before = app.layout.current_window
        app.layout.focus(dialog)
        result = await dialog.wait_till_done()
        app.layout.focus(focused_before)
    except ValueError as ex:
        result = await dialog.wait_till_done()

    if float_ in root_container.floats:
        root_container.floats.remove(float_)

    return result
