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
   rest
   init
   is_empty
   length
   consume


Creating new sequences
======================

.. autosummary::
   cycle
   iterate
   iterate_indexed
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
   unique
   dedupe
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
   accumulate
   fold_by
   reduce_by
   product
   products
   sums
   all_by
   any_by
   top_k


API reference
=============

.. automodule:: sidekick.seq
   :members:
   :inherited-members:
