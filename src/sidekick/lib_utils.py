from collections import Iterator

from .fn import fn
from .placeholder import placeholder
from .predicate import predicate

try:
    import cytoolz as toolz
except ImportError:
    import toolz


NOT_GIVEN = object()
underscore_to_function = (placeholder, fn, predicate)


#
# Extendend function semantics normalizers
#
def as_func(f):
    "Extended function semantics for callable arguments."

    if isinstance(f, underscore_to_function):
        return f._
    elif f is None:
        return lambda x: x
    elif callable(f):
        return f
    else:
        raise ValueError('cannot be interpreted as a function: %r' % f)


def as_key(f):
    "Extended function semantics for key arguments."

    if isinstance(f, underscore_to_function):
        return f._
    elif f is None:
        return lambda x: x
    return f


def as_predicate_func(f):
    """
    Extended function semantics for argument that is expected to be a
    predicate.
    """

    if isinstance(f, underscore_to_function):
        return f._
    elif callable(f):
        return f
    else:
        raise ValueError('cannot be interpreted as a predicate: %r' % f)


#
# Specialized fn classes. These classes provide better speed and static
# guarantees for fn() functions on non-function callables.
#
class fn2_predicate(fn):
    "Specialized fn for functions that take a predicate and another argument"

    def __call__(self, f, x=NOT_GIVEN):
        func = self._
        f = as_predicate_func(f)
        if x is NOT_GIVEN:
            return fn1(lambda x: func(f, x))
        return func(f, x)


class fn2_function(fn):
    "Specialized fn for functions that take a function and another argument"

    def __call__(self, f, x=NOT_GIVEN):
        func = self._
        f = as_func(f)
        if x is NOT_GIVEN:
            return fn1(lambda x: func(f, x))
        return func(f, x)


class fn2_key(fn):
    "Specialized fn for functions that take a function and another argument"

    def __call__(self, f, x=NOT_GIVEN):
        func = self._
        f = as_key(f)
        if x is NOT_GIVEN:
            return fn1(lambda x: func(f, x))
        return func(f, x)


class fn1(fn):
    "Specialized fn for single argument functions"

    def __call__(self, x):
        return self._(x)


class fn2(fn):
    "Specialized fn for double argument curried functions"

    def __call__(self, a, b=NOT_GIVEN):
        func = self._
        if b is NOT_GIVEN:
            return fn1(lambda b: func(a, b))
        return func(a, b)


class fn2_opt(fn):
    """
    Specialized fn for double argument curried functions with optional
    arguments.
    """

    def __call__(self, a, b=NOT_GIVEN, *args, **kwargs):
        func = self._
        if b is NOT_GIVEN:
            return fn1(lambda b, *args: func(a, b, *args, **kwargs))
        return func(a, b, *args, **kwargs)


class fn3(fn):
    "Specialized fn for triple argument curried functions"

    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN):
        func = self._
        if b is NOT_GIVEN:
            return fn2(lambda b, c: func(a, b, c))
        elif c is NOT_GIVEN:
            return fn1(lambda c: func(a, b, c))
        return func(a, b, c)


class fn3_opt(fn):
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
