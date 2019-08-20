import operator as op
from typing import MutableSequence, List, Sequence, TypeVar, Optional, Iterator, Callable

T = TypeVar('T')


class NodeOrLeaf:
    """
    Abstract base class for leaf or node types.
    """
    __slots__ = ("_parent", "__dict__")
    _parent: Optional['Node']
    _children: Sequence['NodeOrLeaf']
    _pretty_printer: Callable[..., str] = None

    #
    # Parent node information
    #

    #: Base node in tree.
    @property
    def root(self):
        root = self
        while root._parent is not None:
            root = root._parent
        return root

    #: Parent and their parents.
    ancestors = property(lambda self: self.path[:-1])

    #: Parent Node.
    parent = property(op.attrgetter('_parent'))

    @parent.setter
    def parent(self, value):
        if value is None:
            self._parent = None
        elif not isinstance(value, Node):
            raise TypeError(f"Parent node {value!r} is not of type 'Node'.")
        elif value is not self._parent:
            if self.is_ancestor_of(value) or value.is_ancestor_of(self) or self is value:
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
        if self._parent is None:
            return ()
        else:
            return tuple(node for node in self._parent._children if node is not self)

    #
    # Properties of node or tree
    #

    #: Number of edges on the longest path to a leaf `Node`.
    height = property(lambda self: max((c.height for c in self._children), default=0) + 1)

    #: Number of edges to the root `Node`.
    depth = property(lambda self: len(self.path) - 1)

    #: True for Nodes with no children.
    is_leaf = property(lambda self: len(self._children) == 0)

    #: True if node is in the base of tree.
    is_root = property(lambda self: self._parent is None)

    #: True if element defines arbitrary meta-data
    has_data = property(lambda self: bool(self.__dict__))

    def __init__(self, *, parent=None, **kwargs):
        self.__dict__ = {}
        self.__dict__.update(kwargs)
        self._parent = parent

    def __repr__(self):
        return self._repr(parent=False)

    def _repr_data(self):
        return self._repr(parent=False, children=False)

    def _repr(self, parent=True, children=True):
        data = self._repr_meta(parent)
        return f'{self.__class__.__name__}({data})'

    def _repr_meta(self, parent=True):
        parts = [f'parent={self._parent!r}' if parent and self._parent else '',
                 ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())]
        return ', '.join(filter(None, parts))

    #
    # Tree shaping
    #
    def detach(self) -> 'NodeOrLeaf':
        """
        Detach itself from tree.

        This method returns self, so it can be chained.
        """
        parent = self._parent
        if parent is not None:
            parent.discard_child(self)
        return self

    #
    # Iterators
    #
    def iter_ancestors(self):
        """
        Iterate over ancestors of node.
        """
        root = self._parent
        while root is not None:
            yield root
            root = root._parent

    def iter_children(self, how='dfs', **kwargs) -> Iterator['NodeOrLeaf']:
        """
        Iterate over child nodes.
        """
        try:
            method = getattr(self, f'_iter_children_{how}')
        except AttributeError as exc:
            msg = f'invalid iteration method: {how}'
            raise ValueError(msg) from exc
        else:
            return method(**kwargs)

    # noinspection PyMethodParameters
    def _iter_children_dfs(node, self=False):
        if self:
            yield node
        for child in node._children:
            yield from child._iter_children_dfs(True)

    #
    # Api
    #
    def is_ancestor_of(self, node):
        """
        Check if node is an ancestor of argument.
        """
        return any(self is ancestor for ancestor in node.iter_ancestors())

    def pretty(self, style='line', renderer=None) -> str:
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


class Leaf(NodeOrLeaf):
    """
    Container element for the leaf node of tree.
    """
    __slots__ = ('value',)
    _children = ()
    is_leaf = True
    height = 0

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def _repr(self, parent=True, children=True):
        data = filter(None, [repr(self.value), self._repr_meta(parent)])
        data = ', '.join(data)
        return f'{self.__class__.__name__}({data})'

    def _repr_data(self):
        if self.has_data:
            return f'{self.value!r} ({self._repr_meta(parent=False)})'
        else:
            return repr(self.value)


