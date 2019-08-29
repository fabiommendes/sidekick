import codecs
import json
import logging
from os import path, remove
from subprocess import check_call
from tempfile import NamedTemporaryFile

from .node_classes import Leaf
from sidekick.tree.node_base import NodeOrLeaf


# noinspection PyShadowingBuiltins
def export_tree(obj: NodeOrLeaf, file=None, format="dict", **kwargs):
    """
    Export tree to given format data source.
    """
    if format == "dict":
        return _to_dict(obj, **kwargs)
    elif format == "json":
        data = _to_dict(obj, **kwargs)
        if file:
            json.dump(data, file)
        else:
            return json.dumps(data)
    elif format == "dot":
        export = DotExporter(obj, **kwargs)
        if file:
            export.to_dotfile(file)
        else:
            return "\n".join(export)
    elif format == "image":
        export = DotExporter(obj, **kwargs)
        export.to_picture(file)
    else:
        raise ValueError(f"invalid import method: {format!r}")


def _to_dict(
    data,
    attrs=lambda x: dict(x.attrs),
    children=lambda x: list(x.children),
    compress=True,
):
    attrs_ = attrs(data)
    children_ = children(data)
    if children_:
        attrs_["children"] = [_to_dict(c, attrs, children, compress) for c in children_]
    elif isinstance(data, Leaf):
        if compress:
            return data.value
        attrs_["value"] = data.value
    return attrs_


class DotExporter(object):
    def __init__(
        self,
        node,
        graph="digraph",
        name="tree",
        options=None,
        indent=4,
        nodenamefunc=None,
        nodeattrfunc=None,
        edgeattrfunc=None,
        edgetypefunc=None,
    ):
        """
        Dot Language Exporter.

        Args:
            node (Node): start node.

        Keyword Args:
            graph: DOT graph type.

            name: DOT graph name.

            options: list of options added to the graph.

            indent (int): number of spaces for indent.

            nodenamefunc: Function to extract node name from `node` object.
                          The function shall accept one `node` object as
                          argument and return the name of it.

            nodeattrfunc: Function to decorate a node with attributes.
                          The function shall accept one `node` object as
                          argument and return the attributes.

            edgeattrfunc: Function to decorate a edge with attributes.
                          The function shall accept two `node` objects as
                          argument. The first the node and the second the child
                          and return the attributes.

            edgetypefunc: Function to which gives the edge type.
                          The function shall accept two `node` objects as
                          argument. The first the node and the second the child
                          and return the edge (i.e. '->').
        """
        self.node = node
        self.graph = graph
        self.name = name
        self.options = options
        self.indent = indent
        self.node_name = nodenamefunc or _nodenamefunc
        self.node_attr = nodeattrfunc or _nodeattrfunc
        self.edge_attr = edgeattrfunc or _edgeattrfunc
        self.edge_type = edgetypefunc or _edgetypefunc

    def __iter__(self):
        indent = " " * self.indent
        name = self.node_name
        yield f"{self.graph} {self.name} {{"
        for option in self._iter_options(indent):
            yield option
        yield from self._iter_nodes(indent, name, self.node_attr)
        yield from self._iter_edges(indent, name, self.edge_attr, self.edge_type)
        yield "}"

    def _iter_options(self, indent):
        options = self.options
        if options:
            for option in options:
                yield "%s%s" % (indent, option)

    def _iter_nodes(self, indent, nodenamefunc, nodeattrfunc):
        for node in self.node.iter_children(self=True):
            nodename = nodenamefunc(node)
            nodeattr = nodeattrfunc(node)
            nodeattr = " [%s]" % nodeattr if nodeattr is not None else ""
            yield '%s"%s"%s;' % (indent, _escape(nodename), nodeattr)

    def _iter_edges(self, indent, nodenamefunc, edgeattrfunc, edgetypefunc):
        for node in self.node.iter_children(self=True):
            nodename = nodenamefunc(node)
            for child in node.children:
                childname = nodenamefunc(child)
                edgeattr = edgeattrfunc(node, child)
                edgetype = edgetypefunc(node, child)
                edgeattr = " [%s]" % edgeattr if edgeattr is not None else ""
                yield '%s"%s" %s "%s"%s;' % (
                    indent,
                    _escape(nodename),
                    edgetype,
                    _escape(childname),
                    edgeattr,
                )

    def to_dotfile(self, filename):
        """
        Write graph to `filename`.

        The generated file should be handed over to the `dot` tool from the
        http://www.graphviz.org/ package::

            $ dot tree.dot -T png -o tree.png
        """
        with codecs.open(filename, "w", "utf-8") as file:
            for line in self:
                file.write("%s\n" % line)

    def to_picture(self, filename):
        """
        Write graph to a temporary file and invoke `dot`.

        The output file type is automatically detected from the file suffix.

        *`graphviz` needs to be installed, before usage of this method.*
        """
        fileformat = path.splitext(filename)[1][1:]
        with NamedTemporaryFile("wb", delete=False) as dotfile:
            dotfilename = dotfile.name
            for line in self:
                dotfile.write(("%s\n" % line).encode("utf-8"))
            dotfile.flush()
            cmd = ["dot", dotfilename, "-T", fileformat, "-o", filename]
            check_call(cmd)
        try:
            remove(dotfilename)
        except Exception as exc:
            msg = "Could not remove temporary file %s" % dotfilename
            logging.getLogger(__name__).warning(msg)


def _escape(st):
    """Escape Strings for Dot exporter."""
    return st.replace('"', '\\"')


def _nodenamefunc(node):
    try:
        return node.tag
    except AttributeError:
        return node._repr_node()


def _nodeattrfunc(node):
    return None


def _edgeattrfunc(node, child):
    return None


def _edgetypefunc(node, child):
    return "->"
