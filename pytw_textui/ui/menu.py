from typing import Callable

from prompt_toolkit.filters import has_completions
from prompt_toolkit.filters import has_focus
from prompt_toolkit.formatted_text import is_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next
from prompt_toolkit.key_binding.bindings.focus import focus_previous
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import D
from prompt_toolkit.layout import DynamicContainer
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import VSplit
from prompt_toolkit.widgets import Box
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Shadow


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
    def __init__(self, body, title='', buttons=None, modal=True, width=None,
                 with_background=False, on_dismiss: Callable[[],None] = None):
        assert is_formatted_text(title)
        assert buttons is None or isinstance(buttons, list)

        self.body = body
        self.title = title

        buttons = buttons or []

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
                    height=D(min=1, max=3, preferred=3))
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
            self.container = Box(
                body=frame,
                style='class:dialog',
                width=width)
        else:
            self.container = frame

    def __pt_container__(self):
        return self.container
