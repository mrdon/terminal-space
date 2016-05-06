import inspect
import json
import types
from functools import wraps

import json_types


def methods_to_json(sink_property='target'):
    def sender(func):
        @wraps(func)
        def inner(self, **kwargs):
            target = getattr(self, sink_property)
            obj = {"type": func.__name__}
            obj.update(kwargs)
            data = json_types.encodes(obj, exclude_none=True, set_as_list=True)
            target(data)
        return inner

    def decorate(cls):
        for name, fn in {name: fn for name, fn in inspect.getmembers(cls) if isinstance(fn, types.FunctionType)
                         and not name.startswith("__")}.items():
            setattr(cls, name, sender(fn))
        return cls
    return decorate


def call_type(obj, data):
    event = json.loads(data)
    event_type = event['type']
    func = getattr(obj, event_type)
    kwargs = json_types.decode(event, func)
    func(**kwargs)
