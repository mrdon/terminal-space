import asyncio
from asyncio import Future

from prompt_toolkit.application import get_app
from prompt_toolkit.layout import HSplit, Float, FloatContainer, Container, AnyContainer
from prompt_toolkit.widgets import Dialog, Label, Button, Box, Frame

from tspace.client.ui.draw import AnimatedPlanetApproach
from tspace.client.ui.starfield import Starfield


class WarpDialog:
    def __init__(self, sector_id: int):
        self._dims = get_app().output.get_size()
        self._starfield = Starfield()
        self.container = Frame(
                title=lambda: f"Warping to {sector_id}",
                body=HSplit(children=[self._starfield],
                                     width=int(self._dims.columns / 2), height=int(self._dims.rows / 2)),
                style="class:dialog.body",
                width=None,
                modal=True,
            )

        self.future = Future()

    def __pt_container__(self) -> AnyContainer:
        return self.container

    async def show(self):
        async def speed_up():
            for _ in range(3):
                self._starfield.speed *= 2.5
                await asyncio.sleep(0.5)

            self.container.body = HSplit(children=[AnimatedPlanetApproach(10)],
                   width=int(self._dims.columns / 2), height=int(self._dims.rows / 2))
            await asyncio.sleep(3)
            # for _ in range(3):
            #     self._starfield.speed /= 2.5
            #     await asyncio.sleep(0.5)
            self.future.set_result(None)

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
