from .fn import fn
from . import bare_functions as _

const = fn(_.const)
identity = fn(_.identity)
construct = fn(_.construct)
flip = fn(_.flip)

del fn