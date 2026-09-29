from __future__ import annotations

from typing import (
    Iterable,
    overload,
    runtime_checkable,
    Any,
    Generic,
    Type,
    Protocol,
    Annotated as Bind,
    Callable as Fn,
)
from .util import a, b, c, a_co, r, F, P, err, err_


# =============================================================================
# SIDEKICK SPECIFIC PROTOCOLS
# =============================================================================
@runtime_checkable
class ToCallable(Protocol):
    """
    Objects that implements this protocol can be converted to callables
    using by the sidekick.protocols.to_callable() function.

    Callable objects can also implement this protocol to expose a more efficient
    callable object than itself when only the __call__ interface is needed.

    This is useful for wrapped functions or objects that must be compiled before
    being converted to functions.
    """

    def __sk_callable__(self) -> Fn[..., Any]:
        raise NotImplementedError


# =============================================================================
# DATA TYPES
# =============================================================================
class Fallible(Protocol, Generic[err, a]):
    """
    Generic interface for classes that wrap the results of fallible computations.

    Instances of this class can be in a failure or success state.

    Attributes:
        is_success:
            True if in a successful state.
        is_failure:
            True if in an error state.
        value (a):
            This is the wrapped value of a successful computation. The error state
            may not expose this attribute or present it with a different type
            (e.g.: a maybe.value is None in the error state)
        error (err):
            Wrapped error value. The success state may not expose this attribute
            or bind it to None or some other type.
    """

    is_success: bool
    is_failure: bool
    value: a
    error: err

    def map(self, func: Fn[[a], b]) -> Fallible[err, b]:
        """
        Apply function to wrapped value in a success state.
        """
        if self.is_success:
            return self.replace(func(self.value))
        else:
            return self  # type: ignore

    def map_error(self, func: Fn[[err], err_]) -> Fallible[err_, a]:
        """
        Apply function to wrapped value in an error state.
        """
        if self.is_failure:
            return self.replace_error(func(self.error))
        else:
            return self  # type: ignore

    def replace(self, value: b) -> Fallible[err, b]:
        """
        Replace the wrapped value of a success state by the given value.

        This is equivalent to self.map(lambda _: value).
        """
        return self.map(lambda _: value)

    def replace_error(self, error: err_) -> Fallible[err_, a]:
        """
        Replace the wrapped value of an error state by the given value.

        This is equivalent to self.map_error(lambda _: error).
        """
        return self.map_error(lambda _: error)

    def flatmap(self, func: Fn[[a], Fallible[err, b]]) -> Fallible[err, b]:
        """
        Apply function that returns another wrapped value and flatten the results.
        """
        if self.is_success:
            return func(self.value)
        else:
            return self  # type: ignore

    def flatmap_error(self, func: Fn[[err], Fallible[err_, a]]) -> Fallible[err_, a]:
        """
        Does nothing, exists for compatibility with Result.
        """
        if self.is_failure:
            return func(self.error)
        else:
            return self  # type: ignore

    def flatten(self: Fallible[err, Fallible[err, a]]) -> Fallible[err, a]:
        """
        Flatten one level of nesting.
        """
        return self.flatmap(lambda x: x)

    def flatten_error(self: Fallible[Fallible[err, a], a]) -> Fallible[err, a]:
        """
        Flatten one level of in the failure state.
        """
        return self.flatmap_error(lambda x: x)

    def flatten_deep(self) -> Fallible[err, Any]:
        """
        Flatten any number of nested wrappings.
        """
        raise NotImplementedError

    def ap(self, func: Fallible[err, Fn[[a], b]]) -> Fallible[err, b]:
        """
        Execute wrapped function with wrapped argument.
        """
        if self.is_success:
            if func.is_success:
                return self.replace(func.value(self.value))
            return func  # type: ignore
        return self  # type: ignore

    def value_or(self, default: a) -> a:
        """
        Extract value from the success state or return the supplied default.
        """
        if self.is_success:
            return self.value
        else:
            return default

    def value_or_call(self, func: Fn[[], a]) -> a:
        """
        Like value_or, but calls a function to compute the default value.

        This function exists for the cases in which the default value is
        expensive to compute.
        """
        if self.is_success:
            return self.value
        else:
            return func()

    def unwrap(self) -> a:
        """
        Return the wrapped value or raise a ValueError if in a failure state.
        """
        if self.is_success:
            return self.value
        else:
            raise ValueError(f"cannot extract value from failure state: {self}")


# =============================================================================
# FUNCTOR-LIKE TYPE CLASSES
# =============================================================================


@runtime_checkable
class Functor(Generic[a_co], Protocol):
    """
    A simple functor.

    Classes with Functor protocol automatically implement instances of the functor interface
    in :mod:`sidekick.classes`.
    """

    def __functor_map__(self: Bind[F, a_co], func: Fn[[a_co], b]) -> Bind[F, b]:
        """
        Pass each element as argument to function and return a new container with
        the transformed results.

        Signature:
            F[a].__functor_map__(a -> b) -> F[b]
        """
        raise NotImplementedError


@runtime_checkable
class FunctorMut(Functor[a], Protocol):
    """
    A functor container with inplace mutation.
    """

    def __functor_map_mut__(self: Bind[F, a], func: Fn[[a], a]) -> None:
        """
        Modify the container object inplace, possibly opening some performance
        gains by avoiding the allocation of intermediate structures in some long
        chain of computations.

        Signature:
            F[a].__func_map_mut__(a -> a) -> None
        """
        raise NotImplementedError


