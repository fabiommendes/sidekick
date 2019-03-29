"""
fn-aware functions from the builtin operator module.
"""
import operator as op

from .core import fn as _fn

_fn3 = _fn.annotate(3)
_fn2 = _fn.annotate(2)
_fn1 = _fn.annotate(1)

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
index_of = _indexOf = _fn2(op.indexOf)
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
# noinspection PyShadowingBuiltins
pow = _fn2(op.pow)
rshift = _fn2(op.rshift)
sub = _fn2(op.sub)
div = truediv = _fn2(op.truediv)
xor = _fn2(op.xor)

#
# Unary operators
#
# noinspection PyShadowingBuiltins
abs = _fn1(op.abs)
attrgetter = _fn1(op.attrgetter)
index = _fn1(op.index)
inv = _fn1(op.inv)
invert = _fn1(op.invert)
itemgetter = _fn1(op.itemgetter)
methodcaller = _fn1(op.methodcaller)
neg = _fn1(op.neg)
not_ = _fn1(op.not_)
pos = _fn1(op.pos)
truth = _fn1(op.truth)

# Methods for Python 3.5+
if hasattr(op, "matmul"):
    matmul = _fn2(op.matmul)
    imatmul = _fn2(op.imatmul)

if hasattr(op, "length_hint"):
    length_hint = _fn(op.length_hint)

del _fn, _fn1, _fn2, _fn3, op
