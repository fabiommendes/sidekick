__author__ = "Fábio Macêdo Mendes"
__version__ = "0.4.1"

try:
    import cytoolz as toolz
    import cytoolz.curried as ctoolz
except ImportError:
    import toolz  # noqa: F401
    import toolz.curried as ctoolz

map = map
filter = filter

from . import op
from .core import *
from .itertools import *
from .functools import *
from .magics import *
from .types import *
# from .lazy import *
# from .lib import *
# from .functools import *
# from .types import json
# from .union import *


# @call()
# def _fix():
#     # Add sidekick.json to sys.modules
#     import sys
#
#     sys.modules["sidekick.json"] = json
#     return None


_ = placeholder
__all__ = ["_", *(attr for attr in globals() if not attr.startswith("_"))]
