==================
``sidekick.proxy``
==================

.. currentmodule:: sidekick.proxy

Sidekick's :func:`sidekick.functions.thunk` is a nice way to represent a lazy computation
through a function. It, however, breaks existing interfaces since we need to call the
result of thunk to obtain its inner value. :mod:`sidekick.proxy` implements a few types that
help exposing lazy objects as proxies, sharing the same interfaces as the wrapped objects.
This is great for code that relies in duck-typing.

Lazy objects are useful both to declare objects that use yet uninitialized resources and
as an optimization that we like to call *"opportunistic procrastination"*: we delay
computation to the last possible time in the hope that we can get away without doing
it at all. This is a powerful strategy since our programs tend to compute a lot of things
in advance that are not always used during program execution.


Proxy types and functions
=========================

.. autosummary::
   Proxy
   deferred
   zombie
   touch
   import_later


Deferred proxies vs zombies
===========================

Sidekick provides two similar kinds of deferred objects: :class:`deferred`
and :func:`zombie`. They are both initialized from a callable with
arbitrary arguments and delay the execution of that callable until the result is
needed. Consider the custom ``User`` class bellow.

>>> class User:
...     def __init__(self, **kwargs):
...         for k, v in kwargs.items():
...             setattr(self, k, v)
...     def __repr__(self):
...         data = ('%s: %r' % item for item in self.__dict__.items())
...         return 'User(%s)' % ', '.join(data)
>>> a = sk.deferred(User, name='Me', age=42)
>>> b = sk.zombie(User, name='Me', age=42)

The main difference between deferred and zombie, is that Zombie instances
assume the type of the result after they awake, while deferred objects are
proxies that simply mimic the interface of the result.

>>> a
Proxy(User(name: 'Me', age: 42))
>>> b
User(name: 'Me', age: 42)

We can see that deferred instances do not change class, while zombie instances
do:

>>> type(a), type(b)                                        # doctest: +ELLIPSIS
(<class '...deferred'>, <class 'User'>)

This limitation makes zombie objects somewhat restricted. Delayed execution cannot
return any type that has a different C layout as regular Python objects. This
excludes all builtin types, C extension classes and even Python classes that
define __slots__. On the plus side, zombie objects fully assume
the properties of the delayed execution, including its type and can replace them
in almost any context.

A slightly safer version of :func:`zombie` allows specifying the return type of
the resulting object. This opens zombies up to a few additional types (e.g., types
that use __slots__) and produces checks if conversion is viable or not.

We specify the return type as an index before declaring the constructor
function:

>>> rec = sk.zombie[sk.record](sk.record, x=1, y=2)
>>> type(rec)                                               # doctest: +ELLIPSIS
<class '...SpecializedZombie'>

Touch it, and the zombie awakes

>>> sk.touch(rec)
record(x=1, y=2)

>>> type(rec)                                               # doctest: +ELLIPSIS
<class '...record'>


API reference
=============

.. automodule:: sidekick.proxy
   :members:
   :inherited-members:
