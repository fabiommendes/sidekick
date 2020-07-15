from .core_functions import quick_fn, to_callable
from .fn import fn
from ..typing import Fn2, Func, TYPE_CHECKING, Sequence, Any

if TYPE_CHECKING:
    from .. import api as sk  # noqa: F401


@fn
def flip(func: Fn2, curry=True) -> Fn2:
    """
    Flip the order of arguments in a binary operator.

    The resulting function is always curried, unless the argument curry=False.

    Examples:
        >>> from operator import sub
        >>> rsub = sk.flip(sub)
        >>> rsub(2, 10)
        8
    """
    func = to_callable(func)
    if curry:
        return fn.curry(2, lambda x, y: func(y, x))
    else:
        return fn(lambda x, y: func(y, x))


@fn
def reverse_args(func: Func) -> fn:
    """
    Creates a function that invokes func with the positional arguments order
    reversed.

    Examples:
        >>> concat = sk.reverse_args(lambda x, y, z: x + y + z)
        >>> concat("a", "b", "c")
        'cba'
    """
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*args[::-1], **kwargs))


@fn.curry(2)
def select_args(idx: Sequence[int], func: Func) -> fn:
    """
    Creates a function that calls func with the arguments reordered.

    Examples:
        >>> double = sk.select_args([0, 0], (X + Y))
        >>> double(21)
        42
    """
    idx = tuple(idx)
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*(args[i] for i in idx), **kwargs))


@fn.curry(2)
def skip_args(n: int, func: Func) -> fn:
    """
    Skips the first n positional arguments before calling func.

    Examples:
        >>> incr = sk.skip_args(1, (X + 1))
        >>> incr('whatever', 41)
        42
    """
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*args[n:], **kwargs))


@fn.curry(2)
def keep_args(n: int, func: Func) -> fn:
    """
    Uses only the first n positional arguments to call func.

    Examples:
        >>> incr = sk.keep_args(1, (X + 1))
        >>> incr(41, 'whatever')
        42
    """
    func = to_callable(func)
    return fn(lambda *args, **kwargs: func(*args[:n], **kwargs))


@fn
def variadic_args(func: Func) -> fn:
    """
    Return a function that receives variadic arguments and pass them as a tuple
    to func.

    Args:
        func:
            Function that receives a single tuple positional argument.

    Example:
        >>> vsum = sk.variadic_args(sum)
        >>> vsum(1, 2, 3, 4)
        10
    """
    return fn(lambda *args, **kwargs: func(args, **kwargs))


@fn
def splice_args(func: Func, slice=None) -> fn:
    """
    Return a function that receives a sequence as single argument and splice
    them into func.

    Args:
        func:
            Function that receives several positional arguments.
        slice:
            If given and is a slice, correspond to the slice in the input
            arguments that will be passed to func.

    Example:
        >>> vsum = sk.splice_args(max)
        >>> vsum([1, 2, 3, 4])
        4
    """
    if slice is None:
        return fn(lambda x, **kwargs: func(*x, **kwargs))
    else:
        return fn(lambda x, **kwargs: func(*x[slice], **kwargs))


@fn
def set_null(*args: Any, **kwargs) -> fn:
    """
    Return a new function that replace all null arguments in the given positions
    by the provided default value.
    """
    func, *defaults = args
    default_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if len(defaults) == 1:
        (x,) = defaults

        def fun(_x, *args, **kwargs):
            kwargs = fix_null(default_kwargs, kwargs)
            return func(x if _x is None else _x, *args, **kwargs)

    else:

        def fun(*args, **kwargs):
            kwargs = fix_null(default_kwargs, kwargs)
            args = iter(args)
            pre = (y if x is None else x for x, y in zip(args, defaults))
            return func(*pre, *args, **kwargs)

    return quick_fn(fun)


def fix_null(ref, out):
    for k, v in ref.items():
        if out.get(k, v) is None:
            out[k] = v
    return out
