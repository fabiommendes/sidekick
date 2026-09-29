import abc
from functools import cached_property
from typing import (
    Any,
    Callable,
    Iterator,
    Type,
    runtime_checkable,
    overload,
    Iterable,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
)

from .common import Object, BinOp

T = TypeVar("T")
Sg = TypeVar("Sg", bound="Semigroup")
T_sm = TypeVar("T_sm", bound="SemigroupT")
NOT_GIVEN: Any = object()


class Semigroup(SemigroupF[T]):
    """
    Implements a semigroup function extended interface.

    This adds some methods to the purely functional interface.
    """

    def __init__(self, **kwargs):
        required = {"op", "combine", "reduce"}
        if not required.intersection(kwargs):
            methods = ", ".join(required)
            raise TypeError(f"must implement one of the required methods: {methods}")

        cls = type(self)
        for k, v in kwargs.items():
            if not hasattr(cls, k):
                raise TypeError(f"invalid argument: {k}")
            setattr(self, k, v)

    def __call__(self, *args):
        if (n := len(args)) == 0:
            return self._empty()
        elif n == 1:
            return self.reduce(args[0])
        elif n <= 4:
            return self.op(*args)
        else:
            return self.reduce(args)

    def op(self, x: T, y: T) -> T:
        """
        Binary operation that defines the given class.
        """
        return self.reduce([x, y])

    def combine(self, x: T, y: T, *args: T) -> T:
        """
        Apply binary operation to several arguments.
        """
        match args:
            case ():
                return self.op(x, y)
            case (z,):
                return self.op(self.op(x, y), z)
            case _:
                return self.op(self.op(x, y), self.combine(*args))

    def reduce(self, seq: Iterable[T]) -> T:
        """
        Reduces iterable by sequence of elements.

        Similar to calling ``self(*iterable)``, but do not put all elements into
        memory at once. This can be slower in many situations, but might have a
        better memory footprint.
        """
        op = self.op
        try:
            x = next(xs := iter(seq))
        except StopIteration:
            return self._empty()
        for x_ in xs:
            x = op(x, x_)
        return x

    def accumulate(self, seq: Iterable[T]) -> Iterator[T]:
        """
        Accumulate iterable using binary reduction of all of its elements.
        """
        op = self.op
        try:
            x = next(xs := iter(seq))
        except StopIteration:
            return
        else:
            yield x

        for x_ in xs:
            x = op(x, x_)
            yield x

    def times(self, x: T, n: int) -> T:
        """
        Execute binary operation n times in x.
        """
        if n == 0:
            return self._empty()
        elif n == 1:
            return x
        res = self.times(x, n // 2)
        res = self.op(res, res)
        return res if n % 2 == 0 else self.op(res, x)

    def dual(self: Sg) -> "Semigroup[T]":
        """
        Dual algebraic structure produced by flipping the binary operation.

        Commutative operations are self-dual, i.e., the dual is equal to the group
        itself.
        """
        func = self.op
        return Semigroup(op=lambda x, y: func(y, x))

    def _empty(self) -> T:
        """
        Function called on empty sequences.
        """
        raise ValueError("semigroup cannot reduce an empty sequence.")


@runtime_checkable
class SemigroupBySummation(Protocol):
    """
    A semigroup that associates using addition.

    This protocol makes the optimistic assumption that
    all implementations of __add__ are associative. This is the case
    for all Python builtins, but there are no guarantees.
    """

    def __add__(self: T, other: T) -> T:
        ...


@runtime_checkable
class SemigroupByProduct(Protocol):
    """
    A semigroup that associates using multiplication.

    This protocol makes the optimistic assumption that
    all implementations of __mul__ are associative. This is the case
    for many Python builtins, but there are no guarantees.
    """

    def __mul__(self: T, other: T) -> T:
        ...


class _SemigroupObject(Object[Semigroup[Any]]):
    """
    Implements the sidekick.classes.semigroup object.
    """

    if TYPE_CHECKING:
        from . import semigroup_instances as instances
    else:

        @cached_property
        def instances(self):
            from . import semigroup_instances

            return semigroup_instances

    _empty_msg = "semigroup do not have a neutral element"

    if TYPE_CHECKING:

        @overload  # type: ignore
        def __getitem__(self, key: Type[T]) -> Semigroup[T]:
            ...

        @overload
        def __getitem__(self, key: str) -> Semigroup[Any]:
            ...

        def __getitem__(self, key):
            return super().__getitem__(key)

    def _dispatch_implicit(self, typ) -> Semigroup[T] | None:
        if issubclass(typ, SemigroupT):
            return typ.semigroup_instance()  # type: ignore

        if issubclass(typ, SemigroupBySummation):
            return self.from_operator(typ.__add__)

        if issubclass(typ, SemigroupByProduct):
            return self.from_operator(typ.__mul__)

        return None

    #
    # Creating instances
    #
    def from_operator(self, op: BinOp[T]) -> Semigroup[T]:
        """
        Create semigroup from binary operation.
        """
        return Semigroup(op=op)

    def from_reducer(self, func: Callable[[Iterable[T]], T]) -> Semigroup[T]:
        """
        Create semigroup from a function that receives an iterable
        and return the result of combining all elements.

        The implementation function should raise a ValueError for empty sequences.
        """
        return Semigroup(reduce=func)


semigroup = _SemigroupObject()
f = semigroup[int]

def semigroup_instance(cls: Type[T_sm]) -> Semigroup[T_sm]:
    """
    Return a semigroup instance for the type.
    """
    if (instance := cls.__dict__.get("_semigroup_instance")) is not None:
        return instance

    cls._semigroup_instance = func = semigroup.from_operator(cls.combine)
    try:
        func.__name__ = cls.__name__ + "_op"  # type: ignore
        func.__qualname__ = cls.__qualname__ + ".combine"  # type: ignore
    except AttributeError:
        pass
    return func