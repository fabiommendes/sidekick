from typing import Iterable, TypeVar
from .semigroup_definition import semigroup as _semigroup
from . import monoid_instances as _monoids

T = TypeVar("T")


__all__ = ["intersection"]


#
# Non-monoidal semigroups
#
@_semigroup.from_reducer
def intersection(sets: Iterable[set]) -> set:
    """
    Intersection of sets.

    Intersection is a semigroup because the neutral
    set for the intersection operation would contain all possible elements
    and cannot be explicitly constructed.

    Sets form a monoid under union.

    >>> intersection({1, 2}, {2, 3})
    {2}
    """
    try:
        elem = next(seq := iter(sets))
    except StopIteration:
        raise ValueError("empty sequence")
    else:
        acc = set(elem)

    for elem in seq:
        acc.intersection_update(elem)
    return acc


@_semigroup.from_operator
def minimum(x: T, y: T) -> T:
    """
    Minimum value of sequence.

    In general, this is not a monoid, unless there is a lower bound to type
    that would serve as neutral element.
    """
    return min(x, y)  # type: ignore


@_semigroup.from_operator
def maximum(x: T, y: T) -> T:
    """
    Minimum value of sequence.

    In general, this is not a monoid, unless there is an upper bound to type
    that would serve as neutral element.
    """
    return max(x, y)  # type: ignore


def __getattr__(attr):
    return getattr(_monoids, attr)


def __dir__():
    return sorted([*__all__, *dir(_monoids)])
