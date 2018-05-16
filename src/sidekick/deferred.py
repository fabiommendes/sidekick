DEFERRED_CACHE = {}
DEFERRED_FACTORIES = {}


class DeferredBase:
    """
    Base class for Deferred and Proxy.
    """
    __slots__ = ()

    def __init__(self, func, *args, **kwargs):
        register_factory(self, lambda: func(*args, **kwargs))

    def __del__(self):
        unregister_factory(self)

    def __getattr__(self, attr):
        result = exec_deferred(self)
        return getattr(result, attr)


class Deferred:
    """
    A magic deferred/zombie object.

    It creates a proxy that is converted to the desired object on almost any
    interaction. This only works with pure Python objects with no slots since
    the Deferred must have the same C level interface as the real object.

    For a safer version of :class:`sidekick.Deferred`, try the
    :class:`sidekick.Proxy` class. One advantage of deferred objects is that,
    when alive, they transform on objects of the correct class.

    Args:
        func (callable):
            Any callable used to create the final object.
        *args, **kwargs:
            Optional positional and keyword arguments used to call the first
            argument.

    Examples:
        Let us create a class

        >>> class Foo:
        ...     def method(self):
        ...         return 42

        Now create a deferred object
        >>> x = Deferred(Foo)
        >>> type(x)
        <type Deferred>

        If we touch any method (even magic methods triggered by operators),
        it is converted to the result of the function passed to the Deferred
        constructor:
        >>> x.method()
        42
        >>> type(x)
        <type Foo>
    """

    _class__ = None
    __init__ = DeferredBase.__init__
    __del__ = DeferredBase.__del__
    __getattr__ = DeferredBase.__getattr__


class Proxy(DeferredBase):

    # Ugly names avoid unwanted collisions
    def _repr__(self):
        return f'Proxy({repr(self._obj__)})'

    def __getattr__(self, attr):
        if attr == '_obj__':
            self._obj__ = run_factory(self)
            return self._obj__
        else:
            return getattr(self._obj__, attr)


class DeferredFunc:
    def __call__(self, func, *args, **kwargs):
        return Deferred(func, *args, **kwargs)

    def __getitem__(self, cls):
        try:
            return DEFERRED_CACHE[cls]
        except KeyError:
            pass

        ns = {'_class__': self}
        if hasattr(cls, '__slots__'):
            ns['__slots__'] = ()

        type_name = 'Deferred[%s]' % cls.__name__
        self = type(type_name, (DeferredBase, cls), ns)
        DEFERRED_CACHE[cls] = self
        return self


deferred = DeferredFunc()


def proxy(func, *args, **kwargs):
    """
    Similar to Deferred, but safer since it creates a Proxy object.

    The proxy delegates all methods to the lazy object. It can break a few
    interfaces since it is never converted to the same value as the proxied
    element.

    Usage:

        >>> from operator import add
        >>> x = Proxy(add, 40, 2)  # add function not called yet
        >>> print(x)               # trigger object construction!
        42
    """
    return Proxy(func, *args, **kwargs)


METHODS = [
    # Arithmetic operators
    'add', 'radd', 'sub', 'rsub', 'mul', 'rmul', 'truediv', 'rtruediv',
    'floordiv', 'rfloordiv',

    # Relations
    'eq', 'ne', 'le', 'lt', 'ge', 'gt',

    # Sequence interface
    'getitem', 'setitem', 'iter', 'len',

    # Conversions
    'repr', 'str', 'nonzero', 'bool',

    # Other Python interfaces
    'call',
]


def _fill_magic_methods(*classes):
    def deferred_method(attr):
        def method(self, *args, **kwargs):
            exec_deferred(self)
            return getattr(self, attr)(*args, **kwargs)

        return method

    def proxy_method(attr):
        def method(self, *args, **kwargs):
            return getattr(self._obj__, attr)(*args, **kwargs)

        return method

    for method_name in METHODS:
        method_name = '__%s__' % method_name
        setattr(DeferredBase, method_name, deferred_method(method_name))
        setattr(Deferred, method_name, deferred_method(method_name))
        setattr(Proxy, method_name, proxy_method(method_name))


# Fill dunder methods
_fill_magic_methods()
Proxy.__repr__ = Proxy._repr__


def register_factory(obj, factory):
    DEFERRED_FACTORIES[id(obj)] = factory


def run_factory(obj):
    factory = DEFERRED_FACTORIES[id(obj)]
    result = factory()
    if result is None:
        raise ValueError(
            'constructor returned None: not a valid deferred object'
        )
    return result


def unregister_factory(obj):
    DEFERRED_FACTORIES.pop(id(obj), None)


def exec_deferred(obj):
    result = run_factory(obj)

    # __dict__ based classes
    if hasattr(result, '__dict__'):
        object.__getattribute__(obj, '__dict__').update(result.__dict__)

    # __slots__ based classes
    if hasattr(result, '__slots__'):
        for slot in result.__class__.__slots__:
            try:
                value = getattr(result, slot)
            except AttributeError:
                pass
            else:
                setattr(obj, slot, value)

    # Safe version of obj.__class__ = type(result)
    object.__setattr__(obj, '__class__', type(result))
    return result
