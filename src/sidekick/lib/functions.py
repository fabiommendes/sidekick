import functools
import inspect
import types
from typing import Callable, TypeVar

from .sequences import transform, transform_map
from .. import toolz
from ..core import extract_function, fn, Placeholder
from ..core.fn import Fn2_

NOT_GIVEN = object()
T = TypeVar("T")
S = TypeVar("S")

__all__ = [
    "partial",
    "rpartial",
    "curry",  # partial application
    "compose",
    "pipe",  # composition
    "const",
    "identity",  # combinators
    "call",
    "map_call",
    "do",
    "juxt",  # calling functions
    "memoize",
    "force_function",  # misc
]


#
# Partial application
#
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
    return functools.partial(extract_function(func), *args, **kwargs)


def rpartial(func, *args, **kwargs):
    """
    Partially apply arguments from the right.
    """
    func = extract_function(func)
    return fn(lambda *args_, **kwargs_: func(*args_, *args, **kwargs, **kwargs_))


def curry(func: Callable) -> fn:
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
        raise TypeError("cannot curry a variadic function")

    def incomplete_factory(arity, used_args):
        return lambda *args: (
            func(*(used_args + args))
            if len(used_args) + len(args) >= arity
            else incomplete_factory(arity, used_args + args)
        )

    return incomplete_factory(len(spec.args), ())


#
# Function Composition and pipelines
#
def compose(*funcs: Callable) -> fn:
    """
    Compose functions or func-like objects to operate in series.

    Returns a function that applies other functions in sequence.
    This is the same as ``f << g << h`` for :class:`sidekick.fn` functions.

    If no arguments are provided, the identity function (f(x) = x) is returned.

    >>> from sidekick import placeholder as _
    >>> compose(str, _ + 1)(3)
    '4'

    See Also:
        pipe
    """
    return fn(toolz.compose(*map(extract_function, funcs)))


def pipe(data, *funcs: Callable):
    """
    Pipe a value through a sequence of functions.

    I.e. ``pipe(data, f, g, h)`` is equivalent to ``h(g(f(data)))`` or
    to ``data | f | g | h``, if ``f, g, h`` are fn objects.

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


#
# Classical functions and combinators
#
def identity(x: T) -> T:
    """
    The identity function.
    """
    return x


def const(x: T) -> Callable[..., T]:
    """
    Return a function that always return x when called with any number of
    arguments.
    """
    return lambda *args, **kwargs: x


#
# Function calling
#
def call(*args, **kwargs):
    """
    Creates a function that receives another function and apply the given
    arguments.

    >>> from sidekick import op
    >>> caller = call(1, 2)
    >>> caller(op.add)
    3

    This function can be used as a decorator to declare self calling functions:

    >>> @call()
    ... def _patch_module():
    ...     import builtins
    ...
    ...     builtins.evil = lambda: print('Evil patch')
    ...     return True

    The variable ``_patch_module`` will be assigned to the return value of the
    function and the function object itself will be garbage collected.
    """
    return lambda f: f(*args, **kwargs)


def map_call(*args, **kwargs):
    """
    Transforms the arguments passed to the result by the functions provided as
    arguments.

    >>> from sidekick import op, placeholder as _
    >>> transformer = map_call(_ + 1, _ * 2)
    >>> func = transformer(op.add)
    >>> func(1, 2) # (1 + 1) + (2 * 2)
    6
    """
    args = tuple(map(extract_function, args))
    kwargs = transform(extract_function, kwargs)
    return lambda *args_, **kwargs_: lambda f: f(
        *transform(args, args_), **transform_map(kwargs, kwargs_)
    )


@Fn2_
def do(func, x, *args, **kwargs):
    """ Runs ``func`` on ``x``, returns ``x``

    Because the results of ``func`` are not returned, only the side
    effects of ``func`` are relevant.

    Logging functions can be made by composing ``do`` with a storage function
    like ``list.append`` or ``file.write``

    >>> log = []
    >>> inc = do(log.append) >> fn(_ + 1)
    >>> [inc(1), inc(11)]
    [2, 12]
    >>> log
    [1, 11]
    """
    func(x, *args, **kwargs)
    return x


def juxt(*funcs: Callable) -> fn:
    """
    Creates a function that calls several functions with the same arguments.

    It return a tuple with the results of calling each function.
    """
    funcs = (extract_function(f) for f in funcs)
    return fn(toolz.juxt(*funcs))


#
# Misc
#
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

    return toolz.memoize(extract_function(func), cache, key)


def force_function(func, name=None) -> Callable:
    """
    Force callable or placeholder expression to be converted into a function
    object.

    If function is anonymous, provide a default function name.
    """

    if isinstance(func, types.FunctionType):
        if name is not None and func.__name__ == "<lambda>":
            func.__name__ = name
        return func
    elif isinstance(func, Placeholder):
        return force_function(func._sk_function_, name)
    else:

        def function(*args, **kwargs):
            return func(*args, **kwargs)

        if name is not None:
            function.__name__ = name
        else:
            function.__name__ = getattr(
                func, "__name__", getattr(func.__class__, "__name__", "function")
            )
        return function
