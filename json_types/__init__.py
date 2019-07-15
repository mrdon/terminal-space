import inspect
import json
import typing
from enum import Enum
from functools import partial


class TypedEncoder(json.JSONEncoder):
    def __init__(self, *args, exclude_none=False, set_as_list=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_none = exclude_none
        self.set_as_list = set_as_list

    def default(self, o):

        if isinstance(o, Enum):
            return o.name

        result = o.__dict__
        if self.set_as_list:
            result = {
                k: v if not isinstance(v, set) else list(v)
                for k, v in o.__dict__.items()
            }

        if self.exclude_none:
            result = {k: v for k, v in result.items() if v is not None}

        return result


def decodes(data, cls, **kwargs):
    result = json.loads(data, **kwargs)
    return decode(result, cls)


def decode(data: dict, cls, context=None, **kwargs):
    return _recursive_decode(data, cls, context)


def encodes(obj, exclude_none=False, set_as_list=False, func_kwargs=None, **kwargs):
    return json.dumps(
        obj,
        cls=partial(
            TypedEncoder, set_as_list=set_as_list, exclude_none=exclude_none, **kwargs
        ),
    )


def _recursive_decode(obj, cls, context):

    origin = cls.__origin__ if hasattr(cls, "__origin__") else None
    is_class = False if origin else inspect.isclass(cls)
    if obj is None:
        return obj
    if cls in (str, int, float, bool):
        return obj
    elif is_class and issubclass(cls, Enum):
        return cls[obj]
    elif origin:
        ptypes = cls.__args__
        if str(origin) == "typing.Union":
            if ptypes:
                for ptype in ptypes:
                    try:
                        return _recursive_decode(obj, ptype, context)
                    except AttributeError:
                        pass
        if issubclass(origin, set):
            if ptypes:
                return {_recursive_decode(x, ptypes[0], context) for x in obj}
        elif issubclass(origin, list):
            if ptypes:
                return [_recursive_decode(x, ptypes[0], context) for x in obj]
        elif issubclass(origin, dict):
            if ptypes:
                return {
                    k: _recursive_decode(v, ptypes[1], context) for k, v in obj.items()
                }
        elif issubclass(origin, tuple):
            if ptypes:
                return (
                    _recursive_decode(obj[0], ptypes[0], context),
                    _recursive_decode(obj[1], ptypes[1], context),
                )

    elif is_class:
        try:
            globalns = {"Dict": typing.Dict, "List": typing.List, "Tuple": typing.Tuple}
            hints = typing.get_type_hints(
                cls.__init__, localns=context, globalns=globalns
            )
        except AttributeError:
            raise Exception("Unable to decode class {}".format(cls))
    else:
        hints = typing.get_type_hints(cls, context)

    kwargs = {}
    for prop, ptype in hints.items():
        val = obj.get(prop)
        kwargs[prop] = _recursive_decode(val, ptype, context)

    if not is_class:
        result = kwargs
    else:
        if "return" in kwargs:
            del kwargs["return"]
        result = cls(**kwargs)
    return result
