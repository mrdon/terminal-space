from asyncio import Future
from functools import partial

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import D
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout import VSplit
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Dialog
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import MenuContainer
from prompt_toolkit.widgets import MenuItem

from pytw_textui.session import Session
from pytw_textui.stream import Terminal
from pytw_textui.terminal_text_area import TerminalTextArea
from pytw_textui.ui.dynamic_label import DynamicLabel
from pytw_textui.ui.menu import MenuDialog


class TitleScene:

    def __init__(self, app: Application):
        self.app = app

        dialog = MenuDialog(
            title="My title",
            body=Label(text="Body here", dont_extend_width=True, width=20,
                       dont_extend_height=True),
            buttons=[
                Button(text="Start Game", handler=partial(self.do_exit, "start")),
                Button(text="Quit", handler=partial(self.do_exit, "quit"))
            ],
            with_background=True,
            on_dismiss=partial(self.do_exit, "quit"))

        self.layout = Layout(
            dialog
        )
        self.future = Future()

    def do_exit(self, result, *_):
        self.future.set_result(result)

    async def start(self):
        result = await self.future
        self.future = Future()
        return result

    def end(self):
        pass