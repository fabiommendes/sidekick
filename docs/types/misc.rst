===================
Miscellaneous types
===================

Sidekick also implement a few straightforward types.

.. module:: sidekick
.. invisible-code-block:: python

    from sidekick import misc


Mappings
========

FrozenDict
----------

:class:`FrozenDict` implements a straightforward immutable dictionary variant.
It differs from ``mappingproxy`` types since it owns its data, instead of
proxying it to another mapping. More importantly, FrozenDict are hashable and
thus can be used as elements in sets and keys in other mappings.

:class:`FrozenKeyDict` is intermediate type in which keys are fixed, but values
can be mutated.

Reference
.........

.. autoclass:: sidekick.types.misc.frozendict.FrozenDict
.. autoclass:: sidekick.types.misc.frozendict.FrozenKeyDict


IdMap
-----

A mapping that saves keys by identity rather than by value. Keys do not need
to be hashable.

>>> key = [1, 2]
>>> dic = misc.IdMap([(key, 3), ([1, 2], 4)])
>>> dic
IdMap({[1, 2]: 3, [1, 2]: 4})

Reference
.........

.. autoclass:: sidekick.types.misc.idmap.IdMap


InvMap
------

An map with an inv attribute that holds inverse data. The example bellow creates
a mapping of natural numbers to their respective squares. This can be inverted
since we can recover the original number from the square.

>>> squares = misc.InvMap((k, k**2) for k in range(5))
>>> squares[2]     # square of 2
4
>>> squares.inv[4] # number whose square is 4
2

The inverse of the inverse is obviously the mapping itself

>>> squares.inv.inv is squares
True

One can use all regular dict methods in order to edit the dictionary or
its inverse, e.g.,

>>> squares[5] = 25
>>> squares.inv[36] = 6

The inverse relation is simply an ``InvMap`` with the direct and
reversed mappings exchanged. When we change one relation the other updates
the corresponding values.

>>> squares.inv
InvMap({0: 0, 1: 1, 4: 2, 9: 3, 16: 4, 25: 5, 36: 6})

Reference
.........

.. autoclass:: sidekick.types.misc.invmap.InvMap


Sequences
=========

ObservableSeq
-------------

View to sequence with the ability to register callback functions to monitor
modifications.

>>> lst = misc.ObservableSeq(['ham', 'spam', 'foo'])
>>> lst[0]
'ham'

Consider a simple callback handler that simply echoes its arguments. Let us
register it to be executed after insertions.

>>> def handler(i, v):
...     print(f'handler called with ({i}, {v})')

>>> lst.register('post-insert', handler)
>>> lst.append('bar')
handler called with (3, bar)

The "pre-*" signals can cancel modification to the list if the handler raise
an StopIteration exception. Other exceptions propagate, which will also
interrupt the operation, but must be handled by the caller.

>>> def handler(i, v):
...     raise StopIteration
>>> lst.register('pre-insert', handler)
>>> lst.append('blah'); lst
ObservableSeq(['ham', 'spam', 'foo', 'bar'])

It is the user's responsibility to raise the appropriate exceptions in
callback functions for cancelled operations if this is the desired
behavior.

Reference
.........

.. autoclass:: sidekick.types.misc.observableseq.ObservableSeq


LazyList
--------

A lazy list is initialized from a (possibly infinite) iterator and consume it
only when necessary. Sidekick implements the :class:`LazyList` class that is
initialized from an iterator and an optional ``size`` argument that sets the
maximum length of the list.

>>> lst = misc.LazyList(x**2 for x in range(10))

Asking for ``lst[idx]`` forces the lazy list to consume elements from
the iterator and store them in memory. LazyLists only use the number of
items necessary to return the value on the desired index:

>>> lst[3]
9
>>> lst
LazyList([0, 1, 4, 9, ...])

LazyList's support all list operations, including append()'s, extend()'s
and pop()'s, which often can be executed without consuming the iterator.

>>> lst.extend([100, 121])
>>> lst
LazyList([0, 1, 4, 9, ..., 100, 121])

Of course there are cases in which it is necessary to fully evaluate the
iterator because we need to transverse all items in the list.

>>> sum(lst)
506

>>> lst
LazyList([0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121])

When this happens, the lazy list sets its ``is_lazy`` attribute to False and
essentially becomes a regular list.

>>> lst.is_lazy
False


Length
......

``len`` is an innocent operation that may trigger a full evaluation of the
iterator because the iterator length is not known in advance. We can prevent
this by setting the size argument of the iterator during initialization. It
specify the maximum number of elements that will be fetch from the iterator at
any time.

>>> lst = misc.LazyList(range(1, 10), size=4)
>>> len(lst)
4
>>> lst
LazyList([...])


Infinite lists
..............

There is nothing that prevents LazyList's from being infinite. It is then highly
advisable to set size="inf" at list creation, which prevents infinite loops
and other unexpected behavior in certain operations.

>>> lst = misc.LazyList(N[1, ...], size='inf')
>>> len(lst)
Traceback (most recent call last):
...
OverflowError: cannot get the size of an infinite iterator

All operations that triggers the consumption of an infinite iterator
raise OverflowError's.

>>> lst.pop()
Traceback (most recent call last):
...
OverflowError: cannot consume an infinite iterator


Reference
.........

.. autoclass::  LazyList