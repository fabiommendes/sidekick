from itertools import chain, cycle, islice
from typing import Sequence, Iterator, Callable

from ..builtins import filter as _filter

ID = lambda x: x
TRUE = lambda x: True
NOT_GIVEN = object()
INF = float("inf")
Nodes = Sequence["WithChildren"]
NodesIter = Iterator["WithChildren"]
SeqFn = Callable[[NodesIter], Nodes]


class NodeOrLeafIteratorMixin:
    """
    Isolate implementation of methods that iterate over children nodes.
    """

    __slots__ = ()
    _children: Sequence["NodeOrLeafIteratorMixin"]
    _parent: "NodeOrLeafIteratorMixin"

    def iter_ancestors(self):
        """
        Iterate over ancestors of node.
        """
        root: NodeOrLeafIteratorMixin = self._parent
        while root is not None:
            yield root
            root = root._parent

    # noinspection PyMethodParameters
    def iter_children(
        node, how=None, *, self=None, leaves=None, nodes=None, **kwargs
    ) -> NodesIter:
        """
        Iterate over child nodes.

        Args:
            how (str):
                Method used to iterate over children.
                'level-order':
                    Breath-first strategy: yield all nodes of the same level
                    sequentially.
                'pre-order':
                    Depth-first strategy. Yield each node followed by its
                    descendents.
                'post-order':
                    Depth-first strategy. Yield descendents followed by node.
                'in-order':
                    Depth-first strategy. Yield left descendants, node, then
                    right descendants. Usually relevant only to binary trees.
                'out-order':
                    Depth-first strategy. Yield right descendants, node, then
                    left descendants. Usually relevant only to binary trees.
            self (bool):
                Control if current node is returned in the output or not.
            leaves (bool):
                If True, return only leaves.
            nodes (bool):
                If True, return only nodes.
            keep (callable):
                Optional callable that select which nodes should be selected for
                iteration. A node that keep(node) == False is not included in
                the result as all of its children.
            max_depth (int):
                Maximum depth of iteration. If given, return nodes only up to
                the given depth.
        """
        if leaves is not None and nodes is not None:
            raise TypeError("cannot set both leaves and nodes at the same time.")

        if how is None and not kwargs:
            data = node._iter_children_simple(self)
        else:
            try:
                how = how or "pre-order"
                attr = how.replace("-", "_")
                method = getattr(node, f"_iter_children_{attr}")
            except AttributeError as exc:
                msg = f"invalid iteration method: {how}"
                raise ValueError(msg) from exc
            data = method(self, **kwargs)

        if leaves is True:
            data = filter(lambda x: x.is_leaf, data)
        elif nodes is True:
            data = filter(lambda x: not x.is_leaf, data)

        return data

    # noinspection PyMethodParameters
    def iter_group(node, how=None, *, self=None, **kwargs) -> Iterator[Nodes]:
        """
        Group iterator over groups of child nodes.
        """
        try:
            how = how or "level-order"
            attr = how.replace("-", "_")
            method = getattr(node, f"_iter_group_{attr}")
        except AttributeError as exc:
            msg = f"invalid iteration method: {how}"
            raise ValueError(msg) from exc
        return method(self, **kwargs)

    def _iter_children_simple(self, yield_self):
        if yield_self:
            yield self
        for child in self._children:
            yield from child._iter_children_simple(True)

    def _iter_children_level_order(self, this, keep=TRUE, max_depth=INF):
        if not keep(self) or max_depth == 0:
            return

        children = self._keep(keep, self._children)
        if this:
            yield self
        while children and max_depth > 0:
            yield from children
            # noinspection PyProtectedMember
            level = chain(*(child._children for child in children))
            children = list(self._keep(keep, level))
            max_depth -= 1

    def _iter_children_pre_order(self, this, keep=TRUE, max_depth=INF):
        if not keep(self) or max_depth < 0:
            return
        if this:
            yield self
        for child in self._children:
            yield from child._iter_children_pre_order(True, keep, max_depth - 1)

    def _iter_children_post_order(self, this, keep=TRUE, max_depth=INF):
        if not keep(self) or max_depth < 0:
            return
        for child in self._children:
            yield from child._iter_children_post_order(True, keep, max_depth - 1)
        if this:
            yield self

    def _iter_children_in_order(self, this, keep=TRUE, max_depth=INF):
        if not keep(self) or max_depth < 0:
            return

        children: Sequence[NodeOrLeafIteratorMixin] = self._children
        if children:
            lhs: NodeOrLeafIteratorMixin
            lhs, *children = children
            yield from lhs._iter_children_in_order(True, keep, max_depth - 1)
        if this is not False:
            yield self
        for child in children:
            yield from child._iter_children_in_order(True, keep, max_depth - 1)

    def _iter_children_out_order(self, this, keep=TRUE, max_depth=INF):
        if not keep(self) or max_depth < 0:
            return

        children: Sequence[NodeOrLeafIteratorMixin] = self._children
        if children:
            rhs: NodeOrLeafIteratorMixin
            *children, rhs = children
            yield from rhs._iter_children_out_order(True, keep, max_depth - 1)
        if this is not False:
            yield self
        for child in children:
            yield from child._iter_children_out_order(True, keep, max_depth - 1)

    def _iter_group_level_order(
        self, this, keep=TRUE, max_depth=INF, seq: SeqFn = tuple
    ):
        if not keep(self) or max_depth == 0:
            return
        if this:
            yield seq([self])

        children = seq(self._keep(keep, self._children))
        while children and max_depth > 0:
            yield children
            # noinspection PyProtectedMember
            level = chain(*(child._children for child in children))
            children = seq(self._keep(keep, level))
            max_depth -= 1

    def _iter_group_zig_zag(self, this, keep=TRUE, max_depth=INF, seq=tuple):
        groups = self._iter_group_level_order(this, keep, max_depth, seq)
        for group, zig in zip(groups, cycle([True, False])):
            yield group if zig else group[::-1]

    @staticmethod
    def _keep(keep, lst: NodesIter) -> Nodes:
        return lst if keep is TRUE else list(filter(keep, lst))

    #
    # Query nodes
    #
    # noinspection PyIncorrectDocstring
    def find_all(*self_and_filter, min_count=0, max_count=INF, **kwargs):
        """
        Search nodes matching `filter`.

        Return tuple with matching nodes.

        Args:
            filter:
                Discard nodes that filter(node) = False, but iterate over its
                children.
            min_count (int):
                Minimum number of nodes.
            max_count (int):
                Maximum number of nodes.
        Keyword Args:
            Accepts all arguments of :meth:`iter_children`
        """
        node, *pred = self_and_filter
        data = node.iter_children(**kwargs)
        if pred:
            (pred,) = pred
            data = _filter(pred, data)

        data = tuple(data)
        size = len(data)
        if size < min_count:
            msg = f"Expecting at least {min_count} elements, but found {size}."
            raise ValueError(msg)
        if size > max_count:
            msg = f"Expecting {max_count} elements at maximum, but found {size}."
            raise ValueError(msg)
        return data

    def find(*self_and_filter, default=NOT_GIVEN, **kwargs):
        """
        Like find_all(), but searches for *single* matching node.

        It raises a ValueError if no Node is found or return the value passed
        as the "default" keyword argument.
        """
        node, *pred = self_and_filter
        data = node.iter_children(**kwargs)
        if pred:
            (pred,) = pred
            data = _filter(pred, data)

        try:
            (node,) = islice(data, 1)
            return node
        except ValueError as exc:
            if default is NOT_GIVEN:
                raise ValueError("no element found") from exc
            return default
