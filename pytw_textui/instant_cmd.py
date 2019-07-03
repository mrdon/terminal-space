from __future__ import annotations

import re
from inspect import isawaitable
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:
    from pytw_textui import Terminal


class Matcher:
    def __init__(self, matcher: Callable[[str], bool], default=False, max_length=0):
        self.default = default
        self.func = matcher
        self.max_length = max_length

    def __call__(self, text):
        return self.func(text)


class InvalidSelectionError(Exception):
    pass


class InstantCmd:

    def __init__(self, out: Terminal):
        self.matchers: Dict[Matcher, Callable[[str], Any]] = {}
        self.out = out

    def regex(self, pattern, default=False, max_length=0):
        return self.matcher(matcher=lambda txt: re.match(pattern, txt) is not None,
                            default=default,
                            max_length=max_length)

    def literal(self, char, default=False):
        return self.matcher(matcher=lambda txt: txt.upper() == char.upper(),
                            default=default,
                            max_length=len(char))

    def matcher(self, matcher: Callable[[str], bool], default: bool, max_length: int):
        def outer(func: Callable[[str], Any]):
            self.matchers[Matcher(
                matcher=matcher,
                default=default,
                max_length=max_length)] = func

            async def inner(*args, **kwargs):
                result = func(*args, **kwargs)
                if isawaitable(result):
                    result = await result

                return result

            return inner

        return outer

    async def cmdloop(self):
        buffer = []

        while True:
            is_end = False
            char = await self.out.read_key()
            # print(f"len: {len(char)} ord: {ord(char)}:", end='')
            if len(char) > 1:
                continue
            elif ord(char) == 127 and buffer:
                buffer = buffer[:-1]
                self.out.write(chr(8))
            elif char == '\n' or char == '\r':
                is_end = True
            else:
                self.out.write_line(('', char))
                buffer.append(char)

            line = "".join(buffer)
            matches = {k: v for k, v in self.matchers.items() if k(line)}

            if len(matches) == 1:
                matcher, func = next(iter(matches.items()))
                if matcher.max_length == len(buffer) or is_end:
                    return await func(line)
            elif is_end:
                func = next(v for k, v in self.matchers.items() if k.default)
                return await func(line)
            elif not len(matches):
                raise InvalidSelectionError()





# m = InstantCmd()
#
# @m.literal('f', default=True)
# def do_f(value):
#     return f"f: {value}"
#
# @m.literal('p')
# def do_p(value):
#     return f"p: {value}"
#
# @m.regex(r"[0-9]+", max_length=4)
# def do_num(value):
#     return f"num: {value}"
#
# result = m.cmdloop()
# print(f"result: {result}")