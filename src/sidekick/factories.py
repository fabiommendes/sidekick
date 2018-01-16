import operator as op


class AttrGetterMeta(type):
    """
    Metaclass for the attrgetter factory.
    """

    __attrs__ = property(lambda x: ())

    def _new(cls, *attrs):  # noqa: N805
        self = object.__new__(cls)
        self._attrs = attrs
        self._getter = op.attrgetter('.'.join(attrs))
        return self

    # When the caller object receives a direct attribute access, we must
    # initialize a new instance with it
    def __getattr__(cls, attr):  # noqa: N805
        return cls._new(attr)


class attrgetter(metaclass=AttrGetterMeta):  # noqa: N801
    """
    A attribute getter factory. It chains any number of attribute accesses.
    This method is similar to op.attrgetter, but the resulting object can be
    introspected and it has a more convenient syntax.
    """

    __slots__ = ('_attrs', '_getter')
    __attrs__ = property(lambda x: x._attrs)

    def __getattr__(self, attr):
        if attr == '__wrapped__':
            raise AttributeError('__wrapped__')
        return attrgetter._new(*(self._attrs + (attr,)))

    def __repr__(self):
        return 'attrgetter{attrs}'.format(
            attrs=''.join('.' + attr for attr in self._attrs),
        )

    def __call__(self, x):
        return self._getter(x)


class CallerMeta(AttrGetterMeta):
    """
    Metaclass for the caller factory.
    """

    def _new(cls, *attrs):  # noqa: N805
        self = object.__new__(cls)
        self._attrs = attrs
        return self

    # When the caller object is called directly, it is chained to this method.
    # We want to return a function that calls its unique argument with the
    # passed args and **kwargs
    def __call__(cls, *args, **kwargs):  # noqa: N805
        return lambda x: x(*args, **kwargs)


class caller(metaclass=CallerMeta):  # noqa: N801
    """
    Method caller factory. It chains an arbitrary number of arguments and than
    makes a method call.

    Usage:

    >>> f = f = caller.real.conjugate()
    >>> f(42+1j)
    42
    """

    __slots__ = ('_attrs')
    __attrs__ = property(lambda x: x._attrs)

    def __getattr__(self, attr):
        # Make it inspectable for doctests
        if attr == '__wrapped__':
            raise AttributeError('__wrapped__')
        return caller._new(*(self._attrs + (attr,)))

    def __call__(self, *args, **kwargs):
        attrs = self._attrs
        methodcaller = op.methodcaller(attrs[-1], *args, **kwargs)

        if len(attrs) == 1:
            return methodcaller
        else:
            getter = op.attrgetter('.'.join(attrs[:-1]))
            return lambda x: methodcaller(getter(x))

    def __repr__(self):
        return 'caller{attrs}'.format(
            attrs=''.join('.' + attr for attr in self._attrs),
        )
