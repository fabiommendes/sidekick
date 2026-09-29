from dataclasses import dataclass
from functools import partial, wraps
from operator import methodcaller
from typing import Any

from sidekick.protocols import to_callable

from .utils import a, r, fn_t, Fn, WrappedFunction


class Combinators(WrappedFunction[fn_t]):
    def power(self, n: int, x: a, /, **kwargs) -> a:
        """
        Execute function n times with arguments

        See also:
            :func:`power`
        """
        func = partial(self, **kwargs) if kwargs else self
        return power(func, n)(x)

    def rec(self) -> a:
        """
        Binds itself to first argument.

        See also:
            :func:`rec`
        """
        return self._wrap(rec(self))

    def do(self, /, *args, **kwargs) -> a:
        """
        Run function with arguments, but return the first argument.

        See also:
            :func:`do`
        """
        return do(self, *args, **kwargs)


def identity(x: a, /, *args: Any, **kwargs: Any) -> a:
    """
    The identity function.

    Return its first argument unchanged. Identity accepts one or more positional
    arguments and any number of keyword arguments.

    Examples:
        >>> identity(1, 2, 3, foo=4)
        1

    See also:
        :func:`ridentity`
    """
    return x


def ridentity(*args: a, **kwargs) -> a:
    """
    Return last positional argument.

    Similar to identity, but return the last positional argument and not the
    first. In the case the function receives a single argument, both identity
    functions coincide.

    Examples
        >>> ridentity(1, 2, 3)
        3

    See also:
        :func:`identity`
    """
    if args:
        return args[-1]
    raise TypeError("must be called with at least 1 positional argument")


def always(x: a) -> Fn[..., a]:
    """
    Return a function that always return x when called with any number of
    arguments.

    Examples:
        >>> f = always(42)
        >>> f('answer', for_what='question of life, the universe ...')
        42
    """
    return lambda *args, **kwargs: x


def trampoline(func: Fn[..., r]) -> Fn[..., r]:
    """
    Decorator that implements tail call elimination via the trampoline technique.

    Args:
        func:
            The function must return a result or recur(*args) telling how tail
            recursion should happen.

    Examples:
        >>> @sk.trampoline
        ... def fat(n, acc=1):
        ...     if n > 0:
        ...         return recur(n - 1, acc * n)
        ...     else:
        ...         return acc

        This fat never breaks the stack!

        >>> fat(5)
        120
    """

    @wraps(func)
    def function(*args, **kwargs) -> r:
        while True:
            out = func(*args, **kwargs)

            if isinstance(out, _Recur):
                args = out.args
                kwargs = out.kwargs
            else:
                return out

    return function


def recur(*args, **kwargs) -> Any:
    """
    Called by functions using the trampoline technique
    to enter another level of tail recursion.
    """
    return _Recur(args, kwargs)


@dataclass
class _Recur:
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


def value(obj: r | Fn[..., r], *args, **kwargs) -> r:
    """
    Evaluate `obj` with arguments if it is a callable or return it otherwise.

    Args:
        obj:
            Callable or some other value. If input is a callable, call it with
            the provided arguments and return. Otherwise, simply return.

    Examples:
        >>> value(42)
        42
        >>> value(lambda: 42)
        42
    """
    if callable(obj):
        return obj(*args, **kwargs)
    return obj


def call(*args: Any, **kwargs: Any) -> Fn[[Fn[..., r]], r]:
    """
    Return a function caller.

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
    return lambda f: f(*args, **kwargs)


class _fn_method:
    __slots__ = ()
    __doc__ = None

    def __init__(self, func):
        super().__init__(func)
        wraps(func)(self)

    def __getattr__(self, attr: str):
        if attr.startswith("_"):
            raise AttributeError(attr)
        return lambda *args, **kwargs: methodcaller(attr, *args, **kwargs)


@_fn_method
def method(*args, **kwargs):
    """
    Return a function that calls a method of its argument with the given values.

    A method caller object. It can be used as a function

    >>> pop_first = method("pop", 0)
    >>> pop_first([1, 2, 3])
    1

    or as a function factory.

    >>> pop_first = method.pop(0)
    >>> pop_first([1, 2, 3])
    1

    The second usage is syntactically cleaner and prevents the usage of
    invalid Python names. All method calls performed in the ``sk.method`` object
    returns the corresponding methodcaller function.
    """
    return methodcaller(*args, **kwargs)


def defaults(func: Fn[..., r], /, *args: Any, **kwargs: Any) -> Fn[..., r]:
    """
    Return a new function that uses the given arguments as default values.

    This is akin to a partial application, but arguments are not fixed. It simply
    chooses the default values that can be easily modified in future function
    calls.

    Ellipsis are used to mark required positional arguments.

    Example:
        Consider a simple function with many arguments

        >>> def compress(x, min_x, max_x):
        ...     return min(max(x, min_x), max_x)
        >>> func = default_args(compress, ..., 0, 10)
    """

    # Check ellipsis
    n_required = 0
    while len(args) > n_required and args[n_required] == ...:
        n_required += 1
    if ... in args[n_required + 1 :]:
        raise ValueError("ellipsis are only accepted in the beginning of sequence")

    default_args = args[n_required:]
    default_kwargs = kwargs

    @wraps(func)
    def f(*args, **kwargs):
        for k, v in default_kwargs.items():
            kwargs.setdefault(k, v)
        return func(*args, *default_args[len(args) :], **kwargs)

    return f


def do(func, x: a, /, *args, **kwargs) -> a:
    """
    Pass argument x to func, but always return x.

    Because the results of func are not returned, it is called only for the side
    effects.

    Logging functions can be made by composing ``do`` with a storage function
    like ``list.append``, ``print`` or ``file.write``

    Examples:
        >>> log = []
        >>> value = do(lst.append, 40) + 2
        >>> value
        42
        >>> log
        [40]
    """
    func(x, *args, **kwargs)
    return x


def power(func: Fn[[a], a], n: int) -> Fn[[a], a]:
    """
    Return a function that applies f to is argument n times.

        power(f, n)(x) ==> f(f(...f(x)))  # apply f n times.

    Examples:
        >>> g = power((2 * X), 3)
        >>> g(10)
        80
    """
    if n == 0:
        return lambda x: x
    elif n == 1:
        return func
    elif n < 0:
        raise TypeError("cannot invert function")

    @wraps(func)
    def power_fn(x):
        for _ in range(n):
            x = func(x)
        return x

    func = to_callable(func)
    return power_fn


def rec(func: Fn[..., r]) -> Fn[..., r]:
    """
    Fix func's first argument as itself.

    This is similar to the  Y-combinator and is useful to implement recursion.
    from scratch.

    Examples:
        In this example, the factorial receive a second argument which is the
        function it must recurse to. rec pass the function to itself so now
        the factorial only needs the usual numeric argument.

        >>> fat = rec(lambda rec, n: 1 if n == 0 else n * rec(rec, n - 1))
        >>> fat(5)
        120

    """
    return lambda *args, **kwargs: func(func, *args, **kwargs)
