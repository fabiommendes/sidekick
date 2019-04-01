import time
from collections.abc import Iterable, Mapping
from functools import wraps, singledispatch

import types
from typing import Callable, TypeVar

from .composition import always
from .. import toolz
from ..core import Placeholder, fn, extract_function

NOT_GIVEN = object()
T = TypeVar("T")
S = TypeVar("S")

__all__ = [
    *["call", "call_over", "do", "juxt"],  # Function calling
    *["call_after", "call_at_most", "once", "thunk", "splice"],  # Call filtering
    *["throttle", "background"],  # Runtime control
    *["flip", "select_args", "skip_args", "keep_args"],  # Runtime control
    *["error", "ignore_error", "retry"],  # Error control
    *["force_function"],  # Misc
]


#
# Function calling
#
def call(*args, **kwargs):
    """
    Creates a function that receives another function and apply the given
    arguments.

    >>> caller = call(1, 2)
    >>> caller(op.add), caller(op.mul)
    (3, 2)

    This function can be used as a decorator to declare self calling functions:

    >>> @call()
    ... def patch_module():
    ...     import builtins
    ...
    ...     builtins.evil = lambda: print('Evil patch')
    ...     return True

    The variable ``patch_module`` will be assigned to the return value of the
    function and the function object itself will be garbage collected.
    """
    return fn(lambda f: f(*args, **kwargs))


def call_over(*args, **kwargs):
    """
    Transforms the arguments passed to the result by the functions provided as
    arguments.

    Return a factory function that binds the transformations to its argument

    >>> transformer = call_over(op.add(1), op.mul(2))
    >>> func = transformer(op.add)
    >>> func(1, 2) # (1 + 1) + (2 * 2)
    6
    """
    f_args = tuple(map(extract_function, args))
    f_kwargs = {k: extract_function(v) for k, v in kwargs.items()}
    identity = lambda x: x

    @fn
    def transformed(func):
        @fn
        def wrapped(*args, **kwargs):
            try:
                extra = args[len(f_args):]
            except IndexError:
                raise TypeError('not enough arguments')
            args = (f(x) for f, x in zip(f_args, args))
            for k, v in kwargs.items():
                kwargs[k] = f_kwargs.get(k, identity)(v)
            return func(*args, *extra, **kwargs)

        return wrapped

    return transformed


