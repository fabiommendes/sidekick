from functools import wraps

from .functions import fn

BUILDING_DOCS = False


@fn
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


@fn
def snake_case(name):
    """
    Convert camel case to snake case.
    """
    return dash_case(name).replace("-", "_")


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
