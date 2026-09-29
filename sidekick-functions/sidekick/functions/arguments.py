from functools import wraps
from typing import Literal, overload, Sequence, Any, TYPE_CHECKING

from sidekick.protocols import to_callable, Curry2

from .utils import a, b, r, Fn

if TYPE_CHECKING:
    from sidekick import api as sk  # noqa: F401

fn = lambda x: x


@overload
def flip(func: Fn[[a, b], r], curry: Literal[True] = True) -> Curry2[b, a, r]:
    ...


@overload
def flip(func: Fn[[a, b], r]) -> Fn[[b, a], r]:
    ...


def flip(func, curry=True):
    """
    Flip the order of arguments in a binary operator.

    The resulting function is always curried, unless the argument curry=False.

    Examples:
        >>> from operator import sub
        >>> rsub = flip(sub)
        >>> rsub(2, 10)
        8
    """
    func = to_callable(func)
    if curry:
        return fn.curry(2, lambda x, y: func(y, x))
    else:
        return fn(lambda x, y: func(y, x))


def reverse_args(func: Fn[..., r]) -> Fn[..., r]:
    """
    Creates a function that invokes func with the positional arguments order
    reversed.

    Examples:
        >>> concat = reverse_args(lambda x, y, z: x + y + z)
        >>> concat("a", "b", "c")
        'cba'
    """
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*args[::-1], **kwargs))


@curry(2)
def select_args(idx: Sequence[int], func: Fn[..., r]) -> Fn[..., r]:
    """
    Creates a function that calls func with the arguments reordered.

    Examples:
        >>> double = select_args([0, 0], (X + Y))
        >>> double(21)
        42
    """
    idx = tuple(idx)
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*(args[i] for i in idx), **kwargs))


@curry(2)
def skip_args(n: int, func: Fn[..., r]) -> Fn[..., r]:
    """
    Skips the first n positional arguments before calling func.

    Examples:
        >>> incr = skip_args(1, (X + 1))
        >>> incr('whatever', 41)
        42
    """
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*args[n:], **kwargs))


@curry(2)
def keep_args(n: int, func: Fn[..., r]) -> Fn[..., r]:
    """
    Uses only the first n positional arguments to call func and ignore the rest.

    Examples:
        >>> incr = keep_args(1, (X + 1))
        >>> incr(41, 'whatever')
        42
    """
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*args[:n], **kwargs))


def variadic(func: Fn[[tuple], r]) -> Fn[..., r]:
    """
    Return a function that receives arguments as a tuple and return a
    variadic function that accept each argument separately.

    Args:
        func:
            Function that receives a single tuple positional argument.

    Example:
        >>> concat = variadic("".join)
        >>> concat("foo", "bar")
        'foobar'
    """
    return fn(lambda *args, **kwargs: func(args, **kwargs))


def unsplice(func: Fn[..., r], slice: slice | None = None) -> Fn[[tuple], r]:
    """
    Return a function that receive arguments separately and return a function
    that receives a single argument as a tuple.

    Args:
        func:
            Function that receives several positional arguments.
        slice:
            If given and is a slice, correspond to the slice in the input
            arguments that will be passed to func.

    Example:
        >>> replacer = unsplice(str.replace)
        >>> replacer(["foo", "f", "g"])
        'goo'
    """
    if slice is None:
        return fn(lambda x, **kwargs: func(*x, **kwargs))
    else:
        return fn(lambda x, **kwargs: func(*x[slice], **kwargs))

