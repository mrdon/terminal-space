from asyncio import Future
from functools import partial

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Label

from tspace.client.ui.menu import MenuDialog
from tspace.client.ui.starfield import Starfield


class TitleScene:
    def __init__(self, app: Application):
        self.app = app

        dialog = MenuDialog(
            title="Terminal Space",
            body=Label(
                text="   A text-based\n space trading game",
                dont_extend_width=False,
                width=20,
                dont_extend_height=True,
            ),
            buttons=[
                Button(text="New Game", handler=partial(self.do_exit, "start")),
                Button(text="Join Game", handler=partial(self.do_exit, "join")),
                Button(text="Quit", handler=partial(self.do_exit, "quit")),
            ],
            background=Starfield(),
            on_dismiss=partial(self.do_exit, "quit"),
        )

        self.layout = Layout(dialog)
        self.future = Future()

    def do_exit(self, result, *_):
        self.future.set_result(result)

    async def start(self):
        result = await self.future
        self.future = Future()
        return result

    def end(self):
        pass
