from functools import partial
from types import MappingProxyType as mappingproxy, FunctionType
from typing import Any, Callable, Union

from ._fn_introspection import arity, signature, stub
from ._fn_meta import FunctionMeta, extract_function, make_xor, mixed_accessor
from ._placeholder import compile_ast, call_node

__all__ = ["fn", "as_fn", "quick_fn"]
_new = object.__new__


class fn(metaclass=FunctionMeta):
    """
    Base class for function-like objects in Sidekick.
    """

    __slots__ = ("_func", "__dict__", "__weakref__")
    func: callable = property(lambda self: self._func)
    __sk_callable__: callable = property(lambda self: self._func)

    @property
    def __wrapped__(self):
        try:
            return self.__dict__["__wrapped__"]
        except KeyError:
            return self._func

    @__wrapped__.setter
    def __wrapped__(self, value):
        self.__dict__["__wrapped__"] = value

    _ok = _err = None
    args = ()
    keywords = mappingproxy({})

    #
    # Alternate constructors
    #
    @mixed_accessor
    def curry(self, n=None):
        """
        Return a curried version of function with arity n.

        If arity is not given, infer from function parameters.
        """
        return fn.curry(n, self.__sk_callable__)

    @curry.classmethod
    def curry(cls, arity, func=None, **kwargs) -> Union["Curried", callable]:
        """
        Return a curried function with given arity.
        """
        if func is None:
            return lambda f: fn.curry(arity, f, **kwargs)
        if isinstance(arity, int):
            return Curried(func, arity)
        else:
            raise NotImplementedError

    @classmethod
    def wraps(cls, func, fn_obj=None):
        """
        Creates a fn function that wraps another function.
        """
        if fn_obj is None:
            return lambda f: cls.wraps(func, f)
        if not isinstance(fn_obj, fn):
            fn_obj = fn(fn_obj)
        for attr in ("__name__", "__qualname__", "__doc__", "__annotations__"):
            value = getattr(func, attr, None)
            if value is not None:
                setattr(fn_obj, attr, value)
        return fn_obj

    def __init__(self, func):
        self._func = extract_function(func)
        self.__dict__ = {}

    def __repr__(self):
        try:
            func = self.__wrapped__.__name__
        except AttributeError:
            func = repr(self.func)
        return f"{self.__class__.__name__}({func})"

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    #
    # Function composition
    #
    def __rshift__(self, other):
        f = extract_function(other)
        g = self.__sk_callable__
        return fn(lambda *args, **kw: f(g(*args, **kw)))

    def __rrshift__(self, other):
        f = extract_function(other)
        g = self.__sk_callable__
        return fn(lambda *args, **kw: g(f(*args, **kw)))

    __lshift__ = __rrshift__
    __rlshift__ = __rshift__

    #
    # Predicate and boolean algebra
    #
    def __xor__(self, g):
        f = self.__sk_callable__
        g = extract_function(g)
        return fn(make_xor(f, g))

    def __rxor__(self, f):
        f = extract_function(f)
        g = self.__sk_callable__
        return fn(make_xor(f, g))

    def __or__(self, g):
        f = self.__sk_callable__
        g = extract_function(g)
        return fn(lambda *xs, **kw: f(*xs, **kw) or g(*xs, **kw))

    def __ror__(self, f):
        f = extract_function(f)
        g = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*xs, **kw) or g(*xs, **kw))

    def __and__(self, g):
        f = self.__sk_callable__
        g = extract_function(g)
        return fn(lambda *xs, **kw: f(*xs, **kw) and g(*xs, **kw))

    def __rand__(self, f):
        f = extract_function(f)
        g = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*xs, **kw) and g(*xs, **kw))

    def __invert__(self):
        f = self.__sk_callable__
        return fn(lambda *xs, **kw: not f(*xs, **kw))

    def __rfloordiv__(self, other):
        return self(other)

    def __mul__(self, other):
        return self(other)

    def __matmul__(self, other):
        return fmap(self, other)

    #
    # Descriptor interface
    #
    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        else:
            return partial(self, instance)

    #
    # Other python interfaces
    #
    def __getattr__(self, attr):
        return getattr(self.__wrapped__, attr)

    def arity(self):
        return arity(self.__sk_callable__)

    def signature(self):
        return signature(self.__sk_callable__)

    def stub(self):
        return stub(self)

    #
    # Partial application
    #
    def thunk(self, *args, **kwargs):
        """
        Pass all arguments to function, without executing.

        Returns a thunk, i.e., a zero-argument function that evaluates only
        during the first execution and re-use the computed value in future
        evaluations.

        See Also:
            :func:`sidekick.api.thunk`
        """
        from .functions import thunk

        return thunk(*args, **kwargs)(self)

    def partial(self, *args, **kwargs):
        """
        Return a fn-function with all given positional and keyword arguments
        applied.
        """
        f = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*args, *xs, **kwargs, **kw))

    def rpartial(self, *args, **kwargs):
        """
        Like partial, but fill positional arguments from right to left.
        """
        f = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*xs, *args, **update_arguments(kwargs, kw)))

    def single(self, *args, **kwargs):
        """
        Similar to partial, but with a few constraints:

        * Resulting function must be a function of a single positional argument.
        * Placeholder expressions are evaluated passing this single argument
          to the resulting function.

        Example:
            >>> add = fn(lambda x, y: x + y)
            >>> g = add.single(_, 2 * _)
            >>> g(10)  # g(x) = x + 2 * x
            30

        Returns:
            fn
        """
        ast = call_node(self.__sk_callable__, *args, **kwargs)
        return compile_ast(ast)

    #
    # Wrapping
    #
    def result(self, *args, **kwargs):
        """
        Return a result instance after function call.

        Exceptions are converted to Err() cases.
        """
        try:
            return self._ok(self.func(*args, **kwargs))
        except Exception as exc:
            return self._err(exc)


