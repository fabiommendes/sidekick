from copy import copy


class lazy_property:
    """
    Lazy property accessor.

    Used to mirror wrapped function properties.
    """

    __slots__ = "func"

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return self.func(instance)


class lazy_string(lazy_property):
    __slots__ = "string"

    def __init__(self, func, string):
        super().__init__(func)
        self.string = string

    def __get__(self, instance, cls=None):
        if instance is None:
            return self.string
        return self.func(instance)


class mixed_accessor:
    """
    Descriptor with different class and an instance implementations.
    """

    __slots__ = ("_cls", "_instance")

    def __init__(self, instance=None, cls=None):
        self._cls = cls
        self._instance = instance
        if cls:
            self._cls = classmethod(cls).__get__
        if instance:
            self._instance = instance.__get__

    def classmethod(self, func):
        new = copy(self)
        new._cls = classmethod(func).__get__
        return new

    def instancemethod(self, func):
        new = copy(self)
        new._instance = func.__get__
        return new

    def __get__(self, instance, cls=None):
        if instance is None:
            return self._cls(cls)
        else:
            return self._instance(instance)

    def __set__(self, instance, value):
        raise TypeError
