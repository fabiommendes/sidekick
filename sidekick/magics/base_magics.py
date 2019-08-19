import operator

from ..core import fn


# ------------------------------------------------------------------------------
# DATA MAGICS
# ------------------------------------------------------------------------------

class DataMagicMeta(type):
    def __new__(mcs, name, bases, ns, *, type=None):
        if type is not None:
            ns = dict(default_namespace(type), **ns)
            meta = ns.get('_meta', {})
            for method in meta.get('methods', ()):
                ns.update(method(type, ns))

        return super().__new__(mcs, name, bases, ns)

    __init__ = lambda *args, **kwargs: None


#
# Factory functions
#
def default_namespace(tt):
    def pipe(self, obj):
        try:
            return tt(obj)
        except TypeError:
            return self.coerce(obj)

    ns = {'type': tt, '__ror__': pipe, '__lt__': pipe}
    return ns


@fn.curry(3)
def pure(name, type, ns, *, arity=None, flip=False):
    base = impure(name, type, ns, arity=arity, flip=flip)
    return base


@fn.curry(3)
def impure(name, tt, ns, *, arity=None, flip=False):
    method = getattr(tt, name)
    if name in ns:
        raise TypeError(f'function already registered: {name}')

    if flip and arity is None:
        arity = 2

    # Simple methods. Just call the inner function
    if arity == 1:
        func = fn.wraps(method, method)

    # Implement methods of arbitrary arity
    elif arity is not None:
        @staticmethod
        @fn.wraps(method)
        @fn.curry(arity)
        def func(*args, **kwargs):
            if len(args) != arity:
                raise TypeError
            args = args[::-1] if flip else args
            obj = args[0]
            if isinstance(obj, type):
                return method(*args, **kwargs)
            else:
                action = getattr(obj, name)
                return action(*args[1:], **kwargs)

    else:
        raise ValueError(name)

    return {name: func}


#
# Base class
#
class DataMagic(metaclass=DataMagicMeta, type=None):
    def coerce(self, obj):
        """Coerce argument to the magic object expected type."""
        if isinstance(obj, self.type):
            return obj
        else:
            return self.convert(obj)

    def convert(self, obj):
        return self.type(obj)


# ------------------------------------------------------------------------------
# OPERATOR BASED MAGICS
# ------------------------------------------------------------------------------
def base_operator_magic(make_op, make_rop=None, arithmetic=True, bitwise=False,
                        logic=True, inplace=True, sequence=True, op=operator):

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

    return Base
