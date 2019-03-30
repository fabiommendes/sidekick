from ..functools.functions import functor_map
from .base_magics import base_operator_magic


# ------------------------------------------------------------------------------
# First argument: X object
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


class X(base_operator_magic(make_op, make_rop, bitwise=False)):
    def __repr__(self):
        return 'X'

    def __call__(self, *args, **kwargs):
        return lambda x: x(*args, **kwargs)

    # attr = staticmethod(op.attrgetter)
    # method = staticmethod(op.methodcaller)


del make_op, make_rop


# ------------------------------------------------------------------------------
# Second argument: Y object
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


class Y(base_operator_magic(make_op, make_rop, bitwise=False)):
    def __repr__(self):
        return 'X'

    def __call__(self, *args, **kwargs):
        return lambda x, y: y(*args, **kwargs)


del make_op, make_rop

# ------------------------------------------------------------------------------
# Function algebra: F object
# ------------------------------------------------------------------------------
make_op = lambda op: lambda _, cte: lambda f: lambda x: op(f(x), cte)
make_rop = lambda op: lambda _, cte: lambda f: lambda x: op(cte, f(x))


class F(base_operator_magic(make_op, make_rop, bitwise=False)):
    def __repr__(self):
        return 'F'


del make_op, make_rop

# ------------------------------------------------------------------------------
# Functor application: X_i object
# ------------------------------------------------------------------------------
make_op = lambda op: lambda _, cte: lambda v: functor_map(lambda x: op(x, cte), v)
make_rop = lambda op: lambda _, cte: lambda v: functor_map(lambda x: op(cte, x), v)


class X_i(base_operator_magic(make_op, make_rop, bitwise=False)):
    def __repr__(self):
        return 'X_i'


del make_op, make_rop
