from asyncio import Queue
from asyncio import Queue
from dataclasses import astuple
from dataclasses import dataclass
from typing import Iterable
from typing import Tuple, Callable, List, Sequence

from prompt_toolkit import ANSI
from prompt_toolkit.formatted_text import to_formatted_text

from pytw_textui.instant_cmd import InstantCmd, InvalidSelectionError
from pytw_textui.twbuffer import TwBuffer


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
        style = ''
        if color:
            style += color
        if bg:
            style += f" bg:{bg}"

        if attrs:
            style += " "
            style += " ".join(attrs)

        lines = text.split(r'\n|\r|\r\n')
        self.write_lines(*[[(style, line)] for line in lines])

    def nl(self, times=1):
        for x in range(times):
            self.write_lines([], [])

    def error(self, msg):
        self.nl()
        self.print(msg, 'red')
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
            ('', ' ' * (header_len - len(row.header.text))),
            astuple(separator)
        )
        pad = False
        for item in row.items:
            if pad:
                stream.write_line(('', " " * (header_len + 2)))
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
            self.options[key] = Option(key=key, description=fn.__doc__.strip(),
                                       function=fn)
            self.instant_prompt.literal(key, key.upper() == default.upper())(fn)

    async def cmdloop(self):
        self.stream.nl()
        for opt in self.options.values():
            self.stream.write_line(
                ('magenta', '<'),
                ('green', opt.key.upper()),
                ('magenta', '>'),
                ('green', opt.description)
            )
            self.stream.nl()
        self.stream.nl()
        while True:
            self.stream.write_line(
                ('magenta', 'Enter your choice '),
                ('bold yellow', f'[{self.default.upper()}] ')
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
            ('magenta', '<'),
            ('green', cmd),
            ('magenta', '> '),
            ('green', text)
        )
        stream.nl()
    stream.nl()

    while True:
        stream.write_line(
            ('magenta', 'Enter your choice '),
            ('bold yellow', f'[{default}] ')
        )
        val = await stream.read_key()
        if val == '':
            val = default

        if val not in [o[0] for o in options]:
            stream.error("Not a valid option")
        else:
            return val


async def amount_prompt(stream: Terminal, prompt: Sequence[Tuple[str, str]], default: int, min: int, max: int):
    _write_prompt_and_default(default, prompt, stream)
    prompt = InstantCmd(stream)

    async def handle_input(txt):
        value = int(txt)
        if value < min or value > max:
            raise ValueError("Number out of range")
        else:
            return value

    prompt.regex('[0-9]+', max_length=len(str(max)))(handle_input)
    prompt.literal('y', default=True)(lambda _: default)
    return await prompt.cmdloop()


def _write_prompt_and_default(default, prompt, stream):
    stream.write_line(*prompt)
    stream.write_line(
        ('magenta', '['),
        ('yellow', str(default)),
        ('magenta', ']?'),
        ('', ' ')
    )


async def yesno_prompt(stream: Terminal, prompt: Sequence[Tuple[str, str]], default: bool, **kwargs):
    _write_prompt_and_default('Y' if default else 'N', prompt, stream)

    val = await stream.read_key()
    if not val.strip():
        val = default
    return val is True or 'y' == val.lower()
