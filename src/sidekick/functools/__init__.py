from .composition import *
from .functions import *
from ..core import fn as _fn

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
