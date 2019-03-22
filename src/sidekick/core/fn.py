from sidekick.core.base_fn import extract_function
from .base_fn import SkFunction, FunctionMeta

__all__ = ["fn"]


class FnMeta(FunctionMeta):
    def __rshift__(cls, other):
        return cls(other)


# noinspection PyPep8Naming
class fn(SkFunction, metaclass=FnMeta):  # noqa: N801
    """
    A function wrapper that enable functional programming superpowers.
    """

    __slots__ = ()

    # Function composition operators
    def __ror__(self, other):
        return self._sk_function_(other)


def as_fn(func):
    """
    Convert callable to an :cls:`fn` object.

    If func is already an :cls:`fn` instance, it is passed as is.
    """
    return func if isinstance(func, fn) else fn(func)


# ------------------------------------------------------------------------------
# Specialized fn classes. These classes provide better speed and static
# guarantees for fn() functions on non-function callables.
# ------------------------------------------------------------------------------
NOT_GIVEN = object()


class Fn1(fn):
    def __call__(self, x):
        return self._sk_function_(x)


class Fn1o(fn):
    def __call__(self, x, **kwargs):
        return self._sk_function_(x, **kwargs)


class Fn2(fn):
    def __call__(self, a, b=NOT_GIVEN):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn1(lambda y: func(a, y))
        return func(a, b)


class Fn2o(fn):
    def __call__(self, a, b=NOT_GIVEN, **kwargs):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn1o(lambda y: func(a, y, **kwargs))
        return func(a, b, **kwargs)


class Fn3(fn):
    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn2(lambda y, z: func(a, y, z))
        elif c is NOT_GIVEN:
            return Fn1(lambda z: func(a, b, z))
        return func(a, b, c)


class Fn3o(fn):
    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN, **kwargs):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn1o(lambda y, z: func(a, y, z, **kwargs))
        elif c is NOT_GIVEN:
            return Fn1o(lambda z: func(a, b, z, **kwargs))
        return func(a, b, c, **kwargs)


#
# Predicate receivers
#
class Fn1P(Fn1o):
    def __call__(self, f, **kwargs):
        return super().__call__(extract_function(f), **kwargs)


class Fn2P(Fn2o):
    def __call__(self, f, x=NOT_GIVEN, **kwargs):
        return super().__call__(extract_function(f), x, **kwargs)


class Fn3P(Fn3o):
    def __call__(self, f, x=NOT_GIVEN, y=NOT_GIVEN, **kwargs):
        return super().__call__(extract_function(f), x, y, **kwargs)
