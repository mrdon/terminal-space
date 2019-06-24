from prompt_toolkit import Application
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.layout import Layout, HSplit, VSplit, D
from prompt_toolkit.layout.processors import Processor
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.widgets import TextArea, Frame, Label, Box, MenuContainer, MenuItem

from pytw_textui.terminal_text_area import TerminalTextArea


class TwApplication(Application):
    def __init__(self):
        super().__init__(
            # layout=Layout(
            #     root_container,
            #     focused_element=yes_button,
            # ),
            # key_bindings=bindings,
            # style=style,
            mouse_support=True,
            full_screen=True)

        textfield = TerminalTextArea(focus_on_click=True, scrollbar=True, width=D(min=70))
        textfield.append_text([("red", "blah")])
        # textfield = TextArea(text="hi frield")

        root_container = HSplit([
            VSplit([
                Frame(body=Label(text='Left frame\ncontent'),
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

        class BufferWriter:
            def write(self, text):
                textfield.append_text(text)

            def flush(self):
                pass

        self.buffer = textfield.buffer



if __name__ == "__main__":
    TwApplication().run()
