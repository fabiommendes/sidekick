import functools
from contextlib import AbstractContextManager
from typing import Iterator

from .union import Union
from ..core import extract_function, fn
from ..functools import error

__all__ = ['Result', 'Err', 'Ok', 'result', 'rapply', 'rcall', 'rpipe',
           'rpipeline', 'result_fn', 'catch_exceptions', 'first_error']


class Result(Union):
    """
    Represents a result with an Ok and an Err state.
    """

    is_success = is_failure = False

    #
    # API methods
    #
    def map(self, func):
        """
        Apply function if object is in the Ok state and return another Result.
        """
        return self and rcall(func, self.value)

    def map_error(self, func):
        """
        Like the .map(func) method, but modifies the error part of the result.
        """
        return self if self else self.Err(func(self.error))

    def map_exception(self, func):
        """
        Similar to map_error, but only apply func (which is usually an Exception
        subclass, if the error is not an Exception.
        """
        if self:
            return self
        else:
            err = self.error
            if isinstance(err, Exception) \
                    or isinstance(err, type) and issubclass(err, Exception):
                return self
            return self.Err(func(err))

    def get_value(self, default=None):
        """
        Extract value from the Ok state. If object is an error, return the
        supplied default or None.

        Examples:

        >>> Ok(42).get_value()
        42
        >>> Err("NaN").get_value("default")
        'default'
        """
        return self.value if self else default

    def check_error(self):
        """
        Raise any error, if in an Err state. Do nothing otherwise.

        Exception error values are raised as is and all other values are
        wrapped into a ValueError.
        """
        self or error(self.error)

    def flip(self):
        """
        Convert Ok to Err and vice-versa.
        """
        return Err(self.value) if self else Ok(self.error)

    def method(self, method, *args, **kwargs):
        """
        Call the given method of success value and promote result to Result.

        Exceptions are wrapped into an Err case. Raise AttributeError if method
        does not exist.

        Examples:
            >>> Ok('Hello {name}!').method('format', 'world')
            Err(KeyError(...))
        """
        if self:
            method = getattr(self.value, method)
            return rcall(method, *args, **kwargs)
        else:
            return self

    def attr(self, attr):
        """
        Retrieves attribute as a Maybe.

        Examples:
            >>> Just(1 + 2j).attr('real')
            Just(1.0)
        """
        return self and result(getattr(self.value, attr))

    def iter(self):
        """
        Iterates over content.

        It returns an empty iterator in the Nothing case.
        """
        if self:
            it: Iterator = self.value
            yield from it

    def to_maybe(self) -> "Maybe":
        """
        Convert result object into a Maybe.
        """
        return Just(self.value) if self else Nothing

    def to_result(self):
        """
        Return itself.

        This function exists so some algorithms can work with both Maybe's and
        Result's using the same interface.
        """
        return self


class Err(Result):
    """
    An error state of a Result.
    """
    error: object
    value = property(lambda self: self.check_error())
    is_failure = True
    __bool__ = lambda _: False

    def __eq__(self, other):
        if isinstance(other, type) and issubclass(other, Exception):
            e = self.error
            return (e == other
                    or isinstance(e, other)
                    or issubclass(e, type) and issubclass(e, other))
        return super().__eq__(other)

    def __repr__(self):
        if isinstance(self.error, type):
            return f'Err({self.error.__name__})'
        return super().__repr__()


class Ok(Result):
    """
    A success state of a Result.
    """
    value: object
    error = None
    is_success = True
    __bool__ = lambda _: True


# ------------------------------------------------------------------------------
# Public API Functions
# ------------------------------------------------------------------------------

def result(obj):
    """
    Coerce argument to a result:

    Objects and exceptions:
        result(obj)        -> Ok(obj)
        result(result_obj) -> result_obj

    Examples:
        >>> result(Err("error"))
        Err('error')
        >>> result(42)
        Ok(42)
    """
    if isinstance(obj, Result):
        return obj
    return Ok(obj)


def first_error(*args):
    """
    Return the first error in a sequence of Result values.

    If no value is an error, return None.

    >>> first_error(Ok(2), Ok(3), Err("not prime"), Ok(5))
    'not prime'
    """
    if len(args) == 1:
        args, = args
    cls = (Err, Exception)
    for x in args:
        if isinstance(x, cls):
            return x.error if x.__class__ is Err else x
        elif isinstance(x, type) and issubclass(x, Exception):
            return x
    return None


