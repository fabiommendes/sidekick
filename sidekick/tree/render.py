from typing import NamedTuple

from .node_base import NodeOrLeaf
from ..seq import uncons
from ..render import PrintContext, PrettyPrinter


class Row(NamedTuple):
    """
    Single line in a pretty printed tree representation.
    """

    pre: str
    fill: str
    node: NodeOrLeaf

    @classmethod
    def from_node(cls, node: NodeOrLeaf, style: "Style", extra=()):
        """
        Create row from node, style and extra prefix items.
        """
        if not extra:
            return Row("", "", node)
        items = [(style.vertical if cont else style.empty) for cont in extra]
        indent = "".join(items[:-1])
        branch = style.horizontal if extra[-1] else style.end
        pre = indent + branch
        fill = "".join(items)
        return Row(pre, fill, node)

    def render(self, renderer=None) -> str:
        """Render row."""
        renderer = renderer or repr_node_root
        return f"{self.pre}{renderer(self.node)}"


class Style(NamedTuple):
    """
    Style of pretty printed tree.
    """

    vertical: str = ""
    horizontal: str = ""
    end: str = ""
    empty = property(lambda self: " " * len(self.end))


def render_node(node, **kwargs):
    """
    Pretty print node.
    """
    tokens = handle_node(node, PrintContext(PrettyPrinter()), **kwargs)
    return "".join(tokens)


def handle_node(node, _ctx, tree_style="line", node_renderer=None):
    """
    Yield pretty fragments for node element.
    """
    try:
        style = STYLES[tree_style]
    except KeyError:
        style = Style(*tree_style)

    first, tail = uncons(iter_rows(node, style=style))
    yield first.render(node_renderer)
    for row in tail:
        yield "\n"
        yield row.render(node_renderer)


def iter_rows(node, style, extra=()):
    """
    Create rows from children of given node.
    """
    yield Row.from_node(node, style, extra)
    children = node.children
    if children:
        last_idx = len(children) - 1
        for idx, child in enumerate(children):
            yield from iter_rows(child, style, extra + (idx != last_idx,))


#
# Utilities
#
NodeOrLeaf._pretty_printer = staticmethod(render_node)


# noinspection PyProtectedMember
def repr_node_root(node):
    return node._repr_node()


STYLES = {
    "empty": Style(),
    "line": Style("│   ", "├── ", "└── "),  # \u2502, \u251c, \u2500, \u2514
    "round": Style("│   ", "├── ", "╰── "),  # \u2502, \u251c, \u2500, \u2570
    "ascii": Style("|   ", "|-- ", "+-- "),
    "double": Style("║   ", "╠══ ", "╚══ "),  # \u2551, \u2560, \u2550, \u255a
}
