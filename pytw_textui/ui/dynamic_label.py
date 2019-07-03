from typing import Callable
from typing import Union

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.formatted_text import fragment_list_to_text
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.layout import D
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.layout import Window
from prompt_toolkit.utils import get_cwidth


class DynamicLabel(object):
    """
    Widget that displays the given text. It is not editable or focusable.

    :param text: The text to be displayed. (This can be multiline. This can be
        formatted text as well.)
    :param style: A style string.
    :param width: When given, use this width, rather than calculating it from
        the text size.
    """
    def __init__(self, text_func: Callable[[], Union[str, FormattedText]], style='', width=None,
                 dont_extend_height=True, dont_extend_width=False):
        self.text_func = text_func

        def get_width():
            if width is None:
                text_fragments = to_formatted_text(self.text_func())
                text = fragment_list_to_text(text_fragments)
                if text:
                    longest_line = max(get_cwidth(line) for line in text.splitlines())
                else:
                    return D(preferred=0)
                return D(preferred=longest_line)
            else:
                return width

        self.formatted_text_control = FormattedTextControl(
            text=text_func)

        self.window = Window(
            content=self.formatted_text_control,
            width=get_width,
            style='class:label ' + style,
            dont_extend_height=dont_extend_height,
            dont_extend_width=dont_extend_width)

    def __pt_container__(self):
        return self.window