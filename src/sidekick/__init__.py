from . import json
from . import op
from .deferred import deferred, delayed, Delayed, Deferred, Proxy
from .factories import attrgetter, caller
from .fn import fn
from .lazy import lazy, property, delegate_to, alias, import_later
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
from .placeholder import placeholder, F
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

__author__ = 'Fábio Macêdo Mendes'
__version__ = '0.4.1'
_ = placeholder
__all__ = ['_', *(attr for attr in globals() if not attr.startswith('_'))]
