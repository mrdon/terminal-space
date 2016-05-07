import re
import sys
from typing import Tuple

from colorclass import Color
from termcolor import colored


class TerminalOutput:
    def __init__(self, out=None):
        if out is None:
            out = sys.stdout
        self.out = out

    def write(self, text):
        self.out.write(text)

    def print(self, text, color=None, on_color=None, attrs=None):
        self.out.write(colored(text, color=color, on_color=on_color, attrs=attrs))

    def nl(self, times=1):
        for x in range(times):
            self.out.write('\n')

    def error(self, msg):
        self.nl()
        self.print(msg, 'red')
        self.nl()
        self.nl()


def print_grid(stream: TerminalOutput, data, separator):
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


def print_action(stream: TerminalOutput, title):
        stream.nl()
        stream.print("<{}>".format(title), 'white', on_color='on_blue', attrs=['bold'])
        stream.nl(2)


def print_menu(stream: TerminalOutput, default: str, options: Tuple[Tuple[str, str]]):
    for cmd, text in options:
        stream.write(Color("{magenta}<{/magenta}{green}{cmd}{magenta}>{/magenta} {green}{text}{/green}").format(
            cmd=cmd,
            text=text
        ))
        stream.nl()
    stream.nl()

    return Color("{magenta}Enter your choice {/magenta}{hiyellow}[{}]{/hiyellow} ").format(default)
