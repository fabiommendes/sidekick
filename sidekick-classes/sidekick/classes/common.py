from functools import singledispatch
from typing import Annotated, Any, Callable, Iterable, Iterator, Mapping, NoReturn, Protocol, Type, TypeVar, overload


V = TypeVar("V")
T = TypeVar("T")
NOT_GIVEN: Any = object()


class BinOp(Protocol[T]):
    def __call__(self, x: T, y: T, /) -> T:
        ...


class Object(Mapping[str | type, V]):
    """
    Implements the sidekick.classes.semigroup object.
    """

    instances: Any
    _empty_msg: str

    def __init__(self):
        name = type(self).__name__.strip("_").removesuffix("Object").lower()
        self._cache = dict[type | str, V]()
        self._fallback = error_fallback("Not a " + name + ": {type}")
        self._dispatcher = singledispatch(self._fallback)

    @overload
    def __call__(self, x: T, y: T, /, *args: T) -> T:
        ...

    @overload
    def __call__(self, x: Iterable[T], /) -> T:
        ...

    def __call__(self, *args):
        match args:
            case ():
                raise TypeError(self._empty_msg)
            case (seq,):
                try:
                    x = next(xs := iter(seq))
                except StopIteration:
                    return self()
                fn = self[type(x)]
                return fn(x, fn(xs))
            case (x, *xs):
                return self[type(x)](x, *xs)

    @overload  # type: ignore
    def __getitem__(self, key: Type[T]) -> Annotated[V, T]:
        ...
    
    @overload
    def __getitem__(self, key: str) -> V:
        ...
        
    def __getitem__(self, key):
        try:
            return self._cache[key]
        except KeyError:
            pass

        if isinstance(key, str):
            try:
                instance = getattr(self.instances, key)
            except AttributeError:
                raise KeyError(key)
        else:
            try:
                instance = self.dispatch(key)
            except TypeError:
                raise KeyError(key)
        return instance
    
    @overload  # type: ignore
    def __setitem__(self, key: Type[T], value: Annotated[V, T]) -> None:
        ...
    
    @overload
    def __setitem__(self, key: str, value: V) -> None:
        ...
        
    def __setitem__(self, key, value):
        if isinstance(key, str):
            if getattr(self.instances, key, None) is None:
                self.instances.__all__.append(key)
                self.instances.__all__.sort()
            setattr(self.instances, key, value)
        else:
            self.register(key, value)
    
    def __iter__(self) -> Iterator[str | type]:
        yield from self._dispatcher.registry()
        yield from dir(self.instances)

    def __len__(self) -> int:
        return len(self._dispatcher.registry) + len(dir(self.instances))

    def dispatch(self, typ: Type[T]) -> Annotated[V, T]:
        """
        Compute instance using type.
        """
        instance = self._dispatcher.dispatch(typ)
        if instance is not self._fallback:
            return instance

        return self._dispatch_implicit(typ) or self._fallback()
        
    def _dispatch_implicit(self, typ):
        return None
    
    @overload
    def register(self, typ: Type[T], impl: Annotated[V, T], /) -> None:
        ...

    @overload
    def register(self, typ: Type[T], /) -> Callable[[V], V]:
        ...

    def register(self, typ, impl=NOT_GIVEN, /):
        """
        Register
        """
        if impl is NOT_GIVEN:
            return lambda impl_: self.register(typ, impl_) or impl_

        self._cache.clear()
        self._dispatcher.register(typ, impl)


def error_fallback(msg: str) -> Callable[[Any], NoReturn]:
    """
    Raise errors with given message
    """

    def impl(x: Any) -> NoReturn:
        raise TypeError(msg.format(type=type(x)))

    setattr(impl, "is_invalid_instance", True)
    return impl


def invalid_instance(*args: T, for_type=None) -> T:
    """
    An invalid instance implementation.
    """
    if for_type is not None:
        name = for_type.__name__
    elif args:
        name = type(args[0]).__name__
    else:
        name = "object"
    raise TypeError(f"{name} is not a valid semigroup instance.")


def is_invalid_instance(impl: Any) -> bool:
    """
    Query if implementation represents a valid class instance or not.
    """
    return getattr(impl, "is_invalid_instance", True)


setattr(invalid_instance, "is_invalid_instance", True)