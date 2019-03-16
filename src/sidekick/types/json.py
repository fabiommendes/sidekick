import json as _json

from .record import record

__all__ = ["JSONEncoder", "dump", "dumps", "load", "loads"]


class JSONEncoder(_json.JSONEncoder):
    def default(self, o):
        try:
            method = o.__json__
        except AttributeError:
            return super().default(o)
        else:
            return method()


#
# Wrapped json functions
#
def dumps(*args, **kwargs):
    kwargs.setdefault("cls", JSONEncoder)
    return _json.dumps(*args, **kwargs)


def dump(*args, **kwargs):
    kwargs.setdefault("cls", JSONEncoder)
    return _json.dump(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs.setdefault("object_hook", record)
    return _json.loads(*args, **kwargs)


def load(*args, **kwargs):
    kwargs.setdefault("object_hook", record)
    return _json.load(*args, **kwargs)
