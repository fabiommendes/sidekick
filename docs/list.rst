====
List
====

**WARNING:** This is a work in progress.

Sidekick implements singly linked lists as the Union type bellow:

.. code-block:: python

    from sidekick import Union, opt


    class Maybe(Union):
        Nothing = opt()
        Just = opt(value=object)


On top of that, of course you can expect a standard sequence interface and
a few methods for better handling those types.

Sidekick's lists are immutable and are efficient for first element
insertion/deletion. You have to consider this when implementing algorithms
with those singly linked lists.

.. code-block:: python

    def sum(lst, start=0):
        while lst:
            x, lst = lst.data
            start += x
        return x


API reference
=============

.. autoclass:: sidekick.List
    :members:
    :noindex:
.. autofunction:: sidekick.linklist
    :noindex:
