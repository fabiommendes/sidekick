=================
``sidekick.pred``
=================

.. currentmodule:: sidekick.pred

This module contains a collection of predicate functions that implement common tests.
Since all functions are fn-enabled, it accepts bitwise logic to compound predicates
into more interesting expressions, like in the example bellow.

>>> sk.filter(is_odd | is_positive, range(-5, 10))
sk.iter([1, 3, 5, 7, 9])


Composing predicates
====================

.. autosummary::
   cond
   any_pred
   all_pred


Testing values
==============

.. autosummary::
   is_a
   is_equal
   is_identical
   is_false
   is_true
   is_none
   is_truthy
   is_falsy


Numeric tests
=============

.. autosummary::
   is_even
   is_odd
   is_negative
   is_positive
   is_strictly_negative
   is_strictly_positive
   is_zero
   is_nonzero
   is_divisible_by


Sequences
=========

.. autosummary::
   is_distinct
   is_iterable
   is_seq_equal


String tests
============

.. autosummary::
   has_pattern


API reference
=============

.. automodule:: sidekick.pred
   :members:
   :inherited-members:
