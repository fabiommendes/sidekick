import operator as op
from typing import Callable as Fn


class Placeholder:
    """
    Base class for placeholder objects.
    """


def operator_wrapping(
    wrap_binary_method,
    wrap_rbinary_method=None,
    wrap_unary_method=None,
    arithmetic=True,
    bitwise=False,
    logic=True,
    inplace=True,
    sequence=True,
    operator_module=op,
) -> type:
    """
    Create a wrapper class that implements the given operations as a
    transformation from operator functions or equivalent.

    Args:
        wrap_binary_method:
            Function of operator -> method that creates binary operator.
            Operator is extracted from the given operator namespace.
        wrap_rbinary_method:
            Function of operator -> method that creates binary operator. For
            reversed operations (e.g., __radd__, __rmul__, etc).
        wrap_unary_method:
            Function of operator -> method that creates unary binary operator.
        arithmetic:
            If False, disable arithmetic operators.
        bitwise:
            If False, disable bitwise operators.
        logic:
            If False, disable logic operators.
        inplace:
            If False, disable inplace operators.
        sequence:
            If False, disable sequencing operators.
        operator_module:
            The operator namespace used to fetch operator functions that will be
            passed to constructors. Defaults to Python stdlib's operator module.
    """

    class Base:
        if arithmetic:
            __add__ = wrap_binary_method(operator_module.add)
            __floordiv__ = wrap_binary_method(operator_module.floordiv)
            __mod__ = wrap_binary_method(operator_module.mod)
            __mul__ = wrap_binary_method(operator_module.mul)
            __pow__ = wrap_binary_method(operator_module.pow)
            __sub__ = wrap_binary_method(operator_module.sub)
            __truediv__ = wrap_binary_method(operator_module.truediv)
            if wrap_rbinary_method:
                __radd__ = wrap_rbinary_method, (operator_module.add)
                __rfloordiv__ = wrap_rbinary_method, (operator_module.floordiv)
                __rmod__ = wrap_rbinary_method, (operator_module.mod)
                __rmul__ = wrap_rbinary_method, (operator_module.mul)
                __rpow__ = wrap_rbinary_method, (operator_module.pow)
                __rsub__ = wrap_rbinary_method, (operator_module.sub)
                __rtruediv__ = wrap_rbinary_method, (operator_module.truediv)
            if inplace:
                __iadd__ = wrap_binary_method(operator_module.iadd)
                __ifloordiv__ = wrap_binary_method(operator_module.ifloordiv)
                __imod__ = wrap_binary_method(operator_module.imod)
                __imul__ = wrap_binary_method(operator_module.imul)
                __ipow__ = wrap_binary_method(operator_module.ipow)
                __isub__ = wrap_binary_method(operator_module.isub)
                __itruediv__ = wrap_binary_method(operator_module.itruediv)
            if wrap_unary_method:
                __abs__ = wrap_unary_method(getattr(operator_module, "abs", abs))
                __int__ = wrap_unary_method(getattr(operator_module, "int", int))
                __float__ = wrap_unary_method(getattr(operator_module, "float", float))
                __complex__ = wrap_unary_method(
                    getattr(operator_module, "complex", complex)
                )
                __index__ = wrap_unary_method(operator_module.index)
                __neg__ = wrap_unary_method(operator_module.neg)
                __pos__ = wrap_unary_method(operator_module.pos)

        if bitwise:
            __and__ = wrap_binary_method(operator_module.and_)
            __lshift__ = wrap_binary_method(operator_module.lshift)
            __rshift__ = wrap_binary_method(operator_module.rshift)
            __or__ = wrap_binary_method(operator_module.or_)
            __xor__ = wrap_binary_method(operator_module.xor)
            if wrap_rbinary_method:
                __rand__ = wrap_rbinary_method, (operator_module.and_)
                __rlshift__ = wrap_rbinary_method, (operator_module.lshift)
                __rrshift__ = wrap_rbinary_method, (operator_module.rshift)
                __ror__ = wrap_rbinary_method, (operator_module.or_)
                __rxor__ = wrap_rbinary_method, (operator_module.xor)
            if inplace:
                __iand__ = wrap_binary_method(operator_module.iand)
                __ilshift__ = wrap_binary_method(operator_module.ilshift)
                __ior__ = wrap_binary_method(operator_module.ior)
                __irshift__ = wrap_binary_method(operator_module.irshift)
                __ixor__ = wrap_binary_method(operator_module.ixor)
            if wrap_unary_method:
                __invert__ = wrap_unary_method(operator_module.invert)

        if logic:
            __eq__ = wrap_binary_method(operator_module.eq)
            __ge__ = wrap_binary_method(operator_module.ge)
            __gt__ = wrap_binary_method(operator_module.gt)
            __le__ = wrap_binary_method(operator_module.le)
            __lt__ = wrap_binary_method(operator_module.lt)
            __ne__ = wrap_binary_method(operator_module.ne)

        if sequence:
            __contains__ = wrap_binary_method(operator_module.contains)
            __delitem__ = wrap_binary_method(operator_module.delitem)
            __getitem__ = wrap_binary_method(operator_module.getitem)

        if wrap_unary_method:
            __hash__ = wrap_unary_method(getattr(operator_module, "hash", hash))
            __len__ = wrap_unary_method(getattr(operator_module, "len", len))
            __str__ = wrap_unary_method(getattr(operator_module, "str", str))
            __repr__ = wrap_unary_method(getattr(operator_module, "repr", repr))

    return Base


# Map symbol functions to their respective names
OP_TO_SYMBOLS: dict[Fn, str] = {
    op.invert: "~",
    op.neg: "-",
    op.pos: "+",
    op.add: "+",
    op.floordiv: "//",
    op.lshift: "<<",
    op.matmul: "@",
    op.mod: "%",
    op.mul: "*",
    op.pow: "**",
    op.rshift: ">>",
    op.sub: "-",
    op.truediv: "/",
    op.and_: "&",
    op.xor: "^ ",
    op.or_: "|",
    op.eq: "==",
    op.ge: ">=",
    op.gt: ">",
    op.le: "<=",
    op.lt: "<",
    op.ne: "!=",
}


def compile(obj) -> Fn:
    """
    Convert possible placeholder expression to callable.

    It is necessary to call this function before using placeholder
    expressions as functions.

    >>> from sidekick.lambdas import _, F
    >>> expr = 2 * _.real + 2
    >>> expr(20)               # not a function!
    (2 * _.real + 2)(20)
    >>> func = compile(expr)   # now it is callable!
    >>> func(20 + 2j)
    42

    This function is a no-op on callables.

    >>> compile(lambda x: x)(42)
    42
    """
    try:
        mk = obj.__sk_callable__
    except AttributeError:
        if callable(obj):
            return obj
        name = type(obj).__name__
        raise TypeError(f"cannot compile: {name}")
    else:
        return mk()
