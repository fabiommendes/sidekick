import operator
from functools import lru_cache
from itertools import chain, product
from numbers import Number

from .fn_interfaces import apply, apply_flat, monoid, group
from .fn_placeholders import X
from .lib_composition import compose
from ..typing import Iterable


#
# Useful semigroups/groups/monoids
#


def coalesce(*xs):
    """
    Coalescing monoid operation: return the first non-null argument or None.

    Examples:
        >>> coalesce(None, None, "not null")
        'not null'
    """
    if len(xs) == 1:
        xs = xs[0]
    for x in xs:
        if x is not None:
            return x
    return None


#
# Useful functors and monads
#
def intersection(sets: Iterable[set]):
    """Intersection of sets"""
    try:
        s = next(sets := iter(sets))
    except StopIteration:
        return set()
    else:
        s = set(s)
    for x in sets:
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


@lru_cache(1)
def register_all():
    # Groups/semigroups/monoids
    group[Number, "+"] = group["+"] = group.from_operator(operator.add, 0, inv=(-X))
    group[Number, "*"] = group["*"] = group.from_operator(operator.mul, 1, inv=(1 / X))
    monoid[callable] = monoid.from_operator(compose, lambda x: x)
    monoid[str] = monoid(lambda *args: "".join(args))
    monoid[bytes] = monoid(lambda *args: b"".join(args))
    monoid[tuple] = monoid(lambda *args: tuple(chain(*args)))
    monoid[list] = monoid(lambda *args: list(chain(*args)))
    monoid[set] = monoid(lambda *args: set(chain(*args)))
    monoid["coalesce"] = monoid(coalesce)

    # Applicative instances
    apply[iter] = apply(apply_iter, lambda x: iter([x]))
    apply[set] = apply(compose(set, apply_iter), lambda x: {x})
    apply[tuple] = apply(compose(tuple, apply_iter), lambda x: (x,))
    apply[list] = apply(compose(list, apply_iter), lambda x: [x])
    apply[dict] = apply(apply_dict)

    # Monad instances
    apply_flat[iter] = apply_flat(apply_flat_iter, lambda x: iter([x]))
    apply_flat[set] = apply_flat(compose(set, apply_flat_iter), lambda x: {x})
    apply_flat[tuple] = apply_flat(compose(tuple, apply_flat_iter), lambda x: (x,))
    apply_flat[list] = apply_flat(compose(list, apply_flat_iter), lambda x: [x])
