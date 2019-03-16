import functools
import importlib
import operator as op
import types
import warnings
from contextlib import AbstractContextManager
from functools import wraps

from .union import Union, opt
from .utils import result_bin_op

flip = lambda f: lambda x, y: f(y, x)
this = None


class Result(Union):
    """
    Represents a result with an Ok and an Err state.
    """

    is_err = is_ok = False
    value: None
    error: None

    class Err(this, args=opt("error")):
        """
        Represents an error state.
        """

        @property
        def value(self):
            raise AttributeError("value")

    class Ok(this, args=opt("value")):
        """
        Represents a success state of a computation.
        """

        error = None

    #
    # API methods
    #
    def map(self, func):
        """
        Apply function if object is in the Ok state and return another Result.
        """
        if self.is_ok:
            return safe_call(func, self.value)
        else:
            return self

    def map_error(self, func):
        """
        Like the .map(func) method, but modifies the error part of the result.
        """

        if self.is_err:
            return self.Err(func(self.error))
        else:
            return self

    def chain(self, *funcs):
        """
        Chain several computations that expect regular types.

        Args:
            *funcs:
                Any number of functions that expect regular types.
        """

        x = self
        for func in funcs:
            if x.is_err:
                return x
            x = x.map(func)
        return x

    def get_value(self, default=None):
        """
        Extract value from the Ok state. If object is an error, return the
        supplied default or None.

        Examples:

        >>> Ok(42).get_value()
        42
        >>> Err("NaN").get_value()
        None
        """

        if self.is_ok:
            return self.value
        else:
            return default

    def check_error(self):
        """
        Raise any error, if in an Err state. Do nothing otherwise.

        Exception error values are raised as is and all other values are
        wrapped into a ValueError.
        """
        if self.is_ok:
            return
        error = self.error
        if (
            isinstance(error, Exception)
            or isinstance(error, type)
            and issubclass(error, Exception)
        ):
            raise error
        else:
            raise ValueError(error)

    def to_maybe(self) -> "Maybe":
        """
        Convert result object into a Maybe.
        """
        if self.is_ok:
            return Just(self.value)
        else:
            return Nothing

    def to_result(self):
        """
        Return itself.

        This function exists so some algorithms can work with both Maybe's and
        Result's using the same interface.
        """
        return self

    # Operators
    __add__ = result_bin_op(op.add)
    __radd__ = result_bin_op(flip(op.add))
    __sub__ = result_bin_op(op.sub)
    __rsub__ = result_bin_op(flip(op.sub))
    __mul__ = result_bin_op(op.mul)
    __rmul__ = result_bin_op(flip(op.mul))
    __truediv__ = result_bin_op(op.truediv)
    __rtruediv__ = result_bin_op(flip(op.truediv))
    __bool__ = lambda x: x.is_ok

    def __or__(self, other):
        if isinstance(other, Result):
            return self if self.is_ok else other
        elif isinstance(other, Maybe):
            return self if self.is_ok else other.to_result()
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, Maybe):
            return other.to_result() if other.just else self
        else:
            return NotImplemented

    def __and__(self, other):
        if isinstance(other, Result):
            return self if self.is_err else other
        elif isinstance(other, Maybe):
            return self if self.is_err else other.to_result()

    def __rand__(self, other):
        if isinstance(other, Maybe):
            return other.to_result() if other.nothing else self
        else:
            return NotImplemented

    def __negate__(self, other):
        return Err(self.value) if self.is_ok else Ok(self.error)


Ok = Result.Ok
Err = Result.Err


#
# Functions
#
def first_error(*args):
    """
    Return the first error in a sequence of Result values.

    If no value is an error, return None.
    """
    cls = Result
    for x in args:
        if isinstance(x, cls) and x.is_err:
            return x.error
        elif isinstance(x, Exception):
            return x
    return None


