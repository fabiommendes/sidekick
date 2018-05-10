from . import deferred
from . import json
from . import op
from .factories import attrgetter, caller
from .fn import fn
from .lazy import lazy, lazy_shared, property
from .lib_functions import (
    compose,
    const,
    curry,
    do,
    force_function,
    identity,
    juxt,
    memoize,
    partial,
    pipe,
    rpartial,
)
from .lib_sequences import *
from .listmagic import L
from .placeholder import _, F
from .predicate import *
from .record import (
    Namespace,
    Record,
    field,
    namespace,
    record,
    record_to_dict,
)
from .union import (
    # Union type
    Union, opt, case, case_fn, casedispatch,

    # Maybes
    Maybe, Just, Nothing, maybe,

    # Result
    Result, Ok, Err, result,

    # List
    List, linklist,
)

__version__ = '0.2.1'
__author__ = 'Fábio Macêdo Mendes'
__all__ = list(x for x in globals().keys() if not x.startswith('_'))
__all__.extend(['__version__', '__author__', '_'])
