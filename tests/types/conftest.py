import pytest

from sidekick import SExpr, Node
from sidekick.hypothesis import trees

tree_gen = trees()


@pytest.fixture
def tree():
    return Node([Node(["a", "b"]), "c"])


@pytest.fixture
def random_tree():
    return tree_gen.example()


@pytest.fixture
def tree_parts(tree):
    c1, c2 = tree.children
    g1, g2 = c1.children
    return c1, g1, g2, c2


@pytest.fixture
def abc_sexpr():
    return SExpr("abc", [SExpr("a"), SExpr("b"), SExpr("c")])


@pytest.fixture
def ai_sexpr():
    return SExpr(
        "a",
        [
            SExpr("b", [SExpr("c"), SExpr("d")]),
            SExpr("c", [SExpr("e"), SExpr("f"), SExpr("g", [SExpr("h"), SExpr("i")])]),
        ],
    )


@pytest.fixture
def abc_id_tree():
    return SExpr("a", [SExpr("b", id="b"), SExpr("c", id="c")], id="a")


@pytest.fixture
def ai_id_tree():
    return SExpr(
        "a",
        children=[
            SExpr("b", id="b", children=[SExpr("c", id="c"), SExpr("d", id="d")]),
            SExpr(
                "c",
                id="c",
                children=[
                    SExpr("e", id="e"),
                    SExpr("f", id="f"),
                    SExpr(
                        "g", id="g", children=[SExpr("h", id="h"), SExpr("i", id="i")]
                    ),
                ],
            ),
        ],
        id="a",
    )
