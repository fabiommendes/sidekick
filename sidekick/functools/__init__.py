import functools as _functools

from . import functions as _functions
from .functions import *
from .functions import fn as _fn

__all__ = sorted(["lru_cache", "args", "kwargs", *_functions.__all__])

#: Alias to functools lru_cache function.
lru_cache = _fn.curry(2, lambda f, **kwargs: _functools.lru_cache(f, **kwargs))

#: Alias to functools cmp_to_key function.
cmp_to_key = _fn(_functools.cmp_to_key)

#: Alias to functools partialmethod function.
partialmethod = _fn(_functools.partialmethod)

#: Alias to functools singledispatch function.
singledispatch = _functools.singledispatch

#: Alias to functools total_ordering decorator.
total_ordering = _functools.total_ordering

#: Alias to functools update_wrapper decorator.
update_wrapper = _functools.update_wrapper


# noinspection PyShadowingNames,PyUnusedLocal
@_fn
def args(*args, **kwargs):
    """
    Return positional arguments as a tuple.
    """
    return args


# noinspection PyShadowingNames,PyUnusedLocal
@_fn
def kwargs(*args, **kwargs):
    """
    Return keyword arguments as a dictionary.
    """
    return kwargs
