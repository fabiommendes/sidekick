from collections.abc import MutableMapping
from functools import wraps


class CachedDict(MutableMapping):
    @classmethod
    def cached(cls, func=None, **kwargs):
        """
        A function that receives
        """

        if func is None:
            return lambda f: cls.cached(f, **kwargs)

        cache = cls(kwargs.pop("data", ()), default=func, **kwargs)

        @wraps(func)
        def func(*args):
            if len(args) != 1:
                return cache[args]
            return cache[args[0]]

        return func

    def __init__(self, file=None, default=None, ttl=None, ttl_policy="default"):
        self._data = {}
        self.default = default
        self.ttl = ttl
        self.ttl_policy = ttl_policy

    def __len__(self):
        ...

    def __iter__(self):
        ...

    def __getitem__(self, item):
        ...

    def __setitem__(self, item, value):
        ...

    def __delitem__(self, key):
        ...

    def __default__(self, key):
        ...

    def get_handle(self, key):
        ...

    def get_cached(self, key):
        ...


class CacheHandle:
    def __init__(self, owner, key, value, expiration):
        self._owner = owner
        self.key = key
        self.value = value
        self.expiration = expiration

    def clear(self):
        ...

    def update(self):
        ...

    def update_background(self):
        ...
