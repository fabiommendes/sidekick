"""
A companion library that enhance your functional superpowers.
"""
__author__ = "Fábio Macêdo Mendes"
__version__ = "0.7.0"

from . import op
from .core import *
from .functools import *
from .itertools import *
from .lazytools import *
from .magics import *
from .misc import misc
from .render import pprint, pformat
from .tree import Node, Leaf
from .tree.node_sexpr import SExpr
from .types import *
from .types import json
from . import tree


@call()
def _fix():
    # Add sidekick.json to sys.modules
    import sys

    sys.modules["sidekick.json"] = json
    return None


_ = placeholder
__all__ = ["_", *(attr for attr in globals() if not attr.startswith("_"))]
