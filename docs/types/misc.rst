===================
Miscellaneous types
===================

Sidekick also implement a few straightforward types.

.. invisible-code-block:: python

    from sidekick import ObservableSeq, InvMap


FrozenDict
==========

:cls:`FrozenDict` implements a straightforward immutable dictionary variant.
It differs from ``mappingproxy`` types since it owns its data, instead of
proxying it to another mapping. More importantly, FrozenDict are hashable and
thus can be used as elements in sets and keys in other mappings.

:cls:`FrozenKeyDict` is intermediate type in which keys are fixed, but values
can be mutated.


InvMap
======

An map with an inv attribute that holds inverse data. The example bellow creates
a mapping of natural numbers to their respective squares. This can be inverted
since we can recover the original number from the square.

>>> squares = InvMap((k, k**2) for k in range(5))
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


ObservableSeq
=============

View to sequence with the ability to register callback functions to monitor
modifications.

>>> lst = ObservableSeq(['ham', 'spam', 'foo'])
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