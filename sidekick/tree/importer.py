import json

from .node_classes import Node, Leaf


def import_tree(obj, how="dict", **kwargs):
    """
    Import tree from data source.
    """
    if how == "dict":
        return _from_dict(obj, **kwargs)
    elif how == "json":
        if isinstance(obj, str):
            data = json.loads(obj)
        else:
            data = json.load(obj)
        return _from_dict(data, **kwargs)
    else:
        raise ValueError(f"invalid import method: {how!r}")


def _from_dict(data, node_class=Node, leaf_class=Leaf, parent=None):
    """
    Import node from dictionary.
    """
    if not isinstance(data, dict):
        return leaf_class(data, parent=parent)

    attrs = dict(data)
    children = attrs.pop("children", ())
    children = [_from_dict(child, node_class, leaf_class) for child in children]
    return node_class(children, parent=parent, **attrs)
