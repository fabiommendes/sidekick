===============
Tree structures
===============

Sidekick implements a tree data structure with a few utility functions for tree
traversal, pretty printing, serialization etc.

A tree is an hierarchical data structure formed by branch Nodes and leaves. Sidekick
implements a basic tree data structure and some generic lookup and traversal algorithms.
There are many specialized trees associated with specific algorithms and tasks
that are not covered by this module (balanced trees, tries, red/black trees, etc).

Keep in mind that when a specialized tree data structure exists for some task, it usually has
a better order of complexity or more efficient storage. By all means you should
use it! That said, trees are often a natural layout for data and the
generic implementation in this module gives you a lot of simple generic algorithms for free :)

A node of is a simple object that have a ''.children'' and (optionally) some arbitrary
attributes.

>>> from sidekick import Node, Leaf
>>> tree = Node([
...     Node(attr1='data',     # Node can set arbitrary attributes
...          children=[1, 2]),
...     # Non-node children are wrapped into Leaf instances
...     Leaf(3),
...     # Leaves can also set attributes
...     Leaf(4, attr2='value'),
... ])
>>> print(tree.pretty())
Node()
├── Node(attr1='data')
│   ├── 1
│   └── 2
├── 3
└── 4 (attr2='value')

The code in this module is a heavily modified version of the anytree_ package
and it shares some of its APIs.

.. _anytree: https://anytree.readthedocs.io/


S-Expressions
=============

# FIXME: continue documentation!

>>> from sidekick import SExpr
>>> expr = SExpr('+', [1, SExpr('*', [2, 3])])
>>> print(expr.pretty())
SExpr('+')
├── 1
└── SExpr('*')
    ├── 2
    └── 3

SExprs behave similarly to a list with a head first element followed
by the children. Notice all leaf nodes are wrapped into Leaf()
objects.

>>> list(SExpr('+', [1, 2]))
['+', Leaf(1), Leaf(2)]