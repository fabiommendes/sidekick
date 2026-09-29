# flake8: noqa
from .anonymous_record import record, namespace
from .maybe import Maybe, Just, Nothing, to_maybe, mapply, mfilter, mpipe, mpipeline
from .named_record import Record, Namespace
from .result import Result, Ok, Err, to_result, rapply, rpipe, rpipeline, first_error
from .union import Union, Case, union

__version__ = "0.1"

__all__ = [
    "Case",
    "Err",
    "Just",
    "Maybe",
    "Namespace",
    "Nothing",
    "Ok",
    "Record",
    "Result",
    "Union",
    "first_error",
    "mapply",
    "mfilter",
    "mpipe",
    "mpipeline",
    "namespace",
    "rapply",
    "record",
    "rpipe",
    "rpipeline",
    "to_maybe",
    "to_result",
    "union",
]
