import asyncio
from asyncio import Future
from functools import partial

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, Window, to_container
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Label

from tspace.client.logging import log
from tspace.client.ui.menu import MenuDialog
from tspace.client.ui.starfield import Starfield


class TitleScene:
    def __init__(self, app: Application):
        self.app = app
        self.starfield = Starfield()
        self.dialog = MenuDialog(
            title="Terminal Space",
            body=Label(
                text="   A text-based\n space trading game",
                dont_extend_width=False,
                width=20,
                dont_extend_height=True,
            ),
            buttons=[
                Button(text="New Game", handler=self.on_new_game),
                Button(text="Join Game", handler=partial(self.do_exit, "join")),
                Button(text="Quit", handler=partial(self.do_exit, "quit")),
            ],
            background=self.starfield,
            on_dismiss=partial(self.do_exit, "quit"),
        )

        self.layout = Layout(self.dialog)
        self.future = Future()

    def on_new_game(self):
        self.layout.container = self.starfield.window

        async def speed_up():
            for _ in range(4):
                self.starfield.speed *= 2.5
                await asyncio.sleep(0.5)

        task = asyncio.create_task(speed_up())
        task.add_done_callback(lambda _: self.do_exit("start"))

    def do_exit(self, result, *_):
        self.starfield.paused = True
        self.future.set_result(result)

    async def start(self):
        log.info("Starting title")
        self.starfield.reset_speed()
        self.layout.container = to_container(self.dialog)
        result = await self.future
        self.future = Future()
        return result

    def end(self):
        self.starfield.paused = True
        pass
