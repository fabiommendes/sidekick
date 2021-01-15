from functools import cached_property

from ..typing import TYPE_CHECKING, Any, Callable, Catchable

if TYPE_CHECKING:
    from .fn import fn


def as_method(method, name):
    method.__name__ = name
    method.__qualname__ = f"fn.{name}"
    method.__doc__ = "Auto generated, see :func:`sidekick.functions.{name}`"
    return method


def curry_n(n, name, options=()):
    """
    Curry if only one argument is given and execute if any additional arguments
    are passed.
    """

    def method(self: "FnMixin", *args, **kwargs):
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
    __slots__ = ()

    if TYPE_CHECKING:
        from .. import functions as _mod

        _mod = _mod
    else:

        @cached_property
        def _mod(self):
            from .. import functions

            return functions

    #
    # Expose functions in sidekick.functions.lib_arguments as methods.
    #
    def flip(self, x, y, /, *args, **kwargs):
        """
        Executes flipping the first two arguments.

        Access as attribute to obtain a flipped version of function.
        """
        return self._func(y, x, *args, **kwargs)

    def reverse_args(self, /, *args, **kwargs):
        """
        Executes reversing the order of positional arguments.

        Access as attribute to obtain a reversed version of function.
        """
        return self._func(*args[::-1], **kwargs)

    select_args = curry_n(1, "select_args")
    skip_args = curry_n(1, "skip_args")
    keep_args = curry_n(1, "keep_args")

    def variadic_args(self, /, *args, **kwargs):
        """
        Pass variadic arguments as single tuple to function.
        """
        return self._func(args, **kwargs)

    def splice_args(self, xs, /, *args, **kwargs):
        """
        Splice first argument.
        """
        return self._func(*xs, *args, **kwargs)

    def set_null(self, /, *defaults: Any, **kwargs: Any) -> "fn":
        """
        Return a new function that replace all null arguments in the given positions
        by the provided default value.
        """
        return self._mod.set_null(self._func, *defaults, **kwargs)

    #
    # Expose functions in sidekick.functions.lib_combinators as methods.
    #
    def do(self, /, *args, **kwargs):
        """
        Execute function, but return the first argument.

        Function result is ignored, hence do is executed only for the function
        side-effects.
        """
        if not args:
            raise TypeError("requires at least a single argument.")
        self(*args, **kwargs)
        return args[0]

    #
    # Expose functions in sidekick.functions.lib_composition as methods.
    #
    def compose(self, *funcs) -> "fn":
        """
        Compose with other functions.

        Argument flow from right to left. Function is thus the last to execute.
        """
        return self._mod.compose(self, *funcs)

    def pipeline(self, *funcs) -> "fn":
        """
        Compose with other functions.

        Argument flow from left to right, starting in self.
        """
        return self._mod.pipeline(self, *funcs)

    def juxt(self, *funcs, **kwargs) -> "fn":
        """
        Return function that juxtaposes fn with all functions in the arguments.
        """
        return self._mod.juxt(self, *funcs, **kwargs)

    #
    # Expose functions in sidekick.functions.lib_runtime as methods.
    #
    def once(self) -> "fn":
        """
        Version of function that perform a single invocation.

        Repeated calls to the function return the value of the first invocation.
        """
        return self._mod.once(self._func)

    def thunk(self, /, *args, **kwargs) -> Callable[[], Any]:
        """
        Return as a thunk.
        """
        return self._mod.thunk(self, *args, **kwargs)

    call_after = curry_n(1, "call_after", {"default"})
    call_at_most = curry_n(1, "call_at_most")

    def throttle(self, dt: float, **kwargs) -> "fn":
        """
        Limit the rate of execution of func to once at each ``dt`` seconds.

        Return a new function.
        """
        return self._mod.throttle(dt, self, **kwargs)

    def background(self, /, *args, **kwargs) -> Any:
        """
        Execute function in the background.

        Current implementation uses threads, but in the future it may use hooks
        to other runtimes such as asyncio, curio, etc.
        """
        return self._mod.background(self, *args, **kwargs)

    def catch(self, error, /, *args, **kwargs):
        """
        Handle exception in function.

        If the exception occurs, return None or the value mapped from the error
        mapping.
        """
        return self._mod.catch(error, self, *args, **kwargs)

    def catching(self, error) -> "fn":
        """
        Handle exception in function.

        If the exception occurs, it executes the given handler.

        Return a new function with the new error handling behavior.
        """
        return self._mod.catching(error, self)

    def retry(
        self, n: int, /, *args, error: Catchable = Exception, sleep=None, **kwargs
    ) -> "fn":
        """
        Try to call function n types before raising an error.

        This is useful for functions that may fail due to interaction with
        external resources (e.g., fetch data from the network).

        Args:
            n:
                Maximum number of times to execute function
            error:
                Exception or tuple with suppressed exceptions.
            sleep:
                Interval between attempts. This is a blocking function, hence
                use with care.

        Other positional and keyword arguments are forwarded to function.
        """

        func = self._mod.retry(n, self, error=error, sleep=sleep)
        return func(*args, **kwargs)