@runtime_checkable
class Applicative(Functor[a], Protocol):
    """
    Applicative functor container that handles variadic functions.

    It must implement an static method ``__functor_apply__(func, args)`` that maps
    some function of many arguments to a tuple of containers and return a new
    functor with transformed results created by the given function.

    This is the main way to define types that understand the applicative interface
    in :mod:`sidekick.classes`.
    """

    @classmethod
    def __functor_apply__(
        cls: Type[F], func: Fn[P, r], args: tuple[F, ...]
    ) -> Bind[F, r]:
        """
        Apply function to tuples of elements from each functor.

        It should be implemented as an static or class method.

        Signature:
            __functor_apply__(a -> r, tuple[F[a]]) -> F[r]
            __functor_apply__((a, b) -> r, tuple[F[a], F[b]]) -> F[r]
            __functor_apply__((a, b, c) -> r, tuple[F[a], F[b], F[c]]) -> F[r]
            __functor_apply__((a, b, c, ...) -> r, tuple[F[a], F[b], F[c], ...]) -> F[r]
        """
        raise NotImplementedError

    @classmethod
    def __functor_wrap__(cls: Type[F], x: a) -> Bind[F, a]:
        """
        Wraps a single element into a simple context for the functor.

        Signature:
            __functor_wrap__(a) -> F[a]
        """
        raise NotImplementedError


@runtime_checkable
class ApplicativeExt(Applicative[a], Protocol):
    """
    Additional functions that can be implemented by the applicative protocol.

    Those are present in the applicative instance and can be overridden by the following
    methods.
    """

    @staticmethod
    def __functor_pair__(
        func: Fn[[a, b], c], fa: Bind[F, a], fb: Bind[F, b]
    ) -> Bind[F, c]:
        """
        Apply a two argument function to pairs of elements of each functor.

        It should be implemented as an static or class method.

        Signature:
            __functor_pair__((a, b) -> c, F[a], F[b]) -> F[c]
        """
        raise NotImplementedError

    def __functor_ap__(self, func: Bind[F, Fn[[a], b]]) -> Bind[F, b]:
        """
        Apply function wrapped inside another functor container.

        Signature:
            F[a].__functor_ap__(F[a -> b]) -> F[b]
        """
        raise NotImplementedError


@runtime_checkable
class Monad(Applicative[a], Protocol):
    """
    A container with monadic operations.

    Applicatives that implement this protocol can create instances of the monad interface
    in :mod:`sidekick.classes`.
    """

    def __functor_flatmap__(self: Bind[F, a], func: Fn[[a], Bind[F, b]]) -> Bind[F, b]:
        """
        Pass each element as argument to function and return a new container with
        the transformed results. The difference from __functor_map__ is that the
        function returns a wrapped value which is flattened in the result.

        Signature:
            F[a].__functor_map__(a -> F[b]) -> F[b]
        """
        raise NotImplementedError


@runtime_checkable
class MonadMut(Monad[a], Protocol):
    """
    The mutable version of a monad that apply transformations inplace.
    """

    def __functor_flatmap_mut__(self: Bind[F, a], func: Fn[[a], Bind[F, a]]) -> None:
        """
        Like __functor_flatmap__, but make changes inplace.

        Signature:
            F[a].__functor_map_mut__(a -> F[a]) -> None
        """
        raise NotImplementedError


@runtime_checkable
class MonadExt(Monad[a], Protocol):
    """
    Additional functions that can be implemented by the monad protocol.

    Those are present in the monad instance and can be overridden by the following
    methods.
    """

    def __functor_flatten__(self: Bind[F, Bind[F, a]]) -> Bind[F, a]:
        """
        Flatten one level of functor nesting.

        Signature:
            F[F[a]].__flatten__() -> F[a]
        """
        raise NotImplementedError


# =============================================================================
# GROUP-LIKE TYPE CLASSES
# =============================================================================
@runtime_checkable
class SemigroupF(Protocol[a]):
    """
    A function/callable that implements the semigroup interface.
    """

    @overload
    def __call__(self, x: a, y: a, /, *args: a) -> a:
        ...

    @overload
    def __call__(self, x: Iterable[a], /) -> a:
        ...

    def __call__(self, *args):
        raise NotImplementedError


@runtime_checkable
class MonoidF(Protocol[a]):
    """
    A function/callable that implements the monoid interface.

    It differs from the semigroup interface in which it also accept empty iterators
    or empty arguments. It returns the neutral element in both situations.
    """

    @overload
    def __call__(self) -> a:
        ...

    @overload
    def __call__(self, x: a, y: a, /, *args: a) -> a:
        ...

    @overload
    def __call__(self, x: Iterable[a], /) -> a:
        ...

    def __call__(self, *args):
        raise NotImplementedError


@runtime_checkable
class Semigroup(Protocol):
    """
    Type with an explicit implementation of semigroups.

    Instances must implement the self.combine(other) method.
    """

    def __group_op__(self: a, other: a, /) -> a:
        """
        Associative operation that defines the (semi)group/monoid.
        """
        raise NotImplementedError


@runtime_checkable
class Monoid(Semigroup, Protocol):
    @classmethod
    def __group_neutral__(cls: Type[a]) -> a:
        """
        Neutral element of the group/monoid.
        """
        raise NotImplementedError


@runtime_checkable
class Group(Monoid, Protocol):
    def __group_inverse__(self: a) -> a:
        """
        Inverse operation of a group.
        """
        raise NotImplementedError
