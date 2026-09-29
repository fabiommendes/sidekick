from __future__ import annotations
import operator
from typing import cast, Any, Callable as Fn

from .base import Placeholder
from .util import a, BinOp


Num = int | float | complex
X_op = Fn[[Any, a | "_X"], Fn[[a], a]]
Y_op = Fn[[Any, a | "_X"], Fn[[a, a], a]]
X_unary = Fn[[Any], Fn[[a], a]]
Y_unary = Fn[[Any], Fn[[a, a], a]]


def x_op(op: BinOp[a]) -> X_op[a]:
    def func(_, other):
        if other is X:
            return lambda x: op(x, x)
        elif other is Y:
            return lambda x, y: op(x, y)
        else:
            return lambda x: op(x, other)

    return func


def x_op_simple(op: BinOp[a]) -> Fn[[Any, a], Fn[[a], a]]:
    return lambda _, other: lambda x: op(x, other)


def x_rop(op: BinOp[a]) -> Fn[[Any, a], Fn[[a], a]]:
    return lambda _, value: lambda x: op(value, x)


def x_unary(op: Fn[[a], a]) -> X_unary[a]:
    return lambda _: op


def y_op(op: BinOp[a]) -> Fn[[Any, a], BinOp[a]]:
    def func(_, other):
        if other is X:
            return lambda x, y: op(y, x)
        elif other is Y:
            return lambda x, y: op(y, y)
        else:
            return lambda x, y: op(y, other)

    return func


def y_rop(op: BinOp[a]) -> Fn[[Any, a], BinOp[a]]:
    return lambda _, value: lambda _, y: op(value, y)


def y_unary(op) -> Fn[[Any], BinOp[a]]:
    return lambda _: lambda _, y: op(y)


class _X(Placeholder):
    def __sk_callable__(self):
        return lambda x: x

    def __repr__(self):
        return "X"

    def __call__(self, *args, **kwargs):
        return lambda x: x(*args, **kwargs)

    def __getattr__(self, attr):
        return operator.attrgetter(attr)

    # FIXME: more flexible annotations
    __add__ = cast(X_op[Num], x_op(operator.add))
    __floordiv__ = cast(X_op[Num], x_op(operator.floordiv))
    __mod__ = cast(X_op[Num], x_op(operator.mod))
    __mul__ = cast(X_op[Num], x_op(operator.mul))
    __pow__ = cast(X_op[Num], x_op(operator.pow))
    __sub__ = cast(X_op[Num], x_op(operator.sub))
    __truediv__ = cast(X_op[Num], x_op(operator.truediv))

    # FIXME: more strict annotations
    __neg__ = cast(X_unary[Any], x_unary(operator.neg))
    __pos__ = cast(X_unary[Any], x_unary(operator.pos))

    __radd__ = x_rop(operator.add)
    __rfloordiv__ = x_rop(operator.floordiv)
    __rmod__ = x_rop(operator.mod)
    __rmul__ = x_rop(operator.mul)
    __rpow__ = x_rop(operator.pow)
    __rsub__ = x_rop(operator.sub)
    __rtruediv__ = x_rop(operator.truediv)

    __and__ = x_op(operator.and_)
    __lshift__ = x_op(operator.lshift)
    __rshift__ = x_op(operator.rshift)
    __or__ = x_op(operator.or_)
    __xor__ = x_op(operator.xor)
    __rand__ = x_rop(operator.and_)
    __rlshift__ = x_rop(operator.lshift)
    __rrshift__ = x_rop(operator.rshift)
    __ror__ = x_rop(operator.or_)
    __rxor__ = x_rop(operator.xor)
    __invert__ = cast(X_unary[Any], x_unary(operator.invert))

    __eq__ = x_op(operator.eq)  # type: ignore[assignment]
    __ge__ = x_op(operator.ge)
    __gt__ = x_op(operator.gt)
    __le__ = x_op(operator.le)
    __lt__ = x_op(operator.lt)
    __ne__ = x_op(operator.ne)  # type: ignore[assignment]

    def __contains__(self, other):
        return lambda x: other in x

    def __getitem__(self, item):
        return lambda x: x[item]

    # There are no operators associated with those
    # __abs__ = ...
    # __int__ = ...
    # __float__ = ...
    # __complex__ = ...
    # __index__ = ...
    # __delitem__ = ...


class _Y(Placeholder):  # type: ignore
    def __sk_callable__(self):
        return lambda x, y: y

    def __repr__(self):
        return "Y"

    def __call__(self, x, y):
        return y

    def __getattr__(self, attr):
        return lambda x, y: getattr(y, attr)

    # FIXME: more flexible annotations
    __add__ = cast(Y_op[Num], y_op(operator.add))
    __floordiv__ = cast(Y_op[Num], y_op(operator.floordiv))
    __mod__ = cast(Y_op[Num], y_op(operator.mod))
    __mul__ = cast(Y_op[Num], y_op(operator.mul))
    __pow__ = cast(Y_op[Num], y_op(operator.pow))
    __sub__ = cast(Y_op[Num], y_op(operator.sub))
    __truediv__ = cast(Y_op[Num], y_op(operator.truediv))

    # FIXME: more strict annotations
    __neg__ = cast(X_unary[Any], y_unary(operator.neg))
    __pos__ = cast(X_unary[Any], y_unary(operator.pos))

    __radd__ = y_rop(operator.add)
    __rfloordiv__ = y_rop(operator.floordiv)
    __rmod__ = y_rop(operator.mod)
    __rmul__ = y_rop(operator.mul)
    __rpow__ = y_rop(operator.pow)
    __rsub__ = y_rop(operator.sub)
    __rtruediv__ = y_rop(operator.truediv)

    __and__ = y_op(operator.and_)
    __lshift__ = y_op(operator.lshift)
    __rshift__ = y_op(operator.rshift)
    __or__ = y_op(operator.or_)
    __xor__ = y_op(operator.xor)
    __rand__ = y_rop(operator.and_)
    __rlshift__ = y_rop(operator.lshift)
    __rrshift__ = y_rop(operator.rshift)
    __ror__ = y_rop(operator.or_)
    __rxor__ = y_rop(operator.xor)
    __invert__ = cast(X_unary[Any], y_unary(operator.invert))

    __eq__ = y_op(operator.eq)  # type: ignore[assignment]
    __ge__ = y_op(operator.ge)
    __gt__ = y_op(operator.gt)
    __le__ = y_op(operator.le)
    __lt__ = y_op(operator.lt)
    __ne__ = y_op(operator.ne)  # type: ignore[assignment]

    def __contains__(self, other):
        return lambda _, y: other in y

    def __getitem__(self, item):
        return lambda _, y: y[item]


class _M(Placeholder):
    def __repr__(self):
        return "M"

    def __call__(self, *args, **kwargs):
        return lambda fn: fn(*args, **kwargs)

    def __getattr__(self, attr):
        return lambda *args, **kwargs: operator.methodcaller(attr, *args, **kwargs)


X = _X()
Y = _Y()
M = _M()
