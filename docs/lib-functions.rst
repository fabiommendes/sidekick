==================================
API Reference - sidekick.functions
==================================

Function creation, manipulation and introspection
=================================================

.. currentmodule:: sidekick.functions

The functions in this module are responsible for creating, transforming,
composing and introspecting other functions. Some of those functions might
be familiar from the standard lib's `functools`_ module. In spite of
those similarities, this module is not a drop-in replacement of the
standard lib's ``functools`` module.

This module also exposes the :class:`fn` type, that extends standard
Python functions with new methods and operators. This extended function
behavior is applied to most sidekick's functions and can be easily
re-used to extend user code.

.. _functools: https://docs.python.org/3/library/functools.html


Basic types
-----------

.. autosummary::
   fn


Function introspection
----------------------

.. autosummary::
   Stub
   arity
   signature
   stub


Partial application
-------------------

.. autosummary::
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



API reference
=============

.. automodule:: sidekick.functions
   :members:
   :inherited-members:
