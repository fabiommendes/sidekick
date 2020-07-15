import time
from types import FunctionType

from .core_functions import to_callable
from .fn import fn
from .utils import lazy_property
from ..typing import TYPE_CHECKING, Any, Callable, Func, Catchable

if TYPE_CHECKING:
    pass


def as_method(method, name):
    method.__name__ = name
    method.__qualname__ = f"fn.{name}"
    method.__doc__ = "Auto generated, see :func:`sidekick.functions.{name}`"
    return method


def as_last_argument(name):
    """
    Declare methods that pass fn._func as last argument to the corresponding
    method in the API.
    """

    def method(self: FnMixin, *args, **kwargs):
        api_func = getattr(self._mod, name)
        return api_func(*args, self, **kwargs)

    return as_method(method, name)


def curry_n(n, name, options=()):
    """
    Curry if only one argument is given and execute if any additional arguments
    are passed.
    """

    def method(self: FnMixin, *args, **kwargs):
        api_func = getattr(self._mod, name)
        api_kwargs = {k: kwargs.pop(k) for k in kwargs if k in options}

        if len(args) == n and not kwargs:
            return api_func(*args, self, **api_kwargs)

        transformed_fn = api_func(*args[:n], self, **api_kwargs)
        return transformed_fn(*args[n:], **kwargs)

    return as_method(method, name)


class FnMixin:
    """
    Basic mixin class that exposes a _mod lazy attribute to access the
    sidekick.functions module and declare the _func attribute that is
    manipulated by methods.
    """

    _func: Callable
    __call__: Callable

    if TYPE_CHECKING:
        from .. import functions

        _mod = functions
        del functions
    else:

        @lazy_property
        def _mod(self):
            from .. import functions

            return functions


# noinspection PyMethodParameters
class FnArgumentsMixin(FnMixin):
    """
    Expose functions in sidekick.functions.lib_arguments as methods.
    """

    def flip(_self, x, y, *args, **kwargs):
        """
        Executes flipping the first two arguments.

        Access as attribute to obtain a flipped version of function.
        """
        return _self._func(y, x, *args, **kwargs)

    def reverse_args(_self, *args, **kwargs) -> fn:
        """
        Executes reversing the order of positional arguments.

        Access as attribute to obtain a reversed version of function.
        """
        return _self._func(*args[::-1], **kwargs)

    select_args = curry_n(1, "select_args")
    skip_args = curry_n(1, "skip_args")
    keep_args = curry_n(1, "keep_args")

    def variadic_args(_self, *args, **kwargs):
        """
        Pass variadic arguments as single tuple to function.
        """
        return _self._func(args, **kwargs)

    def splice_args(_self, x, *args, **kwargs):
        """
        Splice first argument.
        """
        return _self._func(*x, *args, **kwargs)

    def set_null(self, *defaults: Any, **kwargs: Any) -> fn:
        """
        Return a new function that replace all null arguments in the given positions
        by the provided default value.
        """
        return self._mod.set_null(self._func, *defaults, **kwargs)


# noinspection PyMethodParameters
class LibCombinators(FnMixin):
    """
    Expose functions in sidekick.functions.lib_combinators as methods.
    """

    def do(_self, *args, **kwargs):
        """
        Execute function, but return the first argument.

        Function result is ignored, hence do is executed only for the function
        side-effects.
        """
        if not args:
            raise TypeError("requires at least a single argument.")
        _self(*args, **kwargs)
        return args[0]


# noinspection PyMethodParameters
class LibComposition(FnMixin):
    """
    Expose functions in sidekick.functions.lib_composition as methods.
    """

    def compose(self, *funcs):
        """
        Compose with other functions.

        Argument flow from right to left. Function is thus the last to execute.
        """
        return self._mod.compose(self, *funcs)

    def pipeline(self, *funcs):
        """
        Compose with other functions.

        Argument flow from left to right, starting in self.
        """
        return self._mod.pipeline(self, *funcs)

    def juxt(self, *funcs, **kwargs):
        """
        Return function that juxtaposes fn with all functions in the arguments.
        """
        return self._mod.juxt(self, *funcs, **kwargs)


# noinspection PyMethodParameters
class LibRuntime(FnMixin):
    """
    Expose functions in sidekick.functions.lib_runtime as methods.
    """

    def once(self) -> fn:
        """
        Version of function that perform a single invocation.

        Repeated calls to the function return the value of the first invocation.
        """
        return self._mod.once(self._func)

    def thunk(_self, *args, **kwargs) -> FunctionType:
        """
        Return as a thunk.
        """
        return _self._mod.thunk(*args, **kwargs)(_self)

    call_after = curry_n(1, "call_after", {"default"})
    call_at_most = curry_n(1, "call_at_most")

    def throttle(self, dt: float) -> fn:
        """
        Limit the rate of execution of func to once at each ``dt`` seconds.

        Return a new function.
        """
        return self._mod.throttle(dt, self)

    def background(_self, *args, **kwargs) -> fn:
        """
        Execute function in the background.
        """

        try:
            bg_func = _self.__background
        except AttributeError:
            bg_func = _self.__background = _self._mod.background(_self)
        return bg_func(*args, **kwargs)

    def catch(self, exception, *, handler=None, raises=None) -> "fn":
        """
        Handle exception in function. If the exception occurs, it executes the given
        handler.

        Return a new function.
        """
        return self._mod.catch(exception, handler=handler, raises=raises)(self)

    def retry(n: int, func: Func, *, error: Catchable = Exception, sleep=None) -> fn:
        """
        Retry to execute function at least n times before raising an error.

        This is useful for functions that may fail due to interaction with external
        resources (e.g., fetch data from the network).

        Args:
            n:
                Maximum number of times to execute function
            func:
                Function that may raise errors.
            error:
                Exception or tuple with suppressed exceptions.
            sleep:
                Interval in which it sleeps between attempts.

        Example:
            >>> queue = [111, 7, None, None]
            >>> process = sk.retry(5, lambda n: queue.pop() * n)
            >>> process(6)
            42
        """

        @fn.wraps(func)
        def safe_func(*args, **kwargs):
            for _ in range(n - 1):
                try:
                    return func(*args, **kwargs)
                except error:
                    if sleep:
                        time.sleep(sleep)
            return func(*args, **kwargs)

        func = to_callable(func)
        return safe_func
