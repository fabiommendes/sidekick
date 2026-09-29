import inspect
import re
from functools import singledispatch, lru_cache, wraps
from typing import Any, Callable, TypeVar, Tuple, TypeVarTuple, Union, TYPE_CHECKING, overload


# from .signature import Signature
# from .stub import Stub
from .types import FunctionType, PyFunctionTypes, PyFunctionWrapperTypes


T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
Ts = TypeVarTuple("Ts")

if TYPE_CHECKING:
    from .fn import fn  # noqa: F401
    from . import operator  # noqa: F401
    from sidekick import api as sk  # noqa: F401
    from sidekick.functions import Signature, Stub  # noqa: F401


def to_fn(func: Any) -> "fn":
    """
    Convert callable to an :class:`fn` object.

    If func is already an :class:`fn` instance, it is passed as is.
    """
    if isinstance(func, fn):
        return func
    else:
        return fn(func)




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
    if code.startswith("/"):
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
        _empty, head, *rest, mod = expr.split("/")
    except IndexError:
        raise ValueError(f"invalid regex expression: {expr!r}")
    parts = [head]
    rest.reverse()

    while rest:
        nxt = rest.pop()
        if parts[-1].endswith("\\"):
            parts[-1] += nxt + "/"  # This was a escaped solidus
        else:
            parts.append(nxt)

    # We have 2 valid scenarios:
    # /<regex>/ --> parts = [regex]
    # /<regex>/<replace>/ --> parts = [regex, replace]
    if mod:
        raise NotImplementedError("regex modifiers are not accepted yet")
    if len(parts) == 1:
        return re.compile(parts[0]).fullmatch
    elif len(parts) == 2:
        sub = re.compile(parts[0]).sub
        pattern = parts[1]

        # For now we only support the $0-$9 and $$ as a escape
        def sub_fn(m):
            if (r := m.group(1)) == "$":
                return r
            return f"\\g<{r}>"

        pattern = re.sub(r"\$([$0-9])", sub_fn, pattern)
        return lambda st: sub(pattern, st)
    else:
        raise ValueError(f"invalid regex expression: {expr!r}")


from .fn import fn
from .operator import OP_FROM_SYMBOLS
