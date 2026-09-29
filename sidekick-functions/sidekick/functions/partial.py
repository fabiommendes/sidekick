from functools import partial as _partial
from typing import Any, overload

from sidekick.protocols import to_callable

from .introspection import arity
from .utils import fn_t, Fn, WrappedFunction

NOT_GIVEN: Any = object()


class Partial(WrappedFunction[fn_t]):
    def partial(self, *args, **kwargs) -> Fn:
        """
        Partially apply arguments.

        See also:
            :func:`partial`
        """
        return self._wrap(partial(self, *args, **kwargs))

    def rpartial(self, *args, **kwargs) -> Fn:
        """
        Partially apply arguments from right to left.

        See also:
            :func:`rpartial`
        """
        return self._wrap(partial(self, *args, **kwargs))

    def curry(self, n: int = NOT_GIVEN) -> Fn:
        """
        Return a curried version of function.

        See also:
            :func:`curry`
        """
        if n is NOT_GIVEN:
            n = arity(self)
        return self._wrap(curry(n, self))

    def curried(self, *args, **kwargs) -> Any:
        """
        Execute a curried version of function.

        If not all positional arguments are given, return a function
        that receives the remaining arguments.

        See also:
            :func:`curry`
        """
        return self.curry()(*args, **kwargs)


def partial(func: Fn, /, *args, **kwargs) -> Fn:
    """
    Return a new function that partially apply the given arguments and
    keywords.

    Additional positional and keyword arguments after partially applied to
    function

    Args:
        func:
            Function or func-like object.

    Examples:
        >>> from operator import add
        >>> incr =  sk.partial(add, 1)
        >>> incr(41)
        42

    See also:
        :func:`rpartial`
        :func:`defaults`
    """
    return _partial(to_callable(func), *args, **kwargs)


def rpartial(func: Fn, /, *args, **kwargs) -> Fn:
    """
    Partially apply arguments from the right.

    Examples:
        >>> from operator import truediv as div
        >>> half = sk.rpartial(div, 2)
        >>> half(42)
        21.0

    See also:
        :func:`partial`
    """
    func = to_callable(func)
    return lambda *args_, **kwargs_: func(*args_, *args, **kwargs, **kwargs_)


@overload
def curry(n: int, func: Fn) -> Fn:
    ...


@overload
def curry(n: int) -> Fn[[Fn], Fn]:  # noqa: F811
    ...


def curry(n, func=None):  # noqa: F811
    """
    Return the curried version of a function of n arguments.

    Curried functions return partial applications of the function if called with
    missing arguments:

    >>> add = sk.curry(2, lambda x, y: x + y)

    We can call a function two ways:

    >>> add(1, 2) == add(1)(2)
    True

    This is useful for building simple functions from partial application

    >>> succ = add(1)
    >>> succ(2)
    3

    :func:`curry` is itself a curried function, hence it can be called as

    >>> add = sk.curry(2)(lambda x, y: x + y)

    or equivalently as a decorator

    >>> @sk.curry(2)
    ... def add(x, y):
    ...     return x + y


    Currying usually requires functions of fixed number of arguments (the
    number of arguments is called the *arity* of a function). We can control
    how many arguments participate in the auto-currying by passing the arity
    number as the first argument to the :func:`curry` function.

    Variadic functions are accepted, and arity is understood as the minimum
    number of arguments necessary to invoke the function. The caller can,
    however, specify additional arguments.

    But it accepts more than 2 arguments, if needed. (Notice that only the
    first two arguments auto-curry.)

    >>> add = sk.curry(2, lambda *args: sum(args))
    >>> add(1, 2, 3, 4)
    10

    Sometimes we don't want to specify the arity of a function or don't want
    to think too much about it. :func:`curry` accepts ``'auto'`` as an arity
    specifier that makes it try to infer the arity automatically. Under the
    hood, it just calls :func:`arity` to obtain the correct value.

    Sidekick curries most functions where it makes sense. Variadic functions
    cannot be curried if the extra arguments can be passed by position. This
    decorator inspect the decorated function to determine if it can be curried
    or not.
    """

    # Decorator forms
    if callable(n):
        func: Fn = n
        return curry(arity(func), func)

    if func is None:
        return lambda f: curry(n, f)
    else:
        n = arity(func) if n in (..., None, "auto") else n
        if n == 0:
            raise TypeError("cannot curry function that receives no arguments")
        return curry(n, func)
