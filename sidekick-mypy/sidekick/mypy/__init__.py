"""
Better representation of empty values
"""

# flake8: noqa

__author__ = "Fábio Macêdo Mendes"
__version__ = "0.1.0"


from .core_functions import (
    to_fn,
    to_function,
    to_callable,
    quick_fn,
    signature,
    arity,
    declaration as stub,
)
from .fn import fn, wrap_fn_functions
from .empty import empty

__all__ = [
    "to_fn",
    "to_function",
    "to_callable",
    "quick_fn",
    "signature",
    "arity",
    "stub",
    "fn",
    "wrap_fn_functions",
    "empty",
]
