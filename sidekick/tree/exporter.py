import codecs
import json
import logging
from os import path, remove
from subprocess import check_call
from tempfile import NamedTemporaryFile

from sidekick.tree import PreOrderIter


class DictExporter(object):
    def __init__(self, dictcls=dict, attriter=None, childiter=list):
        """
        Tree to dictionary exporter.

        Every node is converted to a dictionary with all instance
        attributes as key-value pairs.
        Child nodes are exported to the children attribute.
        A list of dictionaries.

        Keyword Args:
            dictcls: class used as dictionary. :any:`dict` by default.
            attriter: attribute iterator for sorting and/or filtering.
            childiter: child iterator for sorting and/or filtering.

        >>> from pprint import pprint  # just for nice printing
        >>> from ox.tree import AnyNode
        >>> from ox.tree.exporter import DictExporter
        >>> root = AnyNode(a="root")
        >>> s0 = AnyNode(a="sub0", parent=root)
        >>> s0a = AnyNode(a="sub0A", b="foo", parent=s0)
        >>> s0b = AnyNode(a="sub0B", parent=s0)
        >>> s1 = AnyNode(a="sub1", parent=root)

        >>> exporter = DictExporter()
        >>> pprint(exporter.export(root))  # order within dictionary might vary!
        {'a': 'root',
         'children': [{'a': 'sub0',
                       'children': [{'a': 'sub0A', 'b': 'foo'}, {'a': 'sub0B'}]},
                      {'a': 'sub1'}]}

        Pythons dictionary `dict` does not preserve order.
        :any:`collections.OrderedDict` does.
        In this case attributes can be ordered via `attriter`.

        >>> from collections import OrderedDict
        >>> exporter = DictExporter(dictcls=OrderedDict, attriter=sorted)
        >>> pprint(exporter.export(root))
        OrderedDict([('a', 'root'),
                     ('children',
                      [OrderedDict([('a', 'sub0'),
                                    ('children',
                                     [OrderedDict([('a', 'sub0A'), ('b', 'foo')]),
                                      OrderedDict([('a', 'sub0B')])])]),
                       OrderedDict([('a', 'sub1')])])])

        The attribute iterator `attriter` may be used for filtering too.
        For example, just dump attributes named `a`:

        >>> exporter = DictExporter(attriter=lambda attrs: [(k, v) for k, v in attrs if k == "a"])
        >>> pprint(exporter.export(root))
        {'a': 'root',
         'children': [{'a': 'sub0', 'children': [{'a': 'sub0A'}, {'a': 'sub0B'}]},
                      {'a': 'sub1'}]}

        The child iterator `childiter` can be used for sorting and filtering likewise:

        >>> exporter = DictExporter(childiter=lambda children: [child for child in children if "0" in child.a])
        >>> pprint(exporter.export(root))
        {'a': 'root',
         'children': [{'a': 'sub0',
                       'children': [{'a': 'sub0A', 'b': 'foo'}, {'a': 'sub0B'}]}]}
        """
        self.dictcls = dictcls
        self.attriter = attriter
        self.childiter = childiter

    def export(self, node):
        """Export tree starting at `node`."""
        attriter = self.attriter or (lambda attr_values: attr_values)
        return self.__export(node, self.dictcls, attriter, self.childiter)

    def __export(self, node, dictcls, attriter, childiter):
        attr_values = attriter(self._iter_attr_values(node))
        data = dictcls(attr_values)
        children = [
            self.__export(child, dictcls, attriter, childiter)
            for child in childiter(node.children)
        ]
        if children:
            data["children"] = children
        return data

    def _iter_attr_values(self, node):
        return node.__dict__.items()


class JsonExporter(object):
    def __init__(self, dictexporter=None, **kwargs):
        """
        Tree to JSON exporter.

        The tree is converted to a dictionary via `dictexporter` and exported to JSON.

        Keyword Arguments:
            dictexporter: Dictionary Exporter used (see :any:`DictExporter`).
            kwargs: All other arguments are passed to
                    :any:`json.dump`/:any:`json.dumps`.
                    See documentation for reference.

        >>> from ox.tree import AnyNode
        >>> from ox.tree.exporter import JsonExporter
        >>> root = AnyNode(a="root")
        >>> s0 = AnyNode(a="sub0", parent=root)
        >>> s0a = AnyNode(a="sub0A", b="foo", parent=s0)
        >>> s0b = AnyNode(a="sub0B", parent=s0)
        >>> s1 = AnyNode(a="sub1", parent=root)

        >>> exporter = JsonExporter(indent=2, sort_keys=True)
        >>> print(exporter.export(root))
        {
          "a": "root",
          "children": [
            {
              "a": "sub0",
              "children": [
                {
                  "a": "sub0A",
                  "b": "foo"
                },
                {
                  "a": "sub0B"
                }
              ]
            },
            {
              "a": "sub1"
            }
          ]
        }
        """
        self.dictexporter = dictexporter
        self.kwargs = kwargs

    def export(self, node):
        """Return JSON for tree starting at `node`."""
        dictexporter = self.dictexporter or DictExporter()
        data = dictexporter.export(node)
        return json.dumps(data, **self.kwargs)

    def write(self, node, filehandle):
        """Write JSON to `filehandle` starting at `node`."""
        dictexporter = self.dictexporter or DictExporter()
        data = dictexporter.export(node)
        return json.dump(data, filehandle, **self.kwargs)


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

        >>> from ox.tree import Node
        >>> root = Node("root")
        >>> s0 = Node("sub0", parent=root, edge=2)
        >>> s0b = Node("sub0B", parent=s0, foo=4, edge=109)
        >>> s0a = Node("sub0A", parent=s0, edge="")
        >>> s1 = Node("sub1", parent=root, edge="")
        >>> s1a = Node("sub1A", parent=s1, edge=7)
        >>> s1b = Node("sub1B", parent=s1, edge=8)
        >>> s1c = Node("sub1C", parent=s1, edge=22)
        >>> s1ca = Node("sub1Ca", parent=s1c, edge=42)

        A directed graph:

        >>> from ox.tree.exporter import DotExporter
        >>> for line in DotExporter(root):
        ...     print(line)
        digraph tree {
            "root";
            "sub0";
            "sub0B";
            "sub0A";
            "sub1";
            "sub1A";
            "sub1B";
            "sub1C";
            "sub1Ca";
            "root" -> "sub0";
            "root" -> "sub1";
            "sub0" -> "sub0B";
            "sub0" -> "sub0A";
            "sub1" -> "sub1A";
            "sub1" -> "sub1B";
            "sub1" -> "sub1C";
            "sub1C" -> "sub1Ca";
        }

        An undirected graph:

        >>> def nodenamefunc(node):
        ...     return '%s:%s' % (node.name, node.depth)
        >>> def edgeattrfunc(node, child):
        ...     return 'label="%s:%s"' % (node.name, child.name)
        >>> def edgetypefunc(node, child):
        ...     return '--'
                >>> from ox.tree.exporter import DotExporter
        >>> for line in DotExporter(root, graph="graph",
        ...                             nodenamefunc=nodenamefunc,
        ...                             nodeattrfunc=lambda node: "shape=box",
        ...                             edgeattrfunc=edgeattrfunc,
        ...                             edgetypefunc=edgetypefunc):
        ...     print(line)
        graph tree {
            "root:0" [shape=box];
            "sub0:1" [shape=box];
            "sub0B:2" [shape=box];
            "sub0A:2" [shape=box];
            "sub1:1" [shape=box];
            "sub1A:2" [shape=box];
            "sub1B:2" [shape=box];
            "sub1C:2" [shape=box];
            "sub1Ca:3" [shape=box];
            "root:0" -- "sub0:1" [label="root:sub0"];
            "root:0" -- "sub1:1" [label="root:sub1"];
            "sub0:1" -- "sub0B:2" [label="sub0:sub0B"];
            "sub0:1" -- "sub0A:2" [label="sub0:sub0A"];
            "sub1:1" -- "sub1A:2" [label="sub1:sub1A"];
            "sub1:1" -- "sub1B:2" [label="sub1:sub1B"];
            "sub1:1" -- "sub1C:2" [label="sub1:sub1C"];
            "sub1C:2" -- "sub1Ca:3" [label="sub1C:sub1Ca"];
        }
        """
        self.node = node
        self.graph = graph
        self.name = name
        self.options = options
        self.indent = indent
        self.nodenamefunc = nodenamefunc
        self.nodeattrfunc = nodeattrfunc
        self.edgeattrfunc = edgeattrfunc
        self.edgetypefunc = edgetypefunc

    def __iter__(self):
        # prepare
        indent = " " * self.indent
        nodenamefunc = self.nodenamefunc or DotExporter.__default_nodenamefunc
        nodeattrfunc = self.nodeattrfunc or DotExporter.__default_nodeattrfunc
        edgeattrfunc = self.edgeattrfunc or DotExporter.__default_edgeattrfunc
        edgetypefunc = self.edgetypefunc or DotExporter.__default_edgetypefunc
        return self.__iter(
            indent, nodenamefunc, nodeattrfunc, edgeattrfunc, edgetypefunc
        )

    @staticmethod
    def __default_nodenamefunc(node):
        return node.name

    @staticmethod
    def __default_nodeattrfunc(node):
        return None

    @staticmethod
    def __default_edgeattrfunc(node, child):
        return None

    @staticmethod
    def __default_edgetypefunc(node, child):
        return "->"

    def __iter(self, indent, nodenamefunc, nodeattrfunc, edgeattrfunc, edgetypefunc):
        yield "{self.graph} {self.name} {{".format(self=self)
        for option in self.__iter_options(indent):
            yield option
        for node in self.__iter_nodes(indent, nodenamefunc, nodeattrfunc):
            yield node
        for edge in self.__iter_edges(indent, nodenamefunc, edgeattrfunc, edgetypefunc):
            yield edge
        yield "}"

    def __iter_options(self, indent):
        options = self.options
        if options:
            for option in options:
                yield "%s%s" % (indent, option)

    def __iter_nodes(self, indent, nodenamefunc, nodeattrfunc):
        for node in PreOrderIter(self.node):
            nodename = nodenamefunc(node)
            nodeattr = nodeattrfunc(node)
            nodeattr = " [%s]" % nodeattr if nodeattr is not None else ""
            yield '%s"%s"%s;' % (indent, DotExporter.esc(nodename), nodeattr)

    def __iter_edges(self, indent, nodenamefunc, edgeattrfunc, edgetypefunc):
        for node in PreOrderIter(self.node):
            nodename = nodenamefunc(node)
            for child in node.children:
                childname = nodenamefunc(child)
                edgeattr = edgeattrfunc(node, child)
                edgetype = edgetypefunc(node, child)
                edgeattr = " [%s]" % edgeattr if edgeattr is not None else ""
                yield '%s"%s" %s "%s"%s;' % (
                    indent,
                    DotExporter.esc(nodename),
                    edgetype,
                    DotExporter.esc(childname),
                    edgeattr,
                )

    def to_dotfile(self, filename):
        """
        Write graph to `filename`.

        >>> from ox.tree import Node
        >>> root = Node("root")
        >>> s0 = Node("sub0", parent=root)
        >>> s0b = Node("sub0B", parent=s0)
        >>> s0a = Node("sub0A", parent=s0)
        >>> s1 = Node("sub1", parent=root)
        >>> s1a = Node("sub1A", parent=s1)
        >>> s1b = Node("sub1B", parent=s1)
        >>> s1c = Node("sub1C", parent=s1)
        >>> s1ca = Node("sub1Ca", parent=s1c)

        >>> from ox.tree.exporter import DotExporter
        >>> DotExporter(root).to_dotfile("tree.dot")

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
        except Exception:  # pragma: no cover
            msg = "Could not remove temporary file %s" % dotfilename
            logging.getLogger(__name__).warn(msg)

    @staticmethod
    def esc(str):
        """Escape Strings."""
        return str.replace('"', '\\"')
