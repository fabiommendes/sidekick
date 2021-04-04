import datetime
from functools import wraps, lru_cache
from time import time
from typing import Union, Type, Sequence, NamedTuple, Callable

import joblib

from ..functions import curry
from ..seq import as_seq

MemoryProvider = Callable[[str], joblib.Memory]
MEMORY_PROVIDER: MemoryProvider = None
PERIOD_ALIASES = {
    "day": datetime.timedelta(days=1),
    "week": datetime.timedelta(days=7),
    **{"{n}h": datetime.timedelta(hours=n) for n in range(1, 25)},
}


class Result(NamedTuple):
    value: object
    time: float


# References and similar projects


# - http://joblib.readthedocs.io/
# - https://cachetools.readthedocs.io/
# - https://github.com/lonelyenvoy/python-memoization


# noinspection PyUnresolvedReferences
@curry(2)
def ttl_cache(key, fn, *, timeout=6 * 3600, memory=None, **cache_kwargs):
    """
    Decorator that creates a cached version of function that stores results
    in disk for the given timeout (in seconds).

    Args:
        key:
            Name of memory cache used to store computed results.
        timeout:
            Maximum time the item is kept in cache (in seconds).
        memory:
            A provider of Memory objects. The provider is a function that
            receives a key and returns a joblib Memory object.

    Returns:
        A decorated function that stores items in the given cache for the given
        timeout.

    Examples:
        >>> @ttl_cache("my-cache", timeout=3600)
        ... def expensive_function(url):
        ...     # Some expensive function, possibly touching the internet...
        ...     response = requests.get(url)
        ...     ...
        ...     return pd.DataFrame(response.json())

    Notes:
        The each pair of (cache name, function name) must be unique. It cannot
        decorate multiple lambda functions or callable objects with no __name__
        attribute.
    """
    mem = normalize_memory(memory, key)

    # We need to wrap fn into another decorator to preserve its name and avoid
    # confusion with joblib's cache. This function just wraps the result of fn
    # int a Result() instance with the timestamp as info.
    @mem.cache(**cache_kwargs)
    @wraps(fn)
    def cached(*args, **kwargs):
        return Result(fn(*args, **kwargs), time())

    # Now the decorated function asks for the result in the cache, checks
    # if it is within the given timeout and return or recompute the value
    @wraps_with_cache(fn, cached)
    def decorated(*args, **kwargs):
        mem_item = cached.call_and_shelve(*args, **kwargs)
        result: Result = mem_item.get()
        if result.time + timeout < time():
            mem_item.clear()
            result = cached(*args, **kwargs)
        return result.value

    decorated.clear = mem.clear
    decorated.prune = mem.reduce_size

    return decorated


@curry(2)
def disk_cache(key, fn, memory=None):
    """
    A simple in-disk cache.

    Can be called as ``disk_cache(key, fn)``, to decorate a function or as as
    decorator in ``@disk_cache(key)``.
    """
    return normalize_memory(memory, key).cache(fn)


@curry(2)
def period_cache(
        key: str,
        fn: callable,
        *,
        period: Union[str, int, datetime.timedelta],
        memory=None,
        fallback: Sequence[Type[Exception]] = None,
):
    """
    Keeps value in cache within n intervals of the given time delta.

    Args:
        key:
            Name of memory cache used to store computed results.
        fn:
            The decorated function.
        period:
            Time period in which the cache expires. Can be given as a timedelta,
            a integer (in seconds) or a string in the set {'day', 'week', '1h',
            '2h', ..., '24h'}.

            Other named periods can be registered using the :func:`register_period`
            function.
        memory:
            A provider of Memory objects. The provider is a function that
            receives a key and returns a joblib Memory object.
        fallback:
            If an exception or list of exceptions, correspond to the kinds of
            errors that triggers the cache to check previously stored responses.
            There is nothing that guarantees that the old values will still
            be present, but it gives a second attempt that may hit the cache
            or call the function again.

    Examples:
        >>> @period_cache("numeric", period="day")
        ... def fn(x):
        ...     print('Doing really expensive computation...')
        ...     return ...
    """

    # Select the main method to decorate the cached function
    mem = normalize_memory(memory, key)

    # Reads a period and return a function that return increments of the period
    # according to the current time. This logic is encapsulated into the key()
    # function.
    date = today()
    ref_time = datetime.datetime(date.year, date.month, date.day).timestamp()
    if isinstance(period, str):
        period = PERIOD_ALIASES[period].seconds
    period = int(period)
    get_time = time
    key = lambda: int(get_time() - ref_time) // period

    # The main cached function. This is stored only internally and the function
    # exposed to the user fixes the _cache_bust and _recur parameters to the
    # correct values.
    fallback = tuple(as_seq(fallback)) if fallback else ImpossibleError

    @mem.cache
    def cached(_cache_bust, _recur, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except fallback:
            if _recur > 0:
                return cached(_cache_bust - 1, _recur - 1, *args, **kwargs)
            raise

    # Save function
    @wraps_with_cache(fn, cached)
    def decorated(*args, **kwargs):
        return cached(key(), 1, *args, **kwargs)

    return decorated


class ImpossibleError(Exception):
    """
    It is an error to raise this exception, do not use it!
    """


def wraps_with_cache(fn, cache=None):
    """
    Like functools.wraps, but also copy the cache methods created either
    by lru_cache or by joblib.Memory.cache.
    """
    cache = cache or fn
    wrapped = wraps(fn)
    for attr in ("cache_info", "clear_cache"):
        if hasattr(cache, attr):
            setattr(wrapped, attr, getattr(cache, attr))
    return wrapped


def normalize_memory(memory, key: str) -> joblib.Memory:
    """
    Return the joblib's Memory object with the given name.
    """
    if isinstance(memory, joblib.Memory):
        return memory
    if memory is None:
        memory_provider = get_global_memory_provider()
    else:
        memory_provider = memory
    return memory_provider(key)


def get_global_memory_provider():
    """
    Return the global memory provider.
    """
    if MEMORY_PROVIDER is None:
        raise RuntimeError('must initialize the global memory provider before continuing')
    return MEMORY_PROVIDER


def set_global_memory_provider(func: MemoryProvider):
    """
    Set the global memory provider function.
    """
    global MEMORY_PROVIDER
    MEMORY_PROVIDER = func


def today(n=0) -> datetime.date:
    """
    Return the date today.
    """
    date = datetime.datetime.now().date()
    if n:
        return date + datetime.timedelta(days=n)
    return date
