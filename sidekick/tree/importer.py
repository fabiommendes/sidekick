import json

from .node import AnyNode


class DictImporter(object):
    def __init__(self, nodecls=AnyNode):
        u"""
        Import Tree from dictionary.

        Every dictionary is converted to an instance of `nodecls`.
        The dictionaries listed in the children attribute are converted
        likewise and added as children.

        Keyword Args:
            nodecls: class used for nodes.

        >>> from ox.tree.importer import DictImporter
        >>> from ox.tree import RenderTree
        >>> importer = DictImporter()
        >>> data = {
        ...     'a': 'root',
        ...     'children': [{'a': 'sub0',
        ...                   'children': [{'a': 'sub0A', 'b': 'foo'}, {'a': 'sub0B'}]},
        ...                  {'a': 'sub1'}]}
        >>> root = importer.import_(data)
        >>> print(RenderTree(root))
        AnyNode(a='root')
        ├── AnyNode(a='sub0')
        │   ├── AnyNode(a='sub0A', b='foo')
        │   └── AnyNode(a='sub0B')
        └── AnyNode(a='sub1')
        """
        self.nodecls = nodecls

    def import_(self, data):
        """Import tree from `data`."""
        return self.__import(data)

    def __import(self, data, parent=None):
        assert isinstance(data, dict)
        assert "parent" not in data
        attrs = dict(data)
        children = attrs.pop("children", [])
        node = self.nodecls(parent=parent, **attrs)
        for child in children:
            self.__import(child, parent=node)
        return node


class JsonImporter(object):
    def __init__(self, dictimporter=None, **kwargs):
        u"""
        Import Tree from JSON.

        The JSON is read and converted to a dictionary via `dictimporter`.

        Keyword Arguments:
            dictimporter: Dictionary Importer used (see :any:`DictImporter`).
            kwargs: All other arguments are passed to
                    :any:`json.load`/:any:`json.loads`.
                    See documentation for reference.

        >>> from ox.tree.importer import JsonImporter
        >>> from ox.tree import RenderTree
        >>> importer = JsonImporter()
        >>> data = '''
        ... {
        ...   "a": "root",
        ...   "children": [
        ...     {
        ...       "a": "sub0",
        ...       "children": [
        ...         {
        ...           "a": "sub0A",
        ...           "b": "foo"
        ...         },
        ...         {
        ...           "a": "sub0B"
        ...         }
        ...       ]
        ...     },
        ...     {
        ...       "a": "sub1"
        ...     }
        ...   ]
        ... }'''
        >>> root = importer.import_(data)
        >>> print(RenderTree(root))
        AnyNode(a='root')
        ├── AnyNode(a='sub0')
        │   ├── AnyNode(a='sub0A', b='foo')
        │   └── AnyNode(a='sub0B')
        └── AnyNode(a='sub1')
        """
        self.dictimporter = dictimporter
        self.kwargs = kwargs

    def __import(self, data):
        dictimporter = self.dictimporter or DictImporter()
        return dictimporter.import_(data)

    def import_(self, data):
        """Read JSON from `data`."""
        return self.__import(json.loads(data, **self.kwargs))

    def read(self, filehandle):
        """Read JSON from `filehandle`."""
        return self.__import(json.load(filehandle, **self.kwargs))
