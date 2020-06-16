import typing as _typ
from typing import *

# Types
Func = _typ.Union[_typ.Callable, type(None)]
Pred = _typ.Union[_typ.Callable, type(None)]
Seq = _typ.Iterable
T = _typ.TypeVar("T")
S = _typ.TypeVar("S")
R = _typ.TypeVar("R")
SeqT = Seq[T]
NOT_GIVEN = type("NOT_GIVEN", (), {"__repr__": lambda self: "NOT_GIVEN"})()
