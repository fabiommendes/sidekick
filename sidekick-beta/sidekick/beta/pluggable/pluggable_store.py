import shelve
from contextlib import contextmanager
from functools import lru_cache
from typing import Callable, MutableMapping, Union

NO_OP = lambda: None
FORCE_STORE_CONSTRUCTOR = []
STORE_CONSTRUCTOR_ALIASES = {}


class Store(MutableMapping):
    """
    Store is a mutable mapping that saves data on a persistent location such
    as the hard drive or a database.

    Differently from a Shelf, operations are only flushed to the persistent
    store after calling sync() or close(). Store instances also have an
    `is_closed` attribute and can be used as context managers.

    This interface do not dictates how stores are constructed. The store()
    function offers an uniform interface that declares a pluggable store that
    can be easily replaced by some external configuration.
    """

    @property
    def is_closed(self):
        return isinstance(self._store, _ClosedDict)

    def __init__(self, store):
        self._store = store
        self._cache = {}
        self._remove_later = set()

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        used = set()
        yield from self._cache
        yield from (k for k in self._store if k not in used)

    def __getitem__(self, k):
        try:
            return self._cache[k]
        except KeyError:
            pass
        try:
            return self._store[k]
        except KeyError:
            pass

    def __setitem__(self, k, value):
        self._remove_later.discard(k)
        self._cache[k] = value

    def __delitem__(self, key):
        try:
            del self._cache[key]
        except KeyError:
            self._remove_later.add(key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def flush(self):
        """
        Flush information to the persistent layer.
        """
        for k, v in self._cache.items():
            self._store[k] = v
        for k in self._remove_later:
            try:
                del self._store[k]
            except KeyError:
                pass
        self._cache.clear()
        self._remove_later.clear()
        getattr(self._store, "sync", NO_OP)()

    def close(self):
        """
        Flushes data and closes store so it cannot be used anymore.
        """
        self.flush()
        getattr(self._store, "close", NO_OP)()
        self._store = self._cache = _ClosedDict()


class DbmStore(Store):
    """
    A store that persists to a dbm database.
    """

    def __init__(self, filename, flag="c", protocol=-1):
        super().__init__(shelve.open(filename, flag, protocol))


class _ClosedDict(MutableMapping):
    def _closed(self, *args):
        raise ValueError("invalid operation on closed store")

    __iter__ = __len__ = __getitem__ = __setitem__ = __delitem__ = keys = _closed

    def __repr__(self):
        return "<Closed Dictionary>"


def store(key) -> Store:
    """
    Creates a generic store from key.

    Stores are mappings that can be persisted in the filesystem or a database.

    Args:
        key:
    """

    if FORCE_STORE_CONSTRUCTOR:
        constructor = FORCE_STORE_CONSTRUCTOR[-1](key)
    else:
        constructor = store_constructor(key)
    return constructor()


@contextmanager
def force_store(constructor: Union[str, Callable[[], Store]]):
    """
    A context manager that forces the utilization of an specific type of
    constructor.

    Usage:
        >>> with force_store('memory'):
        ...     db = store('foo')  # do not save to disc
    """
    if isinstance(constructor, str):
        try:
            fn = STORE_CONSTRUCTOR_ALIASES[constructor]
        except KeyError:
            raise ValueError(f'unknown constructor alias: "{constructor}"')
    else:
        fn = lambda key: constructor

    FORCE_STORE_CONSTRUCTOR.append(fn)
    yield constructor
    FORCE_STORE_CONSTRUCTOR.pop()


@lru_cache(128)
def store_constructor(key) -> Callable[[], Store]:
    """
    Returns a store constructor for the given key.

    The constructor is simply a function that takes no arguments and return a
    store instance.

    Args:
        key: The key used to identify the constructor.
    """

    # Fall back to a dbm shelf in the current directory
    return lambda: DbmStore(key + ".dbm")


#
# Update list of store constructors
#
STORE_CONSTRUCTOR_ALIASES.update(
    memory=lambda key: lambda: Store({}), dbm=lambda key: lambda: DbmStore(key + ".dbm")
)
