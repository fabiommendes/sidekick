from __future__ import annotations

import operator
from collections.abc import Iterator
from dataclasses import dataclass
from functools import partial, total_ordering
from typing import (TYPE_CHECKING, Any, Container, Generic, Iterable,
                    TypeGuard, final)

from .util import (BoundAttrGetter, BoundMethodGetter, Constant, Fn, a, b,
                   maybe_operator, r)

if TYPE_CHECKING:
    from .result import Err, Ok, Result

identity = lambda x: x
this = None
DEFAULT_ERROR: Any = Exception


@total_ordering
class Maybe(Generic[a]):
    """
    Represent data that can be missing.

    A Maybe can be in one of two states: Just(value), when some value exists or
    Nothing, when data is missing. This is a type safe alternative to None and
    can be useful to avoid an excessive amount of ``if x is None: ...`` checks
    in your code.
    """

    is_just: TypeGuard[Just] = False
    is_nothing: TypeGuard[_Nothing] = False
    is_success: TypeGuard[Just] = False
    is_failure: TypeGuard[_Nothing] = False

    Just: type[Just]
    Nothing: Maybe
    value: a | None

    @classmethod
    def from_value(cls, value: a, /) -> Maybe[a]:
        """
        Create a Just(x) maybe from argument.
        """
        return Just(value)

    @classmethod
    def from_optional(cls, value: a | None, /) -> Maybe[a]:
        """
        Create a Just(x) maybe from argument or Nothing if argument is None.

        Example:
            >>> Maybe.from_optional(None)
            Nothing
            >>> Maybe.from_optional(42)
            Just(42)
        """
        if value is None:
            return Nothing  # type: ignore
        return Just(value)

    @classmethod
    def apply(cls, func: Fn[..., r], *args: Maybe[a], **kwargs) -> Maybe[r]:
        """
        Execute function with all given Maybe values unwrapping all positional
        arguments and return ``Just(result)`` or ``Nothing`` if result is None.

        If any positional argument is a Nothing, returns Nothing. None values and
        keyword arguments do not propagate the Nothing state.

        Examples:
            >>> Maybe.apply(max, Just(1), Just(2), Just(3))
            Just(3)
            >>> Maybe.apply(max, Just(1), Nothing, Just(3))
            Nothing
        """
        return cls.__functor_apply__(partial(func, **kwargs), args)

    def __new__(self, value: a | None):
        if value is None:
            return Nothing
        else:
            return Just(value)

    def map(self, func: Fn[[a], b]) -> Maybe[b]:
        """
        Apply function if object is in the Just state and return another Maybe.

        Examples:
            >>> Just(40).map(X + 2)
            Just(42)
        """
        match self:
            case Just(x):
                return Just(func(x))
            case _:
                return self  # type: ignore

    def map_error(self, func: Fn[[Any], Any]) -> Maybe[a]:
        """
        Does nothing, exists for compatibility with Result.
        """
        return self

    def replace(self, value: b) -> Maybe[b]:
        """
        Replace the wrapped value of a success state by the given value.

        This is equivalent to self.map(lambda _: value).

        Examples:
            >>> Just(40).replace(42)
            Just(42)
            >>> Nothing.replace(42)
            Nothing
        """
        match self:
            case Just(_):
                return Just(value)
            case _:
                return self  # type: ignore

    def replace_error(self, error: Any) -> Maybe[a]:
        """
        Does nothing, exists for compatibility with Result.
        """
        return self

    def flatmap(self, func: Fn[[a], Maybe[b] | b | None]) -> Maybe[b]:
        """
        Apply function that returns another Maybe and flatten the results.

        Function can also return a nullable value. In that case, None is
        mapped to Nothing and any other value becomes Just(value).

        Examples:
            If function returns a Maybe, like,

            >>> func = lambda x: Maybe.from_optional(x).map(2 * X)

            flatmap will map a function and flatten the nested Maybes. This is different
            from map, which does not flatten the results.

            >>> Just(21).flatmap(func)
            Just(42)
            >>> Just(21).map(func)  # map doesn't flatten.
            Just(Just(42))
        """
        match self:
            case Just(x):
                if isinstance(result := func(x), Maybe):
                    return result
                return self.from_optional(result)
            case _:
                return self  # type: ignore

    def flatmap_error(self, func: Fn[[Any], Maybe[a]]) -> Maybe[a]:
        """
        Does nothing, exists for compatibility with Result.
        """
        return self

    def flatten(self: Maybe[Maybe[a]]) -> Maybe[a]:
        """
        Flatten one level of nested maybe structures.

        It also normalize Just(None) as Nothing.

        Examples:
            >>> Just(Just(42)).flatten()
            Just(42)
            >>> Just(None).flatten()
            Nothing
        """
        return self.flatmap(identity)

    def flatten_error(self) -> Maybe[a]:
        """
        Does nothing, exists for compatibility with Result.
        """
        return self

    def flatten_deep(self) -> Maybe[Any]:
        """
        Flatten any number of nested maybe structures.

        It also normalize Just(None) as Nothing.

        Examples:
            >>> Just(Just(Just(42))).flatten_deep()
            Just(42)
        """
        while type(self) is Just:
            self = self.value
        if self is None or self is Nothing:
            return Nothing  # type: ignore
        return Just(self)

    def ap(self, func: Maybe[Fn[[a], b]]) -> Maybe[b]:
        """
        Execute function inside a Maybe container.

        Examples:
            >>> Just(1).ap(Just(X + 1))
            Just(2)

        It wil return Nothing if either the function or the argument
        is in the Nothing state.
        """
        match self:
            case Just(x):
                return func.map(lambda f: f(x))
            case _:
                return self  # type: ignore

    def value_or(self, default: a) -> a:
        """
        Extract value from the Just state. If object is Nothing, return the
        supplied default.

        The default is required for this function. If tou want to use None as
        default, simply use the ``.value`` attribute.

        Examples:
            >>> Just(42).value_or(0)
            42
            >>> Nothing.value_or(0)
            0
            >>> Nothing.value is None
            True
        """
        match self:
            case Just(x):
                return x
            case _:
                return default

    def value_or_call(self, func: Fn[[], a]) -> a:
        """
        Like value_or, but calls a function to compute the default value.

        This function exists for the cases in which the default value is
        expensive to compute.

        Examples:
            >>> Nothing.value_or_call(lambda: 42)
            42
        """
        match self:
            case Just(x):
                return x
            case _:
                return func()

    def unwrap(self) -> a:
        """
        Return the Just(x) case or raises a ValueError exception.

        Examples:
            >>> Just(42).unwrap()
            42
            >>> Nothing.unwrap()
            Traceback (most recent call last):
            ...
            ValueError: Maybe is in an error state.
        """
        match self:
            case Just(x):
                return x
            case _:
                raise ValueError("Maybe is in an error state.")

    @property
    def method(self) -> BoundMethodGetter[Maybe[Any]]:
        """
        Call the given method of value and promote result to a Maybe.

        Examples:
            >>> Just(1 + 2j).method('conjugate')
            Just((1-2j))
        """
        return BoundMethodGetter(self, self.from_optional)

    @property
    def attr(self) -> BoundAttrGetter[Maybe[a]]:
        """
        Retrieves attribute as a Maybe.

        Nones are converted to Nothing.

        Examples:
            >>> Just(1 + 2j).attr('real')
            Just(1.0)
        """
        return BoundAttrGetter(self, self.from_optional)

    def iter(self: Maybe[Iterable[a]]) -> Iterator[a]:
        """
        Iterates over content.

        It returns an empty iterator in the Nothing case.
        """
        match self:
            case Just(value):
                yield from value
            case _:
                return

    def to_result(self, err: b = DEFAULT_ERROR) -> Result[b, a]:
        """
        Convert Maybe to Result.

        >>> Just(42).to_result()
        Ok(42)
        """
        match self:
            case Just(value):
                return Ok(value)
            case _:
                return Err(err)

    def to_maybe(self) -> Maybe[a]:
        """
        Return itself.

        This function exists so some algorithms can work with both Maybe's and
        Result's using the same interface.
        """
        return self

    # Sidekick functional interfaces
    __functor_map__ = map
    __functor_flatmap__ = flatmap

    @classmethod
    def __functor_apply__(
        cls, func: Fn[..., b], args: tuple[Maybe[a], ...]
    ) -> Maybe[b]:
        return cls.__functor_args__(args).map(func)

    @classmethod
    def __functor_flatapply__(
        cls, func: Fn[..., Maybe[b]], *args: Maybe[a]
    ) -> Maybe[b]:
        match cls.__functor_args__(args):
            case Just(args):
                return func(*args)
            case _:
                return Nothing  # type: ignore

    @staticmethod
    def __functor_args__(args: tuple[Maybe[a], ...]) -> Maybe[tuple]:
        acc: list[a] = []
        for arg in args:
            match arg:
                case Just(x):
                    acc.append(x)
                case _:
                    return Nothing  # type: ignore
        return Just(tuple(acc))

    @staticmethod
    def __functor_wrap__(x: a) -> Maybe[a]:
        return Just(x)

    @staticmethod
    def __alternative_empty__(x) -> Maybe[a]:
        return Nothing  # type: ignore

    @staticmethod
    def __alternative_any__(x: Maybe[a], y: Maybe[a]) -> Maybe[a]:
        return x if x.is_just else y

    # Operators
    __add__ = maybe_operator(operator.add)
    __floordiv__ = maybe_operator(operator.floordiv)
    __mod__ = maybe_operator(operator.mod)
    __mul__ = maybe_operator(operator.mul)
    __pow__ = maybe_operator(operator.pow)
    __sub__ = maybe_operator(operator.sub)
    __truediv__ = maybe_operator(operator.truediv)

    __and__ = maybe_operator(operator.and_)
    __lshift__ = maybe_operator(operator.lshift)
    __rshift__ = maybe_operator(operator.rshift)
    __or__ = maybe_operator(operator.or_)
    __xor__ = maybe_operator(operator.xor)

    def __lt__(self, other: Maybe[a]) -> bool:
        match self:
            case Just(x):
                if type(other) is Just:
                    return x < other.value
                elif other is Nothing:
                    return False
                else:
                    return NotImplemented
            case _:
                if type(other) is Just:
                    return True
                elif other is Nothing:
                    return False
                else:
                    return NotImplemented

    def __eq__(self, other) -> bool:
        match self:
            case Just(x):
                if type(other) is Just:
                    return x == other.value
                elif other is Nothing:
                    return False
                return NotImplemented
            case _:
                if other is Nothing:
                    return True
                elif type(other) is Just:
                    return False
                return NotImplemented

    def __contains__(self, other) -> bool:
        match self:
            case Just(x):
                return other in x
            case _:
                return False

    def __getitem__(self: Maybe[Container[a]], item) -> Maybe[a]:
        match self:
            case Just(value):
                return Just(value[item])
            case _:
                return self  # type: ignore

    def __neg__(self) -> Maybe[a]:
        match self:
            case Just(x):
                return Just(-x)
            case _:
                return self  # type: ignore

    def __pos__(self) -> Maybe[a]:
        match self:
            case Just(x):
                return Just(+x)
            case _:
                return self  # type: ignore

    def __invert__(self) -> Maybe[a]:
        match self:
            case Just(x):
                return Just(~x)
            case _:
                return self  # type: ignore

    def __call__(self: Maybe[Fn[..., b]], /, *args, **kwargs) -> Maybe[b]:
        match self:
            case Just(f):
                return Just(f(*args, **kwargs))
            case _:
                return self  # type: ignore

    def __iter__(self):
        match self:
            case Just(x):
                yield x
            case _:
                yield from ()


@final
@dataclass(frozen=True)
class Just(Maybe[a]):
    """
    The success state of a Maybe.
    """

    value: a
    is_success = True
    is_just = True

    def __new__(cls, value):
        new = object.__new__(cls)
        object.__setattr__(new, "value", value)
        return new

    def __repr__(self):
        return f"Just({self.value!r})"


@final
class _Nothing(Constant, Maybe[a]):
    """
    The failure state of a Maybe.

    Nothing is a special singleton value.
    """

    __slots__ = ()
    value = None
    is_failure = True
    is_nothing = True


Nothing: _Nothing = _Nothing()
Maybe.Just = Just
Maybe.Nothing = Nothing
