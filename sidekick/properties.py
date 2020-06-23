from ..functions import always, to_callable

__all__ = ["lazy", "property", "delegate_to", "alias"]
_property = property
ATTR_ERROR_MSG = """An AttributeError was raised when evaluating a lazy property.

This is often an error and the default behavior is to prevent such errors to
cascade to let Python think that the attribute does not exist. If you really
want to signal that the attribute is missing, consider using the option
"lazy(..., attr_error=True)" of the lazy property decorator.
"""


def lazy(func=None, *, shared=False, name=None, attr_error=False):
    """
    Decorator that defines an attribute that is initialized with first usage
    rather than during instance creation.

    Usage is similar to ``@property``, although lazy attributes do not override
    *setter* and *deleter* methods, allowing instances to write to the
    attribute.

    Optional Args:
        shared (bool):
            A shared attribute behaves as a lazy class variable that is shared
            among all classes and instances. It differs from a simple class
            attribute in that it is initialized lazily from a function. This
            can help to break import cycles and delay expensive computations
            to when they are required.
        name (str):
            By default, a lazy attribute can infer the name of the attribute
            it refers to. In some exceptional cases (when creating classes
            dynamically), the inference algorithm might fail and the name
            attribute must be set explicitly.
        attr_error (Exception, bool):
            If False or an exception class, re-raise attribute errors as the
            given error. This prevent erroneous code that raises AttributeError
            being mistakenly interpreted as if the attribute does not exist.
    """
    if func is None:
        return lambda f: lazy(f, shared=shared, name=name, attr_error=attr_error)

    if attr_error is False:
        attr_error = always(RuntimeError(ATTR_ERROR_MSG))

    if shared:
        return _SharedLazy(func, name=name, attr_error=attr_error)
    else:
        return _Lazy(func, name=name, attr_error=attr_error)


def property(fget=None, fset=None, fdel=None, doc=None):
    """
    A Sidekick-enabled property descriptor. It behaves just as standard Python
    properties, but it also accepts placeholder expressions as a getter input.
    """
    return _Property(fget, fset, fdel, doc)


def delegate_to(attr, *, name=None, read_only=False):
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
        attr:
            Name of the inner variable that receives delegation.
        name:
            The name of the attribute/method of the delegate variable. Can be
            omitted if the name is the same of the attribute.
        read_only:
            If True, makes the the delegation read-only.
    """
    if read_only:
        return _ReadOnlyDelegate(attr, name)
    else:
        return _Delegate(attr, name)


def alias(attr, *, mutable=False, transform=None, prepare=None):
    """
    An alias to an attribute.

    Args:
        attr (str):
            Name of aliased attribute.
        mutable (bool):
            If True, makes the alias mutable.
        transform (callable):
            If given, transform output.
        prepare:
            If given, prepare value before saving.
    """
    if transform is not None or prepare is not None:
        return _TransformingAlias(attr, transform, prepare)
    elif mutable:
        return _MutableAlias(attr)
    else:
        return _ReadOnlyAlias(attr)


#
# Helper classes
#
class _Property(_property):
    """
    Sidekick property descriptor.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        fget = fget if fget is None else to_callable(fget)
        fset = fset if fset is None else to_callable(fset)
        fdel = fdel if fdel is None else to_callable(fdel)
        super().__init__(fget, fset, fdel, doc)

    def getter(self, fget):
        return super().getter(fget if fget is None else to_callable(fget))

    def setter(self, fset):
        return super().setter(fset if fset is None else to_callable(fset))


class _Lazy:
    """
    Lazy attribute of an object
    """

    __slots__ = ("function", "name", "attr_error")

    def __init__(self, func, name=None, attr_error=True):
        self.function = to_callable(func)
        self.name = name
        self.attr_error = attr_error or Exception

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        name = self.name or self._init_name(cls)
        try:
            value = self.function(obj)
        except AttributeError as ex:
            if self.attr_error is True:
                raise
            raise self.attr_error(ex) from ex

        setattr(obj, name, value)
        return value

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def _init_name(self, cls):
        function_name = self.function.__name__
        name = find_descriptor_name(self, cls, hint=function_name)
        self.name = name
        return name


class _SharedLazy(_Lazy):
    """
    Lazy attribute of a class and all its instances.
    """

    __slots__ = ("value",)

    def __get__(self, obj, cls=None):
        try:
            return self.value
        except AttributeError:
            return self._init_value(cls)

    def _init_value(self, cls):
        try:
            self.value = self.function(cls)
        except AttributeError as ex:
            if self.attr_error is True:
                raise
            raise self.attr_error(ex) from ex
        return self.value


class _Delegate:
    """
    Delegate attribute to another attribute.
    """

    __slots__ = ("attr", "name")
    __set_name__ = _Lazy.__set_name__

    def __init__(self, attr, name=None):
        self.attr = attr
        self.name = name

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        name = self.name or self._init_name(cls)
        owner = getattr(obj, self.attr)
        return getattr(owner, name)

    def __set__(self, obj, value):
        owner = getattr(obj, self.attr)
        name = self.name or self._init_name(type(obj))
        setattr(owner, name, value)

    def _init_name(self, cls):
        return find_descriptor_name(self, cls)


class _ReadOnlyDelegate(_Delegate):
    """
    Read only version of Delegate.
    """

    __slots__ = ()

    def __set__(self, obj, value):
        raise AttributeError(self.name or self._init_name(type(obj)))


class _MutableAlias:
    """
    Alias to another attribute/method in class.
    """

    __slots__ = ("attr",)

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, obj, cls=None):
        if obj is not None:
            return getattr(obj, self.attr)
        return self

    def __set__(self, obj, value):
        setattr(obj, self.attr, value)


class _ReadOnlyAlias(_MutableAlias):
    """
    Like alias, but read-only.
    """

    __slots__ = ()

    def __set__(self, key, value):
        raise AttributeError(self.attr)


class _TransformingAlias(_MutableAlias):
    """
    A bijection to another attribute in class.
    """

    __slots__ = ("transform", "prepare")

    def __init__(self, attr, transform=lambda x: x, prepare=None):
        super().__init__(attr)
        self.attr = attr
        self.transform = to_callable(transform)
        self.prepare = None if prepare is None else to_callable(prepare)

    def __get__(self, obj, cls=None):
        if obj is not None:
            return self.transform(getattr(obj, self.attr))
        return self

    def __set__(self, obj, value):
        if self.prepare is None:
            raise AttributeError(self.attr)
        else:
            value = self.prepare(value)
        setattr(obj, self.attr, value)


#
# Utility functions
#
def find_descriptor_name(descriptor, cls: type, hint=None):
    """
    Finds the name of the descriptor in the given class.
    """

    if hint is not None and getattr(cls, hint, None) is descriptor:
        return hint

    for attr in dir(cls):
        value = getattr(cls, attr, None)
        if value is descriptor:
            return attr
    raise RuntimeError("%r is not a member of class" % descriptor)


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
        raise RuntimeError("%r is not a member of %s" % descriptor)
    return owner
