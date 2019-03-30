from . import data_magics as _data
from . import argument_magics as _args
from .list_magic import L as _LType
from .seq_magic import N as _NType

# Argument magics
X = _args.X()
Y = _args.Y()
X_i = _args.X_i()
F = _args.F()

# Sequence type
N = _NType()

# Data magics
L = _LType()
D = _data.D()
S = _data.S()
B = _data.B()
T = _data.T()
