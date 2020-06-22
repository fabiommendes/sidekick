from typing import Any

from .node_base import Node
from .node_classes import NodeOrLeaf
from ..lazy import delegate_to


class SExprBase(Node):
    """
    Abstract class for S-Expressions.
    """

    __slots__ = ()
    tag: Any

    # List methods
    # append
    # clear
    # copy
    count = delegate_to("_children")
    # extend
    index = delegate_to("_children")
    # insert
    pop = delegate_to("_children")
    # remove
    reverse = delegate_to("_children")
    sort = delegate_to("_children")

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            other: SExpr
            return (
                self.tag == other.tag
                and self._attrs == other._attrs
                and self._children == other._children
            )
        return NotImplemented

    def __getitem__(self, i: int) -> NodeOrLeaf:
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

    def _repr(self, children=True):
        data = self._repr_attrs()
        if data and children:
            data += f", children={self._repr_children()}"
        elif children:
            data = self._repr_children()
        args = repr(self.tag)
        if data:
            args += ", " + data
        return f"{self.__class__.__name__}({args})"

    def copy(self):
        children = (x.copy() for x in self._children)
        new = self.__class__(self.tag, children)
        new.attrs = dict(self._attrs)
        return new


class SExpr(SExprBase):
    """
    Concrete S-Expression
    """

    __slots__ = ("tag",)

    def __init__(self, tag, children=None, **kwargs):
        self.tag = tag
        super().__init__(children, **kwargs)
