from .__meta__ import __author__, __version__

from .adt import (
    opt, Union,
    Maybe, Just, Nothing, maybe,
    Result, Ok, Err, result,
)
from .record import Record, field, record
from .placeholder import _, F
from .fn import fn, curry
from .factories import attrgetter, caller
from .functions import (const, construct, identity, flip)
from . import op
