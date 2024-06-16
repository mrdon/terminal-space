import time
from asyncio import Queue
from dataclasses import astuple
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Generator
from typing import Tuple, Callable, List, Sequence

from prompt_toolkit import ANSI
from prompt_toolkit.data_structures import Point
from prompt_toolkit.formatted_text import to_formatted_text

from tspace.client.instant_cmd import InstantCmd, InvalidSelectionError
from tspace.client.logging import log
from tspace.client.terminal import Terminal
from tspace.client.twbuffer import TwBuffer


@dataclass
class Fragment:
    style: str
    text: str


@dataclass
class Item:
    value: List[Fragment]


@dataclass
class Row:
    header: Fragment
    items: List[Item]


@dataclass
class Table:
    rows: List[Row]


def print_grid(stream: Terminal, data: Table, separator: Fragment):
    header_len = max(len(row.header.text) for row in data.rows) + 1
    for row in data.rows:
        stream.write_line(
            astuple(row.header),
            ("", " " * (header_len - len(row.header.text))),
            astuple(separator),
        )
        pad = False
        for item in row.items:
            if pad:
                stream.write_line(("", " " * (header_len + 2)))
            else:
                pad = True

            for frag in item.value:
                stream.write_line(astuple(frag))

            stream.nl()


def print_action(stream: Terminal, title):
    stream.nl()
    stream.print(text=title, color="white", bg="blue")
    stream.nl(2)


@dataclass
class Option:
    key: str
    description: str
    function: Callable[[], None]


class SimpleMenuCmd:
    def __init__(self, stream: Terminal, default: str, option_order: Iterable[str]):
        self.stream = stream
        self.default = default
        self.options = {}

        self.instant_prompt = InstantCmd(stream)
        for key in option_order:
            key = key.lower()
            fn = getattr(self, "do_{}".format(key))
            self.options[key] = Option(
                key=key, description=fn.__doc__.strip(), function=fn
            )
            self.instant_prompt.literal(key, key.upper() == default.upper())(fn)

    async def cmdloop(self):
        self.stream.nl()
        for opt in self.options.values():
            self.stream.write_line(
                ("magenta", "<"),
                ("green", opt.key.upper()),
                ("magenta", ">"),
                ("green", opt.description),
            )
            self.stream.nl()
        self.stream.nl()
        while True:
            self.stream.write_line(
                ("magenta", "Enter your choice "),
                ("bold yellow", f"[{self.default.upper()}] "),
            )
            try:
                await self.instant_prompt.cmdloop()
                break
            except InvalidSelectionError:
                self.stream.error("Not a valid option")
            #
            # self.stream.out.flush()
            # val = self.stream.stdin.readline().strip()
            # if val == "":
            #     val = self.default
            #
            # val = val.lower()
            #
            # if val not in self.options:
            #     self.stream.error("Not a valid option")
            # else:
            #     opt = self.options[val]
            #     opt.function()
            #     break


async def menu_prompt(stream: Terminal, default: str, options: Tuple[Tuple[str, str]]):
    for cmd, text in options:
        stream.write_line(
            ("magenta", "<"), ("green", cmd), ("magenta", "> "), ("green", text)
        )
        stream.nl()
    stream.nl()

    while True:
        stream.write_line(
            ("magenta", "Enter your choice "), ("bold yellow", f"[{default}] ")
        )
        val = await stream.read_key()
        if val == "":
            val = default

        if val not in [o[0] for o in options]:
            stream.error("Not a valid option")
        else:
            return val


async def amount_prompt(
    stream: Terminal,
    prompt: Sequence[Tuple[str, str]],
    default: int,
    min: int,
    max: int,
):
    _write_prompt_and_default(default, prompt, stream)
    prompt = InstantCmd(stream)

    async def handle_input(txt):
        value = int(txt)
        if value < min or value > max:
            raise ValueError("Number out of range")
        else:
            return value

    prompt.regex("[0-9]+", max_length=len(str(max)))(handle_input)
    prompt.literal("y", default=True)(lambda _: default)
    return await prompt.cmdloop()


def _write_prompt_and_default(default, prompt, stream):
    stream.write_line(*prompt)
    stream.write_line(
        ("magenta", "["), ("yellow", str(default)), ("magenta", "]?"), ("", " ")
    )


async def yesno_prompt(
    stream: Terminal, prompt: Sequence[Tuple[str, str]], default: bool, **kwargs
):
    _write_prompt_and_default("Y" if default else "N", prompt, stream)

    val = await stream.read_key()
    if not val.strip():
        val = default
    return val is True or "y" == val.lower()


class CursorOpType(Enum):
    MOVE = auto()


class CursorOperation:
    def __init__(self, op: CursorOpType, x_mod: int, y_mod: int):
        self.op = op
        self.x_mod = x_mod
        self.y_mod = y_mod


class ANSICursor:
    def __init__(self, value: str) -> None:
        self.value = value
        self.parsed: list[CursorOperation | str] = []

        # Process received text.
        parser = self._parse_corot()
        parser.send(None)  # type: ignore
        for c in value:
            parser.send(c)

    def _parse_corot(self) -> Generator[None, str, None]:
        """
        Coroutine that parses the ANSI escape sequences.
        """

        while True:
            # NOTE: CSI is a special token within a stream of characters that
            #       introduces an ANSI control sequence used to set the
            #       style attributes of the following characters.
            csi = False

            c = yield

            # Check for CSI
            if c == "\x1b":
                # Start of color escape sequence.
                square_bracket = yield
                if square_bracket == "[":
                    csi = True
                else:
                    continue
            elif c == "\x9b":
                csi = True

            if csi:
                # Got a CSI sequence. Color codes are following.
                current = ""
                csi_buffer: list[str] = ["\x1b["]
                params = []

                while True:
                    char = yield
                    csi_buffer.append(char)
                    # Construct number
                    if char.isdigit():
                        current += char

                    # Eval number
                    else:
                        # Limit and save number value
                        params.append(min(int(current or 0), 9999))

                        # Get delimiter token if present
                        if char == ";":
                            current = ""

                        # move pos up
                        elif char == "A":
                            self.parsed.append(
                                CursorOperation(
                                    CursorOpType.MOVE, y_mod=params[0] * -1, x_mod=0
                                )
                            )
                            break
                        # move pos down
                        elif char == "B":
                            self.parsed.append(
                                CursorOperation(
                                    CursorOpType.MOVE, y_mod=params[0], x_mod=0
                                )
                            )
                            break
                        # move pos right
                        elif char == "C":
                            self.parsed.append(
                                CursorOperation(
                                    CursorOpType.MOVE, y_mod=0, x_mod=params[0]
                                )
                            )
                            break
                        # move pos left
                        elif char == "D":
                            self.parsed.append(
                                CursorOperation(
                                    CursorOpType.MOVE, y_mod=0, x_mod=params[0]
                                )
                            )
                            break
                        else:
                            invalid_code = "".join(csi_buffer)
                            # log.debug(f"Unexpected ansi code: {invalid_code}")
                            self.parsed.append(invalid_code)
                            csi_buffer.clear()
                            break
            else:
                # Add current character.
                # NOTE: At this point, we could merge the current character
                #       into the previous tuple if the style did not change,
                #       however, it's not worth the effort given that it will
                #       be "Exploded" once again when it's rendered to the
                #       output.
                self.parsed.append(c)
