from __future__ import annotations

import operator
from dataclasses import dataclass
from functools import partial, total_ordering
from typing import (TYPE_CHECKING, Any, Container, Generic, Iterator, Type,
                    final)

from .util import (NOT_GIVEN, Fn, a, assert_never, b, err, err_, r,
                   result_operator, to_raisable)

if TYPE_CHECKING:
    from .maybe import Just, Maybe, Nothing


@total_ordering
class Result(Generic[err, a]):
    """
    Represents a result with an Ok and an Err state.
    """

    is_success = is_failure = is_ok = is_err = False
    Ok: Type[Ok]
    Err: Type[Err]

    #
    # Constructors
    #
    @staticmethod
    def from_call(func: Fn[..., r], /, *args, **kwargs) -> Result[Exception, r]:
        """
        Call some python function with the given arguments and wrap result
        in an Ok(x) value or an Err(exception) if some exception is raised.

        Examples:
            >>> Result.from_call(op.floordiv, 1, 0)
            Err(ZeroDivisionError('integer division or modulo by zero'))
        """
        try:
            return Ok(func(*args, **kwargs))
        except Exception as exc:
            return Err(exc)

    @classmethod
    def from_value(cls, value: a, /) -> Result[err, a]:
        """
        Create a Ok(value) result from argument.
        """
        return Ok(value)

    @classmethod
    def from_error(cls, error: err, /) -> Result[err, a]:
        """
        Create a Err(error) result from argument.
        """
        return Err(error)

    @classmethod
    def apply(cls, func, /, *args, **kwargs):
        """
        Execute function with all given Ok values and return
        ``Ok(func(*values))``. If any argument is an Error return the first
        error.

        Examples:
            >>> Result.apply(max, Ok(1), Ok(2), Ok(3))
            Ok(3)
            >>> Result.apply(max, Ok(1), Ok(2), Ok(3), Err("NaN"))
            Err('NaN')
        """
        try:
            return cls.__functor_apply__(partial(func, **kwargs), args)
        except Exception as exc:
            return Err(exc)

    def __new__(cls, value):
        return Ok(value)

    #
    # API methods
    #
    def map(self, func: Fn[[a], b]) -> Result[err | Exception, b]:
        """
        Apply function if object is in the Ok state and return another Result.

        If function raises an error, return Err(exception).
        """
        match self:
            case Ok(x):
                try:
                    return Ok(func(x))
                except Exception as ex:
                    return Err(ex)
            case _:
                return self  # type: ignore

    def map_error(self, func: Fn[[err], b]) -> Result[b, a]:
        """
        Like the .map(func) method, but modifies the error part of the result.

        If function return a result keep as is. (i.e., function may change Result
        from Err to Ok state).

        Differently from map, exceptions are not wrapped.
        """
        match self:
            case Err(err):
                return Err(func(err))
            case _:
                return self  # type: ignore

    def pipe(self, *funcs: Fn[[Any], Any]) -> Result[err, Any]:
        """
        Map all functions passed as arguments.

        It stops after the first exception, which is wrapped in an Err state, or when the computation completes.

        Examples:
            >>> incr = lambda x: x + 1
            >>> double = lambda x: x + x
            >>> Ok(20).pipe(incr, double)
            Ok(42)
        """
        obj = self
        for func in funcs:
            if obj.is_failure:
                return obj
            obj = obj.map(func)  # type: ignore
        return obj

    def pipe_safe(self, *funcs: Fn[[Any], Result[err, Any]]) -> Result[err, Any]:
        """
        Map all functions passed as arguments.

        Similar to pipe(), but functions must return results and never raise exceptions.

        Examples:
            >>> incr = lambda x: Ok(x + 1)
            >>> double = lambda x: x + x
            >>> Ok(20).pipe_safe(incr, safe(double))
            Ok(42)
        """
        obj = self
        for func in funcs:
            if obj.is_failure:
                return obj
            obj = obj.flatmap(func)  # type: ignore
        return obj

    def replace(self, value: b) -> Result[err, b]:
        """
        Replace the wrapped value of a success state by the given value.

        This is equivalent to self.map(lambda _: value).

        Examples:
            >>> Ok(40).replace(42)
            Ok(42)
            >>> Err(0).replace(42)
            Err(0)
        """
        match self:
            case Ok(_):
                return Ok(value)
            case _:
                return self  # type: ignore

    def replace_error(self, err: err_) -> Result[err_, a]:
        """
        Replace the wrapped error by the given value.

        This is equivalent to self.map_error(lambda _: value).

        Examples:
            >>> Ok(40).replace_error(42)
            Ok(40)
            >>> Err(0).replace_error(42)
            Err(42)
        """
        match self:
            case Err(_):
                return Err(err)
            case _:
                return self  # type: ignore

    def make_exception(
        self, func: Fn[[err], b | Exception] = ValueError
    ) -> Result[b | Exception, a]:
        """
        Similar to map_error, but only apply func (which is usually an Exception
        subclass, if the error is not an Exception.

        This is useful, for instance, if error is a string and you want to
        convert it to an explicit ValueError(string) or any other exception.
        """
        match self:
            case Err(err):
                if (
                    isinstance(err, Exception)
                    or isinstance(err, type)
                    and issubclass(err, Exception)
                ):
                    return self
                return Err(func(err))  # type: ignore
            case _:
                return self  # type: ignore

    def flatmap(self, func: Fn[[a], Result[err, b]]) -> Result[err | Exception, b]:
        """
        Apply function if object is in the Ok state and return another Result.

        If function raises an error, return Err(exception).
        """
        match self:
            case Ok(x):
                try:
                    return func(x)  # type: ignore
                except Exception as ex:
                    return Err(ex)
            case _:
                return self  # type: ignore

    def flatmap_error(
        self, func: Fn[[err], Result[err_, a]]
    ) -> Result[err_ | Exception, a]:
        """
        Apply function if object is in the Err state and return another Result.

        If function raises an error, return Err(exception).
        """
        match self:
            case Err(x):
                try:
                    return func(x)  # type: ignore
                except Exception as ex:
                    return Err(ex)
            case _:
                return self  # type: ignore

    def flatten(self: Result[err, Result[err, a]]) -> Result[err, a]:
        """
        Flatten one level of result nesting in the Ok state.
        """
        match self:
            case Ok(x):
                return x  # type: ignore
            case _:
                return self  # type: ignore

    def flatten_error(self: Result[Result[err, a], a]) -> Result[err, a]:
        """
        Flatten one level of result nesting in the Err state.
        """
        match self:
            case Err(x):
                return x  # type: ignore
            case _:
                return self  # type: ignore

    def ap(self, func: Result[err, Fn[[a], b]]) -> Result[Exception | err, b]:
        """
        Execute function inside a Result container.

        Examples:
            >>> Ok(1).ap(Ok(X + 1))
            Ok(2)

        It will return Err if either the function or the argument
        is in a failure state.
        """
        match self:
            case Ok(x):
                return func.map(lambda f: f(x))
            case _:
                return self  # type: ignore

    def value_or(self, default: a) -> a:
        """
        Extract value from the Ok state. If object is an error, return the
        supplied default.

        Examples:
            >>> Ok(10).value_or(42)
            10
            >>> Err("NaN").value_or(42)
            42
        """
        match self:
            case Ok(x):
                return x  # type: ignore
            case _:
                return default

    def error_or(self, default: err) -> err:
        """
        Like .value_or() for error states.

        Examples:
            >>> Ok(10).error_or(42)
            42
            >>> Err("NaN").error_or(42)
            'NaN'
        """
        match self:
            case Err(x):
                return x  # type: ignore
            case _:
                return default

    def value_or_call(self, func: Fn[[], a]) -> a:
        """
        Like value_or, but calls a function to compute the default value.

        This function exists for the cases in which the default value is
        expensive to compute.

        Examples:
            >>> Err("...").value_or_call(lambda: 42)
            42
        """
        match self:
            case Ok(x):
                return x
            case _:
                return func()

    def error_or_call(self, func: Fn[[], err]) -> err:
        """
        Like value_or_call, for error states.

        Examples:
            >>> Ok("...").error_or_call(lambda: 42)
            42
        """
        match self:
            case Err(x):
                return x
            case _:
                return func()

    def unwrap(self) -> a:
        """
        Return value or raise a ValueError exception.

        Differently from the `.value` attribute, the exception is not
        constructed from the error state.

        Examples:
            >>> Ok(42).unwrap()
            42
            >>> Err(RuntimeError).unwrap()
            Traceback (most recent call last):
            ...
            ValueError: Result is in an error state.
        """
        match self:
            case Ok(x):
                return x
            case _:
                raise ValueError("Result is in an error state.")

    def unwrap_error(self) -> err:
        """
        Return value from error state or raise a ValueError exception.

        Examples:
            >>> Err("error").unwrap_error()
            'error'
            >>> Ok(42).unwrap_error()
            Traceback (most recent call last):
            ...
            ValueError: Result is in an success state.
        """
        match self:
            case Err(x):
                return x
            case _:
                raise ValueError("Result is in an success state.")

    def check_error(self) -> None:
        """
        Raise any error, if in an Err state. Do nothing otherwise.

        Exception error values are raised as is and all other values are
        wrapped into a ValueError.

        Examples:
            >>> Ok(42).check_error()
            >>> Err("too bad").check_error()
            Traceback (most recent call last):
            ...
            ValueError: too bad
        """
        match self:
            case Err(err):
                raise to_raisable(err)
            case _:
                ...

    def catches(self, exc: Type[Exception]) -> bool:
        """
        If in error state, verify if error is compatible with argument.

        Always return True for Ok() values.

        Args:
            exc:
                An error type or a tuple of error types.

        Examples:
            >>> Err(KeyError("foo")).catches(ValueError)
            False
            >>> Err(KeyError("foo")).catches(Exception)
            True

            Non-exception errors are coerced to ValueError.

            >>> Err("bad").catches(ValueError)
            True
        """
        match self:
            case Err(err):
                if isinstance(err, type):
                    return issubclass(err, exc)
                if isinstance(err, Exception):
                    return isinstance(err, exc)
                return isinstance(ValueError(), exc)
            case _:
                return True

    def flip(self) -> Result[a, err]:
        """
        Convert Ok to Err and vice-versa.
        """
        match self:
            case Ok(x):
                return Err(x)
            case Err(err):
                return Ok(err)
            case _:
                assert_never(self)  # type: ignore

    def method(self, method: str, *args, **kwargs) -> Result[err | Exception, Any]:
        """
        Call the given method of success value and promote result to Result.

        Exceptions are wrapped into an Err case. Raise AttributeError if method
        does not exist.

        Examples:
            >>> Ok('Hello {name}!').method('format', name='world')
            Ok('Hello world!')
            >>> Ok('Hello {name}!').method('format', wrong='world')
            Err(KeyError(...))
        """
        match self:
            case Ok(x):
                impl = getattr(x, method)
                try:
                    return Ok(impl(*args, **kwargs))
                except Exception as ex:
                    return Err(ex)
            case _:
                return self  # type: ignore

    def method_error(
        self, method: str, *args, **kwargs
    ) -> Result[err | Exception, Any]:
        """
        Like ``.method``, but for the error state.
        """
        match self:
            case Err(x):
                impl = getattr(x, method)
                try:
                    return Err(impl(*args, **kwargs))
                except Exception as ex:
                    return Err(ex)
            case _:
                return self  # type: ignore

    def attr(self, attr: str) -> Result[err, Any]:
        """
        Retrieve attribute of the Ok state, and propagate error.

        Examples:
            >>> Ok(1 + 2j).attr('real')
            Ok(1.0)
        """
        match self:
            case Ok(x):
                return Ok(getattr(x, attr))
            case _:
                return self

    def attr_error(self, attr: str) -> Result[err, Any]:
        """
        Like .attr, but for the error state.

        Examples:
            >>> Err(1 + 2j).attr_error('real')
            Err(1.0)
        """
        match self:
            case Err(x):
                return Err(getattr(x, attr))
            case _:
                return self

    def iter(self) -> Iterator[a]:
        """
        Iterates over content.

        It returns an empty iterator in the Err case.
        """
        match self:
            case Ok(seq):
                yield from seq
            case _:
                yield from ()

    def iter_error(self) -> Iterator[a]:
        """
        Iterates over content.

        It returns an empty iterator in the Ok case.
        """
        match self:
            case Err(seq):
                yield from seq
            case _:
                yield from ()

    def to_maybe(self) -> Maybe[a]:
        """
        Convert result object into a Maybe.
        """
        match self:
            case Ok(x):
                return Just(x)
            case _:
                return Nothing  # type: ignore

    def to_result(self, error: Any = NOT_GIVEN) -> Result[err, a]:
        """
        Return itself.

        This function exists so some algorithms can work with both Maybe's and
        Result's using the same interface.
        """
        if error is NOT_GIVEN:
            return self
        return self.replace_error(error)

    # Sidekick functional interfaces
    __functor_map__ = map
    __functor_flatmap__ = flatmap

    @staticmethod
    def __functor_wrap__(x):
        if isinstance(x, Result):
            return x
        return Ok(x)

    @staticmethod
    def __functor_apply__(func, args):
        wrapped_args = []
        for arg in args:
            match arg:
                case Err(_):
                    return arg
                case Ok(x) | x:
                    wrapped_args.append(x)
        try:
            out = func(*wrapped_args)
        except Exception as ex:
            return Err(ex)

        return out if isinstance(out, Result) else Ok(out)

    # Operators
    __add__ = result_operator(operator.add)
    __floordiv__ = result_operator(operator.floordiv)
    __mod__ = result_operator(operator.mod)
    __mul__ = result_operator(operator.mul)
    __pow__ = result_operator(operator.pow)
    __sub__ = result_operator(operator.sub)
    __truediv__ = result_operator(operator.truediv)

    __and__ = result_operator(operator.and_)
    __lshift__ = result_operator(operator.lshift)
    __rshift__ = result_operator(operator.rshift)
    __or__ = result_operator(operator.or_)
    __xor__ = result_operator(operator.xor)

    def __lt__(self, other: Result[err, a]) -> bool:
        match self:
            case Ok(x):
                match other:
                    case Ok(y):
                        return x < y
                    case Err(_):
                        return False
            case Err(x):
                match other:
                    case Err(y):
                        return x < y
                    case Ok(_):
                        return True
        return NotImplemented

    def __eq__(self, other) -> bool:
        match self:
            case Ok(x) if type(other) is Ok:
                return x == other.value
            case Err(err) if type(other) is Err:
                return err == other.error
            case _ if isinstance(other, Result):
                return False
        return NotImplemented

    def __contains__(self, other) -> bool:
        match self:
            case Ok(x):
                return other in x
            case _:
                return False

    def __getitem__(self: Result[err, Container[a]], item) -> Result[err, a]:
        match self:
            case Ok(value):
                return Ok(value[item])
            case _:
                return self  # type: ignore

    def __neg__(self) -> Result[err, a]:
        match self:
            case Ok(x):
                return Ok(-x)
            case _:
                return self  # type: ignore

    def __pos__(self) -> Result[err, a]:
        match self:
            case Ok(x):
                return Ok(+x)
            case _:
                return self  # type: ignore

    def __invert__(self) -> Result[err, a]:
        match self:
            case Ok(x):
                return Ok(~x)
            case _:
                return self  # type: ignore

    def __iter__(self):
        match self:
            case Ok(x):
                yield x
            case _:
                yield from ()


@final
@dataclass(frozen=True)
class Err(Result[err, a]):
    """
    An error state of a Result.
    """

    error: err
    is_failure = True
    is_err = True

    @property
    def value(self):
        raise to_raisable(self.error)

    def __new__(cls, error):
        new = object.__new__(cls)
        object.__setattr__(new, "error", error)
        return new

    def __repr__(self):
        if isinstance(self.error, type):
            return f"Err({self.error.__name__})"
        return f"Err({self.error!r})"


@final
@dataclass(frozen=True)
class Ok(Result[err, a]):
    """
    A success state of a Result.
    """

    value: a
    error = None
    is_success = True
    is_ok = True

    def __new__(cls, value):
        new = object.__new__(cls)
        object.__setattr__(new, "value", value)
        return new

    def __repr__(self):
        return f"Ok({self.value!r})"


Result.Ok = Ok
Result.Err = Err
