import re
from functools import wraps
from typing import Any

from sidekick.typing import Raisable, Catchable

SPACES = re.compile(r"\s+")
BUILDING_DOCS = False


def dash_case(name):
    """
    Convert a camel case string to dash case.

    Example:
        >>> dash_case('SomeName')
        'some-name'
    """
    letters = []
    for c in name:
        if c.isupper() and letters and letters[-1] != "-":
            letters.append("-" + c.lower())
        else:
            letters.append(c.lower())
    return "".join(letters)


def snake_case(name):
    """
    Convert camel case to snake case.
    """
    return dash_case(name).replace("-", "_")


def indent(ind, st) -> str:
    """
    Indent string.
    """

    if isinstance(ind, int):
        ind = " " * ind
    return ind.join(st.splitlines(True))


def dedent(st) -> str:
    """
    Dedent string.
    """
    st = st.strip()
    lines = [ln.strip() for ln in st.splitlines()]
    matches = filter(
        None, (SPACES.match(ln) for ln in lines if not SPACES.fullmatch(ln))
    )
    indent = max([0, *map(lambda m: m.span()[1], matches)])
    if not indent:
        return st

    out = []
    for ln in lines:
        if SPACES.fullmatch(ln):
            out.append("")
        else:
            out.append(ln[indent:])
    return "\n".join(out)


def function_in_docs(fn):
    """
    Convert function-like objects to functions to make sphinx understand
    them correctly.
    """
    if BUILDING_DOCS:

        @wraps(fn)
        def function(*args, **kwargs):
            return fn(*args, **kwargs)

        return function
    return fn


def building_docs():
    """
    Activated when building documentation.
    """
    global BUILDING_DOCS
    BUILDING_DOCS = True


def coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg


def safe_repr(x):
    """
    A repr() that never fails, even if object has some bad implementation.
    """
    try:
        return repr(x)
    except:
        name = getattr(type(x), "__name__", "object")
        return f"<{name} instance>"


def is_raisable(obj) -> bool:
    """
    Test if object is valid in a "raise obj" statement.
    """

    return isinstance(obj, Exception) or (
        isinstance(obj, type) and issubclass(obj, Exception)
    )


def is_catchable(obj) -> bool:
    """
    Check if object is valid in a "except obj" statement.
    """

    if isinstance(obj, tuple):
        return all(isinstance(x, type) and issubclass(x, Exception) for x in obj)
    return isinstance(obj, type) and issubclass(obj, Exception)


def to_raisable(obj: Any, exception=ValueError) -> Raisable:
    """
    Wrap object in exception if object is not valid in a "raise obj" statement.
    """

    if not is_raisable(obj):
        return exception(obj)
    return obj


def catches(raisable: Raisable, catchable: Catchable):
    """
    Tests if raisable value would be catchable by catchable value.
    """
    if isinstance(catchable, type):
        catchable = [catchable]

    if isinstance(raisable, type):
        return any(issubclass(raisable, exc) for exc in catchable)
    else:
        return any(isinstance(raisable, exc) for exc in catchable)
