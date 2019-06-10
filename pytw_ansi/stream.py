import inspect
import re
import sys
from collections import namedtuple
from types import FunctionType, MethodType
from typing import Tuple, NamedTuple, Callable

from colorclass import Color
from termcolor import colored

from pytw_ansi.instant_cmd import InstantCmd, InvalidSelectionError


class Terminal:
    def __init__(self, out=None, input=None):
        if out is None:
            out = sys.stdout
        if input is None:
            input = sys.stdin
        self.out = out
        self.stdin = input

    def write(self, text):
        self.out.write(text)
        self.out.flush()

    def print(self, text, color=None, on_color=None, attrs=None):
        self.out.write(colored(text, color=color, on_color=on_color, attrs=attrs))
        self.out.flush()

    def nl(self, times=1):
        for x in range(times):
            self.out.write('\r\n')

    def error(self, msg):
        self.nl()
        self.print(msg, 'red')
        self.nl()
        self.nl()


def print_grid(stream: Terminal, data, separator):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    header_len = max(len(ansi_escape.sub('', h[0])) for h in data) + 1
    for header, row in data:
        text = ansi_escape.sub('', header)
        stream.write(header)
        stream.write(' ' * (header_len - len(text)))
        stream.write(separator)
        pad = False
        for line in row:
            if pad:
                stream.write(" " * (header_len + 2))
            else:
                pad = True
            stream.write(line)
            stream.nl()


def print_action(stream: Terminal, title):
    stream.nl()
    stream.print(Color("{bgblue}{white}<{}>{/bgblue}{/white}").format(title))
    stream.nl(2)


Option = NamedTuple('Option', [('key', str), ('description', str), ('function', Callable[[], None])])


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
