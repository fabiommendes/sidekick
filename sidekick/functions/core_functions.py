import inspect
import re
from functools import singledispatch, lru_cache, wraps

from decorator import decorator

from .signature import Signature
from .stub import Stub
from .. import _operators as operators
from ..typing import (
    Any,
    Callable,
    FunctionType,
    FunctionTypes,
    T,
    Tuple,
    Union,
    TYPE_CHECKING,
    FunctionWrapperTypes,
)

if TYPE_CHECKING:
    from .fn import fn  # noqa: F401
    from .. import api as sk  # noqa: F401


def to_fn(func: Any) -> "fn":
    """
    Convert callable to an :class:`fn` object.

    If func is already an :class:`fn` instance, it is passed as is.
    """
    if isinstance(func, fn):
        return func
    else:
        return fn(func)


def to_function(func: Any, name=None, keep_signature=False) -> FunctionType:
    """
    Return object as as Python function.

    Non-functions are wrapped into a function definition.

    Args:
        func:
            Callable object to be coerced to FunctionType.
        name:
            Force __name__ to have the given value. This modifies lambdas
            inplace and create wrapper methods for other function types.
        keep_signature:
            If true and func is not a FunctionType, wraps into a python function
            with proper signature.
    """

    func = to_callable(func)

    if isinstance(func, FunctionType):
        if name is not None and func.__name__ == "<lambda>":
            func.__name__ = name
        return func

    @wraps(func)
    def f(*args, **kwargs):
        return func(*args, **kwargs)

    if keep_signature:
        f = decorator(func)(f)

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
        elif isinstance(func, FunctionWrapperTypes):
            return func.__func__
        return _to_callable(func)


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


def identity(x, /, *args, **kwargs):
    """
    A simple identity function that accepts a single positional argument
    and ignore keywords.
    """
    return x


identity.fn_extends = None
tuple_identity.fn_extends = ...
to_callable.register = _to_callable.register
to_callable.dispatch = _to_callable.dispatch
to_callable.register(FunctionType, lambda f: f)
to_callable.register(type(Ellipsis), lambda _: tuple_identity)
to_callable.register(type(None), lambda _: identity)
to_callable.register(dict, lambda d: lambda x: d.get(x, x))
to_callable.register(set, lambda s: s.__contains__)
to_callable.register(frozenset, lambda s: s.__contains__)


@to_callable.register(str)
def _(code, ns=None):
    try:
        return operators.FROM_SYMBOLS[code]
    except KeyError:
        pass
    return compile_callable(code, ns)


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


def quick_fn(func: Callable) -> "fn":
    """
    Faster fn constructor.

    This is about twice as fast as the regular fn() constructor. It assumes that
    fn is a FunctionType.
    """
    new: fn = object.__new__(fn)
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


#
# String expression compiling
#
@lru_cache(128)
def compile_callable(code, ns=None):
    """
    Convert strings to the corresponding lambda functions.
    """
    if code.startswith('/'):
        return compile_regex_function(code)

    code = compile(f"lambda {code}", "<sidekick>", "eval", dont_inherit=True)
    return eval(code, {} if ns is None else ns)


def compile_regex_function(expr):
    """
    Compile an regex expression of type:

    * "/<regex>/" -> simple regex match. Return match objects.
    * "/<regex>/<rep>/" -> regex replacement.

    """
    try:
        _empty, head, *rest, mod = expr.split('/')
    except IndexError:
        raise ValueError(f'invalid regex expression: {expr!r}')
    parts = [head]
    rest.reverse()

    while rest:
        nxt = rest.pop()
        if parts[-1].endswith('\\'):
            parts[-1] += nxt + '/'  # This was a escaped solidus
        else:
            parts.append(nxt)

    # We have 2 valid scenarios:
    # /<regex>/ --> parts = [regex]
    # /<regex>/<replace>/ --> parts = [regex, replace]
    if mod:
        raise NotImplementedError('regex modifiers are not accepted yet')
    if len(parts) == 1:
        return re.compile(parts[0]).fullmatch
    elif len(parts) == 2:
        sub = re.compile(parts[0]).sub
        pattern = parts[1]

        # For now we only support the $0-$9 and $$ as a escape
        def sub_fn(m):
            if (r := m.group(1)) == '$':
                return r
            return f'\\g<{r}>'

        pattern = re.sub(r'\$([$0-9])', sub_fn, pattern)
        return lambda st: sub(pattern, st)
    else:
        raise ValueError(f'invalid regex expression: {expr!r}')


from .fn import fn  # noqa: E402, F811
