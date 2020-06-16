=============
API Reference
=============

This page contains a comprehensive list of all functions within ``toolz``.
Docstrings should provide sufficient understanding for any individual function.

Functools
=========

.. currentmodule:: sidekick.functools

Partial application
-------------------

.. autosummary::
   arity
   curry
   partial
   rpartial


Composition
-----------

.. autosummary::
   compose
   pipe
   pipeline
   thread
   rthread


Combinators
-----------

.. autosummary::
   identity
   ridentity
   always
   rec


Predicate functions
-------------------

.. currentmodule:: sidekick.pred
.. autosummary::
   cond
   any_of
   all_of
   is_false
   is_true
   is_none
   is_even
   is_odd
   is_negative
   is_positive
   is_strictly_negative
   is_strictly_positive
   is_zero
   is_nonzero
   is_equal
   is_identical


Itertools
=========

.. currentmodule:: sidekick.itertools

Basic
-----

.. autosummary::
   cons
   uncons
   first
   second
   nth
   last
   rest
   init
   last_n
   is_empty
   length


Creation
--------

.. autosummary::
   cycle
   iterate
   iterate_indexed
   iterate_past
   repeat
   repeatedly
   singleton
   unfold


Filtering
---------

.. autosummary::
    drop_while
    random_sample
    remove
    separate
    take_while
    top_k
    unique
    until_convergence
    without


Extracting items
----------------

.. autosummary::
  consume
  drop
  get
  peek
  take
  take_nth


Mapping
-------

.. autosummary::
   indexed_map
   enumerate


Partitions
----------

.. autosummary::
   chunks
   partition
   partition_by
   fold_by
   reduce_by
   group_by
   partition_at


Reducers
--------

.. autosummary::
   fold
   reduce
   accumulate
   products
   sums
   accumulate
   scan


Transforms
----------

.. autosummary::
   select_indexed
   select_indexes


Zipping
-------

.. autosummary::
   window
   with_next
   with_prev
   zipper
   rzipper
   zip_with


Lazytools
=========

.. currentmodule:: sidekick.lazytools

Properties
----------

.. autosummary::
   alias
   delegate_to
   lazy
   property


Proxy objects
-------------

.. autosummary::
   Deferred
   Proxy
   ZombieTypes
   deferred
   import_later
   touch
   zombie

Collections
===========

.. currentmodule:: sidekick.collections


Records and mappings
--------------------

.. autosummary::
   FrozenDict
   FrozenKeyDict
   IdMap
   InvMap
   Record
   Namespace
   record
   namespace


Sequences
---------

.. autosummary::
   Queue
   List
   ObservableSeq
   TagSeq
   LazyList


Case types and variations
-------------------------

.. autosummary::
   Union
   Maybe
   Result
   union


Other data structures
---------------------

.. autosummary::
   Node
   Leaf
   SExpr


Definitions
===========

.. automodule:: sidekick.functools
   :members:

.. automodule:: sidekick.itertools
   :members:
