from . import deferred
from . import json
from . import op
from .union import (
    Union, opt, case, case_fn, casedispatch,
    Maybe, Just, Nothing, maybe,
    Result, Ok, Err, result,
)
from sidekick import opt
from .factories import attrgetter, caller
from .fn import fn
from .lib_functions import *
from .lib_sequences import *
from .listmagic import L
from .placeholder import _, F
from .predicate import *
from .record import (
    Record, Namespace, field,
    make_record, make_namespace,
    record, namespace, record_to_dict,
)

__all__ = [x for x in globals() if not x.startswith('_')]
__all__.extend(['_', '__author__', '__version__'])
__version__ = '0.1.1'
__author__ = 'Fábio Macêdo Mendes'
