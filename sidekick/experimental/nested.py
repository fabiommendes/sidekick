from collections import deque

from sidekick import generator
from ..functions import fn, to_callable
from ..typing import Seq, Pred, Func, Seq

SEQ_TYPES = (list, tuple, Seq)
is_seqcont = lambda x: isinstance(x, SEQ_TYPES)

__all__ = ["flatten", "tree_leaves", "tree_nodes"]


@fn.curry(1)
@generator
def deep_flatten(seq: Seq, *, follow: Pred = is_seqcont) -> Seq:
    """
    Flattens arbitrary nested sequence of values and other sequences.

    Second argument determines whether to unpack each item.

    By default it dives into lists, tuples and iterators, see is_seqcont() for further
    explanation.
    """
    follow = to_callable(follow)
    for x in seq:
        if follow(x):
            yield from flatten(x)
        else:
            yield x


@fn.generator
def flatten(seq: Seq) -> Seq:
    """
    Flattens one level of a sequence of sequences.

    Examples:
        >>> flatten([[1, 2], [3, 4]) | L
        [1, 2, 3, 4]
    """
    for sub in seq:
        yield from sub


# Adapted from funcy
@fn.generator
def tree_leaves(root: Seq, *, follow: Pred = is_seqcont, children: Func = iter) -> Seq:
    """
    A way to list or iterate over all the tree leaves.

    Args:
        root:
            The nested data structure
        follow:
            A predicate function that decides if a child node should be
            yielded or if it should follow its children.
        children:
            A function to extract the children from the current node.
    """
    follow = to_callable(follow)
    children = to_callable(children)
    q = deque([[root]])
    while q:
        node_iter = iter(q.pop())
        for sub in node_iter:
            if follow(sub):
                q.append(node_iter)
                q.append(children(sub))
                break
            else:
                yield sub


@fn.curry(1)
@generator
def tree_nodes(root: Seq, follow: Pred = is_seqcont, children: Func = iter) -> Seq:
    """
    A way to list or iterate over all the tree nodes.

    This iterator includes both leaf nodes and branches.
    """
    follow = to_callable(follow)
    children = to_callable(children)
    q = deque([[root]])
    while q:
        node_iter = iter(q.pop())
        for sub in node_iter:
            yield sub
            if follow(sub):
                q.append(node_iter)
                q.append(children(sub))
                break
