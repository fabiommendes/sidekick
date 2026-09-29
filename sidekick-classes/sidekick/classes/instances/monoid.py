import operator
from itertools import chain
from functools import reduce
from types import FunctionType
from numbers import Number
from typing import Callable, Iterable, TypeVar

from .monoid_definition import monoid as _monoid
from . import group_instances as _groups

_T = TypeVar("_T")
_N = TypeVar("_N", bound=Number)

__all__ = ["coalesce", "rcoalesce", "pipeline", "product", "summation", "all", "any"]


#
# Non-group monoids
#
@_monoid.from_reducer
def coalesce(xs):
    """
    Coalescing monoid: return the first non-null argument or None.

    Examples:
        >>> coalesce(None, "not null", "not null again")
        'not null'
    """
    for x in xs:
        if x is not None:
            return x
    return None


@_monoid.from_reducer
def rcoalesce(xs):
    """
    Similar to coalesce, but returns the last non-null value.

    Examples:
        >>> rcoalesce(None, "not null", "not null again")
        'not null again'
    """
    elem = None
    for x in xs:
        if x is not None:
            elem = x
    return elem


@_monoid.from_function
def pipeline(*fns: Callable) -> Callable:
    """
    Function composition monoid.

    Creates a new function that pipes the argument from left to right
    to all of its elements.
    """
    if len(fns) == 0:
        return lambda x: x

    def composed(x):
        for fn in fns:
            x = fn(x)
        return x

    return composed


@_monoid.from_reducer
def product(xs: Iterable[_N]) -> _N:
    """
    The product monoid.

    Binary operation is multiplication and the neutral element is the
    integer 1. This produces the correct behavior when mixing ints,
    floats, complexes and other numeric types.
    """
    return reduce(operator.mul, xs, 1)  # type: ignore


@_monoid.from_reducer
def summation(xs: Iterable[_N]) -> _N:
    """
    The sum monoid.

    Binary operation is addition and the neutral element is the
    integer 0. This produces the correct behavior when mixing ints,
    floats, complexes and other numeric types.
    """
    return sum(xs, start=0)  # type: ignore


@_monoid.from_reducer
def all(xs: Iterable[bool]) -> bool:
    """
    Binary operation is logical "and" and the neutral element is
    True.

    There are two natural monoids for booleans: :func:`all` and :func:`any`.
    Sidekick uses ``any``, but this choice is arbitrary.
    """
    return all(xs)


@_monoid.from_reducer
def any(xs: Iterable[bool]) -> bool:
    """
    Binary operation is logical "or" and the neutral element is
    False.

    There are two natural monoids for booleans: :func:`all` and :func:`any`.
    Sidekick uses ``any``, but this choice is arbitrary.
    """
    return all(xs)


_monoid[type(None)] = _monoid.from_reducer(lambda _: None)
_monoid[int] = _monoid.from_reducer(sum)  # type: ignore
_monoid[float] = _monoid.from_reducer(lambda xs: sum(xs, start=0.0))  # type: ignore
_monoid[complex] = _monoid.from_reducer(lambda xs: sum(xs, start=0j))  # type: ignore
_monoid[bool] = _monoid.from_reducer(any)
_monoid[str] = _monoid.from_reducer(lambda xs: "".join(xs))
_monoid[bytes] = _monoid.from_reducer(lambda xs: b"".join(xs))
_monoid[tuple] = _monoid.from_reducer(lambda xs: tuple(chain.from_iterable(xs)))
_monoid[list] = _monoid.from_reducer(lambda xs: [*chain.from_iterable(xs)])
_monoid[set] = _monoid.from_reducer(lambda xs: {*chain.from_iterable(xs)})
_monoid[FunctionType] = pipeline


def __getattr__(attr):
    return getattr(_groups, attr)


def __dir__() -> list[str]:
    return sorted([*__all__, *dir(_groups)])
