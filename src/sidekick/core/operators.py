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
