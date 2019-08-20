import pytest
from hypothesis import given

from sidekick import common_ancestor, common_ancestors
from sidekick.hypothesis import trees, leaves


class TestNode:
    def test_render_tree(self, tree):
        assert tree.pretty().splitlines() == [
            'Node()',
            "├── 'a'",
            '└── Node()',
            "    ├── 'b'",
            "    └── 'c'",
        ]
        assert tree.pretty(style='ascii').splitlines() == [
            'Node()',
            "|-- 'a'",
            '+-- Node()',
            "    |-- 'b'",
            "    +-- 'c'",
        ]

    def test_simple_tree_properties(self, tree):
        assert tree.height == 2
        assert tree.depth == 0
        assert tree.is_root
        assert not tree.is_leaf

    def test_simple_tree_siblings(self, tree, tree_parts):
        a, bc, b, c = tree_parts
        assert bc.left_sibling is a
        assert bc.right_sibling is None
        assert b.left_sibling is None
        assert b.right_sibling is c

        assert common_ancestor(b, c) is bc
        assert common_ancestors(b, c) == [tree, bc]

    def test_simple_tree_api(self, tree):
        assert tree.height == 2
        assert tree.depth == 0


class TestErrors:
    def test_cannot_assign_invalid_parent(self, tree):
        # Bad parent type
        with pytest.raises(TypeError):
            tree.parent = 'bad parent'
        # Leaves cannot be parents
        with pytest.raises(TypeError):
            tree.parent = tree.children[0]
        # Cannot be parent of itself
        with pytest.raises(ValueError):
            tree.parent = tree
        # Child cannot be parent
        with pytest.raises(ValueError):
            tree.parent = tree.children[1]


@pytest.mark.slow()
class TestHypothesis:
    @given(leaves(allow_attrs=False))
    def test_leaf(self, leaf):
        assert isinstance(leaf.value, (int, float, str))

    @given(leaves(allow_attrs=False))
    def test_leaf(self, leaf):
        assert isinstance(leaf.value, (int, float, str))

    @given(trees())
    def test_can_render_key(self, tree):
        assert tree.parent is None
        assert tree.root is tree

    @given(trees(max_depth=5))
    def test_can_render_key(self, tree):
        assert tree.height <= 5
        assert tree.depth == 0
