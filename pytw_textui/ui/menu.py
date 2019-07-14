from __future__ import annotations
from typing import Callable
from typing import List
from typing import Optional

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import has_completions
from prompt_toolkit.filters import has_focus
from prompt_toolkit.formatted_text import is_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next
from prompt_toolkit.key_binding.bindings.focus import focus_previous
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import D
from prompt_toolkit.layout import DynamicContainer
from prompt_toolkit.layout import Float
from prompt_toolkit.layout import FloatContainer
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import VSplit
from prompt_toolkit.layout import Window
from prompt_toolkit.layout import WindowAlign
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.widgets import Box
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Shadow

from pytw_textui.ui.starfield import Starfield


class MenuDialog(object):
    """
    Simple dialog window. This is the base for input dialogs, message dialogs
    and confirmation dialogs.

    Changing the title and body of the dialog is possible at runtime by
    assigning to the `body` and `title` attributes of this class.

    :param body: Child container object.
    :param title: Text to be displayed in the heading of the dialog.
    :param buttons: A list of `Button` widgets, displayed at the bottom.
    """
    def __init__(self, body, title='', buttons: Optional[List[Button]] = None, modal=True, width=None,
                 with_background=False, on_dismiss: Callable[[],None] = None):
        assert is_formatted_text(title)
        assert buttons is None or isinstance(buttons, list)

        self.body = body
        self.title = title

        max_menu_item_length = max(len(x.text) for x in buttons) + 10
        buttons = [] if not buttons else [MenuButton(btn.text, handler=btn.handler, width=max_menu_item_length) for btn in buttons]

        # When a button is selected, handle left/right key bindings.
        buttons_kb = KeyBindings()
        if len(buttons) > 1:
            first_selected = has_focus(buttons[0])
            last_selected = has_focus(buttons[-1])

            buttons_kb.add('up', filter=~first_selected)(focus_previous)
            buttons_kb.add('down', filter=~last_selected)(focus_next)

        if buttons:
            frame_body = HSplit([
                # Add optional padding around the body.
                Box(body=DynamicContainer(lambda: self.body),
                    padding=D(preferred=1, max=1),
                    padding_bottom=1),
                # The buttons.
                Box(body=HSplit(buttons, padding=1, key_bindings=buttons_kb),
                    height=D(min=len(buttons), max=10, preferred=len(buttons) * 2))
            ])
        else:
            frame_body = body

        # Key bindings for whole dialog.
        kb = KeyBindings()
        kb.add('tab', filter=~has_completions)(focus_next)
        kb.add('s-tab', filter=~has_completions)(focus_previous)

        if on_dismiss:
            kb.add('q')(on_dismiss)
            kb.add(Keys.Escape)(on_dismiss)

        frame = Shadow(body=Frame(
            title=lambda: self.title,
            body=frame_body,
            style='class:dialog.body',
            width=(None if with_background is None else width),
            key_bindings=kb,
            modal=modal,
        ))

        if with_background:
            # self.container = Box(
            #     body=frame,
            #     style='class:dialog',
            #     width=width)

            # margin = (width - max_menu_item_length + 12) // 2
            self.container = FloatContainer(
                content=Starfield(),
                floats=[
                    Float(
                          transparent=False,
                          content=Box(
                              body=frame,
                              width=width))
                ]
            )
        else:
            self.container = frame

        # self.container = Starfield()

    def __pt_container__(self):
        return self.container


class MenuButton:
    """
    Clickable button.  Copied from Button but with prompt turned off

    :param text: The caption for the button.
    :param handler: `None` or callable. Called when the button is clicked.
    :param width: Width of the button.
    """

    def __init__(self, text, handler=None, width=20):
        assert isinstance(text, str)
        assert handler is None or callable(handler)
        assert isinstance(width, int)

        self.text = text
        self.handler = handler
        self.width = width
        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=self._get_key_bindings(),
            show_cursor=False,
            focusable=True)

        def get_style():
            if get_app().layout.has_focus(self):
                return 'class:button.focused'
            else:
                return 'class:button'

        self.window = Window(
            self.control,
            align=WindowAlign.CENTER,
            height=1,
            width=width,
            style=get_style,
            dont_extend_width=True,
            dont_extend_height=True)

    def _get_text_fragments(self):
        text = ('{:^%s}' % (self.width - 10)).format(self.text)

        def handler(mouse_event):
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.handler()

        return [
            ('class:button.arrow', '--== ', handler),
            ('[SetCursorPosition]', ''),
            ('class:button.text', text, handler),
            ('class:button.arrow', ' ==--', handler),
        ]

    def _get_key_bindings(self):
        " Key bindings for the Button. "
        kb = KeyBindings()

        @kb.add(' ')
        @kb.add('enter')
        def _(event):
            if self.handler is not None:
                self.handler()

        return kb

    def __pt_container__(self):
        return self.window