def rapply(func, *args, **kwargs):
    """
    Execute function with all given Ok values and return
    ``Ok(func(*values))``. If any argument is an Error return the first
    error.

    Examples:
        >>> rapply(max, Ok(1), Ok(2), Ok(3))
        Ok(3)
        >>> rapply(max, Ok(1), Ok(2), Ok(3), Err("NaN"))
        Err('NaN')
    """
    arg_values = []
    append = arg_values.append
    for arg in args:
        if isinstance(arg, Ok):
            append(arg.value)
        elif isinstance(arg, Err):
            return arg
        else:
            append(arg)
    return rcall(func, *arg_values, **kwargs)


def rcall(func, *args, **kwargs):
    """
    Call function with given arguments and wraps the result into a Result
    type.

    If the function terminates successfully, it wraps the result in an Ok
    case. If it raises any exception, the exception is wrapped into an Err
    case.

    Examples:
        >>> rcall(float, "3,14")
        Err(ValueError(...))
    """
    func = extract_function(func)
    return _rcall(func, *args, **kwargs)


def _rcall(func, *args, **kwargs):
    try:
        return result(func(*args, **kwargs))
    except Exception as ex:
        return Err(ex)


def rpipe(obj, *funcs):
    """
    Pass argument through all functions that return results. It stops function
    application after the first Err or exception is encountered.

    Args:
        obj:
            Initial argument passed to all functions.
        *funcs:
            List of functions in application order.

    Examples:
        >>> rpipe(Ok(20), (X + 1), (X * 2))
        Ok(42)
        >>> rpipe(2, (X - 2), (1 / X))
        Err(ZeroDivisionError(...))

    Returns:
        A Result value.
    """
    return _rpipe(obj, map(extract_function, funcs))


def _rpipe(obj, funcs):
    for func in funcs:
        if isinstance(obj, Err):
            return obj
        elif isinstance(obj, Ok):
            obj = obj.value

        try:
            obj = func(obj)
        except Exception as ex:
            return Err(ex)

    return result(obj)


def rpipeline(*funcs):
    """
    Compose functions that return Result values.

    If any function returns an Err or raises an Exception, the final result will
    be an Err.

    Args:
        *funcs:
            List of functions in application order.

    Returns:
        A function that return Results.

    Examples:
        >>> f = rpipeline((X + 1), (X * 2))
        >>> f(20)
        Ok(42)

    See Also:
        This is similar to :func:`rpipe`, except that it does not require the
        initial argument passed to the functions.
    """
    func, *funcs = map(extract_function, funcs)
    rpipe = _rpipe

    if not funcs:
        return fn(lambda *args, **kwargs: rapply(func, *args, **kwargs))
    return fn(lambda *args, **kwargs: rpipe(rapply(func, *args, **kwargs), funcs))


# noinspection PyPep8Naming
class catch_exceptions(AbstractContextManager):
    """
    A context manager that silences all exceptions that occurs inside the
    block and stores them in the result variable.

    Examples:
        In the block of code bellow, the ``result`` thunk would be set to
        ``Ok(x / y)`` if everything runs smoothly and store the error
        otherwise.

        >>> x_data, y_data = '42', '3;14'
        >>> with catch_exceptions() as err:
        ...     x = int(x_data)
        ...     y = int(y_data)
        ...     err.put(x / y)

        The final result can be extracted by calling ptr

        >>> err.get()
        Err(ValueError(...))
    """

    def __init__(self, *args, value=None):
        self._value = value
        self._result = Ok(None)
        self._catch = args
        self._has_error = False

    def __bool__(self):
        return self._has_error

    def __enter__(self):
        self._result = Ok(self._value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._has_error = True
            self._result = Err(exc_val)
            if not self._catch or isinstance(exc_val, self._catch):
                return True
            raise exc_val

    def put(self, value):
        self._result = result(value)

    def get(self):
        return self._result


def result_fn(func):
    """
    Return a exception-free version of the input function. It wraps the
    result in a Ok state and any exception is converted to an Err state.

    Args:
        func (callable):
            The wrapped function.

    Examples:
        >>> parse_float = result_fn(float)
        >>> parse_float("3.14")
        Ok(3.14)
    """
    return fn(functools.partial(rcall, func))


fn._ok = staticmethod(result)
fn._err = Err

from .maybe import Maybe, Just, Nothing  # noqa: E402
