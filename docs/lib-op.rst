===============
``sidekick.op``
===============

.. currentmodule:: sidekick.op

This module exposes functionality analogous to the operator_ module in the standard lib.
The main difference is that binary operators are curried and all functions are fn-functions.
So we can use it as a drop-in replacement to the operator module:

>>> from sidekick import op
>>> op.add(1, 2)
3

Functions in this module are curried and accepts fn attributes

>>> succ = op.add(1)
>>> succ(41)
42

>>> op.add.signature()
add(Any, Any) -> Any

.. _operator: https://docs.python.org/3/library/operator.html


API reference
=============

.. automodule:: sidekick.op
   :members:
   :inherited-members:
