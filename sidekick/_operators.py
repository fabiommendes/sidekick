import operator
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
SYMBOLS = {
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


NAMES = {
    **{f: normalize(f.__name__) for f in UNARY},
    **{f: normalize(f.__name__) for f in BINARY},
    **{f: normalize(f.__name__) for f in COMPARISON},
    **{f: normalize(f.__name__) for f in METHODS},
}


def op_wrapper_class(
    make_op,
    make_rop=None,
    unary_op=None,
    arithmetic=True,
    bitwise=False,
    logic=True,
    inplace=True,
    sequence=True,
    op=operator,
):
    # noinspection DuplicatedCode
    class Base:
        if arithmetic:
            __add__ = make_op(op.add)
            __floordiv__ = make_op(op.floordiv)
            __mod__ = make_op(op.mod)
            __mul__ = make_op(op.mul)
            __pow__ = make_op(op.pow)
            __sub__ = make_op(op.sub)
            __truediv__ = make_op(op.truediv)
            if make_rop:
                __radd__ = make_rop(op.add)
                __rfloordiv__ = make_rop(op.floordiv)
                __rmod__ = make_rop(op.mod)
                __rmul__ = make_rop(op.mul)
                __rpow__ = make_rop(op.pow)
                __rsub__ = make_rop(op.sub)
                __rtruediv__ = make_rop(op.truediv)
            if inplace:
                __iadd__ = make_op(op.iadd)
                __ifloordiv__ = make_op(op.ifloordiv)
                __imod__ = make_op(op.imod)
                __imul__ = make_op(op.imul)
                __ipow__ = make_op(op.ipow)
                __isub__ = make_op(op.isub)
                __itruediv__ = make_op(op.itruediv)
            if unary_op:
                __abs__ = unary_op(getattr(op, "abs", abs))
                __int__ = unary_op(getattr(op, "int", int))
                __neg__ = unary_op(op.neg)
                __pos__ = unary_op(op.pos)
                __index__ = unary_op(op.index)

        if bitwise:
            __and__ = make_op(op.and_)
            __lshift__ = make_op(op.lshift)
            __rshift__ = make_op(op.rshift)
            __or__ = make_op(op.or_)
            __xor__ = make_op(op.xor)
            if make_rop:
                __rand__ = make_rop(op.and_)
                __rlshift__ = make_rop(op.lshift)
                __rrshift__ = make_rop(op.rshift)
                __ror__ = make_rop(op.or_)
                __rxor__ = make_rop(op.xor)
            if inplace:
                __iand__ = make_op(op.iand)
                __ilshift__ = make_op(op.ilshift)
                __ior__ = make_op(op.ior)
                __irshift__ = make_op(op.irshift)
                __ixor__ = make_op(op.ixor)
            if unary_op:
                __invert__ = unary_op(op.invert)

        if logic:
            __eq__ = make_op(op.eq)
            __ge__ = make_op(op.ge)
            __gt__ = make_op(op.gt)
            __le__ = make_op(op.le)
            __lt__ = make_op(op.lt)
            __ne__ = make_op(op.ne)

        if sequence:
            __contains__ = make_op(op.contains)
            __delitem__ = make_op(op.delitem)
            __getitem__ = make_op(op.getitem)

        if unary_op:
            __hash__ = unary_op(getattr(op, "hash", hash))
            __len__ = unary_op(getattr(op, "len", len))
            __str__ = unary_op(getattr(op, "str", str))
            __repr__ = unary_op(getattr(op, "repr", repr))

    return Base
