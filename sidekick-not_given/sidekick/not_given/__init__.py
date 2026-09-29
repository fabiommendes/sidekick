from __future__ import __annotations__

"""
A better way to define optional values.
"""

from typing import Callable, Generic, TypeVar
from dataclasses import dataclass
from abc import ABC


__author__ = "Fábio Macêdo Mendes"
__version__ = "0.1.0"
__all__ = ["not_given"]
_EMPTY = object()  # Pretty ironic, huh?
T = TypeVar("T")


class Empty(Generic[T], ABC):
    """
    A convenient representation of empty arguments.

    Implementors of this interface can be used to replace the common pattern of setting
    a top level ``NOT_GIVEN = object()`` variable to represent empty arguments.

    The idiomatic way of testing if ``arg is EMPTY`` is still valid, but it defines other
    interfaces to different ways of handling missing arguments.
    """

    def __call__(self, arg, default: T = None) -> T | None:
        return default if arg is self else arg

    def __or__(self, other: T) -> T:
        return other

    def __ror__(self, other: T) -> T:
        return self.__or__(other)

    def __bool__(self) -> bool:
        return False

    def __repr__(self):
        return "<NOT GIVEN>"

    def resolve(self, value: T | Self, default: T) -> T:
        """
        Return default if value is EMPTY or value otherwise.
        """
        return default if value is self else value

    def as_copy(self, other) -> T:
        """
        Return argument as a copy.
        """
        if self.copy is None:
            return None if other is self else other
        else:
            return self.copy(None if other is self else other)


def empty(constructor=_EMPTY, copy=None) -> Empty[T]:
    """
    Create an object that represents empty arguments.

    Empty objects should not be shared across different libraries. Ideally, they
    should be defined in the toplevel of each module that might use it and
    not exposed in module's __all__ list.

    Args:
        constructor:
            An optional callable that is used to construct an empty value. If
            not callable, it is used as the implicit default value.
    """
    if constructor is _EMPTY:
        return EmptyGeneric(copy)
    elif callable(constructor):
        return EmptyFactory(constructor, copy or constructor)
    elif type(constructor) in (list, dict, set):
        cls = type(constructor).__name__
        msg = (
            f"Default value should not be a mutable collection. "
            f"\nCall empty({cls}) instead"
        )
        raise ValueError(msg)
    else:
        return EmptyValue(constructor, copy or type(constructor))


@dataclass(frozen=True)
class EmptyGeneric(Empty[T]):
    ...


@dataclass(frozen=True)
class EmptyFactory(Empty[T]):
    """
    Empty elements that represents default values that require calling a
    constructor. This is a common patterns for default empty lists, empty dicts, etc
    """

    copy: Callable[[Any], T]
    factory: Callable[[], Any]

    def __call__(self, arg, default=_EMPTY):
        if arg is not self:
            return arg
        elif default is _EMPTY:
            return self.factory()
        else:
            return default

    def __or__(self, other):
        return self.factory() if other is self else other

    def as_copy(self, other):
        return self.factory() if other is self else self.copy(other)


@dataclass(frozen=True)
class EmptyValue(Empty[T]):
    """
    Like Empty, but returns a definite value.

    We could have used EmptyFactory(lambda: value), but this is slightly faster.
    """

    value: T
    factory = property(lambda self: lambda: self.value)

    def __call__(self, arg, default=_EMPTY):
        if arg is not self:
            return arg
        elif default is _EMPTY:
            return self.value
        else:
            return default

    def __or__(self, other):
        return self.value if other is self else other

    def as_copy(self, other):
        return self.value if other is self else self.copy(other)
