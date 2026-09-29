import operator as op
import re
from functools import wraps as _wraps
from typing import Any, List, Dict, Callable, Union

from .fn import fn as _fn


BinaryOp = Callable[[Any, Any], Any]
UnaryOp = Callable[[Any], Any]
Op = Union[BinaryOp, UnaryOp]


def _normalize_operator_name(op: Op, irregular={"invert": "not"}) -> str:
    name: str = op.__name__
    if name.endswith("___"):
        return name[:-1]
    else:
        return irregular.get(name, name)


# =============================================================================
# Register and classify operators
# =============================================================================

#: Special methods (__getitem__, __getattr__, etc) as operators
METHODS: List[Callable] = [
    op.getitem,
    op.contains,
    op.delitem,
    op.getitem,
    getattr,
]

#: Unary operators (+, -, etc) and sometimes unary methods
#: such as __bool__, __int__, __index__, etc
UNARY: List[UnaryOp] = [
    op.abs,
    op.invert,
    op.neg,
    op.pos,
    op.index,
    op.not_,
    hash,
    len,
    str,
    int,
    bool,
    repr,
]

#: Tradicional arithmetic and bitwise binary operators
ARITHMETIC_BINARY: List[BinaryOp] = [
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
COMPARISON: List[BinaryOp] = [
    op.eq,
    op.ge,
    op.gt,
    op.le,
    op.lt,
    op.ne,
    op.is_,
    op.is_not,
]

# Map symbol functions to their respective names
OP_TO_SYMBOLS: Dict[Op, str] = {
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

OP_TO_NAMES: Dict[Op, str] = {
    **{f: _normalize_operator_name(f) for f in UNARY},
    **{f: _normalize_operator_name(f) for f in ARITHMETIC_BINARY},
    **{f: _normalize_operator_name(f) for f in COMPARISON},
    **{f: _normalize_operator_name(f) for f in METHODS},
}
OP_FROM_NAMES: Dict[str, Op] = {v: k for k, v in OP_TO_NAMES.items()}
OP_FROM_SYMBOLS: Dict[str, Op] = {v: k for k, v in OP_TO_SYMBOLS.items()}


# =============================================================================
# Operator wrapping base class
# =============================================================================
def operator_wrapping_base(
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

    # noinspection DuplicatedCode
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


# =============================================================================
# fn-aware functions from the builtin operator module.
# =============================================================================
def _fix(
    f, what, re=re.compile(r"Same as (?P<op>.+?(?=(,|\.$| \()))(?P<tail>[.,]?.*)")
):
    out = _wraps(f)(what)
    if out.__doc__:
        doc = out.__doc__.strip().rstrip(".") + "."
        m = re.match(doc)
        if m:
            op, tail = m.group("op", "tail")
            out.__doc__ = f"Same as ``{op}``{tail}"
    return out


_fn3 = lambda f: _fix(f, _fn.curry(3)(f))
_fn2 = lambda f: _fix(f, _fn.curry(2)(f))
_fn1 = lambda f: _fix(f, _fn(f))
_flip = lambda f: lambda x, y: f(y, x)

#
# Ternary operators
#
setitem = _fn3(op.setitem)

# Binary operations
add = _fn2(op.add)
and_ = _fn2(op.and_)
concat = _fn2(op.concat)
contains = _fn2(op.contains)
count_of = _countOf = _fn2(op.countOf)
delitem = _fn2(op.delitem)
eq = _fn2(op.eq)
floordiv = _fn2(op.floordiv)
ge = _fn2(op.ge)
getitem = _fn2(op.getitem)
gt = _fn2(op.gt)
iadd = _fn2(op.iadd)
iand = _fn2(op.iand)
iconcat = _fn2(op.iconcat)
ifloordiv = _fn2(op.ifloordiv)
ilshift = _fn2(op.ilshift)
imod = _fn2(op.imod)
imul = _fn2(op.imul)
index_of = indexOf = _fn2(op.indexOf)
ior = _fn2(op.ior)
ipow = _fn2(op.ipow)
irshift = _fn2(op.irshift)
is_ = _fn2(op.is_)
is_not = _fn2(op.is_not)
isub = _fn2(op.isub)
itruediv = _fn2(op.itruediv)
ixor = _fn2(op.ixor)
le = _fn2(op.le)
lshift = _fn2(op.lshift)
lt = _fn2(op.lt)
mod = _fn2(op.mod)
mul = _fn2(op.mul)
ne = _fn2(op.ne)
or_ = _fn2(op.or_)
pow = _fn2(op.pow)  # noinspection PyShadowingBuiltins
rshift = _fn2(op.rshift)
sub = _fn2(op.sub)
div = truediv = _fn2(op.truediv)
xor = _fn2(op.xor)

#
# Reverse operators
#
radd = _fn2(_flip(op.add))
rcontains = _fn2(_flip(op.contains))
rcount_of = _fn2(_flip(op.countOf))
rdelitem = _fn2(_flip(op.delitem))
rfloordiv = _fn2(_flip(op.floordiv))
rgetitem = _fn2(_flip(op.getitem))
riadd = _fn2(_flip(op.iadd))
riand = _fn2(_flip(op.iand))
riconcat = _fn2(_flip(op.iconcat))
rifloordiv = _fn2(_flip(op.ifloordiv))
rilshift = _fn2(_flip(op.ilshift))
rimod = _fn2(_flip(op.imod))
rimul = _fn2(_flip(op.imul))
rindex_of = _fn2(_flip(op.indexOf))
rior = _fn2(_flip(op.ior))
ripow = _fn2(_flip(op.ipow))
rirshift = _fn2(_flip(op.irshift))
risub = _fn2(_flip(op.isub))
ritruediv = _fn2(_flip(op.itruediv))
rixor = _fn2(_flip(op.ixor))
rlshift = _fn2(_flip(op.lshift))
rmod = _fn2(_flip(op.mod))
rmul = _fn2(_flip(op.mul))
rpow = _fn2(_flip(op.pow))
rrshift = _fn2(_flip(op.rshift))
rsub = _fn2(_flip(op.sub))
rdiv = _fn2(_flip(op.truediv))
rtruediv = _fn2(_flip(op.truediv))
rxor = _fn2(_flip(op.xor))

#
# Unary operators
#
abs = _fn1(op.abs)  # noinspection PyShadowingBuiltins
index = _fn1(op.index)
inv = _fn1(op.inv)
invert = _fn1(op.invert)
neg = _fn1(op.neg)
not_ = _fn1(op.not_)
pos = _fn1(op.pos)
truth = _fn1(op.truth)
matmul = _fn2(op.matmul)
imatmul = _fn2(op.imatmul)
length_hint = _fn(op.length_hint)

#
# Special
#
attrgetter = _fn1(op.attrgetter)
itemgetter = _fn1(op.itemgetter)
methodcaller = _fn1(op.methodcaller)

del op, re, Any, List, Dict, Callable, Union
__all__ = [name for name in globals() if not name.startswith("_")]
