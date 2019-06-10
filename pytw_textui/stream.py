import inspect
import re
import sys
from collections import namedtuple
from dataclasses import dataclass
from types import FunctionType, MethodType
from typing import Tuple, NamedTuple, Callable, List, Sequence

from colorclass import Color
from termcolor import colored

from pytw_textui.instant_cmd import InstantCmd, InvalidSelectionError
from pytw_textui.twbuffer import TwBuffer


class Terminal:
    def __init__(self, buffer: TwBuffer):
        self.buffer = buffer
        self.stdin = input

    def write(self, *text: Sequence[Tuple[str,str]]):
        self.buffer.insert_after(text)

    def print(self, text, color=None, bg=None, attrs=None):
        style = ''
        if color:
            style += color
        if bg:
            style += f" bg:{bg}"

        if attrs:
            style += " ".join(attrs)
        self.write((style, text))

    def nl(self, times=1):
        for x in range(times):
            self.write([])

    def error(self, msg):
        self.nl()
        self.print(msg, 'red')
        self.nl()
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
        stream.write(
            row.header.astuple(),
            ('', ' ' * (header_len - len(row.header.text))),
            separator.astuple()
        )
        pad = False
        for item in row.items:
            if pad:
                stream.write('', " " * (header_len + 2))
            else:
                pad = True
            stream.write(item)
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

    def __init__(self, stream: Terminal, default: str, option_order: Tuple[str]):
        self.stream = stream
        self.default = default
        self.options = {}

        self.instant_prompt = InstantCmd(stream)
        for key in option_order:
            key = key.lower()
            fn = getattr(self, "do_{}".format(key))
            self.options[key] = Option(key=key, description=fn.__doc__.strip(), function=fn)
            self.instant_prompt.literal(key, key.upper() == default.upper())(fn)

    def cmdloop(self):
        self.stream.nl()
        for opt in self.options.values():
            self.stream.write(Color("{magenta}<{/magenta}{green}{cmd}{/green}{magenta}>{/magenta} "
                                    "{green}{text}{/green}").format(
                    cmd=opt.key.upper(),
                    text=opt.description
            ))
            self.stream.nl()
        self.stream.nl()
        while True:
            self.stream.write(Color("{magenta}Enter your choice {/magenta}"
                                    "{b}{yellow}[{}]{/yellow}{/b} ").format(self.default.upper()))
            try:
                self.instant_prompt.cmdloop()
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


def menu_prompt(stream: Terminal, default: str, options: Tuple[Tuple[str, str]]):
    for cmd, text in options:
        stream.write(Color("{magenta}<{/magenta}{green}{cmd}{/green}{magenta}>{/magenta} {green}{text}{/green}").format(
                cmd=cmd,
                text=text
        ))
        stream.nl()
    stream.nl()

    while True:
        stream.write(Color("{magenta}Enter your choice {/magenta}{b}{yellow}[{}]{/yellow}{/b} ").format(default))
        stream.out.flush()
        val = stream.stdin.readline().strip()
        if val == '':
            val = default

        if val not in [o[0] for o in options]:
            stream.error("Not a valid option")
        else:
            return val


def amount_prompt(stream: Terminal, prompt: str, default: int, min: int, max: int, **kwargs):
    while True:
        stream.write(Color(prompt).format(**kwargs))
        stream.write(Color(" {magenta}[{/magenta}{yellow}{default}{/yellow}{magenta}]?{/magenta} ")
                     .format(default=default))
        stream.out.flush()
        line = stream.stdin.readline()
        try:
            value = line
            if not value.strip():
                value = default
            value = int(value)
            if value < min or value > max:
                raise ValueError("Number out of range")
            else:
                return value
        except ValueError:
            stream.error("Not a valid number")


def yesno_prompt(stream: Terminal, prompt: str, default: bool, **kwargs):
    stream.write(Color(prompt).format(**kwargs))
    stream.write(Color(" {magenta}[{/magenta}{yellow}{default}{/yellow}{magenta}]?{/magenta} ")
                 .format(default='Y' if default else 'N'))
    stream.out.flush()
    val = stream.stdin.readline().strip()
    if not val:
        val = default
    return val is True or 'y' == val.lower()
