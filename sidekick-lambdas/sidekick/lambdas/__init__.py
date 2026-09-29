"""
Better representation of empty values
"""
from .placeholder import placeholder, F
from .quick_lambda import X, Y, M
from .base import Placeholder, compile

__author__ = "Fábio Macêdo Mendes"
__version__ = "0.1.0"
__all__ = ["placeholder", "_", "F", "M", "X", "Y", "Placeholder", "compile"]
_ = placeholder
