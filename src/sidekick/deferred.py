DEFERRED_CACHE = {}
DEFERRED_FACTORIES = {}


class DelayedBase:
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


class Delayed:
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
        >>> x = Delayed(Foo)
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
    __init__ = DelayedBase.__init__
    __del__ = DelayedBase.__del__
    __getattr__ = DelayedBase.__getattr__


class Proxy:
    """
    Base class for proxy types.
    """
    __slots__ = ('_obj__',)

    def __init__(self, obj):
        self._obj__ = obj

    def __repr__(self):
        return f'{type(self).__name__}({repr(self._obj__)})'

    def __getattr__(self, attr):
        obj = Proxy._obj__.__get__(self, type(self))
        return getattr(obj, attr)

    __eq__ = (lambda self, other: self._obj__.__eq__(other))
    __ne__ = (lambda self, other: self._obj__.__ne__(other))
    __gt__ = (lambda self, other: self._obj__.__gt__(other))
    __ge__ = (lambda self, other: self._obj__.__ge__(other))
    __lt__ = (lambda self, other: self._obj__.__lt__(other))
    __le__ = (lambda self, other: self._obj__.__le__(other))
    __hash__ = (lambda self: hash(self._obj__))


class Deferred(Proxy, DelayedBase):
    """
    Like Delayed, but wraps object into a proxy shell.
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        DelayedBase.__init__(self, *args, **kwargs)

    def __getattr__(self, attr):
        if attr == '_obj__':
            self._obj__ = run_factory(self)
            return self._obj__
        else:
            return getattr(self._obj__, attr)


class DelayedFunctionType:
    def __call__(self, func, *args, **kwargs):
        return Delayed(func, *args, **kwargs)

    def __getitem__(self, cls):
        try:
            return DEFERRED_CACHE[cls]
        except KeyError:
            pass

        ns = {'_class__': self}
        if hasattr(cls, '__slots__'):
            ns['__slots__'] = ()

        type_name = 'Deferred[%s]' % cls.__name__
        self = type(type_name, (DelayedBase, cls), ns)
        DEFERRED_CACHE[cls] = self
        return self


delayed = DelayedFunctionType()
del DelayedFunctionType


def deferred(func, *args, **kwargs):
    """
    Similar to delayed, but safer since it creates a Deferred object.

    The proxy delegates all methods to the lazy object. It can break a few
    interfaces since it is never converted to the same value as the proxied
    element.

    Usage:

        >>> from operator import add
        >>> x = Deferred(add, 40, 2)  # add function not called yet
        >>> print(x)                  # trigger object construction!
        42
    """
    return Deferred(func, *args, **kwargs)


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

    def update(cls, attr, value):
        force_update = {'__call__'}
        current = getattr(cls, attr, None)
        obj_value = getattr(object, attr, value)
        if current is None or current is obj_value or attr in force_update:
            setattr(cls, attr, value)

    for method_name in METHODS:
        method_name = '__%s__' % method_name
        dfunc = deferred_method(method_name)
        pfunc = proxy_method(method_name)
        update(DelayedBase, method_name, dfunc)
        update(Delayed, method_name, dfunc)
        update(Proxy, method_name, pfunc)


# Fill dunder methods
_fill_magic_methods()


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
