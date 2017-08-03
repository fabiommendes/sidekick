import inspect

import types
from functools import partial

from .fn import fn
from .placeholder import placeholder
from .lib_utils import as_func, toolz


NOT_GIVEN = object()

__all__ = [
    'compose', 'do', 'memoize', 'pipe', 'partial', 'rpartial',
    'force_function', 'identity', 'juxt', 'const', 'curry',
]

compose = toolz.compose
do = toolz.do
memoize = toolz.memoize
pipe = toolz.pipe
partial = partial


def force_function(func, name=None):
    """
    Force callable or placeholder expression to be converted to a function.

    If function is anonymous, provide a default function name.
    """

    if isinstance(func, types.FunctionType):
        if name is not None and func.__name__ == '<lambda>':
            func.__name__ = name
        return func
    elif isinstance(func, placeholder):
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


def rpartial(func, *args):
    """
    Partially apply arguments from the right.
    """
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


@fn
def const(x):
    """
    Return a function that always return x when called with any number of
    arguments.
    """
    return lambda *args, **kwargs: x


def curry(func):
    """
    Return the curried version of a function.
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
