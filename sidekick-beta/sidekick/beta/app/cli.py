import sys
from typing import Any, Callable

import typer

from .function_wrapper import wrap_function
from ...contrib.render import pprint
from ...functions import pipe
from ...proxy import import_later, touch

__all__ = ["run"]
TARGET = None


def run(fn: Callable, parse_value=None, display=None):
    """
    Create a CLI app using function.

    Args:
        fn:
            Input function.
        parse_value:
            Convert string values of non-annotated functions using this
            function.
        display:
            Print the result value of function.
    """
    wrapped = wrap_function(fn, parse_value, display)
    return typer.run(wrapped)


#
# Auxiliary functions
#
def parse_value(x: str) -> Any:
    """
    Parse input value.
    """
    # noinspection PyBroadException
    try:
        return eval(x, {"__builtins__": {}})
    except Exception:
        return x


def display(x) -> None:
    """
    Display result of function computation.
    """
    if x is not None:
        return pprint(x)


def main(runner=run, pop_target=False):
    """
    Called when module is imported as __main__.
    """
    global TARGET
    if pop_target and TARGET is None:
        TARGET = sys.argv.pop(1)
    elif TARGET is None:
        TARGET = sys.argv[1]
    pipe(import_later(TARGET), touch, runner)


if __name__ == "__main__":
    main(pop_target=True)
