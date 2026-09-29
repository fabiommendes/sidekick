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
from . import functor_definition as functors


a = TypeVar("a")
b = TypeVar("b")
c = TypeVar("c")
F = TypeVar("F")
Ft = TypeVar("Ft", bound="ApplicativeT")
NOT_GIVEN: Any = object()


@runtime_checkable
class ApplicativeF(Protocol[F]):
    """
    A function/callable that implements the applicative interface.
    """

    def __call__(self, f: Fn[..., b], *args: F) -> F:
        raise NotImplementedError


class Applicative(ApplicativeF[F], functors.Functor):
    """
    Implements the applicative function extended interface.

    This adds some methods to the purely functional interface.
    """

    def __call__(self, f: Fn[..., b], *args) -> Bind[F, b]:
        return self.apply(f, *args)
    
    def apply(self, f: Fn[..., b], *args) -> Bind[F, b]:
        """
        Apply function of many arguments to elements of many 
        functors. 
        
        This generalizes map() for combining several arguments and, for applicatives,
        ``appl.apply(f, *args) = appl(f, *args)``
        
        Signature:
            apply(a -> b, F[a]) -> F[b]             # same as map()
            apply((a, b) -> c, F[a], F[b]) -> F[c]  # same as apply_pair()
            apply((a, b, c) -> d, F[a], F[b], F[c]) -> F[d]
            ...
        """
        raise NotImplementedError

    def apply_pair(
        self, func: Fn[[a, b], c], fa: Bind[F, a], fb: Bind[F, b]
    ) -> Bind[F, c]:
        """
        Specialized version of apply that works only for two
        arguments.

        Signature:
            apply_pair((a, b) -> c, F[a], F[b]) -> F[c]
        """
        return self(func, fa, fb)

    def lift(self, func: Fn, arity: int = NOT_GIVEN) -> Fn:
        """
        Lift a function of given arity that acts on elements and
        return a function that acts on functors of those elements.

        Args:
            func:
                The input function of given arity.
            arity (int):
                The number of arguments of the lifted the function.
                If not given, arity is introspected from func.
                Sometimes the arity cannot be correctly determined
                or the function may have multiple arities.

        Signature:
            lift(a -> b) -> (F[a] -> F[b])
            lift((a, b) -> c) -> ((F[a], F[b]) -> F[c])
            lift((a, b, c) -> d) -> ((F[a], F[b], F[c]) -> F[d])
            ...
        """
        if arity is NOT_GIVEN:
            return lambda *args: self(func, *args)
        elif arity == 0:
            return lambda: self.pure(func())
        elif arity == 1:
            return lambda fa: self.map(func, fa)
        elif arity == 2:
            return lambda fa, fb: self.apply_pair(func, fa, fb)
        elif arity < 0:
            raise ValueError(f"invalid arity: {arity}")
        else:
            return lambda *args: self(func, *args)

    def unit(self) -> Bind[F, ()]:
        """
        Return an applicative functor in its simplest form.

        Signature:
            unit() -> F[()]
        """
        return self.pure(())

    def pairwise(self, *args: F) -> Bind[F, tuple]:
        """
        Make a pairwise association of members of each argument.

        The resulting tuples are flattened.

        Signature:
            pairwise() -> F[()]
            pairwise(F[a]) -> F[a]
            pairwise(F[a], F[b]) -> F[(a, b)]
            pairwise(F[a], F[b], F[c]) -> F[(a, b, c)]
            ...
        """
        match args:
            case ():
                return self.unit()
            case (fa,):
                return fa
            case (fa, fb):
                return self._make_pairs(fa, fb)
            case _:
                return self(lambda *args_: args_, *args)
    
    def pure(self, x: a) -> Bind[F, a]:
        """
        Return an applicative functor in its simplest form.
        """
        return self._pure(x)

    def ap(self, ff: Bind[F, Fn[[a, b], a]], fa: Bind[F, a]) -> Bind[F, b]:
        """
        Apply function contained in a functor to argument.

        Signature:
            ap(F[a -> b], F[a]) -> F[b]
        """
        return self.apply_pair(lambda f, x: f(x), ff, fa)  # type: ignore

    def seq(self, *args: F) -> F:
        """
        Sequence of actions that keeps the values of the last argument.
        
        This function does not simply return the last functor. 
        It combines all the functors before selecting value of the last argument.
        
        Signature:
            seq(F[a]) -> F[a]
            seq(F[a], F[b]) -> F[b]
            seq(F[a], F[b], F[c]) -> F[c]
            ...
        
        See also:
            rseq
        """
        return self(lambda *args_: args_[-1], *args)

    def rseq(self, *args: F) -> F:
        """
        Sequence of actions that keeps the values of the first argument.
        
        This is simply the flipped version of seq().
        
        Signature:
            seq(F[a]) -> F[a]
            seq(F[a], F[b]) -> F[a]
            seq(F[a], F[b], F[c]) -> F[a]
            ...
            
        See also:
            seq
        """
        return self(lambda *args_: args_[0], *args)
    
    #
    # Alternative
    #
    def empty(self) -> F:
        """
        The empty container with no element, e.g., an empty list or set.
        
        This function is not defined for all functors, but is a relatively common
        occurrence.
        
        Signature:
            empty() -> F[a]
        """
        return self._empty()
    
    def some(self, fa: Bind[F, a]) -> Bind[F, list[a]]:
        """
        Collect one or more elements in the functor.

        Signature:
            some(F[a]) -> F[list[a]]
        """
        raise NotImplementedError
    
    def many(self, fa: Bind[F, a]) -> Bind[F, list[a]]:
        """
        Collect zero or more elements in the functor.

        Signature:
            many(F[a]) -> F[list[a]]
        """
        raise NotImplementedError
    
    # TODO: any, or all, or something else?
    def any(self, *args: Bind[F, a]) -> Bind[F, a]:
        """
        A monoidal association between functors.
        
        Signature:
            any() -> F[a]
            any(F[a]) -> F[a]
            any(F[a], F[a], ...) -> F[a]
        """
        if len(args) == 0:
            return self.empty()
        
        op = self._alternative_concat
        x = next(xs := iter(args))
        for x_ in xs:
            x = op(x, x_)
        return x
    
    def optional(self, fa: Bind[F, a]) -> Bind[F, a | None]:
        """
        An empty functor is mapped to pure(None).
        """
        return self._alternative_concat(fa, self.pure(None))
        
    def _alternative_concat(self, f1, f2):
        raise NotImplementedError

    def _make_pairs(self, fa, fb):
        """
        Private function used to generalize pairwise() to any number of
        arguments.
        """
        return self.apply_pair(lambda x, y: (x, y), fa, fb)


