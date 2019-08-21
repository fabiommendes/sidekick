import random
from functools import partial

from hypothesis import strategies as st

from .base import identifiers, atoms, kwargs, fcall
from ..tree import Leaf, Node


def leaves(data=atoms(), allow_attrs=True, attrs=None):
    """
    Return a list of node elements.
    """
    if allow_attrs:
        return data.map(Leaf)
    else:
        kwds = kwargs(attrs or data, allow_private=False, exclude=("value", "parent"))
        return fcall(Leaf, [data], kwds)


def shallow_trees(*args, **kwargs):
    """
    Return shallow trees.
    """
    return st.lists(leaves(*args, **kwargs)).map(Node)


def trees(*args, max_depth=None, allow_attrs=True, **kwargs):
    """
    Return random trees.
    """
    attrs = st.just([])
    kwargs["allow_attrs"] = allow_attrs
    if allow_attrs:
        keys = identifiers(allow_private=False, exclude=("children", "parent"))
        attr = st.tuples(keys, kwargs.get("attrs") or atoms())
        attrs = st.lists(attr)
    fn = partial(shape_tree, max_depth)
    return st.builds(fn, attrs, st.lists(leaves(*args, **kwargs)))


#
# Utility functions
#
def shape_tree(max_depth, attrs, leaves):
    mk_attrs = mk_random_attrs(attrs)
    strategy = random.choice(["shallow", "deep", "random"])
    root = Node(**mk_attrs())

    if strategy == "shallow":
        root.children = leaves
    elif strategy == "deep":
        node = root
        if max_depth is not None:
            leaves = leaves[: max_depth - 1]
        for leaf in leaves:
            node = Node([leaf], **mk_attrs(), parent=node)
    else:
        nodes = [root]
        while leaves:
            leaf = leaves.pop()
            if random.random() < 0.5:
                random.choice(nodes).children.append(leaf)
            else:
                node = Node([leaf], **mk_attrs())
                random.choice(nodes).children.append(node)
                nodes.append(node)
                if max_depth is not None and node.depth == max_depth:
                    nodes = [n for n in nodes if n is not node]
    return root


def mk_random_attrs(attrs):
    def make():
        if not attrs or random.random() < 0.25:
            return {}
        else:
            k = random.randrange(len(attrs))
            return dict(random.sample(attrs, k))

    return make
