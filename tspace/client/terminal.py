from asyncio import Queue
from asyncio import Queue
from typing import Tuple, Sequence

from prompt_toolkit import ANSI
from prompt_toolkit.formatted_text import to_formatted_text

from tspace.client.twbuffer import TwBuffer


class Terminal:
    def __init__(self, buffer: TwBuffer):
        self.buffer = buffer
        self.stdin = input

    def backspace(self, num_characters: int = 1):
        self.buffer.backspace(num_characters)

    def write_line(self, *fragments: Tuple[str, str]):
        self.write_lines([*fragments])

    def write_lines(self, *text: Sequence[Tuple[str, str]]):
        self.buffer.insert_after(*text)

    def print(self, text: str, color=None, bg=None, attrs=None):
        style = ""
        if color:
            style += color
        if bg:
            style += f" bg:{bg}"

        if attrs:
            style += " "
            style += " ".join(attrs)

        lines = text.split(r"\n|\r|\r\n")
        self.write_lines(*[[(style, line)] for line in lines])

    def nl(self, times=1):
        for x in range(times):
            self.write_lines([], [])

    def error(self, msg):
        self.nl()
        self.print(msg, "red")
        self.nl()
        self.nl()

    async def read_key(self) -> str:
        queue = Queue()

        def receive_input(txt: str):
            queue.put_nowait(txt)

        self.buffer.input_listeners.append(receive_input)
        return await queue.get()

    # def read_line(self, matcher: Callable[[str],bool]) -> str:
    #     queue = Queue()
    #
    #     buffer = []
    #
    #     def receive_input(txt: str):
    #         if txt == '\r' or txt == '\n':
    #             queue.put_nowait("".join(buffer))
    #         elif matcher(txt):
    #             buffer.append(txt)
    #
    #     self.buffer.input_listeners.append(receive_input)
    #     return queue.get()

    def write_ansi(self, text):
        for line in text.split("\n"):
            self.write_line(*to_formatted_text(ANSI(line)))
            self.nl()

    def write_ansi_raw(self, text):
        formatted_text = to_formatted_text(ANSI(text))
        pos = self.buffer.cursor_position
        self.buffer.insert_after(formatted_text)
        self.buffer.cursor_position = pos
        #
        # log.info(f"line: {text}")
        # ansi_cursor = ANSICursor(text)
        # ops = ansi_cursor.parsed
        # for op in ops:
        #     if isinstance(op, str):
        #         # log.info(f"str: {op}")
        #         formatted_text = to_formatted_text(ANSI(op))
        #         self.buffer.insert_after(formatted_text)
        #     else:
        #         # if op.op == CursorOpType.MOVE:
        #     # log.info(f"mov: x:{op.x_mod} y:{op.y_mod}")
        #     self.buffer.cursor_position = Point(self.buffer.cursor_position.x + op.x_mod,
        #                                self.buffer.cursor_position.y + op.y_mod)
