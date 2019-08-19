import functools as _functools

from .composition import *
from .functions import *
from .dispatch import lazy_singledispatch
from ..core import fn as _fn

cmp_to_key = _fn(_functools.cmp_to_key)
lru_cache = _fn.curry(1, lambda f, **kwargs: _functools.lru_cache(f, **kwargs))
partialmethod = _fn(_functools.partialmethod)
singledispatch = _functools.singledispatch
total_ordering = _functools.total_ordering
update_wrapper = _functools.update_wrapper


# Disabled
# reduce - itertools
# partial - implemented
# wraps - fn.wraps


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
