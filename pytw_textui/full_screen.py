import asyncio
from asyncio import Queue

from prompt_toolkit import Application
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout import D
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout import VSplit
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import MenuContainer
from prompt_toolkit.widgets import MenuItem

from pytw_textui.session import Session
from pytw_textui.stream import Terminal
from pytw_textui.terminal_text_area import TerminalTextArea
from pytw_textui.ui.dynamic_label import DynamicLabel


class TwApplication(Application):
    def __init__(self, in_queue: Queue, out_queue: Queue):
        super().__init__(
            mouse_support=True,
            full_screen=True)

        textfield = self._init_layout()
        self.buffer = textfield.buffer
        self.buffer.on_change(lambda: self.invalidate())

        self.terminal = Terminal(self.buffer)
        self.session = Session(self.terminal)
        self.in_queue = in_queue
        self.out_queue = out_queue

    async def start(self):
        use_asyncio_event_loop()
        ui_task = self.run_async().to_asyncio_future()

        input_task = asyncio.create_task(self.session.start(lambda text: self.out_queue.put(text)))
        input_task.add_done_callback(lambda *_: self.exit())

        async def read_events():
            while True:
                event = await self.in_queue.get()
                await self.session.bus(event)

        events_task = asyncio.create_task(read_events())
        events_task.add_done_callback(lambda *_: self.exit())

        await ui_task

    def _init_layout(self):
        textfield = TerminalTextArea(focus_on_click=True, scrollbar=True, width=D(min=70))
        # textfield = TextArea(text="hi frield")

        def get_sector_label():
            if self.session and self.session.game and self.session.game.player and self.session.game.player.ship:
                player = self.session.game.player
                sector = self.session.game.player.ship.sector
                return FormattedText([
                    ('grey', f"Sector:  "),
                    ("bold", str(sector.id)),
                    ('grey', f"\nPort:    "),
                    ("bold", "" if not sector.port else sector.port.class_name),
                    ('grey', f"\nCredits: "),
                    ("bold", str(player.credits))

                ])
            else:
                return FormattedText([('white', "Sector: ???")])
        root_container = HSplit([
            VSplit([
                Frame(body=DynamicLabel(get_sector_label), title="Sector info",
                      width=D(max=25)),
                textfield,
                Frame(body=Label(text='Right frame\ncontent'),
                      width=D(max=25)),
            ], height=D()),
            VSplit([
                Frame(body=Label(text='right bottom frame\ncontent')),
                Frame(body=Label(text='middle frame\ncontent')),
                Frame(body=Label(text='left bottom frame\ncontent')),
            ], padding=1),
        ])

        def do_exit():
            self.exit(result=False)

        menu_container = MenuContainer(body=root_container, menu_items=[
            MenuItem('File', children=[
                MenuItem('New'),
                MenuItem('Exit', handler=do_exit),
            ]),
            MenuItem('Edit', children=[
                MenuItem('Undo'),
                MenuItem('Cut'),
                MenuItem('Copy'),
            ]),
            MenuItem('View', children=[
                MenuItem('Status Bar'),
            ]),
            MenuItem('Info', children=[
                MenuItem('About'),
            ])])
        self.layout = Layout(
            menu_container,
            focused_element=textfield,
        )
        return textfield
