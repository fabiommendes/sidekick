import functools
import inspect
import types

from .fn import fn
from .lib_utils import toolz, ctoolz
from sidekick.extended_semantics import as_func
from .placeholder import Placeholder

NOT_GIVEN = object()


def compose(*funcs):
    """
    Compose functions or func-like objects to operate in series.

    Returns a function that applies other functions in sequence.
    This is the same as ``f << g << h`` for :class:`sidekick.fn` functions.

    If no arguments are provided, the identity function (f(x) = x) is returned.

    >>> compose(str, _ + 1)(3)
    '4'

    See Also:
        pipe
    """
    return toolz.compose(*map(as_func, funcs))


def partial(func, *args, **kwargs):
    """
    Return a new function with partial application of the given arguments and
    keywords.

    Args:
        func:
            Function or func-like object.
        *args, **kwargs:
            Arbitrary positional and keyword arguments partially applied to the
            function.

    Examples:
        >>> from operator import add
        >>> incr =  partial(add, 1)
        >>> incr(42)
        43
    """
    return functools.partial(as_func(func), *args, **kwargs)


def memoize(func=None, cache=None, key=None):
    """
    Cache a function's result for speedy future evaluation

    Considerations:
        Trades memory for speed.
        Only use on pure functions.

    It can be used as a decorator which accepts two optional arguments: a
    initial cache dictionary and a key function that normalize inputs that are
    stored in the cache dictionary.

    Args:
        func:
            A function or function-like object (e.g., a sidekick quick lambda)
        cache (dict):
            An optional initial cache dictionary.
        key (func):
            An optional function that normalizes inputs before they are stored
            or query in the cache dictionary.

    Examples:
        >>> @memoize(cache={0: 1, 1: 1})
        ... def fib(i):
        ...     return fib(i - 1) + fib(i - 2)
        >>> fib(50)   # don't try that without memoization!
        573147844013817084101
    """
    if func is None:
        return lambda func: memoize(func, cache, key)

    return toolz.memoize(as_func(func), cache, key)


def pipe(data, *funcs):
    """
    Pipe a value through a sequence of functions.

    I.e. ``pipe(data, f, g, h)`` is equivalent to ``h(g(f(data)))`` or
    to ``data | f | g | h``, if ``f`` is a fn object.

    >>> from math import sqrt
    >>> pipe(-4, abs, sqrt)
    2.0

    This function is curried and can be called without any function argument:

    >>> arg = pipe(-4)
    >>> arg(abs, sqrt)
    2.0
    """
    if funcs:
        for func in funcs:
            data = func(data)
        return data
    else:
        return lambda *args: pipe(data, *args)


def rpartial(func, *args):
    """
    Partially apply arguments from the right.
    """
    func = as_func(func)
    return fn(lambda *args_, **kwargs: func(*(args_ + args), **kwargs))


def identity(x):
    """
    The identity function.
    """
    return x


def juxt(*funcs):
    """
    Creates a function that calls several functions with the same arguments.

    It return a tuple with the results of calling each function.
    """
    funcs = (as_func(f) for f in funcs)
    return fn(toolz.juxt(*funcs))


def const(x):
    """
    Return a function that always return x when called with any number of
    arguments.
    """
    return lambda *args, **kwargs: x


def curry(func):
    """
    Return the curried version of a function.

    Curried functions return partial applications of the function if called with
    missing arguments:

    >>> @curry
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

    spec = inspect.getfullargspec(func)
    if spec.varargs or spec.varkw or spec.kwonlyargs:
        raise TypeError('cannot curry a variadic function')

    def incomplete_factory(arity, used_args):
        return lambda *args: (
            func(*(used_args + args))
            if len(used_args) + len(args) >= arity
            else incomplete_factory(arity, used_args + args)
        )

    return incomplete_factory(len(spec.args), ())


def force_function(func, name=None):
    """
    Force callable or placeholder expression to be converted into a function.

    If function is anonymous, provide a default function name.
    """

    if isinstance(func, types.FunctionType):
        if name is not None and func.__name__ == '<lambda>':
            func.__name__ = name
        return func
    elif isinstance(func, Placeholder):
        return force_function(func._, name)
    else:
        def function(*args, **kwargs):
            return func(*args, **kwargs)

        if name is not None:
            function.__name__ = name
        else:
            function.__name__ = getattr(
                func, '__name__',
                getattr(
                    func.__class__, '__name__', 'function'
                )
            )
        return function


do = fn.curried(ctoolz.do)
