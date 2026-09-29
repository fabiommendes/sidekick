"""
Better representation of empty values
"""
from . import maybe as _maybe
from . import result as _result
from . import util as _util
from .functions import (args, nullable, safe, safe_block, to_maybe, to_result,
                        values)
from .maybe import Just, Maybe, Nothing
from .result import Err, Ok, Result

__author__ = "Fábio Macêdo Mendes"
__version__ = "0.1.0"
__all__ = [
    "Maybe",
    "Just",
    "Nothing",
    "Result",
    "Ok",
    "Err",
    "to_maybe",
    "to_result",
    "values",
    "args",
    "safe",
    "nullable",
    "safe_block",
]


# Patch modules with defined types. This is necessary to avoid circular imports
_util.Maybe = _result.Maybe = Maybe  # type: ignore
_util.Just = _result.Just = Just  # type: ignore
_util.Nothing = _result.Nothing = Nothing  # type: ignore
_util.Result = _maybe.Result = Result  # type: ignore
_util.Ok = _maybe.Ok = Ok  # type: ignore
_util.Err = _maybe.Err = Err  # type: ignore
