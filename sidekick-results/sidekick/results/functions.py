from contextlib import AbstractContextManager
from functools import wraps
from typing import Any, Generic, Iterable, Iterator, Sequence, overload

from .maybe import Just, Maybe, Nothing
from .result import Err, Ok, Result
from .util import Fn, P, a, err, r


#
# Functions that work on Maybes and Results
#
@overload
def values(seq: Iterable[Maybe[a]]) -> Iterator[a]:
    ...


@overload
def values(seq: Iterable[Result[Any, a]]) -> Iterator[a]:
    ...


def values(seq):
    """
    Remove Nothing and Err elements of sequence and return an
    iterator over the wrapped values.

    Examples:
        >>> [*values([Ok(1), Err(0), Just(2), Ok(3)])]
        [1, 2, 3]
    """
    for x in seq:
        if x.is_success:
            yield x.value  # type: ignore


@overload
def args(seq: Sequence[Result[err, a]]) -> Result[err, tuple[a, ...]]:
    ...


@overload
def args(seq: Sequence[Maybe[a]]) -> Maybe[tuple[a, ...]]:
    ...


def args(args):
    """
    From a sequence of Maybes or Results, extract an wrapped tuple of all
    values or return the first failure state.

    Examples:
        >>> args([Ok(1), Ok(2), Ok(3)])
        Ok((1, 2, 3))
    """
    unwrapped = []
    for arg in args:
        if arg.is_success:
            unwrapped.append(arg.value)
        else:
            return arg

    if not unwrapped:
        return ()

    return args[0].replace(tuple(unwrapped))


@overload
def to_result(obj: Result[err, a]) -> Result[err, a]:
    ...


@overload
def to_result(obj: a) -> Result[err, a]:
    ...


def to_result(obj):
    """
    Coerce argument to a result:

    Objects and exceptions:
        to_result(obj)        -> Ok(obj)
        to_result(result_obj) -> result_obj

    Examples:
        # >>> to_result(42)
        # Ok(42)
        >>> to_result(Ok(42))
        Ok(42)
        >>> to_result(Err("error"))
        Err('error')
    """
    if isinstance(obj, (Ok, Err)):
        return obj
    return Ok(obj)


@overload
def to_maybe(obj: Maybe[a]) -> Maybe[a]:
    ...


@overload
def to_maybe(obj: None) -> Maybe[Any]:
    ...


@overload
def to_maybe(obj: a) -> Maybe[a]:
    ...


def to_maybe(obj):
    """
    Coerce argument to a Maybe:

        maybe(maybe_obj) -> maybe_obj
        maybe(None)      -> Nothing
        maybe(x)         -> Just(x)
    """
    if obj is None or obj is Nothing:
        return Nothing
    elif type(obj) is Just:
        return obj
    else:
        return Just(obj)


def safe(func: Fn[P, r]) -> Fn[P, Result[Exception, r]]:
    """
    Transform a regular function that may raise exception into a safe
    function that wraps the results or errors into a result.

    This function can also be used as a decorator.

    Examples:
        >>> safe(op.truediv)(1, 0)
        Err(ZeroDivisionError('division by zero'))
    """

    @wraps(func)
    def decorated(*args, **kwargs) -> Result[Exception, r]:
        try:
            return Ok(func(*args, **kwargs))
        except Exception as exc:
            return Err(exc)

    return decorated


class safe_block(AbstractContextManager, Generic[a]):
    """
    A context manager that silences all exceptions that occurs inside the
    block and stores them in a result variable.

    Examples:
        In the block of code bellow, the ``value`` thunk would be set to
        ``Ok(x / y)`` if everything runs smoothly or it would store the raised
        exception, otherwise.

        >>> with safe_block() as res:
        ...     x = int("42")
        ...     y = int("3.14")
        ...     res.save(x / y)

        The final result can be extracted by calling the context without
        arguments. The example above fails because the second string represents
        an invalid integer and triggers a ValueError before saving to y.

        >>> res()
        Err(ValueError(...))

        The context manager fails if the .save() method is never called and no
        exception is raised. This help us to ensure that the computed value is stored
        in all branches of computation inside the block. This behavior can be
        overridden by providing an default result to the block constructor.

        >>> with safe_block(Ok(None)) as res:
        ...     x / y
    """

    __slots__ = ("_data",)
    _data: Result[Exception, a] | None

    def __init__(self, default=None):
        self._data = default

    def __iter__(self):
        return iter(self())

    def __call__(self):
        if self._data is None:
            raise self._unused_error()
        return self._data

    def _unused_error(self) -> RuntimeError:
        return RuntimeError("no result was ever saved")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._data = Err(exc_val)
            return True
        elif self._data is None:
            raise RuntimeError(".save(value) was not called inside block")

    def save(self, value: a):
        """
        Save unwrapped value to context.
        """
        self._data = Ok(value)

    def get(self) -> a:
        """
        Return the wrapped value or raise exception.
        """
        return self().unwrap()

    def result(self) -> Result[Exception, a]:
        """
        Return the result

        This is an alias to self().
        """
        return self()


def nullable(func: Fn[P, r | None]) -> Fn[P, Maybe[r]]:
    """
    Transform a regular function that may return a nullable value into a function
    that return maybes.

    This function can also be used as a decorator.

    Examples:
        >>> func = nullable(dict.get)
        >>> func({"foo": "bar"}, "baz")
        Nothing
        >>> func({"foo": "bar"}, "foo")
        Just('bar')
    """

    @wraps(func)
    def decorated(*args, **kwargs) -> Maybe[r]:
        x = func(*args, **kwargs)
        if x is None:
            return Nothing
        return Just(x)

    return decorated


@overload
def pipeline(*funcs: Fn[[a], Maybe[a]]) -> Fn[[Maybe[a]], Maybe[a]]:
    ...


@overload
def pipeline(*funcs: Fn[[a], Result[err, a]]) -> Fn[[Result[err, a]], Result[err, a]]:
    ...


def pipeline(*funcs):
    """
    Compose functions that return Maybes or Results.

    The pipeline stops at the first failure state.

    Args:
        *funcs:
            List of functions in application order.

    Examples:
        >>> func = pipeline(safe(1 / X), safe(X + 1))
        >>> func(Ok(2))
        Ok(1.5)
        >>> func(Ok(0))
        Err(ZeroDivisionError(...))

    See also:
        Use :func:`safe` or :func:`nullable` to convert regular functions that
        transform the wrapped value into functions that return Results or Maybes.
    """
    return lambda x: x.pipe_safe(*funcs)


# FIXME: doctests fail because this module is imported as sidekick.results.functions and results.functions
if __name__ == "results.functions":
    to_result.__doc__ = None
