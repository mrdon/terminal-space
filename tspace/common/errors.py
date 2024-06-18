import importlib
import inspect


class TSpaceError(Exception):
    code = 32010

    def __init__(self, message: str | None = None):
        self.message = message
        self.data = None


class InvalidActionError(TSpaceError):
    code = 32011


def from_code(code: int, message: str | None) -> TSpaceError:
    mod = importlib.import_module("tspace.common.errors", package=None)
    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and obj.code == code:
            return obj(message)

    return TSpaceError(message)
