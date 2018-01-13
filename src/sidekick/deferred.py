class DeferredMeta(type):
    """
    Metaclass for deferred objects.
    """
    
    def __getitem__(cls, item):
        return type('Deferred', (cls, item), {})


class Deferred(metaclass=DeferredMeta):
    """
    A magic deferred object.

    It creates a proxy that is converted to the desired object on almost any
    interaction. This only works with pure Python objects since the Deferred
    must have the same C level interface as the real object.
    """

    def __init__(self, func, *args, **kwargs):
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    # An ugly names that minimizes collisions and do not trigger mangled names
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
    
    The proxy delegates all methods to the lazy object.
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


def fill_magic_methods():
    def method_factory(attr):
        def method(self, *args, **kwargs):
            self._convert__()
            return getattr(self, attr)(*args, **kwargs)
        return method

    for method in ('getitem setitem iter len '
                'repr str '
                'add radd sub rsub mul rmul truediv rtruediv floordiv rfloordiv '
                'eq ne le lt ge gt nonzero bool ').split():
        method = '__%s__' % method
        
        setattr(Deferred, method, method_factory(method))
        setattr(Proxy, method, method_factory(method))

# Fill dunder methods
fill_magic_methods()
del fill_magic_methods
