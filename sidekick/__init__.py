"""
A companion library that enhance your functional superpowers.

Code overview:

All modules starting with a leading underscore are meant to be for internal use
and are either used internally or used to populate `sidekick.api`. Sometimes they
contain non-public implementations of functions and types that may be later be
exposed either by wrapping in a sidekick fn() or generator() functions or
are re-exported from a proper location.
"""
__author__ = "Fábio Macêdo Mendes"
__version__ = "0.8.0"

from . import op
from ._placeholder import _ as placeholder
from .api import *
from .functools import *
from .lazy import *
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
