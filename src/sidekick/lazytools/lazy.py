from importlib import import_module

from .deferred import Deferred
from ..core import extract_function

__all__ = ["lazy", "property", "delegate_to", "alias", "import_later"]
_property = property


def lazy(func=None, *, shared=False, name=None):
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
    """
    if func is None:
        return lambda f: lazy(f, shared=shared, name=name)

    if shared:
        return SharedLazy(func, name=name)
    else:
        return Lazy(func, name=name)


# noinspection PyShadowingBuiltins,PyPep8Naming
class property(_property):
    """
    A Sidekick-enabled property descriptor. It behaves just as standard Python
    properties, but it also accepts placeholder expressions as a getter input.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(extract_function(fget), fset, fdel, doc)

    def getter(self, fget):
        return super().getter(extract_function(fget))

    def setter(self, fset):
        return super().setter(extract_function(fset))


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
        return ReadOnlyDelegate(attr, name)
    else:
        return Delegate(attr, name)


def alias(attr, *, mutable=False, transform=None, prepare=None):
    """
    An alias to an attribute.

    Args:
        attr (str):
            Name of aliased attribute.
        mutable (bool):
            If True, makes the alias mutable.
        transform (callable):
            If given, transforms the resulting value
        prepare
    """
    if transform is not None or prepare is not None:
        return TransformingAlias(attr, transform, prepare)
    elif mutable:
        return MutableAlias(attr)
    else:
        return ReadOnlyAlias(attr)


def import_later(path, package=None):
    """
    Lazily import module or object inside a module. Can refer to a module or
    a symbol exported by that module.

    Args:
        path:
            Python path to module or object. Specific objects inside a module
            are refered as "<module path>:<object name>".
        package:
            Package name if path is a relative module path.

    Usage:
        import_later('numpy.random'):
            Proxy to the numpy.random module.
        import_later('numpy.random:uniform'):
            Proxy to the "uniform" object of the numpy module.
        import_later('.models', package=__package__):
            Relative import
    """
    if ":" in path:
        path, _, obj = path.partition(":")
        return DeferredImport(path, obj, package=package)
    else:
        return LazyModule(path, package=package)


#
# Helper classes
#
class Lazy:
    """
    Lazy attribute of an object
    """

    __slots__ = ("function", "name")

    def __init__(self, func, name=None):
        self.function = extract_function(func)
        self.name = name

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        name = self.name or self._init_name(cls)
        value = self.function(obj)
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


class SharedLazy(Lazy):
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
        self.value = self.function(cls)
        return self.value


class Delegate:
    """
    Delegate attribute to another attribute.
    """

    __slots__ = ("attr", "name")
    __set_name__ = Lazy.__set_name__

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


class ReadOnlyDelegate(Delegate):
    """
    Read only version of Delegate.
    """

    __slots__ = ()

    def __set__(self, obj, value):
        raise AttributeError(self.name or self._init_name(type(obj)))


class MutableAlias:
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


class ReadOnlyAlias(MutableAlias):
    """
    Like alias, but read-only.
    """

    __slots__ = ()

    def __set__(self, key, value):
        raise AttributeError(self.attr)


class TransformingAlias(MutableAlias):
    """
    A bijection to another attribute in class.
    """

    __slots__ = ("transform", "prepare")

    def __init__(self, attr, transform=lambda x: x, prepare=None):
        super().__init__(attr)
        self.attr = attr
        self.transform = extract_function(transform)
        self.prepare = None if prepare is None else extract_function(prepare)

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


class LazyModule(Deferred):
    """
    A module that has not been imported yet.
    """

    def __init__(self, path, package=None):
        super().__init__(import_module, path, package=package)

    def __getattr__(self, attr):
        value = super().__getattr__(attr)
        setattr(self, attr, value)
        return value


class DeferredImport(Deferred):
    """
    An object of a module that has not been imported yet.
    """

    def __init__(self, path, attr, package=None):
        mod = LazyModule(path, package)
        super().__init__(lambda: getattr(mod, attr))


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
