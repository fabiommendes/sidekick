from collections.abc import MutableSequence
from contextlib import AbstractContextManager

from .union import Union
from .._utils import catches
from ..functions import fn, to_callable, error
from ..functions import lib_runtime
from ..typing import Iterator, Catchable


class Result(Union):
    """
    Represents a result with an Ok and an Err state.
    """

    is_success = is_failure = False

    #
    # Applicative functor
    #
    @staticmethod
    def __sk_apply_wrap__(x):
        if isinstance(x, Result):
            return x
        return Ok(x)

    @staticmethod
    def __sk_apply__(func, args):
        wrapped_args = []
        for arg in args:
            if isinstance(arg, Err):
                return arg
            elif not isinstance(arg, Ok):
                arg = arg.value
            wrapped_args.append(arg)
        try:
            out = func(*wrapped_args)
        except Exception as ex:
            return Err(ex)
        return to_result(out)

    def __sk_apply_instance__(self, func):
        return self.map(func)

    #
    # API methods
    #
    def map(self, func):
        """
        Apply function if object is in the Ok state and return another Result.

        If function raises an error, return Err(exception). If it returns a
        Result, map returns it.
        """
        if not self:
            return self
        try:
            out = func(self.value)
        except Exception as ex:
            return Err(ex)
        if isinstance(out, Result):
            return out
        return Ok(out)

    def map_error(self, func):
        """
        Like the .map(func) method, but modifies the error part of the result.

        If function return a result keep as is. (i.e., function may change Result
        from Err to Ok state).

        Differently from map, exceptions are not wrapped.
        """
        if self:
            return self
        out = func(self.error)
        if isinstance(out, Result):
            return out
        return Err(out)

    def map_exception(self, func):
        """
        Similar to map_error, but only apply func (which is usually an Exception
        subclass, if the error is not an Exception.

        This is useful, for instance, if error is a string and you want to
        convert it to an explicit ValueError(string) or any other exception.
        """
        if self:
            return self
        else:
            err = self.error
            if (
                isinstance(err, Exception)
                or isinstance(err, type)
                and issubclass(err, Exception)
            ):
                return self
            return self.Err(func(err))

    def flat(self):
        """
        Flatten one level of result nesting.
        """
        data = self.value if self else self.error
        if isinstance(data, Result):
            return data
        return self

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

    def catches(self, exc: Catchable) -> bool:
        """
        If in error state, verify if error is compatible with argument.

        Args:
            exc:
                An error type or a tuple of error types.
        """
        if self:
            return False

        err = self.error
        if isinstance(err, type):
            return issubclass(err, exc)
        if isinstance(err, Exception):
            return isinstance(err, exc)
        return isinstance(ValueError(), exc)

    def flip(self) -> "Result":
        """
        Convert Ok to Err and vice-versa.
        """
        return Err(self.value) if self else Ok(self.error)

    def method(self, method, *args, **kwargs) -> "Result":
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
            try:
                return to_result(method(*args, **kwargs))
            except Exception as e:
                return Err(e)
        else:
            return self

    def attr(self, attr) -> "Result":
        """
        Retrieve attribute of the Ok state, and propagate error.

        Examples:
            >>> Ok(1 + 2j).attr('real')
            Ok(1.0)
        """
        return self and to_result(getattr(self.value, attr))

    def iter(self):
        """
        Iterates over content.

        It returns an empty iterator in the Err case.
        """
        if self:
            it: Iterator = self.value
            yield from it

    def to_maybe(self) -> "Maybe":
        """
        Convert result object into a Maybe.
        """
        return Just(self.value) if self else Nothing

    def to_result(self) -> "Result":
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

    def __repr__(self):
        if isinstance(self.error, type):
            return f"Err({self.error.__name__})"
        return super().__repr__()


class Ok(Result):
    """
    A success state of a Result.
    """

    value: object
    error = None
    is_success = True
    __bool__ = lambda _: True


def to_result(obj):
    """
    Coerce argument to a result:

    Objects and exceptions:
        result(obj)        -> Ok(obj)
        result(result_obj) -> result_obj

    Examples:
        >>> to_result(Err("error"))
        Err('error')
        >>> to_result(42)
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
        (args,) = args
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

    try:
        return to_result(func(*arg_values, **kwargs))
    except Exception as e:
        return Err(e)


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
    return _rpipe(obj, map(to_callable, funcs))


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

    return to_result(obj)


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
    func, *funcs = map(to_callable, funcs)
    rpipe = _rpipe

    if not funcs:
        return fn(lambda *args, **kwargs: rapply(func, *args, **kwargs))
    return fn(lambda *args, **kwargs: rpipe(rapply(func, *args, **kwargs), funcs))


class results(MutableSequence, AbstractContextManager):
    """
    A context manager that silences all exceptions that occurs inside the
    block and stores them in the result variable.

    Examples:
        In the block of code bellow, the ``result`` thunk would be set to
        ``Ok(x / y)`` if everything runs smoothly and store the error
        otherwise.

        >>> x_data, y_data = '42', '3;14'
        >>> with results() as res:
        ...     x = int(x_data)
        ...     y = int(y_data)
        ...     res.append(x / y)

        The final result can be extracted by calling ptr

        >>> res.value
        Err(ValueError(...))
    """

    @property
    def has_errors(self):
        for x in self._data:
            if not x:
                return True
        return False

    @property
    def has_values(self):
        for x in self._data:
            if x:
                return True
        return False

    @property
    def value(self):
        try:
            return self._data[-1]
        except IndexError:
            return self._default_error()

    def __init__(self, catch: Catchable = Exception, data=()):
        self._data = [to_result(x) for x in data]
        self.catch = catch

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        return self._data[idx]

    def __iter__(self):
        return iter(self)

    def __enter__(self):
        return self

    def __delitem__(self, item):
        del self._data[item]

    def __setitem__(self, idx, value):
        if isinstance(idx, slice):
            self._data[idx] = map(to_result, value)
        else:
            self._data[idx] = to_result(value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if catches(exc_val, self.catch):
                self.push_error(exc_val)
                return True
            raise exc_val

    def _default_error(self):
        return Err(RuntimeError("List contains no value"))

    def insert(self, index: int, object) -> None:
        self._data.insert(index, to_result(object))

    def push(self, value):
        self.append(value)

    def push_error(self, err):
        self.append_error(err)

    def append_error(self, err):
        if isinstance(err, Err):
            err = err.error
        elif isinstance(err, Result):
            err = err.value
        self._data.append(Err(err))

    def pop(self, idx=-1):
        try:
            return self._data.pop(idx)
        except IndexError:
            return self._default_error()


#
# Patch modules
#
fn._to_result = staticmethod(to_result)
fn._ok = Ok
fn._err = Err

lib_runtime.Ok = Ok
lib_runtime.Err = Err
lib_runtime.Result = Result

from .maybe import Maybe, Just, Nothing  # noqa: E402
