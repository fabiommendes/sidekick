import functools
import importlib
import operator as op
import types
import warnings
from functools import wraps

from .maybe import Maybe, Just, Nothing
from .union import Union, opt
from .utils import result_bin_op

flip = lambda f: lambda x, y: f(y, x)


class AttrGetter:
    __slots__ = '_object'

    def __init__(self, obj):
        AttrGetter._object.__set__(self, obj)

    def __getattr__(self, attr):
        obj = self._object
        if obj.is_err:
            return obj
        return Ok(getattr(self._object, attr))

    def __setattr__(self, attr, value):
        setattr(self._object, attr, value)


class MethodGetter:
    __slots__ = '_object'

    def __init__(self, obj):
        MethodGetter._object.__set__(self, obj)

    def __getattr__(self, attr):
        obj = self._object
        if obj.is_err:
            return lambda *args, **kwargs: obj

        func = obj.call(op.attrgetter, attr)
        return lambda *args, **kwargs: Ok()

    def __setattr__(self, attr, value):
        setattr(self._object, attr, value)


class Result(Union):
    """
    Represents a result with an Ok and an Err state.
    """

    Err = opt('error')
    Ok = opt('value')

    @classmethod
    def apply(cls, func, *args):
        """
        Execute function with all given Ok values and return
        ``Ok(func(*values))``. If any argument is an Error return the first
        error.

        Examples:

        >>> Result.apply(max, Ok(1), Ok(2), Ok(3))
        Ok(3)

        >>> Result.apply(max, Ok(1), Ok(2), Ok(3), Err("NaN"))
        Err("NaN")
        """

        arg_values = []
        for arg in args:
            if isinstance(arg, Ok):
                arg_values.append(arg.value)
            elif isinstance(arg, Err):
                return arg
            else:
                arg_values.append(arg)
        return cls.call(func, *arg_values)

    @classmethod
    def safe(cls, func, is_bound=False):
        """
        Return a exception-safe version of the input function. It wraps the
        result in a Ok state and any exception is converted to an Err state.

        Args:
            func (callable):
                The wrapped function.
            is_bound (bool):
                Set to True if the function is bound (i.e., it return Result
                values).
        """
        caller = cls.call_bound if is_bound else cls.call
        return wraps(func)(functools.partial(caller, func))

    @classmethod
    def with_safe(cls, func, is_bound=False):
        """
        Creates a except-safe version of func and saves it into the function's
        safe attribute.
        """
        func.safe = cls.safe(func, is_bound)
        return func

    @classmethod
    def call(cls, func, *args, **kwargs):
        """
        Call function with given arguments and wraps the result into a Result
        type.

        If the function terminates sucessfully, it wraps the result in an Ok
        case. If it raises any exception, the exception is wrapped into an Err
        case.
        """

        try:
            return Ok(func(*args, **kwargs))
        except Exception as ex:
            return Err(ex)

    @classmethod
    def call_bound(cls, func, *args, **kwargs):
        """
        Similar to call, but expects a function that return a Result value.
        """
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            return Err(ex)

    is_err = is_ok = False
    error = property(lambda self: None)
    attr = property(lambda x: AttrGetter(x))
    method = property(lambda x: MethodGetter(x))

    def map(self, func):
        """
        Apply function if object is in the Ok state and return another Result.
        """
        if self.is_ok:
            return self.call(func, self.value)
        else:
            return self

    def map_bound(self, func):
        """
        Calls the a function that receives regular values and returns a Result.
        The result is always a result value.

        Args:
            func (callable):
                A function from A -> Result[B]
        """
        if self.is_ok:
            try:
                return func(self.value)
            except Exception as ex:
                return Err(ex)
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

    def get(self, default=None):
        """
        Extract value from the Ok state. If object is an error, return the
        supplied default or None.

        Examples:

        >>> x = Result.Ok(42)
        >>> x.get()
        42
        >>> x = Result.Err("NaN")
        >>> x.get()
        None
        """

        if self.is_ok:
            return self.value
        else:
            return default

    def raise_error(self):
        """
        Raise any error, if in an Err state. Do nothing otherwise.

        Exception error values are raised as is and all other values are
        wrapped into a ValueError.
        """
        if self.is_ok:
            return
        else:
            error = self.error
            if (isinstance(error, Exception) or
                    isinstance(error, type) and
                    issubclass(error, Exception)):
                raise error
            else:
                raise ValueError(error)

    def to_maybe(self) -> Maybe:
        """
        Convert result object into a Maybe.
        """
        if self.is_ok:
            return Just(self.value)
        else:
            return Nothing

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


def result(obj):
    """
    Coerce argument to a result:

    Objects and exceptions:
        result(obj)   -> Ok(obj)
        result(ex)    -> Err(ex)

    Result instances:
        result(is_ok) -> is_ok
        result(err)   -> err

    Maybe instances:
        result(Just(x)) -> Ok(x)
        result(Nothing) -> Err(None)
    """

    if isinstance(obj, Result):
        return obj
    elif isinstance(obj, Maybe):
        return obj.to_result(None)
    return Err(obj) if isinstance(obj, Exception) else Ok(obj)


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
        if name.startswith('_') and not private:
            continue
        if isinstance(value, types.FunctionType):
            try:
                Result.with_safe(value)
            except Exception:
                func_name = '%s.%s' % (mod.__name__, name)
                warnings.warn('could not create safe version of %s' % func_name)
