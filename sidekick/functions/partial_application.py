from functools import partial as _partial
from typing import Callable

from .._fn import fn, quick_fn, extract_function
from .._fn_introspection import arity
from ..typing import Func


def partial(func: Func, *args, **kwargs) -> fn:
    """
    Return a new function that partially apply the given arguments and
    keywords.

    Args:
        func:
            Function or func-like object.
        *args, **kwargs:
            Arbitrary positional and keyword arguments partially applied to the
            function.

    Examples:
        >>> func = lambda x, y: x + y
        >>> incr =  partial(func, 1)
        >>> incr(41)
        42

    See Also:
        :func:`rpartial`
    """
    return quick_fn(_partial(extract_function(func), *args, **kwargs).__call__)


def rpartial(func: Func, *args, **kwargs) -> fn:
    """
    Partially apply arguments from the right.

    Examples:
        >>> func = lambda x, y: x / y
        >>> half = rpartial(func, 2)
        >>> half(42)
        21.0

    See Also:
        :func:`partial`
    """
    func = extract_function(func)
    return quick_fn(lambda *args_, **kwargs_: func(*args_, *args, **kwargs, **kwargs_))


def curry(n: int, func: Callable = None) -> fn:
    """
    Return the curried version of a function.

    Curried functions return partial applications of the function if called with
    missing arguments:

    >>> @curry(2)
    ... def add(x, y):
    ...     return x + y

    We can call a function two ways:

    >>> add(1, 2) == add(1)(2)
    True

    This is useful for building simple functions from partial application

    >>> inc = add(1)
    >>> inc(2)
    3

    Sidekick curries most functions where it makes sense. Variadic functions
    cannot be curried if the extra arguments can be passed by position. This
    decorator inspect the decorated function to determine if it can be curried
    or not.
    """

    # Decorator forms
    if callable(n):
        func: Callable = n
        return curry(arity(func), func)
    if func is None:
        return quick_fn(lambda f: curry(n, f))
    else:
        n = arity(func) if n in (..., None) else n
        return fn.curry(n, func)
