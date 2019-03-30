========================
Lazy access to resources
========================

Python functional code tends to rely a lot on lazy evaluation. This module
define a few utility functions and types that handles lazy evaluation outside
the context of iterators and sequences.


Lazy attributes
===============

Attributes can be marked lazy (i.e., it is initialized during first access,
rather than instance initialization) using the :func:`sidekick.lazy` decorator:

.. code-block::python

    import math
    from sidekick import *

    class Vec:
        @lazy
        def magnitude(self):
            print('computing...')
            return math.sqrt(self.x**2 + self.y**2)

        def __init__(self, x, y):
            self.x, self.y = x, y


Now the ``magnitude`` attribute is initialized and cached upon first use:

>>> v = Vec(3, 4)
>>> v.magnitude
computing...
5.0

The attribute is writable and apart from the deferred initialization, it behaves
just like any regular Python attribute.

>>> v.magnitude = 42
>>> v.magnitude
42

Lazy attributes can be useful either to simplify the implementation of
``__init__`` or as an optimization technique that delays potentially expensive
computations that are not always necessary in the object's lifecycle. Lazy
attributes are often used together with quick lambdas for very compact
definitions:

.. code-block::python

    import math
    from sidekick import lazy, placeholder as _

    class Square:
        area = lazy(_.width * _.height)
        perimeter = lazy(2 * (_.width + _.height))


.. autofunction:: sidekick.lazy


Delegation
==========

:func:`sidekick.delegate_to` delegates an attribute or method do an inner
object. This is useful when the inner object contains the implementation, but
we want to expose an specific interface in the instance object:

.. code-block::python

    class Arrow:
        magnitude = delegate_to('vector')

        def __init__(self, vector, start=Vec(0, 0)):
            self.vector = vector
            self.start = start

Now, ``arrow.magnitude`` behaves as an alias to ``arrow.vector.magnitude``.
Delegate fields are useful in class composition when one wants to expose a few
selected attributes from the inner objects. delegate_to()
handles attributes and methods with no distinction.


>>> a = Arrow(Vec(6, 8))
>>> a.magnitude
computing...
10.0

.. autofunction:: sidekick.delegate_to


Aliasing
========

Aliasing is another simple form of self-delegation. Aliases are views over
other attributes in the instance itself:

.. code-block::python

    class MyArrow(Arrow):
        abs_value = alias('magnitude')
        origin = alias('start', mutable=True)

This exposes two additional properties: "abs_value" and "origin". The first is
just a read-only view on the "magnitude" property. The second exposes read and
write access to the "start" attribute.


Properties
==========

Sidekick's :mcs:`sidekick.property` decorator is a drop-in replacement for
Python's builtin properties. It behaves similarly to Python's builtin, but also
accepts quick lambdas as input functions. This allows very terse declarations:

.. code-block:: python

    class Vector:
        sqr_radius = property(_.x**2 + _.y**2)


:mcs:`sidekick.lazy` is very similar to property. The main difference between
both is that properties are not cached and hence the function is re-executed
at each attribute access. The desired behavior will depend a lot on what you
want to do.



=====================
Deferred computations
=====================

Until now, we were concerned with the deferred computation of instance
attributes. Sometimes, we just want to defer some expensive computation or the
initialization of an entire object.


Lazy imports
============

Sidekick implements a lazy_import object to delay imports of a module.

.. code-block:: python

    from sidekick import import_later

    np = import_later('numpy')           # a proxy to the numpy module
    array = import_later('numpy:array')  # proxy to the array function in the module


Lazy imports can dramatically decrease the initialization time of your python
modules, specially when heavy weights such as numpy, and pandas are used. Beware
that import errors that normally are triggered during import time
now can be triggered at the first use and may introduce confusing and hard
to spot bugs.

.. autofunction:: sidekick.import_later


Proxy and zombie objects
========================

Sidekick also provides two similar kinds of deferred objects: :mcs:`sidekick.Deferred`
and :mcs:`sidekick.Zombie`. They are both initialized from a callable with
arbitrary arguments and delay the execution of the callable until the result is
needed:

>>> class User:
...     def __init__(self, **kwargs):
...         for k, v in kwargs.items():
...             setattr(self, k, v)
...     def __repr__(self):
...         data = ('%s: %r' % item for item in self.__dict__.items())
...         return 'User(%s)' % ', '.join(data)
>>> a = deferred(User, name='Me', age=42)
>>> b = zombie(User, name='Me', age=42)

The main difference between deferred and zombie, is that Zombie instances
assume the type of the result after they awake, while deferred objects are
proxies that simply mimic the interface of the result.

>>> a
Deferred(User(name: 'Me', age: 42))
>>> b
User(name: 'Me', age: 42)

We can see that deferred instances do not change class, while zombie instances
do:

>>> type(a), type(b)                                        # doctest: +ELLIPSIS
(<class '...Deferred'>, <class 'User'>)

This limitation makes zombie objects much more limited. Delayed execution cannot
return any type that has a different C layout as regular Python objects. This
excludes all builtin types, C extension classes and even Python classes that
define __slots__. On the plus side, zombie objects fully assume
the properties of the delayed result, including its type and can replace them
in almost any context.

A slightly safer version of :func:`zombie` allows specifying the return type of
the resulting object. This opens up a few additional types (e.g., types that
use __slots__) and produces checks if conversion is viable or not.

Use the constructor function output type as an index:

>>> rec = zombie[record](record, x=1, y=2)
>>> type(rec)
Zombie[record]

Touch it, and the zombie awakes

>>> touch(rec)
record(x=1, y=2)

>>> type(rec)
record