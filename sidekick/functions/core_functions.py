import inspect
from functools import singledispatch, lru_cache

from .signature import Signature
from .stub import Stub
from .. import _operators as operators
from ..typing import (
    Any,
    Callable,
    FunctionType,
    Mapping,
    FunctionTypes,
    Set,
    T,
    Tuple,
    Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from .fn import fn  # noqa: F401
    from .. import api as sk  # noqa: F401

_new = object.__new__


def to_fn(func: Any) -> "fn":
    """
    Convert callable to an :class:`fn` object.

    If func is already an :class:`fn` instance, it is passed as is.
    """
    if isinstance(func, fn):
        return func
    else:
        return fn(func)


def to_function(func: Any, name=None) -> FunctionType:
    """
    Return object as as Python function.

    Non-functions are wrapped into a function definition.
    """

    func = to_callable(func)

    if isinstance(func, FunctionType):
        if name is not None and func.__name__ == "<lambda>":
            func.__name__ = name
        return func

    def f(*args, **kwargs):
        return func(*args, **kwargs)

    if name is not None:
        f.__name__ = name
    else:
        name = getattr(type(func), "__name__", "function")
        f.__name__ = getattr(func, "__name__", name)
    return f


@singledispatch
def _to_callable(func: Any):
    try:
        return func.__sk_callable__
    except AttributeError:
        pass

    if callable(func):
        return func
    else:
        raise TypeError("cannot be interpreted as a callable: %r" % func)


def to_callable(func: Any) -> Callable:
    """
    Convert argument to callable.

    This differs from to_function in which it returns the most efficient
    version of object that has the same callable interface as the argument.

    This *removes* sidekick's function wrappers such as fn and try to convert
    argument to a straightforward function value.

    This defines the following semantics:

    * Sidekick's fn: extract the inner function.
    * None: return an identity function.
    * ...: return an tuple identity function, i.e., it behaves like identity
      for single argument calls, but return tuples when multiple arguments are
      given. Keyword arguments are ignored.
    * Mappings: map.__getitem__
    * Sets: set.__contains__
    * Functions, methods and other callables: returned as-is.
    """

    try:
        return func.__sk_callable__
    except AttributeError:
        if isinstance(func, FunctionTypes):
            return func
        return _to_callable(func)


to_callable.register = _to_callable.register
to_callable.dispatch = _to_callable.dispatch

to_callable.register(FunctionType, lambda fn: fn)
to_callable.register(Mapping, lambda dic: lambda x: map_function(dic, x))
to_callable.register(Set, lambda set_: set_.__contains__)


def tuple_identity(*args: T, **kwargs) -> Union[T, Tuple[T, ...]]:
    """
    An extended splicing function when multiple arguments are given.

    It returns its argument when a single argument is given, or the tuple of
    args when the number of arguments is different from 1.

    This behavior is consistent with the algebraic properties of tuple types
    in languages that support real tuples. Python tuples are just immutable
    arrays and accept single element tuples. Languages that with a more rigorous
    implementation of tuples tend to collapse Tuple[T] -> T and usually associate
    Tuple[] -> Nullable type.
    """
    if len(args) == 1:
        return args[0]
    return args


def identity(*args, **kwargs):
    """
    A simple identity function that accepts a single positional argument
    and ignore keywords.
    """
    (x,) = args
    return x


identity.fn_extends = None
tuple_identity.fn_extends = ...

to_callable.register(type(None), lambda fn: identity)
to_callable.register(type(Ellipsis), lambda _: tuple_identity)


def map_function(dic, x):
    try:
        return dic.get(x, x)
    except (KeyError, AttributeError):
        return x


@to_callable.register(str)
def _(code, ns=None):
    try:
        return operators.FROM_SYMBOLS[code]
    except KeyError:
        pass
    return compile_callable(code, ns)


@lru_cache(128)
def compile_callable(code, ns=None):
    """
    Convert strings to the corresponding lambda functions.
    """

    code = compile(f"lambda {code}", "<sidekick>", "eval", dont_inherit=True)
    return eval(code, {} if ns is None else ns)


@singledispatch
def arity(func: Callable, how="short"):
    """
    Return arity of a function.

    Examples:
        >>> from operator import add
        >>> sk.arity(add)
        2
    """

    if hasattr(func, "arity"):
        return func.arity(how)
    return signature(func).arity(how)


@singledispatch
def signature(func: Callable) -> Signature:
    """
    Return the signature of a function.
    """
    return Signature.from_signature(inspect.signature(func))


@singledispatch
def declaration(func: Callable) -> "Stub":
    """
    Return a :class:`Stub` object representing the function signature.
    """

    sig = signature(func)
    return Stub(func.__name__, (sig,))


def quick_fn(func: callable) -> "fn":
    """
    Faster fn constructor.

    This is about twice as fast as the regular fn() constructor. It assumes that
    fn is
    """
    new: fn = _new(fn)
    new._func = func
    new.__dict__ = {}
    return new


def make_xor(f, g):
    """
    Compose functions in a short-circuit version of xor using the following
    table:

    +--------+--------+-------+
    | A      | B      | A^B   |
    +--------+--------+-------+
    | truthy | truthy | not B |
    +--------+--------+-------+
    | truthy | falsy  | A     |
    +--------+--------+-------+
    | falsy  | truthy | B     |
    +--------+--------+-------+
    | falsy  | falsy  | B     |
    +--------+--------+-------+
    """

    def xor(*args, **kwargs):
        a = f(*args, **kwargs)
        if a:
            b = g(*args, **kwargs)
            return not b if b else a
        else:
            return g(*args, **kwargs)

    return xor


from .fn import fn  # noqa: E402, F811
