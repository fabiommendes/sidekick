from collections.abc import Iterable, Mapping
from functools import singledispatch

from sidekick.functions import fn, quick_fn, to_callable

NOT_GIVEN = object()


# TODO: Find a better name and API so it is usable to normalize arguments before
#  passing them to implementation.
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


# TODO: Can we implement this in a robust way? It seems to be impossible with Python
#  unless we accept fragile solutions based on killing threads, multiprocessing
#  and signals
@fn.curry(2)
def timeout(*args, **kwargs):
    """
    Limit the function execution time to the given timeout (in seconds).

    Example:
        >>> fib = lambda n: 1 if n <= 1 else fib(n - 1) + fib(n - 2)
        >>> timeout(0.25, fib, 10)  # wait at most 0.25 seconds
        89
        >>> timeout(0.25, fib, 50)  # stops before the thermal death of the universe
        Traceback (most recent call last)
        ...
        TimeoutError:

    Args:
        timeout (float, seconds):
            The maximum duration of function execution
        func:
            Function to be executed
    """
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

    executor = ProcessPoolExecutor
    timeout, func, *args = args
    if func in ("thread", "process"):
        executor = ThreadPoolExecutor if func == "thread" else ProcessPoolExecutor
        func, *args = args

    with executor() as e:
        future = e.submit(func, *args, **kwargs)
        return future.result(timeout=timeout)


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


@singledispatch
def _fmap(f, x):
    try:
        fmap = x.map
    except AttributeError:
        tname = type(x).__name__
        raise NotImplementedError(f"no map function implemented for {tname}")
    else:
        return fmap(f)


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
