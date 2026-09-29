from typing import Callable, TypeVar
from .functor_definition import functor as _functor
from . import applicative_instances as _applicatives

a = TypeVar("a")
b = TypeVar("b")
k = TypeVar("k")


__all__ = ["map_values"]


#
# Non-applicative functors
#
@_functor.from_map
def map_values(f: Callable[[a], b], dic: dict[k, a]) -> dict[k, b]:
    """
    Map function into dictionary values.
    """
    return {k: f(v) for k, v in dic.items()}


@_functor.from_map
def map_keys(f: Callable[[k], b], dic: dict[k, a]) -> dict[b, a]:
    """
    Map function into dictionary keys.
    """
    return {f(k): v for k, v in dic.items()}


def _mutate_seq(func, seq):
    for i, x in enumerate(seq):
        seq[i] = func(x)
    return seq


def _mutate_mapping(func, seq):
    for i, x in enumerate(seq):
        seq[i] = func(x)
    return seq


_functor[dict] = map_values.with_map_inplace(_mutate_mapping)
_functor[list] = _functor.from_iterable_and_wrap(list, map_inplace=_mutate_seq)
_functor[tuple] = _functor.from_iterable_and_wrap(tuple)
_functor[set] = _functor.from_iterable_and_wrap(set)
_functor[frozenset] = _functor.from_iterable_and_wrap(frozenset)


def __getattr__(attr):
    return getattr(_applicatives, attr)


def __dir__():
    return sorted([*__all__, *dir(_applicatives)])
