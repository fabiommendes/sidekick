==================
``sidekick.empty``
==================

.. currentmodule:: sidekick.not_given


In Python, we can define functions that accept optional arguments, quite easily. 
``None`` is often used as a default value to represent empty arguments to a 
function. 

.. code:: python

    def func(x, opt=None):
        ...

Sometimes, however, None is a legitimate value to the optional argument. A common 
approach to distinguish an argument valued as None from an argument that was not 
set by the caller is to define a top-level ``NOT_GIVEN = object()`` and check for
identity in the function body:


.. code:: python

    NOT_GIVEN = object()

    def func(x, opt=NOT_GIVEN):
        if opt is NOT_GIVEN:
            ... # do something to initialize argument
        
        ...
        

This is nice, but can be slightly more convenient to use :cls:`Empty` instances from this module 
instead of plain objects. They can be used in a similar way, but have some nice convenience 
methods and can be less error prone than using None or the ``NOT_GIVEN = object()`` idiom.

Consider the simple implementation of the builtin ``functools.reduce`` function:

.. code:: python

    NOT_GIVEN = object()

    def reduce(op, seq, initial=NOT_GIVEN):
        if initial is NOT_GIVEN:
            return reduce(op, seq := iter(seq), next(seq))

        for x in seq:
            initial = op(acc, x)
        return initial

The code above implements two function signatures:

* reduce(op, seq, initial) - left fold with a given initial value.
* reduce(op, seq) - extract the initial value from the first element of seq.


``sidekick.core.empty`` aims to formalize this idiom. Instead of using a
generic object instance, we may declare that a value explicitly represents
an empty argument using

.. code:: python

    from sidekick.not_given import not_given

    NOT_GIVEN = not_given()

    def reduce(op, seq, initial=EMPTY):
        if initial is NOT_GIVEN:
            return reduce(op, seq := iter(seq), next(seq))
        ...



>>> transform(42), transform(42, lambda x: -x)
(42, -42)

.. code-block:: python

    EMPTY = empty()

    def transform(x, func=EMPTY):
        return func(x) if func else x

>>> transform(42), transform(42, lambda x: -x)
(42, -42)

.. code-block:: python

    def add(lst, ans=None):
        lst.append(42 if ans is None else ans)

    def add_(lst, ans=EMPTY):
        lst.append(EMPTY(ans, 42))


>>> lst = []; add(lst); ; add(lst, None); add(lst, 43)
>>> lst
[42, 42, 43]

>>> lst = []; add_(lst); ; add_(lst, None); add_(lst, 43)
>>> lst
[42, None, 43]


.. code-block:: python

    def add(lst, ans=None):
        lst.append(42 if ans is None else ans)

    def add_(lst, ans=EMPTY):
        lst.append(EMPTY(ans, 42))


>>> EMPTY_LIST = empty(list)
>>> lst = []
>>> (EMPTY_LIST | lst) is lst
True
>>> EMPTY_LIST(EMPTY_LIST)
[]
>>> EMPTY_LIST | EMPTY_LIST
[]


.. code:: python
    EMPTY_LIST = not_given(list)

    def with_x(x, acc=EMPTY_LIST):
        acc = EMPTY_LIST | acc
        acc.append(x)
        return acc

>>> arg | "default"

API reference
=============

.. automodule:: sidekick.empty
   :members:
   :inherited-members: