from .group_definition import group


import operator
from itertools import chain
from functools import reduce
from types import FunctionType
from numbers import Number
from typing import Callable, Iterable, TypeVar

from .monoid_definition import monoid as _group
from . import group_instances as _groups

_T = TypeVar("_T")
_N = TypeVar("_N", bound=Number)

__all__ = ["product", "summation"]

group[Number, "+"] = group["+"] = group.from_operator(operator.add, 0, inv=(-X))
group[Number, "*"] = group["*"] = group.from_operator(operator.mul, 1, inv=(1 / X))

_group[type(None)] = _group.from_reducer(lambda _: None)
_group[int] = _group.from_reducer(sum)  # type: ignore
_group[float] = _group.from_reducer(lambda xs: sum(xs, start=0.0))  # type: ignore
_group[complex] = _group.from_reducer(lambda xs: sum(xs, start=0j))  # type: ignore
_group[bool] = _group.from_reducer(any)


def __getattr__(attr):
    return getattr(_groups, attr)


def __dir__():
    return sorted(__all__)


del group
