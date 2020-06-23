=================
``sidekick.evil``
=================

.. currentmodule:: sidekick.evil

This module modifies the C Python interpreter and enable some Sidekick
idioms to regular Python functions. It also have some internal facilities
to patch builtin types that uses techniques similar to those found in the
forbiddenfruit_ package. Use if you are curious, but do not use it for
anything serious.

.. _forbiddenfruit: https://pypi.org/project/forbiddenfruit/

The public API has only two functions, :func:`no_evil` and :func:`forbidden_powers`.
For other functionality, dig the code and know what you are doing.


Functions
=========

.. autosummary::
   forbidden_powers
   no_evil


API reference
=============

.. automodule:: sidekick.evil
   :members:
   :inherited-members:
