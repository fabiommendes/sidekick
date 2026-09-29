from typing import Iterable


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
