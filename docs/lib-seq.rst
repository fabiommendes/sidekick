================
``sidekick.seq``
================

.. currentmodule:: sidekick.seq

.. TODO
   Describe the module

Basic types
===========

.. autosummary::
   iter
   generator


Basic manipulation of sequences
===============================

.. autosummary::
   cons
   uncons
   first
   second
   nth
   find
   only
   last
   is_empty
   length
   consume


Creating new sequences
======================

.. autosummary::
   cycle
   iterate
   nums
   repeat
   repeatedly
   singleton
   unfold


Filtering and select sub-sequences
==================================

.. autosummary::
   filter
   remove
   separate
   drop
   rdrop
   take
   rtake
   dedupe
   unique
   converge


Grouping items
==============

.. autosummary::
   group_by
   chunks
   chunks_by
   window
   pairs
   partition
   distribute


Reducing sequences
==================

.. autosummary::
   fold
   reduce
   scan
   acc
   fold_by
   reduce_by
   fold_together
   reduce_together
   scan_together
   acc_together
   product
   products
   sum
   sums
   all_by
   any_by
   top_k


Transforming
=============

.. autosummary::
   map
   map_if
   zip_map


Augmenting
=============

.. autosummary::
   interpose
   pad
   pad_with
   append
   insert


Combining
=============

.. autosummary::
   concat
   interleave
   zip_aligned
   merge_sorted
   join
   diff


API reference
=============

.. automodule:: sidekick.seq
   :members:
   :inherited-members:
