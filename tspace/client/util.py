import inspect
import json
import types
import typing
from asyncio import Future
from dataclasses import dataclass
from functools import wraps
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Iterable
from typing import Sequence
from typing import Tuple

from tspace import common
from tspace.common.rpc import ClientAndServer


def frag_join(
    sep: Tuple[str, str], seq: Iterable[Tuple[str, str]]
) -> Sequence[Tuple[str, str]]:

    first = True
    for frag in seq:
        if not first:
            yield sep
        else:
            first = False
        yield frag


class EventBus:
    def __init__(
        self, target: Any, *, context=None, sender: Callable[[str], Awaitable[None]]
    ):

        self._api = ClientAndServer(sender)
        self._api.register_methods(target)
        self.context = context

    def wire_sending_methods(self, cls):

        return self._api.build_client(cls)

    def append_event_listener(self, target: Any):
        if target is None:
            breakpoint()

        self._api.register_methods(target)

    def remove_event_listener(self, target: Any):
        self._api.unregister_methods(target)

    async def __call__(self, data: str):
        event = json.loads(data)
        event_type = event["type"]
        event_id = event.get("parent_id")

        if event_id:
            args = event["args"]
            waited = self.wait_for_ids[event_id]
            origin = (
                waited.type.__origin__ if hasattr(waited.type, "__origin__") else None
            )
            if origin and issubclass(origin, tuple):
                result = []
                for t in waited.type.__args__:
                    obj = common.decode(args.pop(0), t, context=self.context)
                    result.append(obj)
                obj = (*result,)
            else:
                obj = common.decode(args.pop(0), waited.type, context=self.context)
            waited.future.set_result(obj)

        else:
            for target in self.targets:
                try:
                    func = getattr(target, event_type)
                except AttributeError:
                    continue

                if func:
                    kwargs = common.decode(event, func, context=self.context)
                    return await sync_to_async(func)(**kwargs)

            raise ValueError(f"No listeners found for {event_type} in {self.targets}")


def sync_to_async(func: Callable):

    if inspect.iscoroutinefunction(func):
        return func

    @wraps(func)
    async def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return inner
