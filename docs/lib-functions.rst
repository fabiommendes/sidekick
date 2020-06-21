======================
``sidekick.functions``
======================

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
===========

.. autosummary::
   fn


Function introspection and conversion
=====================================

.. autosummary::
   Stub
   arity
   signature
   stub
   to_callable
   to_function
   to_fn


Partial application
===================

.. autosummary::
   curry
   partial
   rpartial


Composition
===========

.. autosummary::
   compose
   pipe
   pipeline
   thread
   rthread
   thread_if
   rthread_if
   juxt


Combinators
===========

.. autosummary::
   identity
   ridentity
   always
   rec


Runtime control
===============

.. autosummary::
   once
   thunk
   call_after
   call_at_most
   throttle
   background


Transform arguments
===================

.. autosummary::
   flip
   select_args
   keep_args
   reverse_args
   skip_args
   splice_args
   variadic_args


API reference
=============

.. automodule:: sidekick.functions
   :members:
   :inherited-members:
