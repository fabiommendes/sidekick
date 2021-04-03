from typing import (
    Union,
    Optional,
    Type,
    Generic,
    TypeVar,
    Callable,
    Any,
    overload,
    TYPE_CHECKING,
)

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
D = TypeVar("D")


__doctest_skip__ = ["lazy", "delegate_to"]  # requires preparation code

_property = property
ATTR_ERROR_MSG = """An AttributeError was raised when evaluating the {name}
lazy property:

    AttributeError: {error}

This is often an error and the default behavior is to prevent such errors to
cascade to let Python think that the attribute does not exist. If you really
want to signal that the attribute is missing, consider using the option
"lazy(..., attr_error=True
)" of the lazy property decorator.
"""

# TODO: separate module with extended function interface
try:
    from sidekick.functions import to_callable
except ImportError:

    def to_callable(x: Optional[Callable]) -> Callable:
        if x is None:
            return lambda x: x
        return x


class Prop(Generic[T1, T2]):
    """
    A property that produces values of type T1 and accepts values of type T2.

    Often those types are the same, but we cannot express it in Python's
    type system.
    """

    if TYPE_CHECKING:

        @overload
        def __get__(self, obj) -> T1:
            raise NotImplementedError

        @overload
        def __get__(self: D, obj: None, cls: type) -> D:
            ...

        def __get__(self, obj, cls=None):  # type: ignore
            raise NotImplementedError

        def __set__(self, obj, value: T2) -> None:
            ...


@overload
def lazy(
    *,
    shared: bool = False,
    name: str = None,
    attr_error: Union[Type[Exception], bool] = False,
) -> Callable[[Callable[[Any], T]], Prop[T, T]]:
    ...


@overload
def lazy(
    func: Callable[[Any], T],
    *,
    shared: bool = False,
    name: str = None,
    attr_error: Union[Type[Exception], bool] = False,
) -> T:
    ...


def lazy(  # type: ignore
    func=None,
    *,
    shared=False,
    name=None,
    attr_error=False,
):
    """
    Mark attribute that is initialized at first access rather than during
    instance creation.

    Usage is similar to ``@property``, although lazy attributes do not override
    *setter* and *deleter* methods, allowing instances to write to the
    attribute.

    Optional Args:
        shared:
            A shared attribute behaves as a lazy class variable that is shared
            among all sub-classes and instances. It differs from a simple class
            attribute in that it is initialized lazily from a function. This
            can help to break import cycles and delay expensive global
            initializations to when they are required.
        name:
            By default, a lazy attribute can infer the name of the attribute
            it refers to. In some exceptional cases (when creating classes
            dynamically), the inference algorithm might fail and the name
            attribute must be set explicitly.
        attr_error (Exception, bool):
            If False or an exception class, re-raise attribute errors as the
            given error. This prevent erroneous code that raises AttributeError
            being mistakenly interpreted as if the attribute does not exist.

    Examples:
        .. testcode::

            import math

            class Vec:
                @sk.lazy
                def magnitude(self):
                    print('computing...')
                    return math.sqrt(self.x**2 + self.y**2)

                def __init__(self, x, y):
                    self.x, self.y = x, y


        Now the ``magnitude`` attribute is initialized and cached upon first use:

        >>> v = Vec(3, 4)
        >>> v.magnitude
        computing...
        5.0

        The attribute is writable and apart from the deferred initialization, it behaves
        just like any regular Python attribute.

        >>> v.magnitude = 42
        >>> v.magnitude
        42

        Lazy attributes can be useful either to simplify the implementation of
        ``__init__`` or as an optimization technique that delays potentially
        expensive computations that are not always necessary in the object's
        lifecycle. Lazy attributes can be used together with quick lambdas
        for very compact definitions:

        .. testcode::

            import math
            from sidekick import placeholder as _

            class Square:
                area = sk.lazy(_.width * _.height)
                perimeter = sk.lazy(2 * (_.width + _.height))
    """
    if func is None:

        def decorator(fn: Callable[[Any], T]) -> Prop[T, T]:
            return lazy(fn, shared=shared, name=name, attr_error=attr_error)  # type: ignore

        return decorator

    if attr_error is False:

        def mk_error(e):
            name = prop.name
            return RuntimeError(ATTR_ERROR_MSG.format(error=e, name=name))

        attr_error = mk_error

    if shared:
        prop = _SharedLazy(func, name=name, attr_error=attr_error)
    else:
        prop = _Lazy(func, name=name, attr_error=attr_error)
    return prop


@overload
def property(fget: Callable[[Any], T]) -> Prop[T, T]:
    ...


@overload
def property(fget=None, fset=None, fdel=None, doc=None) -> Any:
    ...


def property(fget=None, fset=None, fdel=None, doc=None):
    """
    A Sidekick-enabled property descriptor.

    It is a drop-in replacement for Python's builtin property. It behaves
    similarly to Python's builtin, but also accepts quick lambdas as input
    functions. This allows very terse declarations:

    .. testcode::

        from sidekick.api import placeholder as _

        class Vector:
            sqr_radius = sk.property(_.x**2 + _.y**2)


    :func:`lazy` is very similar to property. The main difference between
    both is that properties are not cached and hence the function is re-executed
    at each attribute access. The desired behavior will depend a lot on what you
    want to do.
    """
    return _Property(fget, fset, fdel, doc)


def delegate_to(attr: str, mutable: bool = False) -> Any:
    """
    Delegate access to an inner variable.

    A delegate is an alias for an attribute of the same name that lives in an
    inner object of an instance. This is useful when the inner object contains the
    implementation (remember the "composition over inheritance mantra"), but we
    want to expose specific interfaces of the inner object.

    Args:
        attr:
            Name of the inner variable that receives delegation. It can be a
            dotted name with one level of nesting. In that case, it associates
            the property with the sub-attribute of the delegate object.
        mutable:
            If True, makes the the delegation read-write. It writes new values
            to attributes of the delegated object.


    Examples:
        .. testcode::

            class Queue:
                pop = sk.delegate_to('_data')
                push = sk.delegate_to('_data.append')

                def __init__(self, data=()):
                    self._data = list(data)

                def __repr__(self):
                    return f'Queue({self._data})'

        Now ``Queue.pop`` simply redirects to the pop method of the ``._data``
        attribute, and ``Queue.push`` searches for ``._data.append``

        >>> q = Queue([1, 2, 3])
        >>> q.pop()
        3
        >>> q.push(4); q
        Queue([1, 2, 4])
    """
    attr, _, name = attr.partition(".")
    if mutable:
        return _MutableDelegate(attr, name or None)
    else:
        return _ReadOnlyDelegate(attr, name or None)


@overload
def alias(attr: str, *, mutable: bool = False) -> Any:
    ...


@overload
def alias(attr: str, *, transform: Callable[[Any], T]) -> T:
    ...


@overload
def alias(attr: str, *, prepare: Callable[[Any], T]) -> T:
    ...


@overload
def alias(
    attr: str, *, transform: Callable[[Any], T1], prepare: Callable[[Any], T2]
) -> Prop[T1, T2]:
    ...


def alias(attr, *, transform=None, prepare=None, **kwargs) -> Any:
    """
    An alias to another attribute.

    Aliasing is another simple form of self-delegation. Aliases are views over
    other attributes in the instance itself:

    Args:
        attr:
            Name of aliased attribute.
        mutable:
            If True, makes the alias mutable. It cannot be set if either
            transform or prepare are given.
        transform:
            If given, transform output by this function before returning.
            A transformed alias without a prepare function is always immutable.
        prepare:
            If given, prepare input value before saving. Implies that transform
            is mutable. If only prepare is given, it assumes that the output
            transform is an identity function.

    Examples:
        .. testcode::

            class Queue(list):
                push: callable = sk.alias('append')

        This exposes push  additional "push" method that simply forwards
        implementation to Queue.append.
    """
    mutable = kwargs.pop("mutable", None)
    if kwargs:
        raise TypeError(f"invalid args: {set(kwargs)}")

    if transform is not None or prepare is not None:
        if mutable is not None:
            raise TypeError("cannot define mutable when a transform is given.")
        return _TransformingAlias(attr, transform, prepare)
    elif mutable:
        return _MutableAlias(attr)
    else:
        return _ReadOnlyAlias(attr)


#
# Helper classes
#
class DescriptorMixin(Prop[T1, T2]):
    """
    Functionality and interfaces shared between all descriptor classes.
    """

    is_property = True
    is_mutable = False
    is_lazy = False
    is_alias = False
    is_delegate = False

    fget: Optional[Callable[[Any], T1]]
    fset: Optional[Callable[[Any, T2], None]]
    fdel: Optional[Callable[[Any], None]]

    fget = fset = fdel = None  # type: ignore
    name: Optional[str] = None

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name


class _Property(DescriptorMixin[T, T], _property):  # type: ignore
    """
    Sidekick property descriptor.
    """

    def __init__(
        self, fget: Optional[Callable[[Any], T]] = None, fset=None, fdel=None, doc=None
    ):
        fget = fget if fget is None else to_callable(fget)
        fset = fset if fset is None else to_callable(fset)
        fdel = fdel if fdel is None else to_callable(fdel)
        super().__init__(fget, fset, fdel, doc)

    def getter(self, fget):
        return super().getter(fget if fget is None else to_callable(fget))

    def setter(self, fset):
        return super().setter(fset if fset is None else to_callable(fset))


class _Lazy(DescriptorMixin[T, T]):
    """
    Lazy attribute of an object
    """

    __slots__ = ("fget", "name", "attr_error")

    is_lazy = True
    is_mutable = True

    def __init__(self, func, name=None, attr_error=True):
        self.fget = to_callable(func)
        self.name = name
        self.attr_error = attr_error or Exception

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        name = self.name or self._init_name(cls)
        try:
            value = self.fget(obj)
        except AttributeError as ex:
            if self.attr_error is True:
                raise
            raise self.attr_error(ex) from ex

        setattr(obj, name, value)
        return value

    def _init_name(self, cls):
        function_name = self.fget.__name__
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
            self.value = self.fget(cls)
        except AttributeError as ex:
            if self.attr_error is True:
                raise
            raise self.attr_error(ex) from ex
        return self.value


class _ReadOnlyDelegate(DescriptorMixin[T, T]):
    """
    Delegate attribute to another attribute.
    """

    __slots__ = ("attr", "name")
    is_delegate = True

    def __init__(self, attr, name=None):
        self.attr = attr
        self.name = name

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        name = self.name or find_descriptor_name(self, cls)
        owner = getattr(obj, self.attr)
        return getattr(owner, name)

    def __set__(self, obj, value):
        raise AttributeError(self.name or find_descriptor_name(self, type(obj)))

    def fget(self, instance):
        return self.__get__(instance)


class _MutableDelegate(_ReadOnlyDelegate):
    """
    Mutable version of Delegate.
    """

    __slots__ = ()
    is_mutable = True

    def __set__(self, obj, value):
        owner = getattr(obj, self.attr)
        name = self.name or find_descriptor_name(self, type(obj))
        setattr(owner, name, value)


class _ReadOnlyAlias(DescriptorMixin[T, T]):
    """
    Like alias, but read-only.
    """

    __slots__ = ("attr",)
    is_alias = True

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, obj, cls=None):
        if obj is not None:
            return getattr(obj, self.attr)
        return self

    def __set__(self, key, value):
        raise AttributeError(self.attr)

    def fget(self, obj):
        return self.__get__(obj)


class _MutableAlias(_ReadOnlyAlias):
    """
    Alias to another attribute/method in class.
    """

    __slots__ = ()
    is_mutable = True

    def __set__(self, obj, value):
        setattr(obj, self.attr, value)

    def fset(self, obj, value):
        return self.__set__(obj, value)


class _TransformingAlias(_MutableAlias):
    """
    A bijection to another attribute in class.
    """

    __slots__ = ("transform", "prepare")
    is_mutable = property(lambda self: self.prepare is not None)

    def __init__(self, attr, transform=None, prepare=None):
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

    def fget(self, obj):
        return self.transform(super().fget(obj))

    def fset(self, obj, value):
        if self.prepare is None:
            raise AttributeError("cannot change attribute")
        super().fset(obj, self.prepare(value))


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
