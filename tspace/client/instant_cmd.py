import asyncio
import re
from asyncio import Future
from inspect import isawaitable
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

from .util import sync_to_async

from .terminal import Terminal
from ..common.errors import TSpaceError


class Matcher:
    def __init__(
        self,
        matcher: Callable[[str], bool],
        default=False,
        max_length=0,
        validator=None,
    ):
        self.default = default
        if validator is None:
            validator = lambda _: True
        self.validator: Callable[[str], bool] = validator
        self.func = matcher
        self.max_length = max_length

    def __call__(self, text):
        return self.validator(text) and self.func(text)


class InvalidSelectionError(Exception):
    pass


class InstantCmd:
    def __init__(
        self, out: Terminal, echo_to_fragment: Callable[[str], tuple[str, str]] = None
    ):
        self.matchers: Dict[Matcher, Callable[[str], Any]] = {}
        self.out = out
        self.echo_to_fragment = (
            echo_to_fragment if echo_to_fragment else self._default_echo_to_fragment
        )

    @staticmethod
    def _default_echo_to_fragment(text: str) -> tuple[str, str]:
        return ("", text)

    def regex(
        self,
        pattern,
        default=False,
        max_length=0,
        validator: Optional[Callable[[str], bool]] = None,
    ):
        return self.matcher(
            matcher=lambda txt: re.match(pattern, txt) is not None,
            default=default,
            max_length=max_length,
            validator=validator,
        )

    def literal(
        self, char, default=False, validator: Optional[Callable[[str], bool]] = None
    ):
        return self.matcher(
            matcher=lambda txt: txt.upper() == char.upper(),
            default=default,
            max_length=len(char),
            validator=validator,
        )

    @classmethod
    async def yes_no(cls, out: Terminal, default: bool = True):
        def validator(txt):
            return txt.upper() in ("Y", "N")

        out.write_line(
            ("yellow", " (Y/N) "),
            ("green", f"[{'Y' if default else 'N'}]? "),
        )

        result = Future()
        cmd = cls(out, echo_to_fragment=lambda x: ("cyan bold", x.upper()))
        cmd.literal("Y", validator=validator)(lambda _: result.set_result(True))
        cmd.literal("N", validator=validator)(lambda _: result.set_result(False))
        cmd.literal("")(lambda _: result.set_result(default))

        task = asyncio.create_task(cmd.cmdloop())
        await task

        return result.result()

    def matcher(
        self,
        matcher: Callable[[str], bool],
        default: bool,
        max_length: int,
        validator: Optional[Callable[[str], bool]] = None,
    ):
        def outer(func: Callable[[str], Any]):
            self.matchers[
                Matcher(
                    matcher=matcher,
                    default=default,
                    max_length=max_length,
                    validator=validator,
                )
            ] = func

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
            should_write = False
            char = await self.out.read_key()
            # print(f"len: {len(char)} ord: {ord(char)}:", end='')
            if len(char) > 1:
                continue
            elif ord(char) == 127 and buffer:
                buffer = buffer[:-1]
                self.out.backspace(1)
                continue
            elif char == "\n" or char == "\r":
                is_end = True
            else:
                should_write = True
                buffer.append(char)

            line = "".join(buffer)
            matches = {k: v for k, v in self.matchers.items() if k(line)}

            if len(matches) == 1:
                matcher, func = next(iter(matches.items()))
                if should_write:
                    self.out.write_line(self.echo_to_fragment(char))
                if matcher.max_length == len(buffer) or is_end:
                    return await sync_to_async(func)(line)
            elif is_end:
                try:
                    func = next(v for k, v in self.matchers.items() if k.default)
                except StopIteration:
                    buffer.clear()
                    continue

                if should_write:
                    self.out.write_line(("", char))
                try:
                    return await sync_to_async(func)(line)
                except TSpaceError as e:
                    self.out.error(e.message)
            elif not len(matches):
                buffer.pop()
            elif should_write:
                self.out.write_line(("", char))


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
