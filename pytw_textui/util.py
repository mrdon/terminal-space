import inspect
import json
import types
import typing
from asyncio import Future
from asyncio import coroutine
from dataclasses import dataclass
from functools import wraps
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Iterable
from typing import Sequence
from typing import Tuple

import json_types


def frag_join(sep: Tuple[str, str], seq: Iterable[Tuple[str, str]]) -> Sequence[
    Tuple[str, str]]:

    first = True
    for frag in seq:
        if not first:
            yield sep
        else:
            first = False
        yield frag


class AutoIncrementId:
    def __init__(self):
        self.id = 1

    def incr(self):
        result = self.id
        self.id += 1
        return result


@dataclass
class WaitForResponse:
    future: Future
    type: typing.Type


class EventBus:
    autoid = AutoIncrementId()

    def __init__(self, *target: Any, context=None, sender: Callable[[str], Awaitable[None]]):
        self.targets = list(target)
        self.context = context
        self.sender = sender
        self.wait_for_ids: typing.Dict[int, WaitForResponse] = {}

    def wire_sending_methods(self, cls):
        out_self = self

        def sender(func):
            @wraps(func)
            async def inner(*_, **kwargs):
                target = out_self.sender
                event_id = out_self.autoid.incr()
                globalns = {
                    'Dict': typing.Dict,
                    'List': typing.List,
                    'Type': typing.Type,
                    'Tuple': typing.Tuple
                }

                hints = typing.get_type_hints(func, localns=self.context, globalns=globalns)
                # breakpoint()
                if hints and "return" in hints:
                    return_type = hints["return"]
                    self.wait_for_ids[event_id] = WaitForResponse(type=return_type, future=Future())
                else:
                    return_type = None

                obj = {"type": func.__name__, 'id': event_id}
                obj.update(kwargs)
                data = json_types.encodes(obj, exclude_none=True, set_as_list=True)
                resp = target(data)
                if not inspect.isawaitable(resp):
                    breakpoint()
                await resp

                if return_type:
                    return await self.wait_for_ids[event_id].future

            return inner

        for name, fn in {name: fn for name, fn in inspect.getmembers(cls)
                         if isinstance(fn, types.FunctionType) and not name.startswith("__")}.items():
            setattr(cls, name, sender(fn))
        return cls

    def append_event_listener(self, target: Any):
        if target is None:
            breakpoint()
        if target not in self.targets:
            self.targets.append(target)

    def remove_event_listener(self, target: Any):
        if target in self.targets:
            self.targets.remove(target)

    async def __call__(self, data: str):
        event = json.loads(data)
        event_type = event['type']
        event_id = event.get('parent_id')

        if event_id:
            args = event["args"]
            waited = self.wait_for_ids[event_id]
            origin = waited.type.__origin__ if hasattr(waited.type, "__origin__") else None
            if origin and issubclass(origin, tuple):
                result = []
                for t in waited.type.__args__:
                    obj = json_types.decode(args.pop(0), t, context=self.context)
                    result.append(obj)
                obj = (*result,)
            else:
                obj = json_types.decode(args.pop(0), waited.type, context=self.context)
            waited.future.set_result(obj)

        else:
            for target in self.targets:
                try:
                    func = getattr(target, event_type)
                except AttributeError:
                    continue

                if func:
                    kwargs = json_types.decode(event, func, context=self.context)
                    return await coroutine(func)(**kwargs)

            raise ValueError(f"No listeners found for {event_type} in {self.targets}")
