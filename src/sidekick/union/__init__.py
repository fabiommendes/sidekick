from . import utils as _utils
from .case_syntax import case, case_fn, casedispatch
from .maybe import Maybe, Just, Nothing, maybe
from .result import Result, Ok, Err, result
from .union import Union
from .list import List, linklist
from .utils import opt

_utils.Maybe = Maybe
_utils.Nothing = Nothing
_utils.Just = Just
_utils.Result = Result
_utils.Err = Err
_utils.Ok = Ok
