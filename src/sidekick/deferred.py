class DeferredMeta(type):
    """
    Metaclass for deferred objects.
    """

    def __getitem__(cls, item):
        return type('Deferred', (cls, item), {})


class Deferred(metaclass=DeferredMeta):
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

    def __init__(self, func, *args, **kwargs):
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    # Ugly names that minimizes collisions and do not trigger Python's builtin
    # name mangling
    def _convert__(self):
        obj = self._execute__()
        self.__dict__.update(obj.__dict__)
        self.__class__ = type(obj)

    def _execute__(self):
        # Create proxy object and copy its state back to the Proxy.
        # Changes the object class to the proxy object class.
        print(self.__func)
        obj = self.__func(*self.__args, **self.__kwargs)

        if obj is None:
            raise ValueError(
                'constructor returned None: not a valid deferred object'
            )

        del self.__func
        del self.__args
        del self.__kwargs
        return obj

    def __getattr__(self, attr):
        self._convert__()
        return getattr(self, attr)


class Proxy:
    """
    Similar to Deferred, but safer since it creates a Proxy object.
    
    The proxy delegates all methods to the lazy object. It can break a few
    interfaces since it is never converted to the same value as the proxied
    element.

    Examples:
        >>> from operator import add
        >>> x = Proxy(add, 40, 2)  # add function not called yet
        >>> print(x)               # trigger object construction!
        42
    """

    __init__ = Deferred.__init__
    _execute__ = Deferred._execute__

    def _convert__(self):
        self.__obj = self._execute__()

    def __getattr__(self, attr):
        try:
            value = self.__obj
        except AttributeError:
            self._convert__()
            value = self.__obj
        return getattr(value, attr)


def _fill_magic_methods(*classes):
    def method_factory(attr):
        def method(self, *args, **kwargs):
            self._convert__()
            return getattr(self, attr)(*args, **kwargs)

        return method

    for method_name in ('getitem setitem iter len repr str add radd sub rsub '
                        'mul rmul truediv rtruediv floordiv rfloordiv eq ne '
                        'le lt ge gt nonzero bool').split():
        method_name = '__%s__' % method_name
        for cls in classes:
            setattr(cls, method_name, method_factory(method_name))


# Fill dunder methods
_fill_magic_methods(Deferred, Proxy)
