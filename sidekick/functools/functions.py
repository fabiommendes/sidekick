import time
from collections.abc import Iterable, Mapping
from functools import singledispatch
from typing import TypeVar

from .. import _toolz as toolz
from ..functions import always, fn, quick_fn, to_callable

NOT_GIVEN = object()
T = TypeVar("T")
S = TypeVar("S")

__all__ = [
    *["call", "call_over", "do"],  # Function calling
    *["error", "catch", "retry"],  # Error control
]


#
# Function calling
#
def call(*args, **kwargs) -> fn:
    """
    Creates a function that receives another function and apply the given
    arguments.

    Examples:
        >>> caller = call(1, 2)
        >>> caller(op.add), caller(op.mul)
        (3, 2)

        This function can be used as a decorator to declare self calling
        functions:

        >>> @call()
        ... def patch_module():
        ...     import builtins
        ...
        ...     builtins.evil = lambda: print('Evil patch')
        ...     return True

        The variable ``patch_module`` will be assigned to the return value of the
        function and the function object itself will be garbage collected.
    """
    return quick_fn(lambda f: f(*args, **kwargs))


def call_over(*args, **kwargs) -> fn:
    """
    Transforms the arguments passed to the result by the functions provided as
    arguments.

    Return a factory function that binds the transformations to its argument

    Examples:
        >>> transformer = call_over(op.add(1), op.mul(2))
        >>> func = transformer(op.add)
        >>> func(1, 2) # (1 + 1) + (2 * 2)
        6
    """
    f_args = tuple(map(to_callable, args))
    f_kwargs = {k: to_callable(v) for k, v in kwargs.items()}
    identity = lambda x: x

    @quick_fn
    def transformed(func):
        @quick_fn
        def wrapped(*args, **kwargs):
            try:
                extra = args[len(f_args) :]
            except IndexError:
                raise TypeError("not enough arguments")
            args = (f(x) for f, x in zip(f_args, args))
            for k, v in kwargs.items():
                kwargs[k] = f_kwargs.get(k, identity)(v)
            return func(*args, *extra, **kwargs)

        return wrapped

    return transformed


@fn.curry(2)
def do(func, x, *args, **kwargs):
    """
    Runs ``func`` on ``x``, returns ``x``.

    Because the results of ``func`` are not returned, only the side
    effects of ``func`` are relevant.

    Logging functions can be made by composing ``do`` with a storage function
    like ``list.append`` or ``file.write``

    Examples:
        >>> log = []
        >>> inc = do(log.append) >> (X + 1)
        >>> [inc(1), inc(11)]
        [2, 12]
        >>> log
        [1, 11]
    """
    func(x, *args, **kwargs)
    return x


# Can we implement this in a robust way? It seems to be impossible with Python
# unless we accept fragile solutions based on killing threads, multiprocessing
# and signals
#
# @fn.curry(2)
# def timeout(*args, **kwargs):
#     """
#     Limit the function execution time to the given timeout (in seconds).
#
#     Example:
#         >>> fib = lambda n: 1 if n <= 1 else fib(n - 1) + fib(n - 2)
#         >>> timeout(0.25, fib, 10)  # wait at most 0.25 seconds
#         89
#         >>> timeout(0.25, fib, 50)  # stops before the thermal death of the universe
#         Traceback (most recent call last)
#         ...
#         TimeoutError:
#
#     Args:
#         timeout (float, seconds):
#             The maximum duration of function execution
#         func:
#             Function to be executed
#     """
#     from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
#
#     executor = ProcessPoolExecutor
#     timeout, func, *args = args
#     if func in ('thread', 'process'):
#         executor = ThreadPoolExecutor if func == 'thread' else ProcessPoolExecutor
#         func, *args = args
#
#     with executor() as e:
#         future = e.submit(func, *args, **kwargs)
#         return future.result(timeout=timeout)


#
# Error control
#
@fn
def error(exc):
    """
    Raises the given exception.

    If argument is not an exception, raises ValueError(exc).

    Examples:
        >>> error('some error')
        Traceback (most recent call last):
        ...
        ValueError: some error
    """
    if (
        isinstance(exc, Exception)
        or isinstance(exc, type)
        and issubclass(exc, Exception)
    ):
        raise exc
    else:
        raise ValueError(exc)


@fn.curry(2)
def catch(exception, func, *, handler=None, raises=None):
    """
    Handle exception in function. If the exception occurs, it executes the given
    handler.

    Examples:
        >>> nan = always(float('nan'))
        >>> div = catch(ZeroDivisionError, (X / Y), handler=nan)
        >>> div(1, 0)
        nan

        The function can be used to re-write exceptions by passing the optional
        raises parameter.

        >>> @sk.catch(KeyError, raises=ValueError("invalid name"))
        ... def get_value(name):
        ...     return data[name]
    """

    if isinstance(raises, Exception):
        handler = error.partial(raises)
    elif raises is not None:
        handler = lambda e: error(raises(e))
    elif handler is None:
        handler = always(None)
    return quick_fn(toolz.excepts(exception, func, handler))


@fn.curry(2)
def retry(n: int, func, *, error=Exception, sleep=None):
    """
    Retry to execute function at least n times before raising an error.

    This is useful for functions that may fail due to interaction with external
    resources (e.g., fetch data from the network).

    Args:
        n:
            Maximum number of times to execute function
        func:
            Function that may raise errors.
        error:
            Exception or tuple with suppressed exceptions.
        sleep:
            Interval in which it sleeps between attempts.

    Example:
        >>> queue = [111, 7, None, None]
        >>> process = retry(5, lambda x: queue.pop() * x)
        >>> process(6)
        42
    """

    @fn.wraps(func)
    def safe_func(*args, **kwargs):
        for _ in range(n - 1):
            try:
                return func(*args, **kwargs)
            except error as ex:
                if sleep:
                    time.sleep(sleep)
        return func(*args, **kwargs)

    return safe_func


#
# Misc
#


@singledispatch
def _fmap(f, x):
    try:
        fmap = x.map
    except AttributeError:
        tname = type(x).__name__
        raise NotImplementedError(f"no map function implemented for {tname}")
    else:
        return fmap(f)


#
# Functor map implementations
#
@fn
def fmap(f, x):
    """
    Register actions to how interpret``f @ x`` if f is a sidekick function.

    Example:
        >>> fmap((X * 2), [1, 2, 3])
        [2, 4, 6]
    """
    return _functor_dispatch(type(x))(f, x)


_functor_dispatch = _fmap.dispatch
fmap.register = lambda cls: _fmap.register(cls)
fmap.dispatch = _fmap.dispatch


@fmap.register(str)
def _(f, st):
    return "".join(map(f, st))


@fmap.register(list)
def _(f, obj):
    return [f(x) for x in obj]


@fmap.register(tuple)
def _(f, obj):
    return tuple(f(x) for x in obj)


@fmap.register(set)
def _(f, obj):
    return {f(x) for x in obj}


@fmap.register(dict)
def _(f, obj):
    return {k: f(v) for k, v in obj.items()}


@fmap.register(Mapping)
def _(f, obj):
    return ((k, f(v)) for k, v in obj.items())


@fmap.register(Iterable)
def _(f, obj):
    return ((k, f(v)) for k, v in obj.items())


#
# Removed functions
#
# toolz.memoize ==> use sk.lru_cache
