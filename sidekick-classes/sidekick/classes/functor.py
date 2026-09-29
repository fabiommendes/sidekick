import abc
import copy
from functools import cached_property
from typing import (
    Any,
    Annotated as Bind,
    Callable as Fn,
    Generic,
    Iterable,
    Literal,
    Type,
    runtime_checkable,
    overload,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
)
from .common import Object

a = TypeVar("a")
b = TypeVar("b")
F = TypeVar("F")
Ft = TypeVar("Ft", bound="FunctorT")
Fmt = TypeVar("Fmt", bound="FunctorMut")
NOT_GIVEN: Any = object()


@runtime_checkable
class FunctorF(Protocol[F]):
    """
    A function/callable that implements the functor interface.
    """

    def __call__(self, f: Fn[[a], b], ft: Bind[F, a]) -> Bind[F, b]:
        raise NotImplementedError


class Functor(FunctorF[F]):
    """
    Implements the functor function extended interface.

    This adds some methods to the purely functional interface.
    """

    _OVERRIDES = {"lift": "lift", "replace": "replace", "void": "void"}

    def __init__(self, map: FunctorF[F], map_inplace=None, **kwargs):
        self._fmap_inplace = map_inplace
        self._fmap = map
        for k, v in kwargs.items():
            try:
                attr = self._OVERRIDES[k]
            except KeyError:
                raise TypeError(f"invalid argument: {k}")
            setattr(self, attr, v)

    def __call__(self, f: Fn[[a], b], ft: Bind[F, a]) -> Bind[F, b]:
        return self._fmap(f, ft)

    def map(self, func: Fn[[a], b], ft: Bind[F, a]) -> Bind[F, b]:
        """
        Maps function to elements of functor.

        For functors, this is an alias to self(f, ft). Applicatives generalize
        functor to receive many arguments and monads automatically flatten
        results.

        Signature:
            map(a -> b, F[a]) -> F[b]
        """
        return self._fmap(func, ft)

    def map_inplace(
        self, func: Fn[[a], b], ft: Bind[F, a], *, force: bool = False
    ) -> Bind[F, b]:
        """
        Modify functor, possibly changing it inplace.

        Returns the modified functor or a new functor.
        """
        if self._fmap_inplace is not None:
            return self._fmap_inplace(func, ft)
        elif force:
            name = type(ft).__name__
            raise TypeError(f"{name} object cannot be modified inplace")
        else:
            return self.map(func, ft)

    def lift(self, func: Fn[[a], b]) -> Fn[[Bind[F, a]], Bind[F, b]]:
        """
        Lift a function that act on elements a to act on functors F[a].

        Signature:
            lift(a -> b) -> (F[a] -> F[b])
        """
        map = self.map
        return lambda fa: map(func, fa)

    def replace(
        self, x: b, ft: Bind[F, a], *, inplace: bool | Literal["force"] = False
    ) -> Bind[F, b]:
        """
        Replace all elements in functor "ft" the the value x.

        If inplace=True, try to modify inplace. If inplace="force", raise an
        error if type do not accept mutation.
        """
        if inplace:
            return self.map_inplace(lambda _: x, ft, force=inplace == "force")
        return self._fmap(lambda _: x, ft)

    def void(
        self, ft: Bind[F, a], *, inplace: bool | Literal["force"] = False
    ) -> Bind[F, None]:
        """
        Discard content of container, keeping only the structure
        of the object.

        If inplace=True, try to modify inplace. If inplace="force", raise an
        error if type do not accept mutation.
        """
        return self.replace(None, ft, inplace=inplace)

    def with_map_inplace(self, func: FunctorF[F]) -> "Functor[F]":
        """
        Creates as new functor instance adding a function for inplace
        mutation.
        """
        new = copy.copy(self)
        new._fmap_inplace = func
        return new


class FunctorT(Generic[a], abc.ABC):
    """
    Type with an explicit implementation of semigroups.

    Instances must implement the self.combine(other) method.
    """

    _functor_instance: Functor

    @classmethod
    def functor_instance(cls: Type[Ft]) -> Functor[Ft]:
        """
        Return a semigroup instance for the type.
        """
        if (instance := cls.__dict__.get("_functor_instance")) is not None:
            return instance

        cls._functor_instance = func = Functor(lambda f, ft: ft.map(f))  # type: ignore
        try:
            func.__name__ = cls.__name__  # type: ignore
            func.__qualname__ = cls.__qualname__ + ".instance"  # type: ignore
        except AttributeError:
            pass
        return func

    @abc.abstractclassmethod
    def map(self: Bind[F, a], func: Fn[[a], b]) -> Bind[F, b]:
        """
        Map function on elements of functor.
        """
        raise NotImplementedError

    def replace(self: Ft, x: a) -> Bind[Ft, a]:
        """
        Replace values on functor by x, producing new functor.
        """
        return self.map(lambda _x: x)


class FunctorMut(FunctorT[a], abc.ABC):
    """
    A functor that accepts inplace mutation.
    """

    @abc.abstractclassmethod
    def map_inplace(self: Bind[F, a], func: Fn[[a], b]) -> None:
        """
        Map function inplace, mutating functor.
        """
        raise NotImplementedError

    def replace(self: Fmt, x: a, *, inplace: bool = False) -> Bind[Fmt, a]:
        """
        Replace values on functor by x.

        Modify functor inplace if inplace=True, otherwise produce a new functor.
        """
        if inplace:
            self.map_inplace(lambda _: x)
            return self
        return self.map(lambda _x: x)


class _FunctorObject(Object[Functor[Any]]):
    """
    Implements the sidekick.classes.functor object.
    """

    @cached_property
    def instances(self):
        from . import functor_instances

        return functor_instances

    if TYPE_CHECKING:

        @overload  # type: ignore
        def __getitem__(self, key: Type[a]) -> Functor[a]:
            ...

        @overload
        def __getitem__(self, key: str) -> Functor[Any]:
            ...

        def __getitem__(self, key):
            return super().__getitem__(key)

    def _dispatch_implicit(self, typ) -> Functor[a] | None:
        if issubclass(typ, FunctorT):
            return typ.functor_instance()  # type: ignore

        return None

    #
    # Creating instances
    #
    def from_map(self, fmap: Fn[[Fn[[a], b], Bind[F, a]], Bind[F, b]], **kwargs) -> Functor[a]:
        """
        Create functor from variadic function that implements
        binary operation on all of its arguments.
        """
        return Functor(fmap, **kwargs)  # type: ignore

    def from_iterable_and_wrap(
        self, wrap: Fn[[Iterable[a]], F], unwrap=iter, **kwargs
    ) -> Functor[F]:
        """
        Create functor from iterable that is wrapped back
        as a container using the given wrapper.

        For most sequence types, the wrapper is a the type and the unwrapper is iter.
        """

        def fmap(f, xs):
            return wrap(f(x) for x in unwrap(xs))

        return Functor(fmap, **kwargs)


functor = _FunctorObject()
