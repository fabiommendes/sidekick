from __future__ import annotations
import abc

import sys
import logging
from typing import (
    Callable as Fn,
    Generic,
    Type,
    TypeVar,
    ParamSpec,
)

if sys.version_info >= (3, 11):
    from typing import Self, TypeVarTuple, assert_never
else:
    from typing_extensions import Self, TypeVarTuple, assert_never  # noqa: F401

log = logging.getLogger("sidekick")
a = TypeVar("a")
b = TypeVar("b")
r = TypeVar("r")
err = TypeVar("err")
err_ = TypeVar("err_")
err_co = TypeVar("err_co", covariant=True)
args_t = TypeVarTuple("args_t")
fn_t = TypeVar("fn_t", Fn)
BinOp = Fn[[a, a], a]
P = ParamSpec("P")
Raisabled = Type[Exception] | Exception
NOT_GIVEN = object()


class WrappedFunction(abc.ABC, Generic[fn_t]):
    @abc.abstractclassmethod
    def _wrap(self, func: Fn) -> fn_t:
        return func
