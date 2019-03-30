======================
Manipulating sequences
======================

.. module:: sidekick

A successful functional code requires functions with predictable and
interoperable interfaces. This usually means we must favor some specific data
types or interfaces and build some functions around them. Python already has
some very useful data structures like dictionaries, lists and sets, but perhaps the
most versatile of those is not even a data structure on its own, but the
*iterator* protocol. This module provides several functions for handling
iterable objects, which is a broad category that includes lists, dicts, sets,
generators, and several other data structures.


The 3 classics
==============

Introductory explanations of what functional programming is often start with
three functions: :func:`map`, :func:`reduce`, and :func:`filter`. It is no
surprise: those 3 very simple functions encode common control flow patterns
that occurs very frequently in code and are a great example of how functional
programming can abstract control flow and data processing.

Python seems to want to outgrow map and filter by replacing them by generators
and list comprehensions. They loosely correspond to the following:


.. invisible-code-block:: python

    import sidekick as sk
    from sidekick import L, N

.. ignore-next-block
.. code-block:: python

    sk.map(func, seq)    == (func(x) for x in seq)
    sk.filter(pred, seq) == (x for x in seq if pred(x))

One advantage of comprehensions is that it is easy combine both map and filter
in the same operation and while still keeping a decent level of legibility. This
is specially true if ``func`` and ``pred`` are defined by lambda expressions.

However, list comprehensions do not compose as well as functions. In sidekick,
map and filter are curried functions, which means that we can easily
create new useful methods by simply omitting the second argument.

>>> drop_nulls = sk.filter(lambda x: x is not None)
>>> drop_nulls([1, 2, None, 3, None, 4]) | L
[1, 2, 3, 4]

# TODO: explain why lazy sequences

We will discuss map, reduce and filter in a later section.


Creating sequences
==================

The first step is to create a sequence. Python has many useful iterable
builtins such as lists, dictionaries, sets, ranges, etc. But, sometimes, none
of those data structures suffice and we need to create our sequences from scratch.
This module provides functions for doing precisely so.

Numeric sequences
-----------------

Sequences of integers can be created using Python's own range function.

>>> range(1, 10, 2) | L
[1, 3, 5, 7, 9]

Useful as it is, range has some limitations:

* It does not generate infinite sequences.
* It forbids float inputs.
* It only generates very regular patterns.

Sidekick uses a magical object ``N`` to provide a flexible syntax for defining
lazy ranges of numbers. Slicing N returns the corresponding sequence (omit stop
value for infinite sequences)

>>> N[1:6] | L
[1, 2, 3, 4, 5]

It also accepts dotted intervals, which are more flexible since they allow
to specify larger parts of the sequence:

>>> N[2, 3, 5, 7, ..., 13] | L  # Some wrong primes ;-)
[2, 3, 5, 7, 9, 11, 13]

The N object also define some useful methods for declaring numeric sequences.
:func:`N.evenly_spaced`, for instance, creates sequences of known size and
bounds:

>>> N.evenly_spaced(0, 5, 11) | L
[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


The N object
............

.. autoclass:: sidekick.magic.seq_magic.N
    :members:


Non-numeric
-----------

Sometimes we need more complicated patterns than those simple and predictable
numeric sequences. Whenever you are tempted of using a ``for``, consider the
:func:`iterate` function (or its variants) instead.

The example bellow creates an infinite stream of pseudo-random numbers using a
technique called `Linear congruential generator`_.

>>> rand = sk.iterate(lambda n: (21 * n + 13) % 100, 50)
>>> rand | L[:10]
[50, 63, 36, 69, 62, 15, 28, 1, 34, 27]

.. _Linear congruential generator:  <https://en.wikipedia.org/wiki/Linear_congruential_generator>

Other options are to :func:`repeat` one value indefinitely or a single
time (:func:`singleton`), :func:`repeatdly` call a function, or to
:func:`cycle` the values of a sequence.

Functions
.........

.. autofunction:: cycle
.. autofunction:: iterate
.. autofunction:: iterate_indexed
.. autofunction:: repeat
.. autofunction:: repeatedly
.. autofunction:: singleton
