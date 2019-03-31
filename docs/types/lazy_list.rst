========
LazyList
========

.. invisible-code-block:: python

    from sidekick import LazyList, N

A lazy list is initialized from a (possibly infinite) iterator and consume it
only when necessary. Sidekick implements the :class:`LazyList` class that is
initialized from an iterator and an optional ``size`` argument that sets the
maximum length of the list.

>>> lst = LazyList(x**2 for x in range(10))

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
------

``len`` is an innocent operation that may trigger a full evaluation of the
iterator because the iterator length is not known in advance. We can prevent
this by setting the size argument of the iterator during initialization. It
specify the maximum number of elements that will be fetch from the iterator at
any time.

>>> lst = LazyList(range(1, 10), size=4)
>>> len(lst)
4
>>> lst
LazyList([...])


Infinite lists
--------------

There is nothing that prevents LazyList's from being infinite. It is then highly
advisable to set size="inf" at list creation, which prevents infinite loops
and other unexpected behavior in certain operations.

>>> lst = LazyList(N[1, ...], size='inf')
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