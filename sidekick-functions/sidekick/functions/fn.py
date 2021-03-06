from functools import partial, cached_property
from types import MappingProxyType as mappingproxy

from .core_functions import arity, declaration, to_callable, make_xor, signature
from .fn_placeholders import compile_ast, call_node
from .signature import Signature
from .utils import mixed_accessor, lazy_string
from .._modules import GetAttrModule, set_module_class
from ..typing import Union, Dict, Any, Callable, TYPE_CHECKING
from . import fn_mixins as mixins

set_module_class(__name__, GetAttrModule)
identity = lambda x: x
thunk: "fn"
apply: "fn"

if TYPE_CHECKING:
    from sidekick.api import X, Y

FUNCTION_ATTRIBUTES = {
    "doc": "__doc__",
    "name": "__name__",
    "annotations": "__annotations__",
    "closure": "__closure__",
    "code": "__code__",
    "defaults": "__defaults__",
    "globals": "__globals__",
    "kwdefaults": "__kwdefaults__",
}


class FunctionMeta(type):
    """Metaclass for the fn type"""

    _curry = None

    def __new__(mcs, name, bases, ns):
        new = super().__new__(mcs, name, bases, ns)
        new.__doc__ = lazy_string(lambda x: x.__getattr__("__doc__"), new.__doc__)
        new.__module__ = lazy_string(
            lambda x: x.__getattr__("__module__"), new.__module__ or ""
        )
        return new

    def __rshift__(self, other):
        if isinstance(other, self):
            return other

        try:
            func = to_callable(other)
        except TypeError:
            return NotImplementedError
        else:
            return self(func)

    def __repr__(cls):
        return cls.__name__

    __lshift__ = __rlshift__ = __rrshift__ = __rshift__


class fn(mixins.FnMixin, metaclass=FunctionMeta):
    """
    Base class for function-like objects in Sidekick.
    """

    __slots__ = ("_func", "__dict__", "__weakref__")
    func: Callable = property(lambda self: self._func)

    @property
    def __sk_callable__(self) -> Callable:
        return self._func

    @cached_property
    def __wrapped__(self) -> Callable:
        return self._func

    @cached_property
    def __signature__(self) -> Signature:
        return signature(self.__wrapped__)

    _ok = _err = _to_result = None
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
    def curry(cls, arity, /, func=None) -> Union["Curried", callable]:
        """
        Return a curried function with given arity.
        """
        if func is None:
            return lambda f: fn.curry(arity, f)
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

    @classmethod
    def generator(cls, func) -> "fn":
        from ..seq import generator

        return generator(func)

    def __init__(self, func):
        self._func = to_callable(func)
        self.__dict__ = {}
        self.__annotations__ = getattr(self._func, "__annotations__", None)

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
        f = to_callable(other)
        g = self.__sk_callable__
        return fn(lambda *args, **kw: f(g(*args, **kw)))

    def __rrshift__(self, other):
        f = to_callable(other)
        g: Callable = self.__sk_callable__
        return fn(lambda *args, **kw: g(f(*args, **kw)))

    __lshift__ = __rrshift__
    __rlshift__ = __rshift__

    #
    # Predicate and boolean algebra
    #
    def __xor__(self, g):
        f = self.__sk_callable__
        g = to_callable(g)
        return fn(make_xor(f, g))

    def __rxor__(self, f):
        f = to_callable(f)
        g = self.__sk_callable__
        return fn(make_xor(f, g))

    def __or__(self, g):
        f = self.__sk_callable__
        g = to_callable(g)
        return fn(lambda *xs, **kw: f(*xs, **kw) or g(*xs, **kw))

    def __ror__(self, f):
        f = to_callable(f)
        g = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*xs, **kw) or g(*xs, **kw))

    def __and__(self, g):
        f = self.__sk_callable__
        g = to_callable(g)
        return fn(lambda *xs, **kw: f(*xs, **kw) and g(*xs, **kw))

    def __rand__(self, f):
        f = to_callable(f)
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
        return apply(self, other)  # noqa: F821

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

    def arity(self, how="short") -> Signature:
        """
        Return function arity.

        The default behaviour how="short" returns the minimal arity before
        saturating the function.
        """
        return arity(self.__sk_callable__)

    def signature(self) -> Signature:
        """
        Return a signature object.
        """
        return self.__signature__

    def declaration(self):
        return declaration(self)

    #
    # Partial application
    #
    def partial(self, /, *args, **kwargs):
        """
        Return a fn-function with all given positional and keyword arguments
        applied.
        """
        f = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*args, *xs, **kwargs, **kw))

    def rpartial(self, /, *args, **kwargs):
        """
        Like partial, but fill positional arguments from right to left.
        """
        f = self.__sk_callable__
        return fn(lambda *xs, **kw: f(*xs, *args, **update_arguments(kwargs, kw)))

    def single(self, /, *args, **kwargs):
        """
        Similar to partial, but with a few constraints:

        * Resulting function must be a function of a single positional argument.
        * Placeholder expressions are evaluated passing this single argument
          to the resulting function.

        Example:
            >>> from sidekick.api import placeholder as _
            >>> add = fn(X + Y)
            >>> g = add.single(_, 2 * _)
            >>> g(10)  # g(x) = x + 2 * x
            30

        Returns:
            fn
        """
        ast = call_node(to_callable(self), *args, **kwargs)
        return compile_ast(ast)

    #
    # Wrapping
    #
    def result(self, /, *args, **kwargs):
        """
        Call function and wraps result in an Ok(result) case.

        Exceptions are converted to Err(exc) values.
        """
        try:
            value = self.func(*args, **kwargs)
        except Exception as exc:
            return self._err(exc)
        else:
            return self._to_result(value)


# Slightly faster access for slotted object
# noinspection PyPropertyAccess
fn.__sk_callable__ = fn._func


class Curried(fn):
    """
    Curried function with known arity.
    """

    __slots__ = ("args", "_arity", "keywords")
    __sk_callable__ = property(lambda self: self)

    @cached_property
    def __signature__(self):
        sig = signature(self.__wrapped__)
        return sig.partial(*self.args, **self.keywords)

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

    def arity(self, how='short'):
        if how != 'short':
            raise ValueError('curried functions only accept short arity specifier')
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


def update_arguments(src, dest: dict):
    duplicate = set(src).intersection(dest)
    if duplicate:
        raise TypeError(f"duplicated keyword arguments: {duplicate}")
    dest.update(src)
    return dest


def wrap_fn_functions(globs: Dict[str, Any], lst=None, exclude=()):
    """
    Wraps all function in namespace using fn.

    This avoids the @fn decorator that sometimes confuses static checkers.
    """

    if lst is None:
        lst = [
            k
            for k, v in globs.items()
            if callable(v) and not isinstance(v, type) and not k.startswith("_")
        ]

    for k in lst:
        v = globs[k]
        if k in exclude or isinstance(v, fn):
            continue
        try:
            globs[k] = fn(v)
        except Exception as e:
            cls = type(e)
            raise RuntimeError(f"cannot wrap {v} as {k}, {cls}: {e}")


def __getattr__(name):
    if name == "make_xor":
        from .core_functions import make_xor

        return make_xor

    from .. import functions

    globals()[name] = value = getattr(functions, name)
    return value
