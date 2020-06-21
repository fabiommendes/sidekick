from functools import wraps
from typing import Callable, Any

from .core_functions import quick_fn, to_callable
from .fn import fn
from ..typing import Func, T, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk
    from ..api import X


@fn
def identity(x: T, *args, **kwargs) -> T:
    """
    The identity function.

    Return its first argument unchanged. Identity accepts one or more positional
    arguments and any number of keyword arguments.

    Examples:
        >>> sk.identity(1, 2, 3, foo=4)
        1

    See Also:
        :func:`ridentity`
    """
    return x


@fn
def ridentity(*args: T, **kwargs) -> T:
    """
    Return last positional argument.

    Similar to identity, but return the last positional argument and not the
    first. In the case the function receives a single argument, both identity
    functions coincide.

    Examples
        >>> sk.ridentity(1, 2, 3)
        3

    See Also:
        :func:`identity`
    """
    if args:
        return args[-1]
    raise TypeError("must be called with at least 1 positional argument")


@fn
def always(x: T) -> Callable[..., T]:
    """
    Return a function that always return x when called with any number of
    arguments.

    Examples:
        >>> f = sk.always(42)
        >>> f('answer', for_what='question of life, the universe ...')
        42
    """
    return quick_fn(lambda *args, **kwargs: x)


@fn
def rec(func: Callable[..., Any]) -> fn:
    """
    Fix func first argument as itself.

    This is a version of the Y-combinator and is useful to implement
    recursion from scratch.

    Examples:
        In this example, the factorial receive a second argument which is the
        function it must recurse to. rec pass the function to itself so now
        the factorial only needs the usual numeric argument.

        >>> sk.map(
        ...     sk.rec(lambda f, n: 1 if n == 0 else n * f(f, n - 1)),
        ...     range(10),
        ... )
        sk.iter([1, 1, 2, 6, 24, 120, ...])
    """
    return quick_fn(lambda *args, **kwargs: func(func, *args, **kwargs))


@fn
def trampoline(func: Callable[..., tuple]) -> Callable[..., Any]:
    """
    Decorator that implements tail recursion via the trampoline technique.

    Trampoline functions accept

    Args:
        func:
            A function that returns (ret, *args) in which ret is True if function
            should return and False if it should recurse. The function recurse
            by passing the results args and keyword arguments to func.

    Examples:
        >>> @sk.trampoline
        ... def fat(n, acc=1):
        ...     if n > 0:
        ...         return n - 1, acc * n
        ...     else:
        ...         raise StopIteration(acc)
        >>> fat(5)
        120
    """

    @wraps(func)
    def function(*args, **kwargs):
        try:
            while True:
                args = func(*args, **kwargs)
        except StopIteration as ex:
            return ex.args[0]

    return function


def power(func: Func, n: int) -> fn:
    """
    Return a function that applies f to is argument n times.

        power(f, n)(x) ==> f(f(...f(x)))  # apply f n times.

    Examples:
        >>> g = sk.power((2 * X), 3)
        >>> g(10)
        80
    """
    if n == 0:
        return fn(lambda x: x)
    elif n == 1:
        return fn(func)
    elif n < 0:
        raise TypeError("cannot invert function")

    func = to_callable(func)

    @quick_fn
    def power_fn(x):
        for _ in range(n):
            x = func(x)
        return x

    return power_fn


@fn
def value(fn_or_value, *args, **kwargs):
    """
    Evaluate argument, if it is a function or return it otherwise.

    Args:
        fn_or_value:
            Callable or some other value. If input is a callable, call it with
            the provided arguments and return. Otherwise, simply return.

    Examples:
        >>> value(42)
        42
        >>> value(lambda: 42)
        42
    """
    if callable(fn_or_value):
        return fn_or_value(*args, **kwargs)
    return fn_or_value
