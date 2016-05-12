import re
import sys
from typing import Tuple, NamedTuple, Callable

from colorclass import Color
from termcolor import colored


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

    def print(self, text, color=None, on_color=None, attrs=None):
        self.out.write(colored(text, color=color, on_color=on_color, attrs=attrs))

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

        for key in option_order:
            key = key.lower()
            fn = getattr(self, "do_{}".format(key))
            self.options[key] = Option(key=key, description=fn.__doc__.strip(), function=fn)

    def cmdloop(self):
        self.stream.nl()
        for opt in self.options.values():
            self.stream.write(Color(
                "{invis}input={{\"value\": \"{cmd}\"}}{/invis}{magenta}<{/magenta}{green}{cmd}{/green}{magenta}>{/magenta}"
                "{invis}<end>{/invis}"
                " {green}{text}{/green}").format(
                    cmd=opt.key.upper(),
                    text=opt.description
            ))
            self.stream.nl(2)
        self.stream.nl()

        while True:
            self.stream.write(Color("{magenta}Enter your choice {/magenta}"
                                    "{invis}input={{\"value\": \"{cmd}\"}}{/invis}{yellow}[{cmd}]{/yellow}{invis}<end>{/invis} ").format(cmd=self.default.upper()))
            self.stream.out.flush()
            val = self.stream.stdin.readline().strip()
            if val == "":
                val = self.default

            val = val.lower()

            if val not in self.options:
                self.stream.error("Not a valid option")
            else:
                opt = self.options[val]
                opt.function()
                break


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
    # with open('assets/boss1.ans', encoding="cp437") as f:
    #     data = f.read()
    #     stream.write(data)

    stream.write(Color("{invis}input={\"value\": \"Y\"}{/invis}"
                       "{magenta}<{/magenta}{green}Y{/green}{magenta}>{/magenta}"
                       " {green}Yes{/green}"
                       "{invis}<end>{/invis}  "))
    stream.write(Color(prompt).format(**kwargs))
    stream.write(Color("{invis}input={\"value\": \"N\"}{/invis}"
                       "{magenta}<{/magenta}{green}Y{/green}{magenta}>{/magenta}"
                       " {green}No{/green}"
                       "{invis}<end>{/invis}"))
    stream.write(Color(" {magenta}[{/magenta}{yellow}{default}{/yellow}{magenta}]?{/magenta} ")
                 .format(default='Y' if default else 'N'))
    stream.out.flush()
    val = stream.stdin.readline().strip()
    if not val:
        val = default
    return val is True or 'y' == val.lower()
