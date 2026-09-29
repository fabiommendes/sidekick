import abc
from functools import cached_property, wraps
import itertools
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
from . import monoid as monoids

T = TypeVar("T")
T_m = TypeVar("T_m", bound="GroupT")
NOT_GIVEN: Any = object()


@runtime_checkable
class GroupF(Protocol[T]):
    """
    A function/callable that implements the monoid interface.

    It differs from the semigroup interface in which it also accept empty iterators
    or empty arguments. It returns the neutral element in both situations.
    """

    @overload
    def __call__(self) -> T:
        ...

    @overload
    def __call__(self, x: T, y: T, /, *args: T) -> T:
        ...

    @overload
    def __call__(self, x: Iterable[T], /) -> T:
        ...

    def __call__(self, *args):
        raise NotImplementedError

    def inv(self, x: T) -> T:
        raise NotImplementedError


class Group(GroupF[T], monoids.Monoid):
    """
    Implements a semigroup function extended interface.

    This adds some methods to the purely functional interface.
    """

    __call__ = monoids.Monoid.__call__  # type: ignore

    def __init__(self, *, inv=NOT_GIVEN, **kwargs):
        if inv is NOT_GIVEN:
            raise ValueError("inverse must be specified")
        self.inv = inv
        super().__init__(**kwargs)

    def inv(self, x: T) -> T:
        """
        Return the neutral element.
        """
        raise NotImplementedError

    def times(self, x: T, n: int) -> T:
        if n < 0:
            return self.times(self.inv(x), n)
        else:
            return super().times(x, n)


class GroupT(monoids.MonoidT, abc.ABC):
    """
    Type with an explicit implementation of semigroups.

    Instances must implement the self.combine(other) method.
    """

    _group_instance: Group

    @abc.abstractclassmethod
    def inv(self: T_m) -> T_m:
        """
        Associative operation that defines the semigroup.
        """
        raise NotImplementedError

    @classmethod
    def group_instance(cls: Type[T_m]) -> Group[T_m]:
        """
        Return a semigroup instance for the type.
        """
        if (instance := cls.__dict__.get("_group_instance")) is not None:
            return instance

        cls._group_instance = func = group.from_operator(
            cls.inv, cls.neutral, cls.combine
        )
        try:
            func.__name__ = cls.__name__  # type: ignore
            func.__qualname__ = cls.__qualname__ + ".instance"  # type: ignore
        except AttributeError:
            pass
        return func


@runtime_checkable
class GroupBySummation(monoids.MonoidBySummation, Protocol):
    """
    A group that associates using addition.

    This protocol makes the optimistic assumption that
    all implementations of __add__ are associative. This is the case
    for all Python builtins, but there are no guarantees.
    """

    @classmethod
    def negate(cls: Type[T]) -> T:
        raise NotImplementedError


@runtime_checkable
class GroupByProduct(monoids.MonoidByProduct, Protocol):
    """
    A group that associates using multiplication.

    This protocol makes the optimistic assumption that
    all implementations of __mul__ are associative. This is the case
    for many Python builtins, but there are no guarantees.
    """

    @classmethod
    def inverse(cls: Type[T]) -> T:
        raise NotImplementedError


class _GroupObject(Object[Group[Any]]):
    """
    Implements the sidekick.classes.semigroup object.
    """

    @cached_property
    def instances(self):
        from . import group_instances

        return group_instances

    _empty_msg = "cannot determine the group in empty sequence: type group[type] to explicitly select it."

    if TYPE_CHECKING:

        @overload  # type: ignore
        def __getitem__(self, key: Type[T]) -> Group[T]:
            ...

        @overload
        def __getitem__(self, key: str) -> Group[Any]:
            ...

        def __getitem__(self, key):
            return super().__getitem__(key)

    def _dispatch_implicit(self, typ) -> Group[T] | None:
        if issubclass(typ, GroupT):
            return typ.monoid_instance()  # type: ignore

        if issubclass(typ, GroupBySummation):
            return self.from_operator(typ.negate, typ.zero, typ.__add__)

        if issubclass(typ, GroupByProduct):
            return self.from_operator(typ.inverse, typ.one, typ.__mul__)

        return None

    #
    # Creating instances
    #
    def from_operator(
        self, neutral: Callable[[], T], inv: Callable[[T], T], op: BinOp[T]
    ) -> Group[T]:
        """
        Create group from binary operation and neutral element.
        """

        @wraps(op)
        def impl(*args):
            if len(args) == 1:
                args = args[0]

            try:
                x = next(xs := iter(args))
            except StopIteration:
                return neutral()
            for x_ in xs:
                x = op(x, x_)
            return x

        impl.inv = inv
        return impl

    def from_reducer(
        self, inv: Callable[[T], T], func: Callable[[Iterable[T]], T]
    ) -> Group[T]:
        """
        Create group from a function that receives an iterable
        and return the result of combining all elements.
        """

        @wraps(func)
        def impl(*args):
            if len(args) == 1:
                return func(args[0])
            else:
                return func(args)

        impl.inv = inv
        return impl

    def from_function(self, inv: Callable[[T], T], func: Callable[..., T]) -> Group[T]:
        """
        Create group from variadic function that implements
        binary operation on all of its arguments.
        """

        @wraps(func)
        def impl(*args):
            if len(args) == 1:
                wait = list[T]()
                seq = iter(args)

                while True:
                    chunk = tuple(itertools.islice(seq, 32))
                    if chunk:
                        wait.append(func(*chunk))
                    else:
                        break

                if (n := len(wait)) == 0:
                    return func()
                elif n > 32:
                    return impl(itertools.chain(wait))
                else:
                    return func(*wait)
            else:
                return func(*args)

        impl.inv = inv
        return impl


group = _GroupObject()
