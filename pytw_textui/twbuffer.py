from dataclasses import dataclass
from typing import Callable
from typing import Tuple, List, Sequence

from prompt_toolkit.layout.screen import Point


class TwBuffer:
    def __init__(self):
        self.buffer: List[List[Tuple[str, str]]] = [[]]
        self.cursor = Point(x=0, y=0)

        self.input_listeners: List[Callable[[str], None]] = []
        self.change_listeners: List[Callable[[], None]] = []

    def insert_after(self, *text: Sequence[Tuple[str, str]]):
        if not isinstance(text, (Tuple, List)):
            raise ValueError()

        if any(isinstance(x, Tuple) for x in text):
            raise ValueError()

        str_buffer = []
        for line in text:
            line_buffer = []
            for frag in line:
                if not isinstance(frag, Tuple):

                    raise ValueError(f"Invalid fragment: {frag}")
                if not isinstance(frag[1], str):
                    line_buffer.append((frag[0], str(frag[1])))
                else:
                    line_buffer.append(frag)
            str_buffer.append(line_buffer)
        text = str_buffer

        if text and text[0]:
            self.buffer[self.cursor.y] += text[0]

        if len(text) > 1:
            self.buffer += text[1:]

        self._set_cursor_to_buffer_end()

        for listener in self.change_listeners:
            listener()

    def _set_cursor_to_buffer_end(self):
        new_y = len(self.buffer) - 1
        new_x = self.get_line_length(new_y) - 1
        self.cursor = Point(x=new_x, y=new_y)

    def on_change(self, listener: Callable[[], None]):
        self.change_listeners.append(listener)

    def get_line(self, index: int) -> List[Tuple[str, str]]:
        result = [] if index >= len(self.buffer) else self.buffer[index]
        return result + [("", " ")]

    def get_line_length(self, index: int) -> int:
        return sum(len(x[1]) for x in self.get_line(index))

    @property
    def line_count(self) -> int:
        return len(self.buffer)

    @property
    def cursor_position(self) -> Point:
        return self.cursor

    def on_key_press(self, txt: str):
        for listener in self.input_listeners:
            listener(txt)

    def backspace(self, num_characters: int):
        line = self.buffer[-1]
        if num_characters >= self.get_line_length(-1):
            self.buffer[-1] = []
        else:
            while num_characters:
                last = line[-1]
                chars = last[1]
                if len(chars) >= num_characters:
                    num_characters = 0
                    chars = chars[0:-num_characters]
                else:
                    num_characters -= len(chars)
                    chars = ""
                line[-1] = (last[0], chars)

        self._set_cursor_to_buffer_end()
