import itertools
from abc import ABC
from collections.abc import Mapping, Sequence
from functools import partial, singledispatch

from ..typing import Any

APPLY_INTERFACE_REGISTRY = {}
CONTAINER_TYPES = (tuple, list, set, frozenset, str, bytes)


class Apply(ABC):
    @classmethod
    def __subclasshook__(cls, other):
        ...


def apply(*args, **kwargs):
    func, x, *args = args
    if kwargs:
        func = partial(func, **kwargs)

    if not args:
        return _apply_instance(x, func)


def register(kind, interface: Any = None):
    """
    Register interface either from callable or from a namespace object with
    the apply implementation.

    It can implement a few functions:

    * apply:
    * apply_wrap:
    * apply_simple:
    * apply_instance:
    """
    if interface is None:
        return lambda i: register(kind, i)
    if not isinstance(interface, Mapping):
        interface = {
            k: getattr(interface, k) for k in dir(interface) if not k.startswith("_")
        }

    # Register apply instance
    registered = False
    try:
        fn_apply_instance = interface["apply_instance"]
    except KeyError:
        pass
    else:
        _apply_instance.register(kind, fn_apply_instance)
        registered = True

    if registered:
        ...
    else:
        raise TypeError

    return interface


def register_class(kind, cls=None):
    """
    Register interface from a class that implement the Apply methods.
    """

    if cls is None:
        return lambda klass: register_class(kind, klass)
    register(kind, cls())
    return cls


apply.register = register


@singledispatch
def _apply_instance(instance, func):
    try:
        method = instance.__sk_apply_instance__
    except AttributeError:
        name = type(instance)
        raise TypeError(f"{name} instances do not support apply()")
    else:
        return method(func)


@singledispatch
def _apply_args(instance, func, args):
    try:
        method = type(instance).__sk_apply__
    except AttributeError:
        name = type(instance)
        msg = f"{name} instances do not support multiple arguments apply()"
        raise TypeError(msg)
    else:
        return method(func, instance, *args)


#
# Apply implementations for builtin methods
#
class iSequenceProduct:
    def __init__(self, kind, constructor=None):
        self._kind = kind
        self._constructor = constructor or kind

    def apply_instance(self, func, xs):
        return self.wrap(func(x) for x in xs)

    def apply(self, func, *args):
        points = itertools.product(*self.iterators(args))
        return self._constructor(self.values(func(*pt) for pt in points))

    def wrap(self, obj):
        if isinstance(obj, self._kind):
            return obj
        try:
            data = iter(obj)
        except TypeError:
            data = [obj]
        return self._constructor(data)

    @staticmethod
    def values(xs):
        for x in xs:
            try:
                yield from iter(x)
            except TypeError:
                yield x

    @staticmethod
    def iterators(xs):
        seqs = CONTAINER_TYPES
        for x in xs:
            if isinstance(x, seqs):
                yield x
            else:
                try:
                    yield iter(x)
                except TypeError:
                    yield [x]


class iSequenceZip(iSequenceProduct):
    def apply_instance(self, func, xs):
        return self.wrap(func(x) for x in xs)

    def apply(self, func, *args):
        points = itertools.product(*self.iterators(args))
        return self._constructor(self.values(func(*pt) for pt in points))

    def wrap(self, obj):
        if isinstance(obj, self._kind):
            return obj
        elif isinstance(obj, Sequence):
            return self._constructor(obj)
        try:
            data = iter(obj)
        except TypeError:
            data = [obj]
        return self._constructor(data)

    @staticmethod
    def values(xs):
        for x in xs:
            try:
                yield from iter(x)
            except TypeError:
                yield x

    @staticmethod
    def iterators(xs):
        seqs = CONTAINER_TYPES
        for x in xs:
            if isinstance(x, seqs):
                yield x
            else:
                try:
                    yield iter(x)
                except TypeError:
                    yield [x]


for cls in [list, tuple, set, frozenset]:
    apply.register(cls, iSequenceProduct(cls))


def flip(fn):
    return lambda x, y: fn(y, x)