def rcall(func, *args, **kwargs):
    """
    Execute function with all given Ok values and return
    ``Ok(func(*values))``. If any argument is an Error return the first
    error.

    Examples:
        >>> rcall(max, Ok(1), Ok(2), Ok(3))
        Ok(3)
        >>> rcall(max, Ok(1), Ok(2), Ok(3), Err("NaN"))
        Err("NaN")
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
    return safe_call(func, *arg_values, **kwargs)


def safe_call(func, *args, **kwargs):
    """
    Call function with given arguments and wraps the result into a Result
    type.

    If the function terminates successfully, it wraps the result in an Ok
    case. If it raises any exception, the exception is wrapped into an Err
    case.
    """
    try:
        return result(func(*args, **kwargs))
    except Exception as ex:
        return Err(ex)


def safe(func, is_bound=False):
    """
    Return a exception-free version of the input function. It wraps the
    result in a Ok state and any exception is converted to an Err state.

    Args:
        func (callable):
            The wrapped function.
    """
    return wraps(func)(functools.partial(safe_call, func))


def with_safe(func):
    """
    Decorator that creates a except-safe version of func and saves it into the
    function's "safe" attribute.

    This implements the following interface:

    >>> @with_safe
    ... def div(x, y):
    ...     return x / y
    >>> div(1, 2)
    0.5
    >>> div.safe(1, 2)
    Ok(0.5)
    """
    func.safe = safe(func)
    return func


#
# Save methods in class
#
Result.first_error = staticmethod(first_error)
Result.apply = staticmethod(rcall)
Result.safe = staticmethod(safe)
Result.with_safe = staticmethod(with_safe)
Result.call = staticmethod(safe_call)


#
# Standalone functions
#
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


def safe_module(mod, private=False):
    """
    Apply Result.with_safe() decorator to all functions in a module.

    Args:
        mod:
            A python module or a python module path.

    Usage:
        If you want to convert all functions of the current module, type this
        at the end of the module:

        >>> safe_module(__name__)
    """
    if isinstance(mod, str):
        mod = importlib.import_module(mod)
    for name, value in vars(mod).items():
        if name.startswith("_") and not private:
            continue
        if isinstance(value, types.FunctionType):
            try:
                with_safe(value)
            except Exception:
                func_name = "%s.%s" % (mod.__name__, name)
                warnings.warn("could not create safe version of %s" % func_name)


def rcompose(*funcs):
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
    return lambda x: rpipe(x, *funcs)


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
    for func in funcs:
        if isinstance(obj, Err):
            return obj
        elif isinstance(obj, Ok):
            obj = obj.value

        try:
            obj = func(obj)
        except Exception as ex:
            return Result(ex)

    return result(obj)


# noinspection PyPep8Naming
class safe_block(AbstractContextManager):
    """
    A context manager that silences all exceptions that occurs inside the with
    block and stores them in the result variable.

    Examples:

        In the block of code bellow, the ``result`` variable will be set to
        ``Ok(x / y)`` if everything runs smoothly, but it will replace the
        content of result by an ``Err(exc)`` if an exception is raised inside
        the with block.

        Be careful to only assign to the result variable in the end of the
        block since it would not be able to track exceptions after the
        assignment.

        >>> with safe_block() as result:
        ...     x = int(input('x: '))
        ...     y = int(input('y: '))
        ...     result = Ok(x / y)

        Result will be ``Err(ValueError(...))`` if the user inputs invalid
        numbers or ``Err(ZeroDivisionError(...))`` if a numeric error occurs.
        In case of success, it will be able to execute the last line to bind
        ``result`` to ``Ok(x / y)``.
    """

    def __init__(self, value=None):
        self.value = value
        self.result = None

    def __enter__(self):
        self.result = result = Ok(self.value)
        return result

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            result = self.result
            result.__class__ = Err
            result.args = (exc_val,)
            return True


from .maybe import Maybe, Just, Nothing  # noqa: E402
