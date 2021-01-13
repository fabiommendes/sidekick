"""
========================
``sidekick.types.empty``
========================

.. currentmodule:: sidekick.types

``None`` is often used to represent empty arguments in a function. But what
happens if None is a legitimate value to some argument? A common approach is to
define a toplevel ``EMPTY = object()`` and check if ``arg is EMPTY`` in the
function body. This is nice, but can be slightly more convenient to use Empty
instances. They can be used in the same way, but have some nice conveniences.

Consider the example

.. code-block:: python

    def transform(x, func=None):
        return func(x) if func else x

>>> transform(42), transform(42, lambda x: -x)
(42, -42)

.. code-block:: python

    EMPTY = empty()

    def transform(x, func=EMPTY):
        return func(x) if func else x

>>> transform(42), transform(42, lambda x: -x)
(42, -42)

.. code-block:: python

    def add(lst, ans=None):
        lst.append(42 if ans is None else ans)

    def add_(lst, ans=EMPTY):
        lst.append(EMPTY(ans, 42))


>>> lst = []; add(lst); ; add(lst, None); add(lst, 43)
>>> lst
[42, 42, 43]

>>> lst = []; add_(lst); ; add_(lst, None); add_(lst, 43)
>>> lst
[42, None, 43]


.. code-block:: python

    def add(lst, ans=None):
        lst.append(42 if ans is None else ans)

    def add_(lst, ans=EMPTY):
        lst.append(EMPTY(ans, 42))


>>> EMPTY_LIST = empty(list)
>>> lst = []
>>> (EMPTY_LIST | lst) is lst
True
>>> EMPTY_LIST(EMPTY_LIST)
[]
>>> EMPTY_LIST | EMPTY_LIST
[]


API reference
=============

.. automodule:: sidekick.types.empty
   :members:
   :inherited-members:

"""
from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Optional

EMPTY = object()  # Pretty ironic, huh?
T = TypeVar("T")


def empty(constructor=EMPTY, copy=None):
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
    if constructor is EMPTY:
        return Empty(copy)
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
class Empty:
    """
    A convenient representation of empty arguments.

    This class is designed to be used to replace the common pattern of setting
    a top level ``EMPTY = object()`` variable to represent empty arguments. The
    idiomatic way of testing if ``arg is EMPTY`` is still valid.
    """

    copy: Optional[Callable[[Any], T]]

    def __call__(self, arg, default=None):
        return default if arg is self else arg

    def __or__(self, other):
        return other

    def __ror__(self, other):
        return self.__or__(other)

    def __repr__(self):
        return "<empty>"

    def __bool__(self):
        return False

    def resolve(self, value, default):
        """
        Return default if value is EMPTY or value otherwise.
        """
        return default if value is self else value

    def as_copy(self, other):
        """
        Return argument as a copy.
        """
        if self.copy is None:
            return None if other is self else other
        else:
            return self.copy(None if other is self else other)


@dataclass(frozen=True)
class EmptyFactory(Empty):
    """
    Empty elements that represents default values that require calling a
    constructor. This is a common patterns for default empty lists, empty dicts, etc
    """

    copy: Callable[[Any], T]
    factory: Callable[[], Any]

    def __call__(self, arg, default=EMPTY):
        if arg is not self:
            return arg
        elif default is EMPTY:
            return self.factory()
        else:
            return default

    def __or__(self, other):
        return self.factory() if other is self else other

    def as_copy(self, other):
        return self.factory() if other is self else self.copy(other)


@dataclass(frozen=True)
class EmptyValue(Empty):
    """
    Like Empty, but returns a definite value.

    We could have used EmptyFactory(lambda: value), but this is slightly faster.
    """

    value: T
    factory = property(lambda self: lambda: self.value)

    def __call__(self, arg, default=EMPTY):
        if arg is not self:
            return arg
        elif default is EMPTY:
            return self.value
        else:
            return default

    def __or__(self, other):
        return self.value if other is self else other

    def as_copy(self, other):
        return self.value if other is self else self.copy(other)
