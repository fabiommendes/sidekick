import operator as op

from .node_iterators import NodeOrLeafIteratorMixin
from ...typing import Optional, Sequence, Callable


class NodeOrLeaf(NodeOrLeafIteratorMixin):
    """
    Abstract base class for leaf or node types.
    """

    __slots__ = ("_parent", "_attrs")
    _parent: Optional["Node"]
    _children: Sequence["NodeOrLeaf"]
    _pretty_printer: Callable[..., str] = None

    #: True if sub-tree cannot have children (a Leaf instance)
    is_leaf = False

    #: True for Nodes with no children.
    has_children = property(lambda self: len(self._children) == 0)

    #: Expose mapping of attributes
    attrs = property(lambda self: self._attrs)

    @attrs.setter
    def attrs(self, value):
        self._attrs.clear()
        self._attrs.update(value)

    #
    # Parent node information
    #

    #: Base node in tree.
    @property
    def root(self):
        root: NodeOrLeaf = self
        while root._parent is not None:
            root = root._parent
        return root

    #: Parent and their parents.
    ancestors = property(lambda self: self.path[:-1])

    #: Parent Node.
    parent = property(op.attrgetter("_parent"))

    @parent.setter
    def parent(self, value):
        if value is None:
            self._parent = None
        elif not isinstance(value, Node):
            raise TypeError(f"Parent node {value!r} is not of type 'Node'.")
        elif value is not self._parent:
            has_loop = (
                self.is_ancestor_of(value)
                or value.is_ancestor_of(self)
                or self is value
            )
            if has_loop:
                msg = f"Setting parent to {value} would create a dependency loop"
                raise ValueError(msg)
            self.detach()
            value.children.append(self)

    @property
    def path(self):
        """Path from root to node"""
        path = []
        node = self
        while node:
            path.append(node)
            node = node._parent
        return tuple(reversed(path))

    #
    # Children and sibling nodes
    #

    #: List of children nodes
    children = property(lambda self: self._children)

    #: Tuple of leaf nodes.
    leaves = property(lambda self: tuple(filter(lambda c: c.is_leaf, self.iter())))

    #: Children and children of children.
    descendants = property(lambda self: tuple(self.iter_descendants()))

    def _sibling(self, delta):
        if self._parent is not None:
            siblings = self._parent.children
            for idx, sibling in enumerate(siblings):
                if self is sibling:
                    try:
                        new_idx = idx + delta
                        if new_idx < 0:
                            return None
                        return siblings[new_idx]
                    except IndexError:
                        break
        return None

    #: Left siblings or None
    left_sibling = property(lambda self: self._sibling(-1))

    #: Right siblings or None
    right_sibling = property(lambda self: self._sibling(+1))

    @property
    def siblings(self):
        """
        Tuple of nodes with the same parent.
        """
        parent = self._parent
        if parent is None:
            return ()
        else:
            parent: NodeOrLeaf
            generation = parent._children
            return tuple(node for node in generation if node is not self)

    #
    # Properties of node or tree
    #

    #: Number of edges on the longest path to a leaf `Node`.
    height = property(
        lambda self: max((c.height for c in self._children), default=0) + 1
    )

    #: Number of edges to the root `Node`.
    depth = property(lambda self: len(self.path) - 1)

    #: True if node is in the base of tree.
    is_root = property(lambda self: self._parent is None)

    #: True if element defines arbitrary meta-data
    has_attrs = property(lambda self: bool(self._attrs))

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            raise NotImplementedError("must be implemented in subclass")
        return NotImplemented

    #
    # Tree shaping
    #
    def detach(self) -> "NodeOrLeaf":
        """
        Detach itself from tree.

        This method returns self, so it can be chained.
        """
        parent = self._parent
        if parent is not None:
            parent.discard_child(self)
        return self

    def is_ancestor_of(self, node) -> bool:
        """
        Check if node is an ancestor of argument.
        """
        return any(self is ancestor for ancestor in node.iter_ancestors())

    def copy(self) -> "NodeOrLeaf":
        """
        Create a copy of tree.
        """
        raise NotImplementedError

    #
    # Tree Rendering
    #
    def __repr__(self):
        return self._repr()

    def _repr(self, children=True):
        data = self._repr_attrs()
        return f"{self.__class__.__name__}({data})"

    def _repr_as_child(self):
        return self._repr()

    def _repr_attrs(self):
        return ", ".join(f"{k}={v!r}" for k, v in self._attrs.items())

    def _repr_node(self):
        """
        Simplified representation used to show element as node in a pretty
        printed tree.

        This method never show children.
        """
        return self._repr(children=False)

    def pretty(self, style="line", renderer=None) -> str:
        """
        Pretty-printed representation of tree.

        Args:
            style:
                One of 'ascii', 'line', 'rounded', or 'double'. It can also
                be a 3-string tuple with the (vertical, horizontal, end) prefixes
                for each rendered line.
            renderer:
                A function that renders row omitting its children.
        """
        return self._pretty_printer(self, tree_style=style, node_renderer=renderer)


from .node_classes import Node  # noqa: E402
