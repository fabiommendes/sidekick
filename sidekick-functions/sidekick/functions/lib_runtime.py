import time
from functools import wraps

from .core_functions import quick_fn
from .fn import fn, to_callable
from .lib_combinators import always
from .._utils import to_raisable, is_raisable
from ..typing import (
    NOT_GIVEN,
    TYPE_CHECKING,
    Func,
    Catchable,
    Literal,
    Callable,
    overload,
    Any,
    Union,
    Dict,
    T,
)

Err = Ok = Result = None

if TYPE_CHECKING:
    from .. import api as sk  # noqa: F401
    from ..api import X, Y  # noqa: F401
    from ..types.maybe import Maybe  # noqa: F401
    from ..types.result import Result  # noqa: F401

__doctest_skip__ = ["result"]


@fn
def once(func: Func) -> fn:
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

    func = to_callable(func)

    # We create the local binding without initializing the variable. We chose
    # this approach instead of initializing with a "not_given" value, since the
    # common path of returning the pre-computed result of func() can be
    # executed faster inside a try/except block
    if False:
        value = None  # noqa

    @wraps(func)
    @quick_fn
    def once_fn(*args, **kwargs):
        nonlocal value
        try:
            return value
        except NameError:
            value = func(*args, **kwargs)
            return value

    return once_fn


@overload
def thunk(
    func: type(Ellipsis), /, *args, **kwargs
) -> Callable[[Callable], Callable[[], Any]]:
    ...


@overload
def thunk(func: Callable, /, *args, **kwargs) -> Callable[[], Any]:
    ...


@fn
def thunk(func, /, *args, **kwargs):
    """
    A thunk that represents a lazy computation.

    Python thunks are represented by zero-argument functions that compute the
    value of computation on demand and store it for subsequent invocations.

    This function receives a function as the first argument, but behaves as a
    decorator if the caller passes an ellipsis.

    Example:
        >>> conf = sk.thunk(dict)
        >>> conf() is conf() == {}
        True
        >>> @sk.thunk(..., host='localhost', port=5432)
        ... def db(host, port):  # noqa
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
    # We create the local binding without initializing the variable. We chose
    # this approach instead of initializing with a "not_given" value, since the
    # common path of returning the pre-computed result of func() can be
    # executed faster inside a try/except block
    if func is ...:
        result = None  # noqa
        return lambda f: thunk(f, *args, **kwargs)

    @wraps(func)
    def get_value() -> Any:
        nonlocal result
        try:
            return result
        except NameError:
            result = func(*args, **kwargs)
            return result

    # Lambda golf:
    # thunk = lambda f, *args: (lambda v=f(*args): lambda: v)()
    return get_value


@fn.curry(2)
def call_after(n: int, func: Func, *, default=None) -> fn:
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
    """
    if n <= 0:  # nocover
        raise ValueError("n must be positive")

    @fn.wraps(func)
    def after(*args, **kwargs):
        nonlocal n
        if n == 0:
            return func(*args, **kwargs)
        else:
            n -= 1
            return default

    func = to_callable(func)
    return after


@fn.curry(2)
def call_at_most(n: int, func: Func) -> fn:
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

    if n <= 0:  # nocover
        raise ValueError("n must be positive")

    result = None  # noqa

    @fn.wraps(func)
    def at_most(*args, **kwargs):
        nonlocal n, result
        if n == 0:
            return result
        else:
            n -= 1
            result = func(*args, **kwargs)
            return result

    func = to_callable(func)
    return at_most


@fn.curry(2)
def throttle(
    dt: float,
    func: Func,
    policy: Literal["last", "block"] = "last",
    clock: Callable[[], T] = time.monotonic,
    sleep: Callable[[T], None] = time.sleep,
) -> fn:
    """
    Limit the rate of execution of func to once at each ``dt`` seconds.

    When rate-limited, returns the last result returned by func.

    Args:
        dt:
            Interval between actual function calls.
        func:
            Target function.
        policy:
            One of 'last' (default) or 'block'. Control how function behaves
            when called between two successive intervals.
            * 'last': return the last computed value.
            * 'block': block execution until deadline is reached.
        clock:
            The timing function used to compute deadlines. Defaults to ``time.monotonic``
        sleep:
            Sleep function used in conjunction with clock. Both functions must use
            the same time units.

    Example:
        >>> f = sk.throttle(1, (X * 2))
        >>> [f(21), f(14), f(7), f(0)]
        [42, 42, 42, 42]
    """

    deadline = -float("inf")
    last_result = None

    if policy == "last":

        def limited(*args, **kwargs):
            nonlocal deadline, last_result
            now = clock()
            if now >= deadline:
                deadline = now + dt
                last_result = func(*args, **kwargs)
            return last_result

    elif policy == "block":

        def limited(*args, **kwargs):
            nonlocal deadline
            now = clock()
            if now < deadline:
                sleep(deadline - now)
            deadline = now + dt
            return func(*args, **kwargs)

    else:  # nocover
        raise TypeError(f"invalid policy: {policy!r}")

    func = to_callable(func)
    return fn.wraps(func)(limited)


