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
   only
   last
   rest
   init
   is_empty
   length


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


Filtering and sub-sequencing
============================

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


Grouping items
==============

.. autosummary::
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
