from dataclasses import dataclass
from typing import Callable
from typing import Tuple, List, Sequence

from prompt_toolkit.layout.screen import Point


class TwBuffer:
    def __init__(self):
        self.buffer: List[List[Tuple[str,str]]] = [[]]
        self.cursor = Point(x=0, y=0)

        self.input_listeners: List[Callable[[str], None]] = []

    def insert_after(self, *text: Sequence[Tuple[str,str]]):
        if not isinstance(text, (Tuple, List)):
            raise ValueError()

        if any(isinstance(x, Tuple) for x in text):
            raise ValueError()

        str_buffer = []
        for line in text:
            line_buffer = []
            for frag in line:
                if not isinstance(frag, Tuple):

                    raise ValueError(f"Invalid frgament: {frag}")
                if not isinstance(frag[1], str):
                    line_buffer.append((frag[0], str(frag[1])))
                else:
                    line_buffer.append(frag)
            str_buffer.append(line_buffer)
        text = str_buffer

        if text and text[0]:
            self.buffer[self.cursor.y] += text[0]

        new_y = self.cursor.y
        if len(text) > 1:
            self.buffer += text[1:]
            new_y = len(self.buffer) - 1
        new_x = self.get_line_length(new_y) - 1
        self.cursor = Point(x=new_x, y=new_y)

    def get_line(self, index: int) -> List[Tuple[str, str]]:
        result = [] if index >= len(self.buffer) else self.buffer[index]
        return result

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

