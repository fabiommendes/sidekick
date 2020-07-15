import functools
import operator

from .semigroup import semigroup
from ..functions import fn, always
from ..typing import Monoid, Seq, T


#
# Monoid class
#
class monoid(semigroup):
    @classmethod
    def from_operator(cls, neutral, op=None, **kwargs):
        if op is None:
            return lambda f: cls.from_operator(cls, neutral, op=f, **kwargs)

        if not callable(neutral):
            neutral = always(neutral)

        return cls(lambda *args: functools.reduce(op, args, neutral())).wraps(fn)

    @classmethod
    def _fn_getitem(cls, item):
        if isinstance(item, tuple):
            monoids = tuple(enumerate(item))

            @monoid
            def tuple_monoid(*args):
                return tuple(combine(m, (x[i] for x in args)) for i, m in monoids)

            return tuple_monoid
        return super()._fn_getitem(item)

    def neutral(self):
        return self._func()


#
# Useful functions
#
@fn.curry(2)
def combine(func: Monoid[T], seq: Seq[T], stable=False) -> T:
    """
    Combine sequence with monoidal function.
    """
    if stable:
        raise NotImplemented
    try:
        return functools.reduce(func, seq)
    except ValueError:
        return func()


def times(func: Monoid[T], x: T, n: int) -> T:
    """
    Execute monoid operation n times in x.

    Example:
        >>> sk.times(Str, "foo", 5)
        "foofoofoofoofoo"
    """
    if n == 0:
        return func()
    elif n == 1:
        return x
    res = times(func, x, n // 2)
    res = func(res, res)
    return res if n % 2 == 0 else func(res, x)


#
# Useful monoids
#
Add = monoid.from_operator(operator.add, 0)
Mul = monoid.from_operator(operator.mul, 1)
Str = monoid.from_operator(operator.add, "")
List = monoid.from_operator(operator.add, list)
Set = monoid.from_operator(operator.__or__, set)
Tuple = monoid.from_operator((), operator.add)


@fn.curry(3)
def combine_map(monoid, func, seq):
    return combine(monoid, map(func, seq))


@monoid(op=lambda x, y: y if x is None else y)
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