class Background:
    """
    Wraps a background computation.
    """

    __slots__ = "_output", "_error", "thread"
    _output: Any

    def __init__(self, target):
        from threading import Thread

        self._error = None

        def _real_target():
            try:
                self._output = target()
            except Exception as e:
                self._error = e

        self.thread = Thread(target=_real_target)
        self.thread.start()

    def __repr__(self):
        if self.thread.is_alive():
            return "Background(...)"
        elif self._error is not None:
            return f"Background({self._error!r})"
        else:
            return f"Background({self._output!r})"

    def __call__(self, **kwargs):
        return self.get(**kwargs)

    def get(self, timeout=None, *, default=NOT_GIVEN):
        """
        Return result of computation.

        Can set optional timeout and default arguments.
        """
        try:
            return self._output
        except AttributeError:
            pass
        if self._error is not None:
            raise self._error

        self.thread.join(timeout)
        if self.thread.is_alive():
            if default is NOT_GIVEN:
                raise TimeoutError
            return default
        if self._error is not None:
            raise self._error
        return self._output

    def maybe(self) -> "Maybe":  # noqa
        """
        Return Just(result), if available or Nothing.
        """
        from ..types.maybe import Just, Nothing

        sentinel = object()
        res = self.get(0, default=sentinel)
        return Nothing if res is sentinel else Just(res)

    def result(self) -> "Result":  # noqa
        """
        Wrap result in an Result value.

        Return Err(TimeoutError) if the function has not terminated yet.
        """
        from ..types.maybe import Err

        try:
            return self.maybe().to_result(TimeoutError)
        except Exception as e:
            return Err(e)


def background(func: Func, /, *args, **kwargs) -> Background:
    """
    Run function in the background with the supplied arguments.

    This function returns a Background value responsible for fetching the
    result of computation. If called with no parameters, it blocks until the
    function ends computation and return the result.

    The function also accepts the timeout and default parameters.

    Args:
        func:
            Function or callable wrapped to support being called in the
            background.

    Examples:
        >>> fib = lambda n: 1 if n <= 2 else fib(n - 1) + fib(n - 2)
        >>> res = sk.background(fib, 30)  # Do not block execution, return a thunk

        We can inspect partial results. ``res.maybe`` will return Just(value)
        if computation is completed and ``Nothing`` otherwise.

        >>> res = sk.background(fib, 30)
        >>> res.maybe()
        Nothing

        In order to inspect errors or the current state of excution, use
        the result method.

        >>> res = sk.background(fib, 30)
        >>> res.result()
        Err(TimeoutError)

        We can finally force completion using the blocking operation:

        >>> res = sk.background(fib, 30)
        >>> res.get()
        832040
    """
    func = to_callable(func)
    return Background(lambda: func(*args, **kwargs))


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


@fn.curry(2)
def catch(exc: Union[Catchable, Dict[Catchable, Any]], func: Func, /, *args, **kwargs):
    """
    Handle exception in function. If the exception occurs, it executes the given
    handler.

    Examples:
        >>> div = (X / Y)
        >>> print(sk.catch(ZeroDivisionError, div, 1, 0))
        None

        It is possible to map the return value in case of errors to other errors
        or to other values.

        >>> sk.catch({ZeroDivisionError: float('nan')}, div, 1, 0)
        nan
    """

    try:
        return func(*args, **kwargs)
    except Exception as e:
        is_exc = isinstance(exc, type)
        if is_exc and isinstance(e, exc):
            return None
        elif not is_exc:
            res = exc[type(e)]
            if is_raisable(res):
                raise res
            return res
        raise


@fn.curry(2)
def catching(errors: Catchable, func: Func):
    """
    Similar to catch, but decorates a function rewriting its error handling
    policy.

    Examples:
        >>> @sk.catching({KeyError: ValueError})
        ... def get_value(name):
        ...     return db[name]  # noqa
    """

    if isinstance(errors, type):
        errors = {errors: None}

    exceptions = tuple(errors)
    handlers = {}

    for err, handler in errors.items():
        if is_raisable(handler):
            handlers[err] = error.partial(handler)
        else:
            handlers[err] = always(handler)

    def runner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            try:
                handler_fn = handlers[type(e)]
            except KeyError:
                raise
            return handler_fn(e)

    return quick_fn(runner)


@fn
def result(func, /, *args, **kwargs) -> "Result":
    """
    Execute function and wrap result in a Result type.

    If execution is successful, return Ok(result), if it raises an exception,
    return Err(exception).

    >>> res = result(very_complex_computation, 42)  # noqa
    >>> res.is_ok  # computation was not successful!
    False
    """
    func = to_callable(func)

    try:
        res = func(*args, **kwargs)
    except Exception as ex:
        return Err(ex)
    else:
        if isinstance(res, Result):
            return res
        return Ok(res)


# noinspection PyShadowingNames
@fn.curry(2)
def retry(n: int, func: Func, *, error: Catchable = Exception, sleep=None) -> fn:
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
            except error:
                if sleep:
                    time.sleep(sleep)
        return func(*args, **kwargs)

    func = to_callable(func)
    return safe_func
