import typing as _typ
from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType
from typing import *

if TYPE_CHECKING:
    pass

#
# Sidekick types
#

#: Func is anything that can be converted to a callable using the sk.to_callable()
#: function. This includes regular functions, None, Dict, etc
Func = _typ.Union[_typ.Callable, Dict, Set, None]

#: Pred is similar to Func, but it returns a callable that returns booleans.
Pred = _typ.Union[_typ.Callable, Dict, Set, None]

# Types
FunctionTypes = FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType
Fn2 = Callable[[Any, Any], Any]
Seq = _typ.Iterable
T = _typ.TypeVar("T")
S = _typ.TypeVar("S")
R = _typ.TypeVar("R")
SeqT = Seq[T]
NOT_GIVEN = type("NOT_GIVEN", (), {"__repr__": lambda self: "NOT_GIVEN"})()

#: Anything that can go into an isinstance check.
TypeCheck = Union[type, Tuple[type, ...]]

#: Anything that can be raised
Raisable = Union[Exception, Type[Exception]]

#: Anything that can be in an except obj statement
Catchable = Union[Type[Exception], Tuple[Type[Exception], ...]]

#: Something that can be passed as the index option for sidekick functions.
Index = Union[int, bool, Seq]

#: Interfaces
Magma = Generic
Semigroup = Magma
Monoid = Semigroup
Group = Monoid
Lattice = Group

Functor = Generic
Applicative = Functor
Monad = Applicative
