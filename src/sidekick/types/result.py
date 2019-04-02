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
    def map(self, func, *funcs):
        """
        Apply function if object is in the Ok state and return another Result.
        """
        if self:
            if funcs:
                return rpipe(self.value, func, *funcs)
            else:
                return rcall(func, self.value)
        else:
            return self

    def map_error(self, func):
        """
        Like the .map(func) method, but modifies the error part of the result.
        """
        return self if self else self.Err(func(self.error))

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
            Err(KeyError('name'))
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
        return self and maybe(getattr(self.value, attr))

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
    cls = Result
    for x in args:
        if isinstance(x, cls) and x.is_err:
            return x.error
        elif isinstance(x, Exception):
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
        Err(ValueError("could not convert string to float: '3,14'"))
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

    See Also:
        This is similar to :func:`rpipe`, except that it does not require the
        initial argument passed to the functions.
    """
    funcs = tuple(map(extract_function, funcs))
    return lambda x: _rpipe(x, *funcs)


# noinspection PyPep8Naming
class catch_exceptions(AbstractContextManager):
    """
    A context manager that silences all exceptions that occurs inside the
    block and stores them in the result variable.

    Examples:

        In the block of code bellow, the ``result`` thunk would be set to
        ``Ok(x / y)`` if everything runs smoothly and store the error
        otherwise.

        >>> x_data, y_data = '42', '3,14'
        >>> with catch_exceptions() as ptr:
        ...     x = int(x_data)
        ...     y = int(y_data)
        ...     ptr(Ok(x / y))

        The final result can be extracted by calling ptr

        >>> ptr()
        Err(ValueError(...))
    """

    def __init__(self, value=None):
        self.value = value
        self.result = None

    def __enter__(self):
        self.result = Ok(self.value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.result = Err(exc_val)
            return True

    def __call__(self, *args):
        if args:
            self.result, = args
        return self.result


def result_fn(func):
    """
    Return a exception-free version of the input function. It wraps the
    result in a Ok state and any exception is converted to an Err state.

    Args:
        func (callable):
            The wrapped function.

    Examples:
        >>> safe_float = result_fn(float)
        >>> safe_float("3.14")
        Ok(3.14)
    """
    return fn(functools.partial(rcall, func))


fn._ok = staticmethod(result)
fn._err = Err

from .maybe import Maybe, Just, Nothing, maybe  # noqa: E402
