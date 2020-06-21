import json

import pytest
from hypothesis import given

from sidekick import Node, SExpr
from sidekick.hypothesis import trees, leaves, AtomT
from sidekick.tree import (
    Leaf,
    common_ancestor,
    common_ancestors,
    walk,
    import_tree,
    export_tree,
    NodeOrLeaf,
)


class TestNode:
    """
    Test basic tree behavior and functionalities
    """

    def test_render_tree(self, tree):
        assert tree.pretty().splitlines() == [
            "Node()",
            "├── Node()",
            "│   ├── 'a'",
            "│   └── 'b'",
            "└── 'c'",
        ]
        assert tree.pretty(style="ascii").splitlines() == [
            "Node()",
            "|-- Node()",
            "|   |-- 'a'",
            "|   +-- 'b'",
            "+-- 'c'",
        ]

    def test_equality(self):
        assert Leaf("a") == Leaf("a")
        assert Leaf("a") != Leaf("b")
        assert Leaf("a") == Leaf("a", prop=True)

    def test_simple_tree_properties(self, tree):
        assert tree.height == 2
        assert tree.depth == 0
        assert tree.is_root
        assert not tree.is_leaf

    def test_simple_tree_siblings(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert ab.left_sibling is None
        assert ab.right_sibling is c
        assert a.left_sibling is None
        assert a.right_sibling is b

        assert common_ancestor(a, b) is ab
        assert common_ancestors(a, b) == [tree, ab]

    def test_walk_tree(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert walk(a, a) == ((), a, ())
        assert walk(a, tree) == ((a, ab), tree, ())
        assert walk(tree, a) == ((), tree, (ab, a))
        assert walk(a, c) == ((a, ab), tree, (c,))
        assert walk(a, b) == ((a,), ab, (b,))

    def test_simple_tree_api(self, tree):
        assert tree.height == 2
        assert tree.depth == 0


class TestIterators:
    """
    Test iteration on trees.
    """

    def test_simple_iterator(self, tree, tree_parts):
        assert tuple(tree.iter_children()) == tree_parts
        assert tuple(tree.iter_children(self=True)) == (tree, *tree_parts)

    def test_depth_first(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_children()) == tree_parts
        assert tuple(tree.iter_children(max_depth=1)) == (ab, c)

    def test_level_order(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_children("level-order")) == (ab, c, a, b)
        assert tuple(tree.iter_children("level-order", max_depth=1)) == (ab, c)

    def test_pre_order(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_children("pre-order")) == tree_parts
        assert tuple(tree.iter_children("pre-order", max_depth=1)) == (ab, c)

    def test_post_order(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_children("post-order")) == (a, b, ab, c)
        assert tuple(tree.iter_children("post-order", max_depth=1)) == (ab, c)

    def test_in_order(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_children("in-order")) == (a, ab, b, tree, c)
        assert tuple(tree.iter_children("in-order", max_depth=1)) == (ab, tree, c)

    def test_out_order(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_children("out-order")) == (c, tree, b, ab, a)
        assert tuple(tree.iter_children("out-order", max_depth=1)) == (c, tree, ab)

    def test_group_level(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_group("level-order")) == ((ab, c), (a, b))
        assert tuple(tree.iter_group("level-order", max_depth=1)) == ((ab, c),)

    def test_group_zigzag(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tuple(tree.iter_group("zig-zag")) == ((ab, c), (b, a))
        assert tuple(tree.iter_group("zig-zag", max_depth=1)) == ((ab, c),)

    def test_search(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tree.find_all(lambda x: x.is_leaf and x.value in ["b", "c"]) == (b, c)
        assert tree.find(lambda x: x.is_leaf and x.value in ["b", "c"]) == b
        assert tree.find(lambda x: x.is_leaf and x.value == "d", default=None) is None

    def test_leaf_search(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        assert tree.find_all(lambda x: x.value in ["b", "c"], leaves=True) == (b, c)
        assert tree.find(lambda x: x.value in ["b", "c"], leaves=True) == b
        assert tree.find(lambda x: x.value == "d", default=None, leaves=True) is None


class TestImportExport:
    """
    Test persistence, visualization and serialization.
    """

    def test_dict_importer(self, tree):
        data = {"children": [{"children": ["a", "b"]}, "c"]}
        assert tree == import_tree(data, how="dict")

    def test_json_importer(self, tree):
        data = {"children": [{"children": ["a", "b"]}, "c"]}
        data = json.dumps(data)
        assert tree == import_tree(data, how="json")

    def test_dict_exporter(self, tree):
        data = {"children": [{"children": ["a", "b"]}, "c"]}
        assert export_tree(tree, format="dict") == data

    def test_json_exporter(self, tree):
        data = {"children": [{"children": ["a", "b"]}, "c"]}
        assert export_tree(tree, format="json") == json.dumps(data)

    def test_dot_exporter(self, tree):
        assert export_tree(tree, format="dot") == (
            """digraph tree {\n"""
            """    "Node()";\n"""
            """    "Node()";\n"""
            """    "'a'";\n"""
            """    "'b'";\n"""
            """    "'c'";\n"""
            """    "Node()" -> "Node()";\n"""
            """    "Node()" -> "'c'";\n"""
            """    "Node()" -> "'a'";\n"""
            """    "Node()" -> "'b'";\n"""
            """}"""
        )


class TestClasses:
    """
    Check class structure and invariants.
    """

    def test_tree_classes_have_slots(self):
        import sidekick.tree as tree

        for k, v in vars(tree).items():
            if isinstance(v, type) and issubclass(v, NodeOrLeaf):
                assert "__slots__" in v.__dict__, v.__name__

        x = Leaf(42)
        y = Node([x])
        z = SExpr("test", [y])
        for item in [x, y, z]:
            with pytest.raises(AttributeError):
                print(item.__dict__)


class TestErrors:
    """
    Check it raises the correct errors.
    """

    def test_cannot_assign_invalid_parent(self, tree, tree_parts):
        ab, a, b, c = tree_parts
        # Bad parent type
        with pytest.raises(TypeError):
            tree.parent = "bad parent"
        # Leaves cannot be parents
        with pytest.raises(TypeError):
            tree.parent = b
        # Cannot be parent of itself
        with pytest.raises(ValueError):
            tree.parent = tree
        # Child cannot be parent
        with pytest.raises(ValueError):
            tree.parent = ab


@pytest.mark.slow()
class TestHypothesis:
    """
    Parametric testing for trees.
    """

    @given(leaves(allow_attrs=False))
    def test_leaf(self, leaf):
        assert isinstance(leaf.value, AtomT)
        assert leaf.attrs == {}

    @given(leaves(allow_attrs=False))
    def test_leaf(self, leaf):
        assert isinstance(leaf.value, AtomT)

    @given(trees())
    def test_can_render_key(self, tree):
        assert tree.parent is None
        assert tree.root is tree

    @given(trees(max_depth=5))
    def test_can_render_key(self, tree):
        assert tree.height <= 5
        assert tree.depth == 0
