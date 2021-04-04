from ..functions import fmap
from ..._operators import op_wrapper_class

# ------------------------------------------------------------------------------
make_op = lambda op: lambda _, cte: lambda v: fmap(lambda x: op(x, cte), v)
make_rop = lambda op: lambda _, cte: lambda v: fmap(lambda x: op(cte, x), v)


class X_i(op_wrapper_class(make_op, make_rop, bitwise=False)):
    def __repr__(self):
        return "X_i"


del make_op, make_rop
