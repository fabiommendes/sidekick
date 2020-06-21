from functools import wraps

from .core_functions import quick_fn
from .fn import fn
from ..typing import Callable, NOT_GIVEN, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk
    from ..api import X


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
    from time import time

    last_time = -float("inf")
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
            Default value to resturn if if function timeout when evaluation is
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

        def maybe(*, timeout=timeout):
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
