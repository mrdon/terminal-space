import inspect
import json
import types
from functools import wraps
from typing import Any

import json_types


class AutoIncrementId:
    def __init__(self):
        self.id = 1

    def incr(self):
        result = self.id
        self.id += 1
        return result


def methods_to_json(sink_property='target'):
    autoid = AutoIncrementId()

    def sender(func):
        @wraps(func)
        async def inner(self, **kwargs):
            target = getattr(self, sink_property)
            obj = {"type": func.__name__, 'id': autoid.incr()}
            obj.update(kwargs)
            data = json_types.encodes(obj, exclude_none=True, set_as_list=True)
            resp = target(data)
            if not inspect.isawaitable(resp):
                breakpoint()
            await resp

        return inner

    def decorate(cls):
        for name, fn in {name: fn for name, fn in inspect.getmembers(cls)
                         if isinstance(fn, types.FunctionType) and name.startswith("on_")}.items():
            setattr(cls, name, sender(fn))
        return cls

    return decorate


class CallMethodOnEventType:
    def __init__(self, *target: Any, context=None):
        self.targets = list(target)
        self.context = context

    def append(self, target: Any):
        if target is None:
            breakpoint()
        if target not in self.targets:
            self.targets.append(target)

    def remove(self, target: Any):
        if target in self.targets:
            self.targets.remove(target)

    async def __call__(self, data: str):
        event = json.loads(data)
        event_type = event['type']
        for target in self.targets:
            try:
                func = getattr(target, event_type)
            except AttributeError:
                continue

            if func:
                kwargs = json_types.decode(event, func, context=self.context)
                kwargs["parent_id"] = event["id"]
                return await func(**kwargs)

        raise ValueError(f"No listeners found for {event_type} in {self.targets}")


class AutoIdDict(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.autoid = AutoIncrementId()

    def append(self, val):
        key = self.autoid.incr()
        self[key] = val
        val.id = key
        return val
