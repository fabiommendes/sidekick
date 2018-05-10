import builtins

from .extended_semantics import as_func


#
# Lazy attributes
#
class lazy:
    """
    Decorator that defines an attribute that is initialized with first usage
    rather than at instance creation.

    Usage is similar to the ``@property`` decorator, although lazy attributes do
    not override *setter* and *deleter* methods.
    """

    __slots__ = ('_function', '_name')

    def __init__(self, function):
        self._function = as_func(function)

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        value = self._function(obj)
        try:
            name = self._name
        except AttributeError:
            function_name = self._function.__name__
            name = find_descriptor_name(self, cls, hint=function_name)
        setattr(obj, name, value)
        return value

    def __set_name__(self, owner, name):
        self._name = name


class lazy_shared(lazy):
    """
    A lazy accessor that initializes class variables. The state is computed
    statically at first access and is injected in the base class namespace.
    After that, it become a class variable that is shared between all
    instances.

    Differently from lazy attributes, lazy_shared expect a classmethod as first
    argument. It can be used to delay expensive computation of class contants
    or to break dependency cycles between Python modules.

    Usage:
        To break a dependency cycle. Consider class Foo on foo.py and class Bar
        on bar.py.

        .. code-block:: python

            # foo.py
            import sidekick as sk

            class Foo:
                @sk.lazy_shared
                def _bar(self):
                    # We can't import Bar because bar.py imports Foo
                    # This would create a dependency cycle.
                    from .bar import Bar
                    return Bar

                def __init__(self, a):
                    self.a = a

                def bar(self):
                    return self._bar(self.a)

        .. code-block:: python

            # bar.py
            from .foo import Foo

            class Bar:
                def __init__(self, a):
                    self.a = a

                def foo(self):
                    return Foo(self.a)
    """

    def __get__(self, obj, cls: type=None):
        try:
            return self._value
        except AttributeError:
            pass

        try:
            name = self._name
        except AttributeError:
            function_name = self._function.__name__
            name = find_descriptor_name(self, cls, hint=function_name)
        owner_class = find_descriptor_owner(self, cls, name=name)
        self._value = self._function(owner_class)
        setattr(owner_class, name, self._value)
        return self._value


class property(builtins.property):
    """
    A Sidekick-enabled property descriptor. It behaves just as standard Python
    properties, but it also accepts placeholder expressions as a getter input.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(as_func(fget), fset, fdel, doc)

    def getter(self, fget):
        return super(as_func(fget))


#
# Delegation
#
class delegate_to(object):
    """
    Delegate access to an inner variable.

    A delegate is an alias for an attribute of the same name that lives in an
    inner object of a class.

    Example:
        Consider the very simple example::

            class Foo(object):
                data = "foo-bar"
                upper = delegate_to('data')

            x = Foo()

        ``x.upper()`` is now an alias for ``x.data.upper()``.

    Args:
        attribute:
            Name of the inner variable that receives delegation.
        readonly:
            If true, makes the the delegate readonly.
        inner_name:
            The name of the inner variable. Can be ommited if the name is the
            same of the attribute.
    """

    def __init__(self, attribute, name=None, readonly=False, ):
        self.attribute = attribute
        self.name = name
        self.readonly = readonly
        self._getter = None
        self._setter = None

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        owner = getattr(obj, self.attribute)
        try:
            attr = self._name
        except AttributeError:
            attr = self._name = self._get_name(cls)
        return getattr(owner, attr)

    def __set__(self, obj, value):
        if self.readonly:
            raise AttributeError
        owner = getattr(obj, self.attribute)
        try:
            attr = self._name
        except AttributeError:
            attr = self._name = self._get_name(type(obj))
        setattr(owner, attr, value)

    def __set_name__(self, owner, name):
        self.name = name


class delegate_ro(delegate_to):
    """
    A read-only version of delegate_to()
    """

    def __init__(self, attribute):
        super().__init__(attribute, readonly=True)


class alias(object):
    """
    An alias to an attribute.

    Args:
        attribute (str):
            Name of aliased attribute.
        readonly (bool):
            If True, makes the alias read only.
    """

    def __init__(self, attribute, readonly=False):
        self.attribute = attribute
        self.readonly = readonly

    def __get__(self, obj, cls=None):
        if obj is not None:
            return getattr(obj, self.attribute)
        return self

    def __set__(self, obj, value):
        if self.readonly:
            raise AttributeError(self.attribute)

        setattr(obj, self.attribute, value)


class readonly(alias):
    """
    A read-only alias to an attribute.
    """

    def __init__(self, attribute):
        super(readonly, self).__init__(attribute, readonly=True)


def find_descriptor_name(descriptor, cls: type, hint=None):
    """
    Finds the name of the descriptor in the given class.
    """

    if hint is not None and getattr(cls, hint) is descriptor:
        return hint

    for attr in dir(cls):
        value = getattr(cls, attr, None)
        if value is descriptor:
            return attr
    raise RuntimeError('%r is not a member of class' % descriptor)


def find_descriptor_owner(descriptor, cls: type, name=None):
    """
    Find the class that owns the descriptor.
    """
    name = name or find_descriptor_name(descriptor, cls)
    owner = None
    for super_class in cls.mro():
        # We use dict to avoid recursion caused by the descriptor protocol
        value = super_class.__dict__.get(name, None)
        if value is descriptor:
            owner = super_class
    if owner is None:
        raise RuntimeError('%r is not a member of %s' % descriptor)
    return owner