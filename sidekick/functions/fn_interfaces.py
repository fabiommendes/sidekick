import copy
from collections import ChainMap
from functools import reduce, partial, singledispatch
from itertools import chain

from .core_functions import to_callable
from .fn import fn
from ..typing import T, MutableMapping, Callable


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

    def __len__(cls):
        return len(cls._registry)

    def __iter__(cls):
        yield from cls._registry

    # This metaclass interacts poorly with ABCMeta. We just copy the relevant
    # methods instead of inheriting from MutableMapping.
    keys = MutableMapping.keys
    values = MutableMapping.values
    items = MutableMapping.items
    get = MutableMapping.get


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

    def reduce(self, iterable):
        """
        Reduces iterable by sequence of elements.

        Similar to calling fn(*iterable), but do not put all elements into
        memory at once. This can be slower in many situations, but might have a
        better memory footprint.
        """
        return reduce(self._func, iterable)

    def accumulate(self, iterable):
        """
        Accumulate iterable using binary reduction of all of its elements.
        """
        op = self._func
        iterable = iter(iterable)
        try:
            x = next(iterable)
        except StopIteration:
            return
        yield x
        for y in iterable:
            yield (x := op(x, y))

    def times(self, x: T, n: int) -> T:
        """
        Execute binary operation n times in x.
        """
        if n == 0:
            return self.unit
        elif n == 1:
            return x
        res = self.times(x, n // 2)
        res = self(res, res)
        return res if n % 2 == 0 else self(res, x)

    def dual(self):
        """
        Dual algebraic structure produced by flipping the binary operation.

        Commutative operations are self-dual, i.e., the dual is equal to the group
        itself.
        """
        fn = to_callable(self)
        new = copy.copy(self)
        new._func = lambda *xs: fn(*xs[::-1])
        return new


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


def mtimes(value, n):
    """
    Apply monoidal or group operation n times in value.

    This function infers the monoid from value.
    """
    if n < 0:
        instance = group[type(value)]
    elif n == 0:
        instance = monoid[type(value)]
    else:
        instance = semigroup[type(value)]
    return instance.times(value, n)


def mconcat(*args):
    """
    Apply monoidal concat operation in arguments.

    This function infers the monoid from value, hence it requires at least
    one argument to operate.
    """
    values = args[0] if len(args) == 1 else args
    instance = semigroup[type(values[0])]
    return instance(*values)


#
# Functor, applicative and monad
#
class ApplyMixin:
    _func: Callable

    def __init__(self, func, wrap=None, description=None):
        super().__init__(func)
        self._wrap = wrap
        self.__doc__ = description

    def __call__(self, fn, /, *args, **kwargs):
        if args:
            if kwargs:
                fn = partial(fn, **kwargs)
            return self._func(fn, *args)
        return partial(self, fn, **kwargs)

    def wrap(self, x):
        """
        Wrap value into the functor.
        """

        if self._wrap is None:
            raise ValueError("Functor does not implements a wrap function.")
        else:
            return self._wrap(x)


class apply(ApplyMixin, fn, metaclass=IndexedFunc):
    """
    A function that implements a functor application.

    In sidekick, single and applicative functors are implemented as a variadic
    function with the following signatures:

    * apply(f) - convert ``f(a) -> b`` to ``F[a] -> F[b]``
    * apply(f, xs) - apply f(x) to xs.
    * apply(f, xs, ys) - apply f(x, y) to xs and ys.
    * So on...
    """

    description = semigroup.description

    def from_binary(self, op):
        """
        Create a generic applicative from a function that can apply functions of
        one or two arguments.
        """
        raise NotImplementedError

    @classmethod
    def with_wrap(cls, wrap, description=None):
        """
        Decorator that defines an apply with a given wrap function.
        """
        return lambda func: cls(func, wrap, description)


class apply_flat(ApplyMixin, fn, metaclass=IndexedFunc):
    """
    A function that implements monadic bind.

    In sidekick, single and applicative functors are implemented as a variadic
    function with the following signatures:

    * apply_flat(f) - convert ``f(a) -> F[b]`` to ``F[a] -> F[b]``
    * apply_flat(f, xs) - apply f(x) to xs, flattening results.
    * apply_flat(f, xs, ys) - apply f(x, y) to xs and ys, flattening results.
    * So on...
    """

    @classmethod
    def from_single(cls, rbind, wrap=None, description=None):
        def apply_flat(f, *args):
            if len(args) == 1:
                return rbind(f, args[0])
            xs, *args = args
            return rbind(lambda x: rbind(partial(f, x), *args), xs)

        return cls(apply_flat, wrap, description)

    def call_simple(self, f, *args, **kwargs):
        """
        Calls a simple function that returns an non-wrapped result.
        """
        return self(lambda x: self.wrap(f(x, **kwargs)), *args)

    def flatten(self, m):
        """
        Flatten monad.
        """
        return self(lambda x: x, m)
