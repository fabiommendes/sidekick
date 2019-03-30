=============
Magic objects
=============

Sidekick's magic objects are just function factories for common Python idioms.
The most important of those objects, perhaps, is the magic argument X that
is used to quickly create partial applications of Python operators.

There are a few other similar objects centered around constructing small
functions to deal with common Python types such as lists, tuples, sets,
dictionaries, strings, and more.


Operator centered (argument factories)
======================================

Magic arguments (X, Y)
----------------------

Start with

>>> from sidekick import X, Y

X and Y are factories that create functions that simply reproduce the operation
applied to the argument object itself. The difference between the two that X is
always treated as the first argument of the function and Y as the second. If the
expression only involves X, it always return a single argument function.

**Examples**

>>> is_even = X % 2
>>> rmod = Y % X
>>> is_even(3), rmod(5, 13)
(1, 3)



Magic Function (F)
------------------

>>> F + 1  # lambda f: lambda x: f(x) + 1



Magic item (X_i)
----------------

Similar to the X object, but all operations are mapped using :func:`functor_map`:

>>> X_i + 1  # lambda v: functor_map(lambda x: x + 1, v)


Data centric
============


Magic list (L)
--------------

Expose a curried version of the list API in which the list is always passed as
the last parameter.

>>> from sidekick import L, T, S, D
>>> L.append(10, range(10))
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

It also accepts conversion using the pipe notation:

>>> range(1, 5) | L
[1, 2, 3, 4]

>>> L[2]([1, 2, 3, 4])
3
>>> L[[1, 1, 2]]([1, 2, 3, 4])
[2, 2, 3]

.. autoclass:: sidekick.L
:members:


Magic set (S)
-------------

Same with sets.

>>> range(5) | S
{0, 1, 2, 3, 4}

.. autoclass:: sidekick.S
:members:


Magic dictionary (D)
--------------------

>>> zip("abcd", range(1, 5)) | D
{'a': 1, 'b': 2 'c': 3, 'd': 4}

>>> D.get('foo')({'foo': 'bar', 'ham': 'spam'})
'bar'

.. autoclass:: sidekick.D
:members:


Magic string (T)
----------------

>>> 42.0 | T
'42.0'

>>> T.split('.')('42.0')
['42', '0']

.. autoclass:: sidekick.D
:members:


Magic bytes (B)
----------------

>>> 42.0 | B
b'42.0'

>>> B.split(b'.')('42.0')
[b'42', b'0']

.. autoclass:: sidekick.D
:members:



