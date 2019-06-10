from typing import Tuple, List

from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, is_true
from prompt_toolkit.layout import Window, UIControl, ScrollbarMargin, UIContent

from pytw_textui.twbuffer import TwBuffer


class TerminalTextArea(UIControl):
    """
    A simple input field.

    This is a higher level abstraction on top of several other classes with
    sane defaults.

    This widget does have the most common options, but it does not intend to
    cover every single use case. For more configurations options, you can
    always build a text area manually, using a
    :class:`~prompt_toolkit.buffer.Buffer`,
    :class:`~prompt_toolkit.layout.BufferControl` and
    :class:`~prompt_toolkit.layout.Window`.

    Buffer attributes:

    :param text: The initial text.
    :param multiline: If True, allow multiline input.
    :param completer: :class:`~prompt_toolkit.completion.Completer` instance
        for auto completion.
    :param complete_while_typing: Boolean.
    :param accept_handler: Called when `Enter` is pressed (This should be a
        callable that takes a buffer as input).
    :param history: :class:`~prompt_toolkit.history.History` instance.
    :param auto_suggest: :class:`~prompt_toolkit.auto_suggest.AutoSuggest`
        instance for input suggestions.

    BufferControl attributes:

    :param password: When `True`, display using asterisks.
    :param focusable: When `True`, allow this widget to receive the focus.
    :param focus_on_click: When `True`, focus after mouse click.
    :param input_processors: `None` or a list of
        :class:`~prompt_toolkit.layout.Processor` objects.

    Window attributes:

    :param lexer: :class:`~prompt_toolkit.lexers.Lexer` instance for syntax
        highlighting.
    :param wrap_lines: When `True`, don't scroll horizontally, but wrap lines.
    :param width: Window width. (:class:`~prompt_toolkit.layout.Dimension` object.)
    :param height: Window height. (:class:`~prompt_toolkit.layout.Dimension` object.)
    :param scrollbar: When `True`, display a scroll bar.
    :param style: A style string.
    :param dont_extend_width: When `True`, don't take up more width then the
                              preferred width reported by the control.
    :param dont_extend_height: When `True`, don't take up more width then the
                               preferred height reported by the control.
    :param get_line_prefix: None or a callable that returns formatted text to
        be inserted before a line. It takes a line number (int) and a
        wrap_count and returns formatted text. This can be used for
        implementation of line continuations, things like Vim "breakindent" and
        so on.

    Other attributes:

    :param search_field: An optional `SearchToolbar` object.
    """
    def __init__(self, text='', multiline=True, password=False,
                 lexer=None, auto_suggest=None, completer=None,
                 complete_while_typing=True, accept_handler=None, history=None,
                 focusable=True, focus_on_click=False, wrap_lines=True,
                 read_only=False, width=None, height=None,
                 dont_extend_height=False, dont_extend_width=False,
                 line_numbers=False, get_line_prefix=None, scrollbar=False,
                 style='', search_field=None, preview_search=True, prompt='',
                 input_processors=None):


        # Writeable attributes.

        self.buffer = TwBuffer()
        self.wrap_lines = wrap_lines

        # if scrollbar:
        #     right_margins = [ScrollbarMargin(display_arrows=True)]
        # else:
        right_margins = []
        left_margins = []

        self.window = Window(
            height=height,
            width=width,
            dont_extend_height=dont_extend_height,
            dont_extend_width=dont_extend_width,
            content=self,
            style=style,
            wrap_lines=Condition(lambda: is_true(self.wrap_lines)),
            left_margins=left_margins,
            right_margins=right_margins,
            get_line_prefix=get_line_prefix)

    def append_text(self, text: List[List[Tuple[str,str]]]):
        self.buffer.insert_after(text)

    # @property
    # def accept_handler(self):
    #     """
    #     The accept handler. Called when the user accepts the input.
    #     """
    #     return self.buffer.accept_handler
    #
    # @accept_handler.setter
    # def accept_handler(self, value):
    #     self.buffer.accept_handler = value

    def __pt_container__(self):
        return self.window


    def create_content(self, width, height):
        return UIContent(get_line=self.buffer.get_line,
                         line_count=self.buffer.line_count,
                         cursor_position=self.buffer.cursor_position,
                         show_cursor=True)


