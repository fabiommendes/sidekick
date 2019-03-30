from . import data_magics as _data
from .argument_magic import X as _XType, Y as _YType
from .list_magic import L as _LType
from .seq_magic import N as _NType

# Argument magics
X = _XType()
Y = _YType()

# Sequence type
N = _NType()

# Data magics
L = _LType()
D = _data.D()
S = _data.S()
B = _data.B()
T = _data.T()
