import re
from functools import lru_cache, singledispatch, wraps
from types import EllipsisType, FunctionType, MethodDescriptorType, MethodType
from typing import Any, overload
import token 
import tokenize
from decorator import decorator

from .util import a, b, args_t, r, P, Fn, Unpack, UNARY_OP, BINARY_OP, SIDEKICK_GLOBALS
from .protocols import ToCallable


@singledispatch
def to_callable(func: Fn | ToCallable) -> Fn:
    """
    Convert argument to callable.

    It returns the most efficient version of object that has the same callable
    interface as the argument. It also extends the "function" interface to
    non-callable objects like sets, strings, and more, to make it convenient
    to create easy and simple functions.

    This function *removes* sidekick's function wrappers and can produce slightly more
    efficient callables than the wrapped value.

    * None:
        Return an identity function.

    * Ellipsis (...):
        Return an tuple identity function, i.e., it behaves like identity
        for single argument calls, but return tuples when multiple arguments are
        given. Keyword arguments are ignored.

    * Mappings:
        Same as map.get

    * Sets:
        Same as set.__contains__

    * Quick lambdas:
        Compile object, when necessary and return the compiled function.

    * Strings:
        "/regex/":
            Predicate functions for regex matches.
        "/regex/bar/":
            Regex substitution.
        "op":
            For known Python operators (+, -, *, etc), return the corresponding operator.

    * Sidekick's fn:
        Extract the inner function.

    * Functions, methods and other callables:
        Returned as-is.
    """
    if callable(func):
        return func

    try:
        mk_callable = func.__sk_callable__
    except AttributeError:
        raise TypeError("not a valid callable.")
    return mk_callable()


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
    return f  # type: ignore 


@overload
def tuple_identity(x: a, /, **kwargs) -> a:
    ...


@overload
def tuple_identity(
    x: a, y: b, *args: Unpack[args_t], **kwargs
) -> tuple[a, b, Unpack[args_t]]:
    ...


def tuple_identity(*args, **_):
    """
    An extended splicing function when multiple arguments are given.

    It returns its argument when a single argument is given, or the tuple of
    args when the number of arguments is different from 1.

    This behavior is consistent with the algebraic properties of tuple types
    in languages that support real tuples. Python tuples are just immutable
    arrays and accept single element tuples. Languages with a more rigorous
    implementation of tuples tend to collapse Tuple[T] -> T and usually associate
    Tuple[] to the Nullable type (NoneType, in Python).
    """
    if len(args) == 1:
        return args[0]
    return args


def identity(x: a, **_) -> a:
    """
    A simple identity function that accepts a single positional argument
    and ignore keywords.
    """
    return x


@to_callable.register(FunctionType)
@to_callable.register(MethodType)
@to_callable.register(MethodDescriptorType)
def _(f: Fn[P, r]) -> Fn[P, r]:
    return f


@to_callable.register
def _(_: None) -> Fn[[a, Unpack[args_t]], a]:
    return identity


@to_callable.register
def _(_: EllipsisType) -> Fn[[Unpack[args_t]], tuple[Unpack[args_t]]]:
    return tuple_identity


@to_callable.register
def _(d: dict[a, b]) -> Fn[[a], b | None]:
    return d.get


@to_callable.register
def _(s: set[a]) -> Fn[[a], bool]:
    return s.__contains__


@to_callable.register
def _(s: frozenset[a]) -> Fn[[a], bool]:
    return s.__contains__


@to_callable.register(str)
@lru_cache(256)
def _(code: str, ns=None) -> Fn:
    if (fn := BINARY_OP.get(code)) is not None:
        return fn

    if (fn := UNARY_OP.get(code)) is not None:
        return fn

    if code.startswith("/"):
        return compile_regex(code)
    else:
        return compile_lambda_source(code)


def compile_lambda_source(src: str, var_names=("x", "y", "z", "w")) -> Fn:
    """
    Compile a lambda function.

    Example:
        >>> fn = compile_lambda_source("x + 2 * y + 1")
        >>> fn(1, 2)
        6
    """
    lines = iter(src.encode("utf-8").splitlines())
    seen = {name: False for name in var_names}

    for tk in tokenize.tokenize(lines.__next__):
        if tk.type == token.NAME and tk.string in seen:
            seen[tk.string] = True

    args = list[str]()
    for v in reversed(var_names):
        if seen[v] or args:
            args.append(v)
    args.reverse()
    argdefs = ", ".join(args)

    return eval(f"lambda {argdefs}: {src}", SIDEKICK_GLOBALS, {})


def compile_regex(src: str) -> Fn:
    """
    Compile a regex function.
    
    Examples:
        Regex can represent substitutions
        
        >>> func = compile_regex(r"/f../bar/")
        >>> func("foobar")
        'barbar'
        
        Or simple string queries
        
        >>> func = compile_regex(r"/f../")
        >>> func("foo")
        True
    """
    parts = []
    
    next_is_escape = False
    for part in src.split("/"):
        if next_is_escape:
            parts[-1] += part
        else:
            parts.append(part)
        next_is_escape = part.endswith("\\")
        
    match parts:
        case ["", regex, flags]:
            pattern = re.compile(regex, flags=parse_re_flags(flags))
            return lambda st: bool(pattern.fullmatch(st))
            
        case ["", regex, repl, flags]:
            pattern = re.compile(regex, flags=parse_re_flags(flags))

            # For now we only support the $0-$9 and $$ as escape sequences
            def sub_fn(m):
                if (r := m.group(1)) == "$":
                    return r
                return f"\\g<{r}>"

            repl = re.sub(r"\$([$0-9])", sub_fn, repl)
            return lambda st: pattern.sub(repl, st)
        
        case _:
            raise ValueError(f"invalid regex pattern: {src}")
    

def parse_re_flags(flags: str) -> int:
    """
    Convert string based regex flags into a proper int flag.
    """
    
    if not flags:
        return 0
    raise NotImplementedError("flags are not supported yet!")