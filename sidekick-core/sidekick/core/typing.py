import typing as _typ
from types import (
    FunctionType,
    MethodType,
    BuiltinFunctionType,
    BuiltinMethodType,
    MappingProxyType,
)
from typing import *

from ._empty import empty

#
# Sidekick types
#

#: Func is anything that can be converted to a callable using the sk.to_callable()
#: function. This includes regular functions, None, Dict, etc
Func = _typ.Union[_typ.Callable, _typ.Dict, _typ.Set, None]

#: Pred is similar to Func, but it returns a callable that returns booleans.
Pred = _typ.Union[_typ.Callable, _typ.Dict, _typ.Set, None]

# Types
FunctionTypes = FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType
FunctionWrapperTypes = (staticmethod,)
Fn2 = _typ.Callable[[_typ.Any, _typ.Any], _typ.Any]
Seq = _typ.Iterable
T = _typ.TypeVar("T")
S = _typ.TypeVar("S")
R = _typ.TypeVar("R")
SeqT = Seq[T]
NOT_GIVEN = type("NOT_GIVEN", (), {"__repr__": lambda self: "NOT_GIVEN"})()

#: Anything that can go into an isinstance check.
TypeCheck = _typ.Union[type, _typ.Tuple[type, ...]]

#: Anything that can be raised
Raisable = _typ.Union[Exception, _typ.Type[Exception]]

#: Anything that can be in an except obj statement
Catchable = _typ.Union[_typ.Type[Exception], _typ.Tuple[_typ.Type[Exception], ...]]

#: Something that can be passed as the index option for sidekick functions.
Index = _typ.Union[int, bool, Seq]

#: Interfaces
Magma = Generic
Semigroup = Magma
Monoid = Semigroup
Group = Monoid
Lattice = Group

Functor = Generic
Applicative = Functor
Monad = Applicative

#: Empty values
#: Sharing empty collection types is generally a good practice since coercing
#: EMPTY_LIST to [] is generally an acceptable semantics.
EMPTY_LIST = empty(list)
EMPTY_DICT = empty(dict)
EMPTY_SET = empty(set)
EMPTY_ITERATOR = empty([].__iter__)

#: Immutable container wrappers exist for symmetry and uniform syntax;
#: e.g. we might want to use EMPTY_TUPLE | lst instead of lst | () to preserve
#: the argument.
EMPTY_TUPLE = empty(())
EMPTY_FROZENSET = empty(frozenset())
EMPTY_FROZENMAP = empty(MappingProxyType({}))
EMPTY_INT = empty(0)
EMPTY_FLOAT = empty(0.0)
EMPTY_COMPLEX = empty(0j)