class Node(NodeOrLeaf):
    """
    Base class for all node types (including SExprs and Leaves).

    Node store a reference to its parent and children. Children can be other
    nodes or Leaves.
    """
    __slots__ = ("_children",)
    _separator = "."
    _children: List[NodeOrLeaf]

    #: All child nodes
    children = property(lambda self: Children(self, self._children))

    @children.deleter
    def children(self):
        for child in self.children:
            child.parent = None
        assert len(self.children) == 0

    @children.setter
    def children(self, children):
        # convert iterable to tuple
        children = tuple(children)
        old_children = self.children
        self._children.clear()
        try:
            for child in children:
                child.parent = self
            assert len(self.children) == len(children)
        except Exception:
            self._children[:] = old_children
            raise

    def __init__(self, children=(), *, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self._children = []

        # During object creation we cannot have cycles in children since there
        # are no references to self.
        if children:
            add = self._children.append
            for child in children:
                if isinstance(child, NodeOrLeaf):
                    child: NodeOrLeaf
                    if child._parent is not None:
                        raise TreeError("parent node already set")
                else:
                    child = Leaf(child)

                child._parent = self
                add(child)

    def _repr_children(self):
        parts = []
        for child in self._children:
            if isinstance(child, Leaf) and not child.has_data:
                parts.append(repr(child.value))
            else:
                parts.append(child._repr(False))
        parts = ', '.join(parts)
        return f'[{parts}]' if parts else ''

    def _repr(self, parent=True, children=True):
        data = self._repr_meta(parent)
        if data and children:
            data += f', children={self._repr_children()}'
        elif children:
            data = self._repr_children()
        return f'{self.__class__.__name__}({data})'

    def _check_child(self, child):
        if not isinstance(child, Node):
            return Leaf(child)
        for c in self._children:
            if c is child:
                raise ValueError('node already present in tree.')
        return child

    #
    # Children control
    #
    def discard_child(self, child, raises=False):
        """
        Discard child if present in tree.
        """
        for idx, elem in self._children:
            if elem is child:
                break
        else:
            if raises:
                raise TreeError('child not present in tree')
            return
        del self._children[idx]

    def replace_child(self, child, other, raises=False, append=False):
        """
        Replace element for child.
        """
        other.parent = self
        for idx, elem in self._children:
            if elem is child:
                break
        else:
            if raises:
                raise TreeError('child not present in tree')
            if append:
                self._children.append(other)
            return
        self._children[idx] = other


class SExpr(Node, Sequence):
    """
    Generic S-Expression
    """
    __slots__ = ('tag',)

    def __init__(self, tag, children=None, parent=None, **kwargs):
        self.tag = tag
        super().__init__(children, parent=parent, **kwargs)

    def __getitem__(self, i: int) -> T:
        if isinstance(i, int):
            if i == 0 or i == len(self._children):
                return self.tag
            if i > 0:
                return self._children[i - 1]
            else:
                return self._children[i]

    def __len__(self) -> int:
        return len(self._children) + 1

    def __iter__(self):
        yield self.tag
        yield from self._children

    def _repr(self, parent=True, children=True):
        data = self._repr_meta(parent)
        if data and children:
            data += f', children={self._repr_children()}'
        elif children:
            data = self._repr_children()
        args = repr(self.tag)
        if data:
            args += ', ' + data
        return f'{self.__class__.__name__}({args})'


class TreeError(ValueError):
    """
    Generic tree error.
    """


class Children(MutableSequence):
    """
    List of children nodes of tree.
    """

    __slots__ = ('_owner', '_data')
    _data: List[NodeOrLeaf]
    _owner: Node

    def __init__(self, owner, data):
        self._data = data
        self._owner = owner

    def __getitem__(self, i):
        return self._data[i]

    def __setitem__(self, i: int, obj: T) -> None:
        if isinstance(i, int):
            obj = self._owner._check_child(obj)
        elif isinstance(i, slice):
            obj = [self._owner._check_child(node) for node in obj]
        else:
            raise TypeError(f'invalid index: {i.__class__.__name__}')
        self._data[i] = obj

    def __delitem__(self, i):
        data = self[i]
        if isinstance(data, Node):
            data._parent = None
        else:
            for node in data:
                node._parent = None
        del self._data[i]

    def __len__(self) -> int:
        return len(self._data)

    def insert(self, index: int, obj: T) -> None:
        obj = self._owner._check_child(obj)
        self._data.insert(index, obj)
