import operator as op
from typing import List, Optional

from .node_base import NodeOrLeaf
from .node_classes import Node


def common_ancestors(*nodes: NodeOrLeaf) -> List[Node]:
    """
    Determine common ancestors of all arguments.

    If arguments are not in the same tree, return an empty list.
    """
    common = []
    for parents in zip(*map(op.attrgetter("ancestors"), nodes)):
        parent = parents[0]
        if all([parent is p for p in parents[1:]]):
            common.append(parent)
        else:
            break
    return common


def common_ancestor(*nodes: NodeOrLeaf, raises=True) -> Optional[Node]:
    """
    Determine the deepest common ancestor of all arguments.
    """
    try:
        return common_ancestors(*nodes)[-1]
    except IndexError as exc:
        if raises:
            raise ValueError("not in the same tree") from exc
        return None


def walk(start, end):
    """
    Walk from `start` node to `end` node.

    Returns:
        (upwards, common, downwards): `upwards` is a list of nodes to go upward to.
        `common` top node. `downwards` is a list of nodes to go downward to.

    Raises:
        ValueError: on no common root node.
    """
    xs = start.path
    ys = end.path
    if xs[0] != ys[0]:
        raise ValueError(f"{start} and {end} are not part of the same tree.")

    common = [x for x, y in zip(xs, ys) if x is y]
    n_common = len(common)
    up = () if start is common[-1] else xs[: n_common - 1 : -1]
    down = () if end is common[-1] else ys[n_common:]
    return up, common[-1], down
