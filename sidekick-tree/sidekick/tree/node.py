from __future__ import annotations
import abc

from typing import (
    Collection,
    Iterator,
    Sequence,
    Callable,
    TypeVar,
    overload,
    TYPE_CHECKING,
)
import weakref
from functools import reduce
from sidekick.seq import first


T = TypeVar("T")
D = TypeVar("D")
S = TypeVar("S")
DataTree = tuple[T, list["DataTree"]]


class INode(Collection[T], abc.ABC):
    """
    Abstract protocol for node types.

    - T is the type of the Payload of each node in the tree.
    """

    __slots__ = ()

    #
    # Attributes
    #

    #: Payload stored in node
    data: T

    #: Parent node. None if it is root or if it does not
    #: hold reference to parent
    parent: INode[T] | None

    #: Sequence of child nodes. Ideally sequence should be
    #: reverse-iterable. It is a good idea to protect the children
    #: to avoid direct mutation that can lead to inconsistent states.
    children: Sequence[INode[T]]

    #: The left sibling, if it exists.
    left_sibling: INode[T] | None

    #: The right sibling, if it exists.
    right_sibling: INode[T] | None

    #: Root node of tree. Return itself, if it is root node.
    root: INode[T]

    #: Number of edges on the longest path to a leaf node.
    height: int

    #: Number of edges to the root node.
    depth: int

    #
    # Properties methods
    #
    if not TYPE_CHECKING:

        @property
        def root(self):
            return reduce(lambda _, y: y, self.iter_ancestors(), self)

        @property
        def depth(self):
            return sum(1 for _ in self.iter_ancestors())

        @property
        def height(self):
            return max((n.height for n in self.children), default=-1) + 1

        @property
        def left_sibling(self):
            return first(self.iter_left_siblings(), default=None)

        @property
        def right_sibling(self):
            return first(self.iter_right_siblings(), default=None)

    #
    # Constructors
    #
    @classmethod
    def from_data_tree(
        cls, tree: DataTree[T], parent: INode[T] | None = None
    ) -> INode[T]:
        """
        A convenient constructor for trees based on data.

        Each data point is a 2-tuple with (data, children)

        Example:
            tree = Tree.from_tree(
                [ "root"
                , [ [ "child1"
                    , [ "leaf1"
                      , "leaf2"
                      ]
                    ]
                , [ "child2"
                  , [ [ "grandchild2"
                      , ["leaf3"]
                      ]
                    , "leaf"
                    ]
                  ]
                ]
            )
        """
        data, children_data = tree
        root = cls.from_data(data)
        for child_data in children_data:
            child = cls.from_data_tree(child_data, parent=root)
            root.append_child(child)
        return root

    @classmethod
    def from_data(cls, data: T, *, parent: INode[T] | None = None) -> INode[T]:
        """
        Create empty node from data.
        """
        raise NotImplementedError

    #
    # Dunder methods
    #
    @abc.abstractmethod
    def __contains__(self, node):
        "Check if node is descendent of self."

        try:
            get_ancestors = node.iter_ancestors
        except AttributeError:
            return False
        else:
            return any(n is self for n in get_ancestors())

    #
    # Tree Rendering
    #
    def __repr__(self) -> str:
        name = type(self).__name__
        args = []

        if self.data:
            args.append(repr(self.data))

        if self.parent is not None:
            args.append("parent=<...>")

        if self.children:
            children = ", ".join(n.__repr_simple__() for n in self.iter_children())
            args.append(f"children=[{children}]")

        rendered_args = ", ".join(args)
        return f"{name}({rendered_args})"

    def __repr_simple__(self) -> str:
        raise NotImplementedError

    #
    # Iterators
    #
    def iter_ancestors(self) -> Iterator[INode[T]]:
        """
        Iterate over all ancestors, starting with parent up to root node.
        """
        while (parent := self.parent) is not None:
            yield parent

    def iter_descendants(self) -> Iterator[INode[T]]:
        """
        Iterate over all descendants, depth first.
        """
        for child in self.iter_children():
            yield from child.iter_descendants()

    def iter_leaves(self) -> Iterator[INode[T]]:
        """
        Iterate over descendants, yielding only leaf nodes.
        """
        return (n for n in self.iter_descendants() if not n)

    @abc.abstractclassmethod
    def iter_children(self) -> Iterator[INode[T]]:
        """
        Iterate over children
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def iter_siblings(self) -> Iterator[INode[T]]:
        """
        Iterate over all siblings, including self.
        """
        raise NotImplementedError

    def iter_left_siblings(self) -> Iterator[INode[T]]:
        """
        Iterate over all siblings before self.
        """
        seq = self.iter_siblings()
        to_left = []
        for x in seq:
            if x is self:
                break
            else:
                to_left.append(x)
        yield from to_left

    def iter_right_siblings(self) -> Iterator[INode[T]]:
        """
        Iterate over all siblings right of self.
        """
        seq = self.iter_siblings()
        for x in seq:
            if x is self:
                break
        yield from seq

    #
    # Tree shaping
    #
    def append_child(self, node: INode[T]) -> None:
        """
        Add child to node.
        """
        n = sum(1 for _ in self.iter_children())
        self.insert_child(n, node)

    @abc.abstractmethod
    def insert_child(self, idx: int, node: INode[T]) -> None:
        """
        Insert child at specific location.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def insert_left_sibling(self, node: INode[T]) -> None:
        """
        Insert sibling to the left of self.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def insert_right_sibling(self, node: INode[T]) -> None:
        """
        Insert sibling to the right of self.
        """
        raise NotImplementedError

    def detach(self) -> None:
        """
        Detach itself from tree and disconnect all children.

        Raise ValueError, if it cannot be removed.
        """
        if (parent := self.parent) is not None:
            parent.remove_child(self)

    def remove(self, node: INode[T]) -> None:
        """
        Remove node and its children from tree.

        If successful, the argument will be the root of a separate tree.

        Raise ValueError, if node is not present in tree or cannot be removed.
        """
        if (parent := node.parent) is None:
            raise ValueError
        if parent is self or parent in self:
            parent.remove_child(node)

    @abc.abstractmethod
    def remove_child(self, node: INode[T]) -> Node:
        """
        Remove a direct children.
        """

    #
    # Transformations
    #
    @abc.abstractmethod
    def with_data(self, data: S) -> INode[S]:
        """
        Return a shallow copy of self, replacing the data content..
        """
        raise NotImplementedError

    def copy(self, deep: bool = False) -> INode[T]:
        """
        Return a shallow copy of self.

        Do not copy children or parent.
        """
        return self.with_data(self.data)

    def deepcopy(self):
        """
        Copy node and all its children.
        """
        new = self.copy(self)
        for child in self.iter_children():
            new.append_child(child.copy(deep=True))
        return new

    def map(self, func: Callable[[INode[T]], INode[T]]) -> INode[T]:
        """
        Create new tree with function applied to all nodes.
        """
        raise NotImplementedError

    def map_data(self, func: Callable[[T], S]) -> INode[S]:
        """
        Create new tree mapping function in the payload of all elements.
        """
        new = self.with_data(func(self.data))
        for n in self.iter_children():
            child = n.map_data(func)
            new.append_child(child)
        return new

    #
    # Generic methods
    #
    @overload
    def path(self, key: Callable[[INode[T]], S]) -> list[S]:
        ...

    @overload
    def path(self) -> list[INode[T]]:
        ...

    def path(self, key=lambda x: x):
        """
        Path from root to node.

        By default, return a list of ancestors from root to self, inclusive.
        If a key function is given, it is used to compute the path fragment to
        each node, i.e., ``node.path(key) ~= map(key, node.path())``.
        """
        path = []
        node = self
        while node:
            path.append(key(node))
            node = node.parent
        path.reverse()
        return path


class WithParentMixin(INode[T], abc.ABC):
    """
    Mixin class for implementations that have an explicit ``.parent`` reference.
    """

    __slots__ = ("_parent",)
    _parent: weakref.ReferenceType[INode[T]]

    @property  # type: ignore
    def parent(self) -> INode[T] | None:
        return self._parent()

    @parent.setter
    def parent(self, parent: INode[T]) -> None:
        if parent is None:
            self._parent = None
        elif self._parent() is not parent:
            if parent in self or self in parent:
                msg = f"Setting parent to {parent} would create a dependency loop"
                raise ValueError(msg)
            self._parent = weakref.ref(parent)

    def __init__(self, parent=None):
        self._parent = lambda: None
        if parent is not None:
            self.parent = parent


class LinkTree(INode[T]):
    __slots__ = ("_parent", "_left", "_right", "_first_child", "_last_child")

    def __init__(self, data, parent=None):
        self._parent = parent
        self._left = None
        self._right = None
        self._first_child = None
        self._last_child = None


class VecTree(INode[T]):
    pass


class Node(INode[T]):
    """
    Abstract base class for leaf or node types.
    """

    #
    # Parent node information
    #

    #: Parent Node.

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
