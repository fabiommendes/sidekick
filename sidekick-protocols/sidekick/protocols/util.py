from __future__ import annotations

import sys
import logging
import operator as op
from types import MappingProxyType
from typing import (
    Any,
    Callable as Fn,
    TypeVar,
    ParamSpec,
)

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack, assert_never
else:
    from typing_extensions import TypeVarTuple, Unpack, assert_never  # noqa: F401


log = logging.getLogger("sidekick")
a = TypeVar("a")
b = TypeVar("b")
c = TypeVar("c")
d = TypeVar("d")
e = TypeVar("e")
r = TypeVar("r")

a_co = TypeVar("a_co", covariant=True)
b_co = TypeVar("b_co", covariant=True)
c_co = TypeVar("c_co", covariant=True)
d_co = TypeVar("d_co", covariant=True)
e_co = TypeVar("e_co", covariant=True)
r_co = TypeVar("r_co", covariant=True)

a_contra = TypeVar("a_contra", contravariant=True)
b_contra = TypeVar("b_contra", contravariant=True)
c_contra = TypeVar("c_contra", contravariant=True)
d_contra = TypeVar("d_contra", contravariant=True)
e_contra = TypeVar("e_contra", contravariant=True)
r_contra = TypeVar("r_contra", contravariant=True)

err = TypeVar("err")
err_ = TypeVar("err_")
err_co = TypeVar("err_co", covariant=True)
args_t = TypeVarTuple("args_t")
BinOp = Fn[[a, a], a]
P = ParamSpec("P")
F = TypeVar("F")
F_co = TypeVar("F_co", covariant=True)

NOT_GIVEN = object()

BINARY_OP: dict[str, Fn[[Any, Any], Any]] = {
    "+": op.add,
    "//": op.floordiv,
    "<<": op.lshift,
    "@": op.matmul,
    "%": op.mod,
    "*": op.mul,
    "**": op.pow,
    ">>": op.rshift,
    "-": op.sub,
    "/": op.truediv,
    "&": op.and_,
    "^ ": op.xor,
    "|": op.or_,
    "==": op.eq,
    ">=": op.ge,
    ">": op.gt,
    "<=": op.le,
    "<": op.lt,
    "!=": op.ne,
    "or": op.or_,
    "and": op.and_,
    "is": op.is_,
    "is not": op.is_not,
}

UNARY_OP: dict[str, Fn[[Any], Any]] = {
    "~": op.invert,
    "-": op.neg,
    "+": op.pos,
    "not": op.not_,
}


SIDEKICK_GLOBALS = MappingProxyType(
    {
        "fn": "fn",
    }
)
