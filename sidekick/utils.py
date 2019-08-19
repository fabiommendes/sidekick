from .core import fn


# ------------------------------------------------------------------------------
# Random utility functions
# ------------------------------------------------------------------------------

# STRING/TEXT PROCESSING =======================================================
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
