from functools import partial as _partial

import toolz
from typing import Callable, TypeVar

from ..core import fn, extract_function, Func
from ..core.fn_meta import arity as _arity

T = TypeVar("T")
__all__ = [
    *["arity", "curry", "partial", "rpartial"],  # Partial application
    *["compose", "pipe", "pipeline", "thread", "rthread"],  # Composition
    *["identity", "ridentity", "always", "rec"],  # Combinators
]


#
# Partial application
#
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
        >>> incr =  partial(lambda x, y: x + y, 1)
        >>> incr(41)
        42
    """
    return fn(_partial(extract_function(func), *args, **kwargs).__call__)


def rpartial(func: Func, *args, **kwargs) -> fn:
    """
    Partially apply arguments from the right.

    Examples:
        >>> half = rpartial(lambda x, y: x / y, 2)
        >>> half(42)
        21.0
    """
    func = extract_function(func)
    return fn(lambda *args_, **kwargs_: func(*args_, *args, **kwargs, **kwargs_))


def power(func: Func, n: int) -> fn:
    """
    Return a function that applies f to is argument n times.

        power(f, n)(x) ==> f(f(...f(x)))  # apply f n times.

    Examples:
        >>> g = power(lambda x: 2 * x, 3)
        >>> g(10)
        80
    """
    if n == 0:
        return fn(lambda x: x)
    elif n == 1:
        return fn(func)
    elif n < 0:
        raise TypeError('cannot invert function')

    func = extract_function(func)

    def power(x):
        for _ in range(n):
            x = func(x)
        return x

    return fn(power)


@fn
def arity(func: Func) -> int:
    """
    Return arity of function.

    >>> arity(lambda x, y: x + y)
    2
    """
    return _arity(func)


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
        return lambda f: curry(n, f)
    else:
        n = arity(func) if n in (..., None) else n
        return fn.curry(n, func)


#
# Function composition and pipelines
#
def compose(*funcs: Func) -> fn:
    """
    Create function that apply argument from right to left.

        compose(f, g, h, ...) ==> f << g << h << ...

    Example:
        >>> f = compose((X + 1), (X * 2))
        >>> f(2)  # double than increment
        5

    See Also:
        pipe
        pipeline
    """
    return fn(toolz.compose(*map(extract_function, funcs)))


def pipeline(*funcs: Func) -> fn:
    """
    Similar to compose, but order of application is reversed, i.e.:

        pipeline(f, g, h, ...) ==> f >> g >> h >> ...

    Example:
        >>> f = pipeline((X + 1), (X * 2))
        >>> f(2)  # increment and double
        6

    See Also:
        pipe
        compose
    """
    return fn(toolz.compose(*map(extract_function, reversed(funcs))))


@fn
def pipe(data, *funcs: Callable):
    """
    Pipe a value through a sequence of functions.

    I.e. ``pipe(data, f, g, h)`` is equivalent to ``h(g(f(data)))`` or
    to ``data | f | g | h``, if ``f, g, h`` are fn objects.

    Examples:
        >>> from math import sqrt
        >>> pipe(-4, abs, sqrt)
        2.0

    See Also:
        pipeline
        compose
        thread
        rthread
    """
    if funcs:
        for func in funcs:
            data = func(data)
        return data
    else:
        return lambda *args: pipe(data, *args)


def thread(data, *forms):
    """
    Similar to pipe, but accept extra arguments to each function in the
    pipeline.

    Arguments are passed as tuples and the value is passed as the
    first argument.

    Examples:
        >>> thread(20, (op.div, 2), (op.mul, 4), (op.add, 2))
        42.0

    See Also:
        pipe
        rthread
    """
    for form in forms:
        if isinstance(form, tuple):
            func, *args = form
        else:
            func = form
            args = ()
        data = func(data, *args)
    return data


def rthread(data, *forms):
    """
    Like thread, but data is passed as last argument to functions,
    instead of first.

    Examples:
        >>> rthread(2, (op.div, 20), (op.mul, 4), (op.add, 2))
        42.0

    See Also:
        pipe
        thread
    """
    for form in forms:
        if isinstance(form, tuple):
            func, *args = form
        else:
            func = form
            args = ()
        data = func(*args, data)
    return data


#
# Classical functions and combinators
#
# noinspection PyUnusedLocal
@fn
def identity(x: T, *args, **kwargs) -> T:
    """
    The identity function.

    Return its first argument unchanged.

    Examples:
        Identity accepts one or more positional arguments and any number of
        keyword arguments.
        >>> identity(1, 2, 3, foo=4)
        1
    """
    return x


# noinspection PyUnusedLocal
@fn
def ridentity(*args, **kwargs):
    """
    Similar to identity, but return the last positional argument and not the
    first. In the case the function receives a single argument, both identity
    functions coincide.

    >>> ridentity(1, 2, 3)
    3
    """
    if not args:
        raise TypeError('must be called with at least one positional argument.')
    return args[-1]


@fn
def always(x: T) -> Callable[..., T]:
    """
    Return a function that always return x when called with any number of
    arguments.

    Examples:
        >>> f = always(42)
        >>> f('answer', for_what='question of life, the universe ...')
        42
    """
    return lambda *args, **kwargs: x


@fn
def rec(func):
    """
    Fix func as first argument as itself.

    This is a version of the Y-combinator and is useful to implement
    recursion from scratch.

    Examples:
        In this example, the factorial receive a second argument which is the
        function it must recurse to. rec pass the function to itself so now
        the factorial only needs the usual numeric argument.
        >>> map(rec(lambda f, n: 1 if n == 0 else n * f(f, n - 1)), 
        ...     range(10)) | L
        [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880]
    """
    return fn(lambda *args, **kwargs: func(func, *args, **kwargs))