# Slightly faster access for slotted object
# noinspection PyPropertyAccess
fn.__sk_callable__ = fn._func


#
# Specialized classes: curried
#
class Curried(fn):
    """
    Curried function with known arity.
    """

    __slots__ = ("args", "_arity", "keywords")
    __sk_callable__ = property(lambda self: self)

    def __init__(
        self,
        func: callable,
        arity: int,
        args: tuple = (),
        keywords: dict = mappingproxy({}),
        **kwargs,
    ):
        super().__init__(func)
        self.args = args
        self.keywords = keywords
        self._arity = arity

    def arity(self):
        return self._arity

    def __repr__(self):
        try:
            func = self.__name__
        except AttributeError:
            func = repr(self._func)
        args = ", ".join(map(repr, self.args))
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self.keywords.items())
        if not args:
            args = kwargs
        elif kwargs:
            args = ", ".join([args, kwargs])
        return f"<curry {func}({args})>"

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            raise TypeError("curried function cannot be called without arguments")

        try:
            return self._func(*self.args, *args, **self.keywords, **kwargs)
        except TypeError:
            n = len(args)
            if n == 0 and not kwargs:
                msg = f"function receives between 1 and {self.arity} arguments"
                raise TypeError(msg)
            elif n >= self._arity:
                raise
            else:
                args = self.args + args
                update_arguments(self.keywords, kwargs)
                return Curried(self._func, self._arity - n, args, kwargs)

    def partial(self, *args, **kwargs):
        update_arguments(self.keywords, kwargs)
        n_args = self._arity - len(args)
        return Curried(self.__sk_callable__, n_args, args + self.args, kwargs)

    def rpartial(self, *args, **kwargs):
        update_arguments(self.keywords, kwargs)
        wrapped = self.__sk_callable__
        if self.args:
            wrapped = partial(wrapped, args)
        return fn(wrapped).rpartial(*args, **kwargs)


#
# Utility functions and types
#
def as_fn(func: Any) -> fn:
    """
    Convert callable to an :class:`fn` object.

    If func is already an :class:`fn` instance, it is passed as is.
    """
    return func if isinstance(func, fn) else fn(func)


def as_callable(func: Any) -> Callable:
    """
    Return function as callable.
    """
    return ...


def as_function(func: Any) -> FunctionType:
    """
    Return object as as Python function.

    Callables are wrapped into a function definition.
    """
    return ...


def quick_fn(func: callable) -> fn:
    """
    Faster fn constructor.

    This is about twice as fast as the regular fn() constructor. It assumes that
    fn is
    """
    new: fn = _new(fn)
    new._func = func
    new.__dict__ = {}
    return new


class AmbiguousOperation(ValueError):
    """
    Raised when calling (lhs | func) for a callable lhs.
    """

    @classmethod
    def default(cls):
        return cls(
            "do you want to compose predicates or pass argument to function?"
            "\nUse `fn(lhs) | func` in the former and `lhs > func` in the latter."
        )


def update_arguments(src, dest: dict):
    duplicate = set(src).intersection(dest)
    if duplicate:
        raise TypeError(f"duplicated keyword arguments: {duplicate}")
    dest.update(src)
    return dest
