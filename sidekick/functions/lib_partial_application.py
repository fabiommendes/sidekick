from functools import partial as _partial

from .core_functions import arity, to_callable, quick_fn
from .fn import fn, Curried
from ..typing import Func, Callable, overload, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk


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
        >>> from operator import add
        >>> incr =  sk.partial(add, 1)
        >>> incr(41)
        42

    See Also:
        :func:`rpartial`
    """
    return quick_fn(_partial(to_callable(func), *args, **kwargs).__call__)


def rpartial(func: Func, *args, **kwargs) -> fn:
    """
    Partially apply arguments from the right.

    Examples:
        >>> from operator import truediv as div
        >>> half = sk.rpartial(div, 2)
        >>> half(42)
        21.0

    See Also:
        :func:`partial`
    """
    func = to_callable(func)
    return quick_fn(lambda *args_, **kwargs_: func(*args_, *args, **kwargs, **kwargs_))


@overload
def curry(n: int, func: Callable) -> Curried:
    ...


@overload
def curry(n: int) -> Callable[[Callable], Curried]:
    ...


def curry(n, func=None):
    """
    Return the curried version of a function of n arguments.

    Curried functions return partial applications of the function if called with
    missing arguments:

    >>> add = sk.curry(2, lambda x, y: x + y)

    We can call a function two ways:

    >>> add(1, 2) == add(1)(2)
    True

    This is useful for building simple functions from partial application

    >>> succ = add(1)
    >>> succ(2)
    3

    :func:`curry` is itself a curried function, hence it can be called as

    >>> add = sk.curry(2)(lambda x, y: x + y)

    or equivalently as a decorator

    >>> @sk.curry(2)
    ... def add(x, y):
    ...     return x + y


    Currying usually requires functions of fixed number of arguments (the
    number of arguments is called the *arity* of a function). We can control
    how many arguments participate in the auto-currying by passing the arity
    number as the first argument to the :func:`curry` function.

    Variadic functions are accepted, and arity is understood as the minimum
    number of arguments necessary to invoke the function. The caller can,
    however, specify additional arguments.

    But it accepts more than 2 arguments, if needed. (Notice that only the
    first two arguments auto-curry.)

    >>> add = sk.curry(2, lambda *args: sum(args))
    >>> add(1, 2, 3, 4)
    10

    Sometimes we don't want to specify the arity of a function or don't want
    to think too much about it. :func:`curry` accepts ``'auto'`` as an arity
    specifier that makes it try to infer the arity automatically. Under the
    hood, it just calls :func:`arity` to obtain the correct value.

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
        n = arity(func) if n in (..., None, "auto") else n
        return fn.curry(n, func)
