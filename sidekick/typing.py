import typing as _typ
from typing import *
from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType

FunctionTypes = FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType

# Types
Fn2 = Callable[[Any, Any], Any]
Func = _typ.Union[_typ.Callable, type(None)]
Pred = _typ.Union[_typ.Callable, type(None)]
Seq = _typ.Iterable
T = _typ.TypeVar("T")
S = _typ.TypeVar("S")
R = _typ.TypeVar("R")
SeqT = Seq[T]
NOT_GIVEN = type("NOT_GIVEN", (), {"__repr__": lambda self: "NOT_GIVEN"})()

#: Anything that can go into an isinstance check.
TypeCheck = Union[type, Tuple[type, ...]]
