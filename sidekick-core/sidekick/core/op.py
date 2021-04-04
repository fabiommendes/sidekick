"""
fn-aware functions from the builtin operator module.
"""
import operator as _op
import re as _re
from functools import wraps as _wraps

from .functions import fn as _fn


def _fix(
    f, what, re=_re.compile(r"Same as (?P<op>.+?(?=(,|\.$| \()))(?P<tail>[.,]?.*)")
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
setitem = _fn3(_op.setitem)

# Binary operations
add = _fn2(_op.add)
and_ = _fn2(_op.and_)
concat = _fn2(_op.concat)
contains = _fn2(_op.contains)
count_of = _countOf = _fn2(_op.countOf)
delitem = _fn2(_op.delitem)
eq = _fn2(_op.eq)
floordiv = _fn2(_op.floordiv)
ge = _fn2(_op.ge)
getitem = _fn2(_op.getitem)
gt = _fn2(_op.gt)
iadd = _fn2(_op.iadd)
iand = _fn2(_op.iand)
iconcat = _fn2(_op.iconcat)
ifloordiv = _fn2(_op.ifloordiv)
ilshift = _fn2(_op.ilshift)
imod = _fn2(_op.imod)
imul = _fn2(_op.imul)
index_of = _indexOf = _fn2(_op.indexOf)
ior = _fn2(_op.ior)
ipow = _fn2(_op.ipow)
# imul.__doc__ = "Same as ``a *= b``"
# ior.__doc__ = "Same as ``a |= b``"
# ipow.__doc__ = "Same as ``a **= b``"
irshift = _fn2(_op.irshift)
is_ = _fn2(_op.is_)
is_not = _fn2(_op.is_not)
isub = _fn2(_op.isub)
itruediv = _fn2(_op.itruediv)
ixor = _fn2(_op.ixor)
le = _fn2(_op.le)
lshift = _fn2(_op.lshift)
lt = _fn2(_op.lt)
mod = _fn2(_op.mod)
mul = _fn2(_op.mul)
ne = _fn2(_op.ne)
or_ = _fn2(_op.or_)
# noinspection PyShadowingBuiltins
pow = _fn2(_op.pow)
rshift = _fn2(_op.rshift)
sub = _fn2(_op.sub)
div = truediv = _fn2(_op.truediv)
xor = _fn2(_op.xor)

#
# Reverse operators
#
radd = _fn2(_flip(_op.add))
rcontains = _fn2(_flip(_op.contains))
rcount_of = _fn2(_flip(_op.countOf))
rdelitem = _fn2(_flip(_op.delitem))
rfloordiv = _fn2(_flip(_op.floordiv))
rgetitem = _fn2(_flip(_op.getitem))
riadd = _fn2(_flip(_op.iadd))
riand = _fn2(_flip(_op.iand))
riconcat = _fn2(_flip(_op.iconcat))
rifloordiv = _fn2(_flip(_op.ifloordiv))
rilshift = _fn2(_flip(_op.ilshift))
rimod = _fn2(_flip(_op.imod))
rimul = _fn2(_flip(_op.imul))
rindex_of = _fn2(_flip(_op.indexOf))
rior = _fn2(_flip(_op.ior))
ripow = _fn2(_flip(_op.ipow))
rirshift = _fn2(_flip(_op.irshift))
risub = _fn2(_flip(_op.isub))
ritruediv = _fn2(_flip(_op.itruediv))
rixor = _fn2(_flip(_op.ixor))
rlshift = _fn2(_flip(_op.lshift))
rmod = _fn2(_flip(_op.mod))
rmul = _fn2(_flip(_op.mul))
rpow = _fn2(_flip(_op.pow))
rrshift = _fn2(_flip(_op.rshift))
rsub = _fn2(_flip(_op.sub))
rdiv = _fn2(_flip(_op.truediv))
rtruediv = _fn2(_flip(_op.truediv))
rxor = _fn2(_flip(_op.xor))

#
# Unary operators
#
# noinspection PyShadowingBuiltins
abs = _fn1(_op.abs)
index = _fn1(_op.index)
inv = _fn1(_op.inv)
invert = _fn1(_op.invert)
neg = _fn1(_op.neg)
not_ = _fn1(_op.not_)
pos = _fn1(_op.pos)
truth = _fn1(_op.truth)
matmul = _fn2(_op.matmul)
imatmul = _fn2(_op.imatmul)
length_hint = _fn(_op.length_hint)

#
# Special
#
attrgetter = _fn1(_op.attrgetter)
itemgetter = _fn1(_op.itemgetter)
methodcaller = _fn1(_op.methodcaller)

__all__ = [name for name in globals() if not name.startswith("_")]
