"""Node Searching."""

from .iterators import PreOrderIter


def findall(node, filter=None, *, stop=None, maxlevel: int = None, mincount: int = None,
            maxcount: int = None):
    """
    Search nodes matching `filter` but stop at `maxlevel` or `stop`.

    Return tuple with matching nodes.

    Args:
        node:
            top node, start searching.
        filter:
            function called with every `node` as argument, `node` is returned if `True`.
        stop:
            stop iteration at `node` if `stop` function returns `True` for `node`.
        maxlevel (int):
            maximum decending in the node hierarchy.
        mincount (int):
            minimum number of nodes.
        maxcount (int):
            maximum number of nodes.
    """
    result = tuple(PreOrderIter(node, filter, stop, maxlevel))
    n_result = len(result)
    if mincount is not None and n_result < mincount:
        msg = f"Expecting at least {mincount} elements, but found {n_result}."
        raise CountError(msg, result)
    if maxcount is not None and n_result > maxcount:
        msg = f"Expecting {maxcount} elements at maximum, but found {n_result}."
        raise CountError(msg, result)
    return result


def findall_by_attr(
        node, value, name: str = "name", maxlevel: int = None, mincount: int = None,
        maxcount: int = None
):
    """
    Search nodes with attribute `name` having `value` but stop at `maxlevel`.

    Return tuple with matching nodes.

    Args:
        node:
            top node, start searching.
        value:
            value which need to match
        name (str):
            attribute name need to match
        maxlevel (int):
            maximum decending in the node hierarchy.
        mincount (int):
            minimum number of nodes.
        maxcount (int):
            maximum number of nodes.
    """
    return findall(
        node,
        filter=lambda n: _filter_by_name(n, name, value),
        maxlevel=maxlevel,
        mincount=mincount,
        maxcount=maxcount,
    )


def find(node, filter=None, stop=None, maxlevel: int = None):
    """
    Search for *single* node matching `filter` but stop at `maxlevel` or `stop`.

    Return matching node.

    Args:
        node:
            top node, start searching.
        filter:
            function called with every `node` as argument, `node` is returned if `True`.
        stop:
            stop iteration at `node` if `stop` function returns `True` for `node`.
        maxlevel (int):
            maximum decending in the node hierarchy.
    """
    items = findall(node, filter, stop=stop, maxlevel=maxlevel, maxcount=1)
    return items[0] if items else None


def find_by_attr(node, value, name="tag", maxlevel: int = None):
    """
    Search for *single* node with attribute `name` having `value` but stop at `maxlevel`.

    Return tuple with matching nodes.

    Args:
        node: top node, start searching.
        value: value which need to match

    Keyword Args:
        name (str): attribute name need to match
        maxlevel (int): maximum decending in the node hierarchy.

    """
    fn = (lambda n: _filter_by_name(n, name, value))
    return find(node, filter=fn, maxlevel=maxlevel)


def _filter_by_name(node, name, value):
    try:
        return getattr(node, name) == value
    except AttributeError:
        return False


class CountError(ValueError):
    def __init__(self, msg, result):
        """Error raised on `mincount` or `maxcount` mismatch."""
        if result:
            msg += " " + repr(result)
        super(CountError, self).__init__(msg)
