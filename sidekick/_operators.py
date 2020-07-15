import operator as op

#  Lists of methods
METHODS = [op.getitem, op.contains, op.delitem, op.getitem, getattr]
UNARY = [op.abs, op.invert, op.neg, op.pos, op.index, hash, len, str, int, repr]
BINARY = [
    op.add,
    op.and_,
    op.floordiv,
    op.lshift,
    op.matmul,
    op.mod,
    op.mul,
    op.or_,
    op.pow,
    op.rshift,
    op.sub,
    op.truediv,
    op.xor,
]
COMPARISON = [op.eq, op.ge, op.gt, op.le, op.lt, op.ne]
KEYWORDS = [op.is_, op.is_not, op.not_]

# Map symbol functions to their respective names
OP_SYMBOLS = {
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

IRREGULAR = {"invert": "not"}


def normalize(name):
    if name.endswith("___"):
        return name[:-1]
    else:
        return IRREGULAR.get(name, name)


OP_NAMES = {
    **{f: normalize(f.__name__) for f in UNARY},
    **{f: normalize(f.__name__) for f in BINARY},
    **{f: normalize(f.__name__) for f in COMPARISON},
    **{f: normalize(f.__name__) for f in METHODS},
}
FROM_NAMES = {v: k for k, v in OP_NAMES.items()}
FROM_SYMBOLS = {v: k for k, v in OP_SYMBOLS.items()}


def op_wrapper_class(
    binary,
    rbinary=None,
    unary=None,
    arithmetic=True,
    bitwise=False,
    logic=True,
    inplace=True,
    sequence=True,
    operator=op,
) -> type:
    """
    Create a wrapper class that implements the given operations as a
    transformation from operator functions or equivalent.

    Args:
        binary:
            Function of operator -> method that creates binary operator.
            Operator is extracted from the given operator namespace.
        rbinary:
            Function of operator -> method that creates binary operator. For
            reversed operations (e.g., __radd__, __rmul__, etc).
        unary:
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
        operator:
            The operator namespace used to fetch operator functions that will be
            passed to constructors. Defaults to Python stdlib's operator module.
    """

    # noinspection DuplicatedCode
    class Base:
        if arithmetic:
            __add__ = binary(operator.add)
            __floordiv__ = binary(operator.floordiv)
            __mod__ = binary(operator.mod)
            __mul__ = binary(operator.mul)
            __pow__ = binary(operator.pow)
            __sub__ = binary(operator.sub)
            __truediv__ = binary(operator.truediv)
            if rbinary:
                __radd__ = rbinary(operator.add)
                __rfloordiv__ = rbinary(operator.floordiv)
                __rmod__ = rbinary(operator.mod)
                __rmul__ = rbinary(operator.mul)
                __rpow__ = rbinary(operator.pow)
                __rsub__ = rbinary(operator.sub)
                __rtruediv__ = rbinary(operator.truediv)
            if inplace:
                __iadd__ = binary(operator.iadd)
                __ifloordiv__ = binary(operator.ifloordiv)
                __imod__ = binary(operator.imod)
                __imul__ = binary(operator.imul)
                __ipow__ = binary(operator.ipow)
                __isub__ = binary(operator.isub)
                __itruediv__ = binary(operator.itruediv)
            if unary:
                __abs__ = unary(getattr(operator, "abs", abs))
                __int__ = unary(getattr(operator, "int", int))
                __neg__ = unary(operator.neg)
                __pos__ = unary(operator.pos)
                __index__ = unary(operator.index)

        if bitwise:
            __and__ = binary(operator.and_)
            __lshift__ = binary(operator.lshift)
            __rshift__ = binary(operator.rshift)
            __or__ = binary(operator.or_)
            __xor__ = binary(operator.xor)
            if rbinary:
                __rand__ = rbinary(operator.and_)
                __rlshift__ = rbinary(operator.lshift)
                __rrshift__ = rbinary(operator.rshift)
                __ror__ = rbinary(operator.or_)
                __rxor__ = rbinary(operator.xor)
            if inplace:
                __iand__ = binary(operator.iand)
                __ilshift__ = binary(operator.ilshift)
                __ior__ = binary(operator.ior)
                __irshift__ = binary(operator.irshift)
                __ixor__ = binary(operator.ixor)
            if unary:
                __invert__ = unary(operator.invert)

        if logic:
            __eq__ = binary(operator.eq)
            __ge__ = binary(operator.ge)
            __gt__ = binary(operator.gt)
            __le__ = binary(operator.le)
            __lt__ = binary(operator.lt)
            __ne__ = binary(operator.ne)

        if sequence:
            __contains__ = binary(operator.contains)
            __delitem__ = binary(operator.delitem)
            __getitem__ = binary(operator.getitem)

        if unary:
            __hash__ = unary(getattr(operator, "hash", hash))
            __len__ = unary(getattr(operator, "len", len))
            __str__ = unary(getattr(operator, "str", str))
            __repr__ = unary(getattr(operator, "repr", repr))

    return Base
