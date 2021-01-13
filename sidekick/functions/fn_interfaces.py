import copy
import operator
from functools import reduce, partial, singledispatch
from itertools import chain, product
from numbers import Number

from ..functions import fn, to_callable, compose
from ..properties import alias
from ..seq import uncons, singleton
from ..typing import T, MutableMapping, Iterable, Callable


class UnitFactory:
    """
    Unit attribute of monoids.
    """

    __slots__ = ("_func",)

    def __get__(self, obj, cls=None):
        if obj is None:
            return cls
        return obj()


class IndexedFunc(MutableMapping, type(fn)):
    """
    A fn-function that accepts indexing.

    Indexing is used to register instances of the function specialized to
    specific types or contexts.
    """

    def __init__(self, name, cls, ns, **kwargs):

        # We want to use singledispatch algorithm to find best implementations
        # to type-based keys
        self._type_dispatcher = singledispatch(_raise_key_error)

        # This dict holds the non-type based keys
        self._non_type_registry = {}

        # A cache for both types
        self._cache = {}

    def __contains__(self, item):
        return item in self._non_type_registry or self._type_dispatcher.registry

    def __getitem__(self, key):
        try:
            return self._cache[key]
        except KeyError:
            if isinstance(key, type):
                value = self._type_dispatcher.dispatch(key)
            else:
                value = self._non_type_registry[key]
            self._cache[key] = value
            return value

    def __delitem__(self, key):
        cls = type(self).__name__
        raise KeyError(f"cannot delete implementations from {cls}")

    def __setitem__(self, key, value):
        if key in self:
            cls = type(self).__name__
            raise KeyError(f"cannot override implementations in {cls}")

        if isinstance(key, type):
            self._non_type_registry[key] = value
        else:
            self._type_dispatcher.register(key, value)

        for base in type(self).__bases__:
            if isinstance(base, IndexedFunc) and key not in base:
                base[key] = value

    def __len__(self):
        return len(self._non_type_registry) + len(self._type_dispatcher.registry)

    def __iter__(self):
        yield from self._type_dispatcher.registry
        yield from self._non_type_registry


class semigroup(fn, metaclass=IndexedFunc):
    """
    A function that implements a semigroup structure.

    In sidekick, semigroups are implemented as a variadic function with the
    following signatures:

    * fn(x) = x
    * fn(x, y) = op(x, y)
    * fn(x, y, z) = op(op(x, y), z) = op(x, op(y, z))

    ``op`` is the associative binary operator that defines the particular
    semigroup structure. Calling a semigroup function with more arguments simply
    combine all elements using the semigroup definition.
    """

    description = alias("__doc__")

    @classmethod
    def from_operator(cls, op, description=None):
        """
        Creates a new semigroup function from the given binary operator.
        """
        return cls(lambda *args: reduce(op, args), description)

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
        try:
            x, rest = uncons(iterable)
        except ValueError:
            return
        yield x
        for y in rest:
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
            return cls(lambda *args: reduce(op, args) if args else unit)
        elif unit_factory is not None:
            return cls(lambda *args: reduce(op, args) if args else unit_factory())
        else:
            raise TypeError("unit or unit_factory must be given")

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

    def __init__(self, func, inv, description=None):
        super().__init__(func, description)
        self.inv = inv


#
# Useful semigroups/groups/monoids
#
group[Number, "+"] = group["+"] = group.from_operator(operator.add, 0, inv=lambda x: -x)
group[Number, "*"] = group["*"] = group.from_operator(
    operator.mul, 1, inv=lambda x: 1 / x
)
monoid[type(lambda: ...)] = monoid["function"] = monoid(to_callable(compose))
monoid[str] = monoid(lambda *args: "".join(args))
monoid[bytes] = monoid(lambda *args: b"".join(args))
monoid[tuple] = monoid(lambda *args: tuple(chain(*args)))
monoid[list] = monoid(lambda *args: list(chain(*args)))
monoid[set] = monoid(lambda *args: set(chain(*args)))


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


@monoid
def coalesce(xs):
    """
    Coalescing monoid: return None if first argument is None else return the
    second argument.

    Examples:
        >>> coalesce(None, None, "not null")
        'not null'
    """
    for x in xs:
        if x is not None:
            return x
    return None


monoid["coalesce"] = coalesce


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

    description = alias("__doc__")

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


class apply_flat(ApplyMixin, fn):
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
        return self(compose(self.wrap, f), *args, **kwargs)

    def flatten(self, m):
        """
        Flatten monad.
        """
        return self(lambda x: x, m)


#
# Useful functors and monads
#
def intersection(sets: Iterable[set]):
    """Intersection of sets"""
    s, rest = uncons(sets)
    s = set(s)
    for x in rest:
        s.intersection_update(x)
    return s


def apply_iter(f, *args: Iterable) -> Iterable:
    if len(args) == 1:
        return map(f, args[0])
    return (f(*args_i) for args_i in product(*args))


def apply_flat_iter(f, *args: Iterable) -> Iterable:
    return chain.from_iterable(apply_iter(f, *args))


def apply_dict(f, *args: dict):
    """
    Dicts are not true applicative objects since we cannot implement a reasonable
    wrap() function.
    """
    if len(args) == 1:
        return {k: f(v) for k, v in args[0].items()}
    keys = intersection(map(set, args))
    return {f(*(d[k] for d in product(*args))) for k in keys}


# Applicative instances
apply["iter"] = apply(apply_iter, singleton)
apply[set] = apply(compose(set, apply_iter), lambda x: {x})
apply[tuple] = apply(compose(tuple, apply_iter), lambda x: (x,))
apply[list] = apply(compose(list, apply_iter), lambda x: [x])
apply[dict] = apply(apply_dict)

# Monad instances
apply_flat["iter"] = apply_flat(apply_flat_iter, singleton)
apply_flat[set] = apply_flat(compose(set, apply_flat_iter), lambda x: {x})
apply_flat[tuple] = apply_flat(compose(tuple, apply_flat_iter), lambda x: (x,))
apply_flat[list] = apply_flat(compose(list, apply_flat_iter), lambda x: [x])


#
# Utility functions
#
def _raise_key_error(x):
    raise KeyError(x)