class ApplicativeT(Generic[a], abc.ABC):
    """
    Type with an explicit implementation of semigroups.

    Instances must implement the self.combine(other) method.
    """

    _applicative_instance: Applicative

    @classmethod
    def applicative_instance(cls: Type[Ft]) -> Applicative[Ft]:
        """
        Return a semigroup instance for the type.
        """
        if (instance := cls.__dict__.get("_applicative_instance")) is not None:
            return instance

        cls._applicative_instance = func = Applicative(lambda f, ft: ft.map(f))  # type: ignore
        try:
            func.__name__ = cls.__name__  # type: ignore
            func.__qualname__ = cls.__qualname__ + ".instance"  # type: ignore
        except AttributeError:
            pass
        return func
    
    @abc.abstractclassmethod
    def apply(self: Bind[F, a], func: Fn[[a], b]) -> Bind[F, b]:
        """
        Associative operation that defines the semigroup.
        """
        raise NotImplementedError


class _ApplicativeObject(Object[Applicative[Any]]):
    """
    Implements the sidekick.classes.applicative object.
    """

    @cached_property
    def instances(self):
        from . import applicative_instances

        return applicative_instances

    if TYPE_CHECKING:

        @overload  # type: ignore
        def __getitem__(self, key: Type[a]) -> Applicative[a]:
            ...

        @overload
        def __getitem__(self, key: str) -> Applicative[Any]:
            ...

        def __getitem__(self, key):
            return super().__getitem__(key)

    def _dispatch_implicit(self, typ) -> Applicative[a] | None:
        if issubclass(typ, ApplicativeT):
            return typ.applicative_instance()  # type: ignore

        return None

    #
    # Creating instances
    #
    def from_fmap(
        self, fmap: Fn[[Fn[[a], b], Bind[F, a]], Bind[F, b]]
    ) -> Applicative[a]:
        """
        Create applicative from variadic function that implements
        binary operation on all of its arguments.
        """
        return Applicative(fmap)  # type: ignore

    def from_iterable_and_wrap(self, wrapper: Fn[[Iterable[a]], F]) -> Applicative[F]:
        """
        Create applicative from iterable that is wrapped back
        as a container using the given wrapper.
        """

        def fmap(f, xs):
            return wrapper(f(x) for x in xs)

        return Applicative(fmap)


applicative = _ApplicativeObject()
