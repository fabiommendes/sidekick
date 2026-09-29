from typing import Literal

from .utils import Fn
from .signature import Signature
from .stub import Stub

ArityT = Literal["short", "long"]


class IntrospectableFn:
    """
    Callables that can be introspected.
    """

    def arity(self, how="short") -> Signature:
        """
        Return function arity.

        See also:
            :func:`arity`
        """
        return arity(self, how=how)

    def signature(self) -> Signature:
        """
        Function's signature.

        See also:
            :func:`signature`
        """
        return signature(self)

    def declaration(self) -> Stub:
        """
        Stub with complete function signature, including overloads.

        See also:
            :func:`declaration`
        """
        return declaration(self)


def arity(func: Fn, *, how: ArityT = "short") -> int:
    """
    Return the function arity.

    A "short" arity (default) represents the minimum number positional
    parameters necessary to call the function.

    The "long" arity represents the maximum number of positional
    parameters, including parameters with default values.

    Examples:
        >>> from operator import add
        >>> arity(add)
        2
    """
    return signature(func).arity(how)


def signature(func: Fn) -> Signature:
    """
    Function's signature.

    Examples:
        >>> def incr(x: int, by: int=1):
        ...     return x + by
        >>> signature(incr)
        TODO
    """
    return Signature.from_callable(func)


def declaration(func: Fn) -> Stub:
    """
    Stub with complete function signature, including overloads.

    Examples:
        >>> def incr(x: int, by: int=1):
        ...     return x + by
        >>> declaration(incr)
        TODO
    """
    sig = signature(func)
    return Stub(func.__name__, (sig,))
