from collections import Iterator

from .extended_semantics import as_key, as_func, as_predicate_func

from .fn import fn

try:
    import cytoolz as toolz
    import cytoolz.curried as ctoolz
except ImportError:
    import toolz  # noqa: F401
    import toolz.curried as ctoolz


NOT_GIVEN = object()


#
# Specialized fn classes. These classes provide better speed and static
# guarantees for fn() functions on non-function callables.
#
class fn2_predicate(fn):  # noqa: N801
    "Specialized fn for functions that take a predicate and another argument"

    def __call__(self, f, x=NOT_GIVEN):
        func = self._
        f = as_predicate_func(f)
        if x is NOT_GIVEN:
            return fn1(lambda x: func(f, x))
        return func(f, x)


class fn2_function(fn):  # noqa: N801
    "Specialized fn for functions that take a function and another argument"

    def __call__(self, f, x=NOT_GIVEN):
        func = self._
        f = as_func(f)
        if x is NOT_GIVEN:
            return fn1(lambda x: func(f, x))
        return func(f, x)


class fn2_key(fn):  # noqa: N801
    "Specialized fn for functions that take a function and another argument"

    def __call__(self, f, x=NOT_GIVEN):
        func = self._
        f = as_key(f)
        if x is NOT_GIVEN:
            return fn1(lambda x: func(f, x))
        return func(f, x)


class fn1(fn):  # noqa: N801
    "Specialized fn for single argument functions"

    def __call__(self, x):
        return self._(x)


class fn2(fn):  # noqa: N801
    "Specialized fn for double argument curried functions"

    def __call__(self, a, b=NOT_GIVEN):
        func = self._
        if b is NOT_GIVEN:
            return fn1(lambda b: func(a, b))
        return func(a, b)


class fn2_opt(fn):  # noqa: N801
    """
    Specialized fn for double argument curried functions with optional
    arguments.
    """

    def __call__(self, a, b=NOT_GIVEN, *args, **kwargs):
        func = self._
        if b is NOT_GIVEN:
            return fn1(lambda b, *args: func(a, b, *args, **kwargs))
        return func(a, b, *args, **kwargs)


class fn3(fn):  # noqa: N801
    "Specialized fn for triple argument curried functions"

    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN):
        func = self._
        if b is NOT_GIVEN:
            return fn2(lambda b, c: func(a, b, c))
        elif c is NOT_GIVEN:
            return fn1(lambda c: func(a, b, c))
        return func(a, b, c)


class fn3_opt(fn):  # noqa: N801
    """
    Specialized fn for triple argument curried functions with optional
    parameters.
    """

    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN, *args, **kwargs):
        func = self._
        if b is NOT_GIVEN:
            return fn2(lambda b, c, *args: func(a, b, c, *args, **kwargs))
        elif c is NOT_GIVEN:
            return fn1(lambda c, *args: func(a, b, c, *args, **kwargs))
        return func(a, b, c, *args, **kwargs)


is_seqcont = lambda x: isinstance(x, (tuple, list, Iterator))
