import operator as op


# ------------------------------------------------------------------------------
# First argument
# ------------------------------------------------------------------------------

def make_op(op):
    def operator(_, other):
        if isinstance(other, X):
            return lambda x: op(x, x)
        elif isinstance(other, Y):
            return lambda x, y: op(x, y)
        else:
            return lambda x: op(x, other)

    return operator


make_rop = lambda op: lambda _, value: lambda x: op(value, x)


class X:
    def __repr__(self):
        return 'X'

    # Arithmetic
    __add__ = make_op(op.add)
    __floordiv__ = make_op(op.floordiv)
    __mod__ = make_op(op.mod)
    __mul__ = make_op(op.mul)
    __pow__ = make_op(op.pow)
    __sub__ = make_op(op.sub)
    __truediv__ = make_op(op.truediv)

    # Bitwise?
    # __and__ = make_op(op.and_)
    # __lshift__ = make_op(op.lshift)
    # __rshift__ = make_op(op.rshift)
    # __or__ = make_op(op.or_)
    # __xor__ = make_op(op.xor)
    # __rand__ = make_rop(op.and_)
    # __rlshift__ = make_rop(op.lshift)
    # __rrshift__ = make_rop(op.rshift)
    # __ror__ = make_rop(op.or_)
    # __rxor__ = make_rop(op.xor)

    # Reversed
    __radd__ = make_rop(op.add)
    __rfloordiv__ = make_rop(op.floordiv)
    __rmod__ = make_rop(op.mod)
    __rmul__ = make_rop(op.mul)
    __rpow__ = make_rop(op.pow)
    __rsub__ = make_rop(op.sub)
    __rtruediv__ = make_rop(op.truediv)

    # Logic
    __eq__ = make_op(op.eq)
    __ge__ = make_op(op.ge)
    __gt__ = make_op(op.gt)
    __le__ = make_op(op.le)
    __lt__ = make_op(op.lt)
    __ne__ = make_op(op.ne)

    # Sequence
    __contains__ = make_op(op.contains)
    __delitem__ = make_op(op.delitem)
    __getitem__ = make_op(op.getitem)

    # Inplace
    __iadd__ = make_op(op.iadd)
    __iand__ = make_op(op.iand)
    __ifloordiv__ = make_op(op.ifloordiv)
    __ilshift__ = make_op(op.ilshift)
    __imod__ = make_op(op.imod)
    __imul__ = make_op(op.imul)
    __ior__ = make_op(op.ior)
    __ipow__ = make_op(op.ipow)
    __irshift__ = make_op(op.irshift)
    __isub__ = make_op(op.isub)
    __itruediv__ = make_op(op.itruediv)
    __ixor__ = make_op(op.ixor)

    def __call__(self, *args, **kwargs):
        return lambda f: f(*args, **kwargs)

    # attr = staticmethod(op.attrgetter)
    # method = staticmethod(op.methodcaller)


del make_op, make_rop


# ------------------------------------------------------------------------------
# Second argument
# ------------------------------------------------------------------------------


def make_op(op):
    def operator(_, other):
        if isinstance(other, X):
            return lambda x, y: op(y, x)
        elif isinstance(other, Y):
            return lambda x, y: op(y, y)
        else:
            return lambda x, y: op(y, other)

    return operator


make_rop = lambda op: lambda _, value: lambda x, y: op(value, y)


class Y:
    def __repr__(self):
        return 'Y'

    # Arithmetic
    __add__ = make_op(op.add)
    __floordiv__ = make_op(op.floordiv)
    __mod__ = make_op(op.mod)
    __mul__ = make_op(op.mul)
    __pow__ = make_op(op.pow)
    __sub__ = make_op(op.sub)
    __truediv__ = make_op(op.truediv)

    # Bitwise?
    # __and__ = make_op(op.and_)
    # __lshift__ = make_op(op.lshift)
    # __rshift__ = make_op(op.rshift)
    # __or__ = make_op(op.or_)
    # __xor__ = make_op(op.xor)
    # __rand__ = make_rop(op.and_)
    # __rlshift__ = make_rop(op.lshift)
    # __rrshift__ = make_rop(op.rshift)
    # __ror__ = make_rop(op.or_)
    # __rxor__ = make_rop(op.xor)

    # Reversed
    __radd__ = make_rop(op.add)
    __rfloordiv__ = make_rop(op.floordiv)
    __rmod__ = make_rop(op.mod)
    __rmul__ = make_rop(op.mul)
    __rpow__ = make_rop(op.pow)
    __rsub__ = make_rop(op.sub)
    __rtruediv__ = make_rop(op.truediv)

    # Logic
    __eq__ = make_op(op.eq)
    __ge__ = make_op(op.ge)
    __gt__ = make_op(op.gt)
    __le__ = make_op(op.le)
    __lt__ = make_op(op.lt)
    __ne__ = make_op(op.ne)

    # Sequence
    __contains__ = make_op(op.contains)
    __delitem__ = make_op(op.delitem)
    __getitem__ = make_op(op.getitem)

    # Inplace
    __iadd__ = make_op(op.iadd)
    __iand__ = make_op(op.iand)
    __ifloordiv__ = make_op(op.ifloordiv)
    __ilshift__ = make_op(op.ilshift)
    __imod__ = make_op(op.imod)
    __imul__ = make_op(op.imul)
    __ior__ = make_op(op.ior)
    __ipow__ = make_op(op.ipow)
    __irshift__ = make_op(op.irshift)
    __isub__ = make_op(op.isub)
    __itruediv__ = make_op(op.itruediv)
    __ixor__ = make_op(op.ixor)

    def __call__(self, *args, **kwargs):
        return lambda f: f(*args, **kwargs)

    # attr = staticmethod(op.attrgetter)
    # method = staticmethod(op.methodcaller)


del make_op, make_rop
