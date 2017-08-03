from .__meta__ import __author__, __version__
from .adt import (
    opt, Union,
    Maybe, Just, Nothing, maybe,
    Result, Ok, Err, result,
)
from .record import Record, field, record, namespace
from .placeholder import _, F
from .fn import fn
from .factories import attrgetter, caller
from .predicate import *
from .lib_functions import *
from .lib_sequences import *
from .listmagic import L
from . import op


__all__ = [x for x in globals() if not x.startswith('_')]
__all__.extend(['_', '__author__', '__version__'])