@fn.annotate(2)
def do(func, x, *args, **kwargs):
    """
    Runs ``func`` on ``x``, returns ``x``.

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


def juxt(*funcs: Callable, first=None, last=None) -> fn:
    """
    Creates a function that calls several functions with the same arguments.

    It return a tuple with the results of calling each function.
    """
    funcs = (extract_function(f) for f in funcs)

    if first is True:
        result_func, *funcs = funcs
        if not funcs:
            return fn(result_func)
        funcs = tuple(funcs)

        def juxt_first(*args, **kwargs):
            result = result_func(*args, **kwargs)
            for func in funcs:
                func(*args, **kwargs)
            return result

        return fn(juxt_first)

    if last is True:
        result_func, *funcs = funcs
        if not funcs:
            return fn(result_func)
        funcs = tuple(funcs)

        def juxt_last(*args, **kwargs):
            for func in funcs:
                func(*args, **kwargs)
            return result_func(*args, **kwargs)

        return fn(juxt_last)

    return fn(toolz.juxt(*funcs))


#
# Call filtering
#
@fn.annotate(2)
def call_after(n, func, *, result=None):
    """
    Creates a function that invokes func once it's called n or more times.

    Args:
        n:
            Number of times before starting invoking n.
        func:
            Function to be invoked.
        result:
            Value returned func() starts being called.
    """

    @fn.wraps(func)
    def after(*args, **kwargs):
        nonlocal n
        if n == 0:
            return func(*args, **kwargs)
        else:
            n -= 1
            return result

    return after


@fn.annotate(2)
def call_at_most(n, func):
    """
    Creates a function that invokes func while it's called less than n times.
    Subsequent calls to the created function return the result of the last
    func invocation.

    Args:
        n:
            The number of calls at which func is no longer invoked.
        func:
            Function to restrict.
    """

    if n <= 0:
        raise ValueError('n must be positive')

    result = None

    @fn.wraps(func)
    def at_most(*args, **kwargs):
        nonlocal n, result
        if n == 0:
            return result
        else:
            n -= 1
            result = func(*args, **kwargs)
            return result

    return at_most


@fn
def once(func):
    """
    Creates a function that is restricted to invoking func once. Repeat calls
    to the function return the value of the first invocation.
    """

    # We create the local binding without initializing the variable. We chose
    # this approach instead of initializing with a "not_given" value, since the
    # common path of returning the pre-computed result of func() can be
    # executed faster inside a try/except block
    if False:
        result = None

    @wraps(func)
    def limited(*args, **kwargs):
        nonlocal result
        try:
            return result
        except NameError:
            result = func(*args, **kwargs)
            return result

    return limited


def thunk(*args, **kwargs):
    """
    Creates a thunk that represents a lazy computation. Python thunks are
    represented by zero-argument functions that compute the value of
    computation by demand.

    This function is designed to be used as a decorator.
    """

    if False:
        result = None

    def decorator(func):
        @wraps(func)
        def limited():
            nonlocal result
            try:
                return result
            except NameError:
                result = func(*args, **kwargs)
                return result

        return limited

    return fn(decorator)


@fn
def splice(func):
    """
    Return a function that receives variadic arguments and pass them as a tuple
    to func.

    Args:
        func:
            Function that receives a single tuple positional argument.
    """
    return fn(lambda *args, **kwargs: func(args, **kwargs))


#
# Time control
#
@fn.annotate(2)
def throttle(dt, func):
    """
    Limit the rate of execution of func to once at each ``dt`` seconds.

    When rate-limited, returns the last result returned by func.
    """
    from time import time
    last_time = -float('inf')
    last_result = None

    @fn.wraps(func)
    def limited(*args, **kwargs):
        nonlocal last_time, last_result
        now = time()
        if now - last_time >= dt:
            last_time = now
            last_result = func(*args, **kwargs)
        return last_result

    return limited


@fn
def background(func, *, timeout=None):
    """
    Return a function that executes in the background.

    The transformed function return a thunk that forces the evaluation of the
    function in a blocking manner.

    Examples:
    >>> fib = lambda n: 1 if n <= 2 else fib(n - 1) + fib(n - 2)
    >>> fib_bg = background(fib, timeout=1.0)
    >>> result = fib_bg(10)  # Do not block execution, return a thunk
    >>> result()             # Call the result to get value (blocking operation)
    55
    """
    from threading import Thread

    def caller(*args, **kwargs):
        output = None

        def target():
            nonlocal output
            output = func(*args, **kwargs)

        thread = Thread(target=target)
        thread.start()

        @once
        def result():
            thread.join(timeout)
            return output

        return result

    return caller


# Can we implement this in a robust way? It seems to be impossible with Python
# unless we accept fragile solutions based on killing threads, multiprocessing
# and signals
#
# @fn.annotate(2)
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
# Argument order
#
@fn
def flip(func):
    """
    Flip the order of arguments in a binary operator.

    The resulting function is always curried.
    """
    func = extract_function(func)
    return fn.annotate(2)(lambda x, y: func(y, x))


@fn
def reversed(func):
    """
    Creates a function that invokes func with the positional arguments order
    """
    return fn(lambda *args, **kwargs: func(*args[::-1], **kwargs))


@fn.annotate(2)
def select_args(idx, func):
    """
    Creates a function that calls func with the arguments reorganized.
    """
    return lambda *args, **kwargs: func(*(args[i] for i in idx), **kwargs)


@fn.annotate(2)
def skip_args(n, func):
    """
    Skips the first n positional arguments before calling func.
    """
    return lambda *args, **kwargs: func(*args[n:], **kwargs)


@fn.annotate(2)
def keep_args(n, func):
    """
    Uses only the first n positional arguments to call func.
    """
    return lambda *args, **kwargs: func(*args[:n], **kwargs)


#
# Error control
#
@fn
def error(exc):
    """
    Raises the given exception.

    If argument is not an exception, raises ValueError(exc).
    """
    if isinstance(exc, Exception):
        raise exc
    elif isinstance(exc, type) and issubclass(exc, Exception):
        raise exc()
    else:
        raise ValueError(exc)


@fn.annotate(2)
def ignore_error(exception, func, *, handler=always(None)):
    """
    Ignore exception in function. If the exception occurs, it executes the given
    handler.
    """
    return toolz.excepts(exception, func, handler)


@fn.annotate(2)
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

        def f(*args, **kwargs):
            return func(*args, **kwargs)

        if name is not None:
            f.__name__ = name
        else:
            name = getattr(func.__class__, "__name__", "function")
            f.__name__ = getattr(func, "__name__", name)
        return f


@singledispatch
def _fmap(f, x):
    try:
        fmap = x.map
    except AttributeError:
        tname = type(x).__name__
        raise NotImplementedError(f'no map function implemented for {tname}')
    else:
        return fmap(f)


#
# Functor map implementations
#
@fn
def fmap(f, x):
    """
    Register actions to how interpret``f @ x`` if f is a sidekick function.
    """
    return _functor_dispatch(type(x))(f, x)


_functor_dispatch = _fmap.dispatch
fmap.register = lambda cls: _fmap.register(cls)
fmap.dispatch = _fmap.dispatch


@fmap.register(str)
def _(f, st):
    return ''.join(map(f, st))


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
    return ((k, f(v)) for k, v in ob1j.items())


@fmap.register(Iterable)
def _(f, obj):
    return ((k, f(v)) for k, v in obj.items())

#
# Removed functions
#
# toolz.memoize ==> use sk.lru_cache
