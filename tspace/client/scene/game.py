from typing import Awaitable
from typing import Callable

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout import D
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout import VSplit
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import MenuContainer
from prompt_toolkit.widgets import MenuItem

from tspace.client.session import Session
from tspace.client.stream import Terminal
from tspace.client.terminal_text_area import TerminalTextArea
from tspace.client.ui.dynamic_label import DynamicLabel


class TerminalScene:
    def __init__(self, app: Application, writer: Callable[[str], Awaitable[None]]):
        self.app = app
        self.writer = writer
        textfield = TerminalTextArea(focus_on_click=True, width=D(min=70))
        self.buffer = textfield.buffer
        self.buffer.on_change(lambda: app.invalidate())

        self.terminal = Terminal(self.buffer)
        self.session = Session(self.terminal)

        def get_sector_label():
            if (
                self.session
                and self.session.game
                and self.session.game.player
                and self.session.game.player.ship
            ):
                player = self.session.game.player
                sector = self.session.game.player.ship.sector
                return FormattedText(
                    [
                        ("grey", f"Sector:  "),
                        ("bold", str(sector.id)),
                        ("grey", f"\nPort:    "),
                        ("bold", "" if not sector.port else sector.port.class_name),
                        ("grey", f"\nCredits: "),
                        ("bold", str(player.credits)),
                    ]
                )
            else:
                return FormattedText([("white", "Sector: ???")])

        root_container = HSplit(
            [
                VSplit(
                    [
                        Frame(
                            body=DynamicLabel(get_sector_label),
                            title="Sector info",
                            width=D(max=25),
                        ),
                        textfield,
                        Frame(body=Label(text="Right frame\ncontent"), width=D(max=25)),
                    ],
                    height=D(),
                ),
                VSplit(
                    [
                        Frame(body=Label(text="right bottom frame\ncontent")),
                        Frame(body=Label(text="middle frame\ncontent")),
                        Frame(body=Label(text="left bottom frame\ncontent")),
                    ],
                    padding=1,
                ),
            ],
            style="bg:black",
        )

        def do_exit():
            self.session.quit()

        menu_container = MenuContainer(
            body=root_container,
            menu_items=[
                MenuItem(
                    "File",
                    children=[MenuItem("New"), MenuItem("Exit", handler=do_exit)],
                ),
                MenuItem(
                    "Edit",
                    children=[MenuItem("Undo"), MenuItem("Cut"), MenuItem("Copy")],
                ),
                MenuItem("View", children=[MenuItem("Status Bar")]),
                MenuItem("Info", children=[MenuItem("About")]),
            ],
        )
        self.layout = Layout(menu_container, focused_element=textfield)
        self.textfield = textfield

    async def start(self):
        return await self.session.start(self.writer)

    def end(self):
        pass
