import json
import os
from functools import lru_cache

LITERALS = {"TRUE": True, "FALSE": False, "NULL": None}


class ENVIRON(dict):
    """
    The configuration environment.
    """

    def __missing__(self, key):
        data = os.environ.get(key, "")
        return _value(data)

    def __getattr__(self, item):
        if item.isupper() and not item.startswith("_"):
            return self[item]
        raise AttributeError(item)


@lru_cache(128)
def _value(data):
    if not data:
        return None
    try:
        return LITERALS[data]
    except KeyError:
        pass
    try:
        return json.loads(data)
    except ValueError:
        return data


env = ENVIRON()
