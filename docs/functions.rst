=========
Functions
=========

Sidekick defines several functions that operates on sequences and iterators.

Creating sequences
==================

.. autofunction:: sidekick.count
.. autofunction:: sidekick.cycle
.. autofunction:: sidekick.enumerate
.. autofunction:: sidekick.iterate
.. autofunction:: sidekick.repeat
.. autofunction:: sidekick.repeatedly


Retrieving items from a sequence
================================

.. autofunction:: sidekick.butlast
.. autofunction:: sidekick.consume
.. autofunction:: sidekick.drop
.. autofunction:: sidekick.first
.. autofunction:: sidekick.get
.. autofunction:: sidekick.getslice
.. autofunction:: sidekick.last
.. autofunction:: sidekick.nth
.. autofunction:: sidekick.peek
.. autofunction:: sidekick.rest
.. autofunction:: sidekick.second
.. autofunction:: sidekick.tail
.. autofunction:: sidekick.take
.. autofunction:: sidekick.take_nth


Sequence properties
===================

.. autofunction:: sidekick.count
.. autofunction:: sidekick.countby
.. autofunction:: sidekick.frequencies
.. autofunction:: sidekick.isdistinct
.. autofunction:: sidekick.isiterable
.. autofunction:: sidekick.has


Joining iterables
=================

.. autofunction:: sidekick.append
.. autofunction:: sidekick.concat
.. autofunction:: sidekick.cons
.. autofunction:: sidekick.interleave
.. autofunction:: sidekick.interpose
.. autofunction:: sidekick.mapcat


Transforming items
==================

.. autofunction:: sidekick.accumulate
.. autofunction:: sidekick.map
.. autofunction:: sidekick.order_by


Filtering items
===============

.. autofunction:: sidekick.distinct
.. autofunction:: sidekick.dropwhile
.. autofunction:: sidekick.filter
.. autofunction:: sidekick.keep
.. autofunction:: sidekick.random_sample
.. autofunction:: sidekick.remove
.. autofunction:: sidekick.takewhile
.. autofunction:: sidekick.topk
.. autofunction:: sidekick.unique
.. autofunction:: sidekick.without



Partitioning an iterable
========================

.. autofunction:: sidekick.groupby
.. autofunction:: sidekick.partition
.. autofunction:: sidekick.partitionby
.. autofunction:: sidekick.partition_all
.. autofunction:: sidekick.reduceby
.. autofunction:: sidekick.sliding_window
.. autofunction:: sidekick.split
.. autofunction:: sidekick.split_at
.. autofunction:: sidekick.split_by


Special types of iteration
==========================

.. autofunction:: sidekick.pairwise
.. autofunction:: sidekick.reductions
.. autofunction:: sidekick.sums
.. autofunction:: sidekick.with_prev
.. autofunction:: sidekick.with_next


Multiple sequences
==================

.. autofunction:: sidekick.diff
.. autofunction:: sidekick.isequal
.. autofunction:: sidekick.join
.. autofunction:: sidekick.merge_sorted
.. autofunction:: sidekick.pluck
.. autofunction:: sidekick.zipwith
.. autofunction:: sidekick.rzipwith


Nested structures
=================

.. autofunction:: sidekick.flatten
.. autofunction:: sidekick.tree_leaves
.. autofunction:: sidekick.tree_nodes
