import abc
from functools import cached_property
from typing import (
    Any,
    Annotated as Bind,
    Callable as Fn,
    Generic,
    Iterable,
    Type,
    runtime_checkable,
    overload,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
)
from .common_definition import Object
from . import applicative_definition as applicatives

T = TypeVar("T")
S = TypeVar("S")
F = TypeVar("F")
Ft = TypeVar("Ft", bound="MonadT")
NOT_GIVEN: Any = object()


@runtime_checkable
class MonadF(Protocol[F]):
    """
    A function/callable that implements the apply_flat interface.
    """

    def __call__(self, f: Fn[[T], Bind[F, S]], ft: Bind[F, T]) -> Bind[F, S]:
        raise NotImplementedError


class Monad(applicatives.Applicative[F]):
    """
    Implements the monad function extended interface.

    This adds some methods to the purely functional interface.
    """

    def __init__(self, fmap: Fn[[Fn[[T], S], Bind[F, T]], Bind[F, S]]):
        self._fmap = fmap

    def __call__(self, f: Fn[[T], S], ft: Bind[F, T]) -> Bind[F, S]:
        return self._fmap(f, ft)

    def map(self, func: Fn[[T], S], ft: Bind[F, T]) -> Bind[F, S]:
        """
        Maps function to elements of functor.
1
        This is equivalent to self(f, ft).

        Args:
            func (a -> b):
                Function mapped over elements.
            ft (F[a]):
                Monad of a

        Returns:
            F[b]: A functor with the results of application of func to ft.
        """
        return self._fmap(func, ft)

    def replace(self, x: S, ft: Bind[F, T]) -> Bind[F, S]:
        """
        Replace all elements in functor "ft" the the value x.
        """
        return self._fmap(lambda _: x, ft)  # type: ignore

    def void(self, ft: Bind[F, T]) -> Bind[F, None]:
        """
        Discard content of container, keeping only the structure
        of the object.
        """
        return self.replace(None, ft)


class MonadT(applicatives.Applicative[F], abc.ABC):
    """
    Type with an explicit implementation of semigroups.

    Instances must implement the self.combine(other) method.
    """

    _monad_instance: Monad

    @classmethod
    def monad_instance(cls: Type[Ft]) -> Monad[Ft]:
        """
        Return a semigroup instance for the type.
        """
        if (instance := cls.__dict__.get("_monad_instance")) is not None:
            return instance

        cls._monad_instance = func = Monad(lambda f, ft: ft.map(f))  # type: ignore
        try:
            func.__name__ = cls.__name__  # type: ignore
            func.__qualname__ = cls.__qualname__ + ".instance"  # type: ignore
        except AttributeError:
            pass
        return func


class _MonadObject(Object[Monad[Any]]):
    """
    Implements the sidekick.classes.functor object.
    """

    @cached_property
    def instances(self):
        from . import functor_instances

        return functor_instances

    if TYPE_CHECKING:

        @overload  # type: ignore
        def __getitem__(self, key: Type[T]) -> Monad[T]:
            ...

        @overload
        def __getitem__(self, key: str) -> Monad[Any]:
            ...

        def __getitem__(self, key):
            return super().__getitem__(key)

    def _dispatch_implicit(self, typ) -> Monad[T] | None:
        if issubclass(typ, MonadT):
            return typ.functor_instance()  # type: ignore

        return None

    #
    # Creating instances
    #
    def from_fmap(self, fmap: Fn[[Fn[[T], S], Bind[F, T]], Bind[F, S]]) -> Monad[T]:
        """
        Create functor from variadic function that implements
        binary operation on all of its arguments.
        """
        return Monad(fmap)  # type: ignore

    def from_iterable_and_wrap(self, wrapper: Fn[[Iterable[T]], F]) -> Monad[F]:
        """
        Create functor from iterable that is wrapped back
        as a container using the given wrapper.
        """

        def fmap(f, xs):
            return wrapper(f(x) for x in xs)

        return Monad(fmap)


monad = _MonadObject()
