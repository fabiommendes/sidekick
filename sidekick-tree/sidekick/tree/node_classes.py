from ...typing import MutableSequence

from .children import Children
from .node_base import NodeOrLeaf


class Leaf(NodeOrLeaf):
    """
    Container element for the leaf node of tree.
    """

    __slots__ = ("_value",)
    _children = ()
    is_leaf = True
    height = 0
    value = property(lambda self: self._value)

    def __init__(self, value, *, parent=None, **kwargs):
        self._value = value
        self._attrs = kwargs
        self._parent = parent

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            other: Leaf
            return self._value == other._value
        return NotImplemented

    def __hash__(self):
        return hash(self._value)

    def _repr(self, children=True):
        data = filter(None, [repr(self._value), self._repr_attrs()])
        data = ", ".join(data)
        return f"{self.__class__.__name__}({data})"

    def _repr_node(self):
        if self.has_attrs:
            return f"{self._value!r} ({self._repr_attrs()})"
        else:
            return repr(self._value)

    def _repr_as_child(self):
        return self._repr_node()

    def copy(self):
        return type(self)(self._value, **self._attrs)


class Node(NodeOrLeaf):
    """
    Base class for all node types (including SExprs and Leaves).

    Node store a reference to its parent and children. Children can be other
    nodes or Leaves.
    """

    __slots__ = ("_children",)
    _separator = "."
    _children: MutableSequence[NodeOrLeaf]
    _leaf_class = Leaf

    def _get_children(self):
        return Children(self, self._children)

    def _set_children(self, children):
        n = len(self._children)
        try:
            for child in children:
                child.parent = self
        except Exception:
            del self._children[n:]
            raise
        else:
            del self._children[:n]

    def _del_children(self):
        for child in self._children:
            child._parent = None
        self._children.clear()

    #: All child nodes
    children = property(fget=_get_children, fset=_set_children, fdel=_del_children)
    del _get_children, _set_children, _del_children

    def __init__(self, children=(), *, parent=None, leaf_class=None, **kwargs):
        self._attrs = kwargs
        self._parent = parent
        self._children = []

        # During object creation we cannot have cycles in children since there
        # are no references to self.
        leaf_class = leaf_class or self._leaf_class
        if children:
            add = self._children.append
            for child in children:
                if isinstance(child, NodeOrLeaf):
                    child: NodeOrLeaf
                    if child._parent is not None:
                        raise TreeError("parent node already set")
                else:
                    child = leaf_class(child)

                child._parent = self
                add(child)

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            other: Node
            return self._attrs == other._attrs and self._children == other._children
        return NotImplemented

    def _repr_children(self):
        parts = []
        for child in self._children:
            parts.append(child._repr_as_child())
        parts = ", ".join(parts)
        return f"[{parts}]" if parts else ""

    def _repr(self, children=True):
        data = self._repr_attrs()
        if data and children:
            data += f", children={self._repr_children()}"
        elif children:
            data = self._repr_children()
        return f"{self.__class__.__name__}({data})"

    def _check_child(self, child):
        if not isinstance(child, Node):
            return self._leaf_class(child)
        for c in self._children:
            if c is child:
                raise ValueError("node already present in tree.")
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
                raise TreeError("child not present in tree")
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
                raise TreeError("child not present in tree")
            if append:
                self._children.append(other)
            return
        self._children[idx] = other

    def copy(self):
        children = (x.copy() for x in self._children)
        return type(self)(children, **self._attrs)


class TreeError(ValueError):
    """
    Generic tree error.
    """
