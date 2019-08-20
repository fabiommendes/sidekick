import operator as op
from typing import List, Optional

from .node import Node, NodeOrLeaf


def common_ancestors(*nodes: NodeOrLeaf) -> List[Node]:
    """
    Determine common ancestors of all arguments.

    If arguments are not in the same tree, return an empty list.
    """
    common = []
    for parents in zip(*map(op.attrgetter('ancestors'), nodes)):
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
            raise ValueError('not in the same tree') from exc
        return None
