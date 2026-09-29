import os
import sys
import json
from functools import cached_property, singledispatch
from typing import Any, Callable, Optional, IO, NoReturn
from pprint import pprint

Parser = Callable[[str], Any]
Display = Callable[[Any, IO], NoReturn]


class Config:
    @cached_property
    def envfile(self):
        return None

    def __init__(self):
        self.data = {}

    def get_config(self, key, eval=False, path=False):
        ...

    def get_fn(self, fn, key):
        ...

    def get_arg(self, arg, key):
        ...


def parse_input(x: str) -> Any:
    """
    Parse input value.
    """
    if not isinstance(x, str):
        return x
    try:
        return eval(x, {"__builtins__": {}})
    except BaseException:
        return x


@singledispatch
def display_result(x: Any, file=sys.stdout):
    """
    Display result of function computation.
    """
    if x is not None:
        pprint(x, stream=file)
