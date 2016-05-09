import inspect
import json
import types
from functools import wraps
from typing import Any

import json_types
from colorclass import Color


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
        def inner(self, **kwargs):
            target = getattr(self, sink_property)
            obj = {"type": func.__name__, 'id': autoid.incr()}
            obj.update(kwargs)
            data = json_types.encodes(obj, exclude_none=True, set_as_list=True)
            target(data)

        return inner

    def decorate(cls):
        for name, fn in {name: fn for name, fn in inspect.getmembers(cls)
                         if isinstance(fn, types.FunctionType) and not name.startswith("__")}.items():
            setattr(cls, name, sender(fn))
        return cls

    return decorate


class CallMethodOnEventType:
    def __init__(self, target: Any, prefix="received"):
        self.target = target
        self.prefix = prefix

    def __call__(self, data: str):
        if self.prefix is not None:
            print(Color("{hiblue}{}: {blue}{}").format(self.prefix, data))
        event = json.loads(data)
        event_type = event['type']
        func = getattr(self.target, event_type)
        kwargs = json_types.decode(event, func)
        func(**kwargs)


class AutoIdDict(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.autoid = AutoIncrementId()

    def append(self, val):
        key = self.autoid.incr()
        self[key] = val
        val.id = key
        return val
