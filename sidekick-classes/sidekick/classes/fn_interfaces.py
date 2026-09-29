import copy
from collections import ChainMap
from collections.abc import Callable, MutableMapping
from functools import reduce, partial, singledispatch
from itertools import chain
from typing import TypeVar

from sidekick.core.core_functions import to_callable
from sidekick.core.fn import fn

T = TypeVar("T")

#
# Utility functions and types
#
def _raise_key_error(x):
    raise KeyError(x)


class UnitFactory:
    """
    Unit attribute of monoids.
    """

    __slots__ = ("_func",)

    def __get__(self, obj, cls=None):
        if obj is None:
            return cls
        return obj()


class IndexedFunc(type(fn)):
    """
    A fn-function that accepts indexing.

    Indexing is used to register instances of the function specialized to
    specific types or contexts.
    """

    def __init__(cls, name, typ, ns, **kwargs):
        # We want to use singledispatch algorithm to find best implementations
        # to type-based missing keys
        cls._type_dispatcher = singledispatch(
            lambda x, *args: _raise_key_error(type(x))
        )

        # This dict holds the non-type based keys
        cls._registry = {}

        # A cache for both types
        cls._cache = ChainMap({}, cls._registry)

    def __contains__(cls, item):
        return item in cls._registry

    def __getitem__(cls, key):
        try:
            return cls._cache[key]
        except KeyError:
            if not isinstance(key, type):
                raise
            cls._cache[key] = value = cls._type_dispatcher.dispatch(key)
            return value

    def __delitem__(cls, key):
        raise KeyError(f"cannot delete implementations from {cls.__name__}")

    def __setitem__(cls, key, value):
        if key in cls:
            raise KeyError(f"cannot override {key} implementation in {cls.__name__}")

        cls._registry[key] = cls._cache[key] = value
        if isinstance(key, type):
            cls._type_dispatcher.register(key, value)
            cls._cache.clear()
            cls._cache.update(cls._registry)

        for base in cls.__bases__:
            if isinstance(base, IndexedFunc):
                base[key] = value


class semigroup(fn, metaclass=IndexedFunc):
    """
    A function that implements a semigroup structure.

    In sidekick, semigroups are implemented as a variadic function with the
    following signatures:

    * fn(xs) = fn(*xs)
    * fn(x, y) = op(x, y)
    * fn(x, y, z) = op(op(x, y), z) = op(x, op(y, z))
    * and so on for mor arguments...

    ``op`` is the associative binary operator that defines the particular
    semigroup structure. Calling a semigroup function with more arguments simply
    combine all elements using the semigroup definition.
    """

    @property
    def description(self):
        return self.__doc__

    @description.setter
    def description(self, value):
        self.__doc__ = value

    @classmethod
    def from_operator(cls, op, description=None):
        """
        Creates a new semigroup function from the given binary operator.
        """

        def semigroup_fn(x_or_seq, /, *xs):
            if xs:
                return reduce(op, xs, x_or_seq)
            return reduce(op, x_or_seq)

        return cls(semigroup_fn, description)

    @classmethod
    def from_reducer(cls, func, description=None):
        """
        Creates a new semigroup from a function that reduces a
        non-empty sequence of arguments.
        """

        def semigroup_fn(*args):
            if (n := len(args)) == 1:
                return func(args[0])
            elif n == 0:
                raise TypeError("semigroup requires at least one argument")
            return func(args)

        return cls(semigroup_fn, description)

    @property
    def unit(self):
        raise TypeError("semigroup does not have a unit element.")

    def __init__(self, func, description=None):
        super().__init__(func)
        self.__doc__ = description

    

class monoid(semigroup):
    """
    Monoid is a semigroup with a unit element.

    In sidekick, monoids are implemented as a variadic functions similar to
    semigroups. The main difference is that by calling a monoid with no arguments
    return the unit element, instead of raising an error.
    """

    @classmethod
    def from_semigroup(cls, semigroup, unit=None, unit_factory=None):
        """
        Creates a monoid from semigroup, supplying the unit element or the unit
        factory.
        """
        semigroup_fn = to_callable(semigroup)

        if unit is not None:
            return cls(lambda *args: semigroup_fn(*args) if args else unit)
        elif unit_factory is not None:
            return cls(lambda *args: semigroup_fn(*args) if args else unit_factory())
        else:
            raise TypeError("unit or unit_factory must be given")

    @classmethod
    def from_operator(cls, op, unit=None, unit_factory=None):
        """
        Creates monoid from binary operator.
        """
        if unit is not None:

            def monoid_fn(*args):
                if (n := len(args)) == 0:
                    return unit
                elif n == 1:
                    return reduce(op, args, unit)
                else:
                    return reduce(op, args, unit)

        elif unit_factory is not None:

            def monoid_fn(*args):
                if (n := len(args)) == 0:
                    return unit_factory()
                elif n == 1:
                    return reduce(op, args, unit_factory())
                else:
                    return reduce(op, args)

        else:
            raise TypeError("unit or unit_factory must be given")
        return cls(monoid_fn)

    @classmethod
    def from_reducer(cls, func, description=None):
        """
        Creates a new monoid from a function that reduces a sequence of arguments.
        """

        def monoid_fn(*args):
            return func(args[0]) if len(args) == 1 else func(args)

        return cls(monoid_fn, description)

    unit = UnitFactory()

    def reduce(self, iterable):
        try:
            return super().reduce(iterable)
        except IndexError:
            return self.unit

    def accumulate(self, iterable, unit=False):
        if unit:
            return super().accumulate(chain([self.unit], iterable))
        return super().accumulate(iterable)


class group(monoid):
    """
    A monoid with an inverse operation.

    This behaves similarly to a monoid, but also has an inverse method named
    inv.
    """

    @classmethod
    def from_monoid(cls, monoid, *, inv):
        """
        Creates group from a monoid and an inverse function.
        """
        return cls(to_callable(monoid), inv, description=monoid.description)

    # noinspection PyMethodOverriding
    @classmethod
    def from_semigroup(cls, semigroup, unit=None, unit_factory=None, *, inv):
        """
        Creates a group from semigroup, supplying the inverse function and the
        unit element or the unit factory.
        """
        mono = monoid.from_semigroup(semigroup, unit, unit_factory)
        return cls.from_monoid(mono, inv=inv)

    # noinspection PyMethodOverriding
    @classmethod
    def from_operator(cls, op, unit=None, unit_factory=None, *, inv):
        """
        Creates group from binary operator.
        """
        mono = monoid.from_operator(op, unit, unit_factory)
        return cls.from_monoid(mono, inv=inv)

    # noinspection PyMethodOverriding
    @classmethod
    def from_reducer(cls, func, *, inv, description=None):
        """
        Creates a group from semigroup, supplying the inverse function and the
        unit element or the unit factory.
        """
        mono = monoid.from_reducer(func, description)
        return cls.from_monoid(mono, inv=inv)

    def __init__(self, func, inv, description=None):
        super().__init__(func, description)
        self.inv = inv
