import time
from functools import wraps

from .core_functions import quick_fn
from .fn import fn
from .lib_combinators import always
from .._toolz import excepts
from ..typing import Callable, NOT_GIVEN, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk, time
    from ..api import X, Y
    from ..types.maybe import Maybe

    # Help with Pycharm's confusion with doctrings
    host: None
    port: None
    name: None
    data: None


@fn
def once(func: Callable) -> fn:
    """
    Limit function to a single invocation.

    Repeated calls to the function return the value of the first invocation.

    Examples:
        This is useful to wrap initialization routines or singleton factories.
        >>> @sk.once
        ... def configure():
        ...     print('setting up...')
        ...     return {'status': 'ok'}
        >>> configure()
        setting up...
        {'status': 'ok'}

    See Also:
        :func:`thunk`
        :func:`call_after`
        :func:`call_at_most`
    """

    # We create the local binding without initializing the variable. We chose
    # this approach instead of initializing with a "not_given" value, since the
    # common path of returning the pre-computed result of func() can be
    # executed faster inside a try/except block
    result = None

    @wraps(func)
    @quick_fn
    def once_fn(*args, **kwargs):
        nonlocal result
        try:
            return result
        except NameError:
            result = func(*args, **kwargs)
            return result

    del result
    return once_fn


@fn
def thunk(*args, **kwargs):
    """
    A thunk that represents a lazy computation.

    Python thunks are represented by zero-argument functions that compute the
    value of computation on demand and store it for subsequent invocations.

    This function is designed to be used as a decorator.

    Example:
        >>> @sk.thunk(host='localhost', port=5432)
        ... def db(host, port):
        ...     print(f'connecting to SQL server at {host}:{port}...')
        ...     return {'host': host, 'port': port}
        >>> db()
        connecting to SQL server at localhost:5432...
        {'host': 'localhost', 'port': 5432}
        >>> db()
        {'host': 'localhost', 'port': 5432}

    See Also:
        :func:`once`
    """

    def decorator(func, has_result=False):
        # We create the local binding without initializing the variable. We chose
        # this approach instead of initializing with a "not_given" value, since the
        # common path of returning the pre-computed result of func() can be
        # executed faster inside a try/except block
        if has_result:
            result = None

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


@fn.curry(2)
def call_after(n, func, *, default=None):
    """
    Creates a function that invokes func once it's called more than n times.

    Args:
        n:
            Number of times before starting invoking n.
        func:
            Function to be invoked.
        default:
            Value returned before func() starts being called.

    Example:
        >>> f = sk.call_after(2, (X * 2), default=0)
        >>> [f(1), f(2), f(3), f(4), ...]
        [0, 0, 6, 8, ...]

    See Also:
        :func:`once`
        :func:`call_at_most`
    """

    @fn.wraps(func)
    def after(*args, **kwargs):
        nonlocal n
        if n == 0:
            return func(*args, **kwargs)
        else:
            n -= 1
            return default

    return after


@fn.curry(2)
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

    Examples:
        >>> log = sk.call_at_most(2, print)
        >>> log("error1"); log("error2"); log("error3"); log("error4")
        error1
        error2

    See Also:
        :func:`once`
        :func:`call_after`
    """

    if n <= 0:
        raise ValueError("n must be positive")

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


@fn.curry(2)
def throttle(dt, func):
    """
    Limit the rate of execution of func to once at each ``dt`` seconds.

    When rate-limited, returns the last result returned by func.

    Example:
        >>> f = sk.throttle(1, (X * 2))
        >>> [f(21), f(14), f(7), f(0)]
        [42, 42, 42, 42]
    """

    last_time = -float("inf")
    last_result = None

    @fn.wraps(func)
    def limited(*args, **kwargs):
        nonlocal last_time, last_result
        now = time.monotonic()
        if now - last_time >= dt:
            last_time = now
            last_result = func(*args, **kwargs)
        return last_result

    return limited


@fn.curry(1)
def background(func, *, timeout: float = None, default=NOT_GIVEN):
    """
    Return a function that executes in the background.

    The transformed function return a thunk that forces the evaluation of the
    function in a blocking manner. Function can also be used as a decorator.

    Args:
        func:
            Function or callable wrapped to support being called in the
            background.
        timeout (float):
            Timeout in seconds.
        default:
            Default value to return if if function timeout when evaluation is
            requested, otherwise, raises a TimeoutError.

    Examples:

        >>> fib = lambda n: 1 if n <= 2 else fib(n - 1) + fib(n - 2)
        >>> fib_bg = sk.background(fib, timeout=1.0)
        >>> result = fib_bg(10)  # Do not block execution, return a thunk
        >>> result()             # Call the result to get value (blocking operation)
        55
    """

    from threading import Thread

    @fn.wraps(func)
    def background_fn(*args, **kwargs):
        output = None

        def target():
            nonlocal output
            output = func(*args, **kwargs)

        thread = Thread(target=target)
        thread.start()

        @once
        def out():
            """
            Return result of computation.
            """
            thread.join(timeout)
            if thread.is_alive():
                if default is NOT_GIVEN:
                    raise TimeoutError
                return default
            return output

        def maybe(*, timeout=timeout) -> "Maybe":
            """
            Return result if available.
            """
            from ..types.maybe import Just, Nothing

            thread.join(timeout)
            if thread.is_alive():
                return Nothing
            return Just(output)

        out.maybe = maybe
        return out

    return background_fn


@fn
def error(exc):
    """
    Raises the given exception.

    If argument is not an exception, raises ValueError(exc).

    Examples:
        >>> sk.error('some error')
        Traceback (most recent call last):
        ...
        ValueError: some error

    See Also:
        * :func:`raising`: create a function that raises an error instead of
        raising it immediately
    """
    raise to_raisable(exc)


@fn.curry(1)
def raising(exc, n_args=None):
    """
    Creates function that raises the given exception.

    If argument is not an exception, raises ValueError(exc). The returning
    function accepts any number of arguments.

    Examples:
        >>> func = sk.raising('some error')
        >>> func()
        Traceback (most recent call last):
        ...
        ValueError: some error

    See Also:
        * :func:`raising`: create a function that raises an error instead of
        raising it immediately
    """

    if n_args:

        @fn
        def error_raiser(*args, **kwargs):
            args = args[:n_args]
            raise to_raisable(exc(*args))

        return error_raiser
    else:
        return fn(lambda *args, **kwargs: error(exc))


@fn.curry(2)
def catch(exception, func, *, handler=None, raises=None):
    """
    Handle exception in function. If the exception occurs, it executes the given
    handler.

    Examples:
        >>> nan = sk.always(float('nan'))
        >>> div = sk.catch(ZeroDivisionError, (X / Y), handler=nan)
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
    return quick_fn(excepts(exception, func, handler))


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
        >>> process = sk.retry(5, lambda n: queue.pop() * n)
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
# Auxiliary functions
#
def is_raisable(obj):
    """
    Test if object is valid in a "raise obj" statement.
    """

    return isinstance(obj, Exception) or (
        isinstance(obj, type) and issubclass(obj, Exception)
    )


def is_catchable(obj):
    """
    Check if object is valid in a "except obj" statement.
    """

    if isinstance(obj, tuple):
        return all(isinstance(x, type) and issubclass(x, Exception) for x in obj)
    return isinstance(obj, type) and issubclass(obj, Exception)


def to_raisable(obj, exception=ValueError):
    """
    Wrap object in exception if object is not valid in a "raise obj" statement.
    """

    if not is_raisable(obj):
        return exception(obj)
    return obj
