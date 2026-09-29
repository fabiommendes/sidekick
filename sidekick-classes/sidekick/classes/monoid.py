import abc
from functools import cached_property
from typing import (
    Any,
    Callable,
    Type,
    runtime_checkable,
    overload,
    Iterable,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
)

from .common import Object, BinOp
from . import semigroup_definition as semigroups

T = TypeVar("T")
T_m = TypeVar("T_m", bound="MonoidT")
NOT_GIVEN: Any = object()


class Monoid(MonoidF[T], semigroups.Semigroup):
    """
    Implements a semigroup function extended interface.

    This adds some methods to the purely functional interface.
    """

    __call__ = semigroups.Semigroup  # type: ignore

    def __init__(
        self, *, neutral_element=NOT_GIVEN, neutral_factory=NOT_GIVEN, **kwargs
    ):
        if neutral_element is not NOT_GIVEN:
            self._neutral_element = neutral_element
        elif neutral_factory is not NOT_GIVEN:
            self._neutral_factory = self.neutral = neutral_factory
        elif "reduce" in kwargs:
            reducer = kwargs["reduce"]
            self.neutral = lambda: reducer(())
        else:
            raise ValueError("neutral element must be specified")
        super().__init__(**kwargs)

    def neutral(self):
        """
        Return the neutral element.
        """
        return self._neutral_element

    def _empty(self) -> T:
        return self.neutral()


class MonoidT(abc.ABC):
    """
    Type with an explicit implementation of semigroups.

    Instances must implement the self.combine(other) method.
    """

    _monoid_instance: Monoid

    @abc.abstractclassmethod
    def combine(self: T_m, other: T_m, /) -> T_m:
        """
        Associative operation that defines the semigroup.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    @classmethod
    def neutral(cls: Type[T_m]) -> T_m:
        """
        Associative operation that defines the semigroup.
        """
        raise NotImplementedError

    @classmethod
    def monoid_instance(cls: Type[T_m]) -> Monoid[T_m]:
        """
        Return a semigroup instance for the type.
        """
        if (instance := cls.__dict__.get("_monoid_instance")) is not None:
            return instance

        cls._monoid_instance = func = monoid.from_operator(cls.combine, cls.neutral)
        try:
            func.__name__ = cls.__name__  # type: ignore
            func.__qualname__ = cls.__qualname__ + ".instance"  # type: ignore
        except AttributeError:
            pass
        return func


@runtime_checkable
class MonoidBySummation(semigroups.SemigroupBySummation, Protocol):
    """
    A monoid that associates using addition.

    This protocol makes the optimistic assumption that
    all implementations of __add__ are associative. This is the case
    for all Python builtins, but there are no guarantees.
    """

    @classmethod
    def zero(cls: Type[T]) -> T:
        raise NotImplementedError


@runtime_checkable
class MonoidByProduct(semigroups.SemigroupByProduct, Protocol):
    """
    A monoid that associates using multiplication.

    This protocol makes the optimistic assumption that
    all implementations of __mul__ are associative. This is the case
    for many Python builtins, but there are no guarantees.
    """

    @classmethod
    def one(cls: Type[T]) -> T:
        raise NotImplementedError


class _MonoidObject(Object[Monoid[Any]]):
    """
    Implements the sidekick.classes.semigroup object.
    """

    @cached_property
    def instances(self):
        from . import monoid_instances

        return monoid_instances

    _empty_msg = "cannot determine the monoid in empty sequence: type monoid[type] to explicitly select it."

    if TYPE_CHECKING:

        @overload  # type: ignore
        def __getitem__(self, key: Type[T]) -> Monoid[T]:
            ...

        @overload
        def __getitem__(self, key: str) -> Monoid[Any]:
            ...

        def __getitem__(self, key):
            return super().__getitem__(key)

    def _dispatch_implicit(self, typ) -> Monoid[T] | None:
        if issubclass(typ, MonoidT):
            return typ.monoid_instance()  # type: ignore

        if issubclass(typ, MonoidBySummation):
            return self.from_operator(typ.zero, typ.__add__)

        if issubclass(typ, MonoidByProduct):
            return self.from_operator(typ.one, typ.__mul__)

        return None

    #
    # Creating instances
    #
    def from_operator(self, neutral: Callable[[], T], op: BinOp[T]) -> Monoid[T]:
        """
        Create monoid from binary operation and neutral element.
        """
        return Monoid(op=op, neutral_factory=neutral)

    def from_function(self, func: Callable[..., T]) -> Monoid[T]:
        """
        Create monoid from variadic function that implements
        binary operation on all of its arguments.
        """
        return Monoid(op=func, reduce=func, combine=func)


monoid = _MonoidObject()
