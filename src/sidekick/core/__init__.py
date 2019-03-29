import typing as _typ

from .fn import *
from .fn_meta import extract_function
from .placeholder import *

# Types
Func = _typ.Union[_typ.Callable, Placeholder, type(None)]
Pred  = _typ.Union[_typ.Callable, Placeholder, type(None)]
Seq = _typ.Iterable
