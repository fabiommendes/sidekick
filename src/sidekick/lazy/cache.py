# TODO: integrate https://cachetools.readthedocs.io/en/stable/
from functools import wraps

from sidekick import record

_NOT_GIVEN = object()


def single_cache(maxsize=256, mode='lru'):
    def decorator(func):
        cache = {}

        if mode == 'lrc':
            @wraps(func)
            def decorated(x):
                try:
                    return cache[x]
                except KeyError:
                    cache[x] = result = func(x)
                    if len(cache) > maxsize:
                        del cache[next(iter(cache))]
                    return result
        else:
            last = [_NOT_GIVEN, _NOT_GIVEN, _NOT_GIVEN]
            first = _NOT_GIVEN

            @wraps(func)
            def decorated(x):
                nonlocal last, first
                try:
                    result, prev, next = lst = cache[x]
                except KeyError:
                    result = func(x)
                    cache[x] = last = [result, last[0], _NOT_GIVEN]

                    # if full:
                    #     _, _, first = cache.pop(first)
                    if len(cache) > maxsize:
                        _, _, first = cache.pop(first)
                        # full = len(cache) > maxsize

                else:
                    if next is not _NOT_GIVEN:
                        cache[prev][2] = next
                        cache[next][1] = prev
                        last[2] = lst
                        last = lst

                return result

        def cache_clear(key=_NOT_GIVEN):
            # nonlocal full
            if key is _NOT_GIVEN:
                cache.clear()
                # keys.clear()
            else:
                # try:
                #     # keys.remove(key)
                # except ValueError:
                #     pass
                cache.pop(key, None)
            # full = False

        def cache_info():
            return record(maxsize=maxsize, currsize=len(cache), hits=None, misses=None)

        decorated.cache_clear = cache_clear
        decorated.cache_info = cache_info
        decorated.__wrapped__ = func
        decorated.__cache = cache
        return decorated

    return decorator
