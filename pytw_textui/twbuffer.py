from dataclasses import dataclass
from typing import Tuple, List, Sequence

from prompt_toolkit.layout.screen import Point





class TwBuffer:
    def __init__(self):
        self.buffer: List[List[Tuple[str,str]]] = [[]]
        self.cursor = Point(x=0, y=0)

    def insert_after(self, text: Sequence[Sequence[Tuple[str,str]]]):
        # breakpoint()
        if text:
            self.buffer[self.cursor.y] += text[0]

        if len(text) > 1:
            self.buffer += text[1:]

    def get_line(self, index: int) -> List[Tuple[str, str]]:
        return [] if len(self.buffer) >= index else self.buffer[index]

    @property
    def line_count(self) -> int:
        return len(self.buffer)

    @property
    def cursor_position(self) -> Point:
        return self.cursor

