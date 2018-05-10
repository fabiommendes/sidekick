"""
fn-aware functions from the builtin operator module.
"""
import operator as op
from .fn import fn

abs = fn(op.abs)
add = fn(op.add)
and_ = fn(op.and_)
attrgetter = fn(op.attrgetter)
concat = fn(op.concat)
contains = fn(op.contains)
countOf = fn(op.countOf)
delitem = fn(op.delitem)
eq = fn(op.eq)
floordiv = fn(op.floordiv)
ge = fn(op.ge)
getitem = fn(op.getitem)
gt = fn(op.gt)
iadd = fn(op.iadd)
iand = fn(op.iand)
iconcat = fn(op.iconcat)
ifloordiv = fn(op.ifloordiv)
ilshift = fn(op.ilshift)
imod = fn(op.imod)
imul = fn(op.imul)
index = fn(op.index)
indexOf = fn(op.indexOf)
inv = fn(op.inv)
invert = fn(op.invert)
ior = fn(op.ior)
ipow = fn(op.ipow)
irshift = fn(op.irshift)
is_ = fn(op.is_)
is_not = fn(op.is_not)
isub = fn(op.isub)
itemgetter = fn(op.itemgetter)
itruediv = fn(op.itruediv)
ixor = fn(op.ixor)
le = fn(op.le)
lshift = fn(op.lshift)
lt = fn(op.lt)
methodcaller = fn(op.methodcaller)
mod = fn(op.mod)
mul = fn(op.mul)
ne = fn(op.ne)
neg = fn(op.neg)
not_ = fn(op.not_)
or_ = fn(op.or_)
pos = fn(op.pos)
pow = fn(op.pow)
rshift = fn(op.rshift)
setitem = fn(op.setitem)
sub = fn(op.sub)
truediv = fn(op.truediv)
truth = fn(op.truth)
xor = fn(op.xor)

# Methods for Python 3.5+
if hasattr(op, 'matmul'):
    matmul = fn(op.matmul)
    imatmul = fn(op.imatmul)

if hasattr(op, 'length_hint'):
    length_hint = fn(op.length_hint)

del fn, op
