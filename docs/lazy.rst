========================
Lazy access to resources
========================

Sidekick encourages lazy evaluation of code and has a few functions that helps
to implement lazy access to resources and objects.


Lazy attributes
===============

We can mark an attribute as lazy (i.e., it is initialized during first access,
rather than instance initialization). :func:`sidekick.lazy` can be used as a
decorator or quick lambda:

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
computations that are not always necessary in the object's lifecycle.

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

Now, ``arrow.magnitude`` delegates to ``arrow.vector.magnitude``. Delegate
fields are useful in class composition when one
wants to expose a few selected attributes from the inner objects. delegate_to()
handles attributes and methods with no distinction.


>>> a = Arrow(Vec(6, 8))
>>> a.magnitude
computing...
10.0

.. autofunction:: sidekick.delegate_to


Aliasing
========

Aliasing is a very simple form of delegation. Aliases are simple views over
other attributes in the instance itself:

.. code-block::python

    class MyArrow(Arrow):
        abs_value = alias('magnitude', read_only=True)
        origin = alias('start')

This exposes two additional properties: "abs_value" and "origin". The first is
just a read-only view on the "magnitude" property. The second exposes read and
write access to the "start" attribute.


Properties
==========

Sidekick's :cls:`sidekick.property` decorator is a drop-in replacement for
Python's builtin properties. It behaves similarly to Python's builtin, but also
accepts placeholder expressions and quick lambdas as input functions. This
allows very terse declarations:

.. code-block:: python

    class Vector:
        sqr_radius = property(_.x**2 + _.y**2)


:cls:`sidekick.lazy` also accepts quick lambdas. The main difference between
both is that properties are read only and not cached, while lazy attributes
are cached and writable.




=====================
Deferred computations
=====================

Until now, we were concened with the deferred computation of instance
attributes. Sometimes, we just want to defer some expensive computation or the
initialization of an entire object.


Lazy imports
============

Sidekick implements a lazy_import object that can be used to delay imports in
a module. It can lazily import a module or a function inside a module:

.. code-block:: python

    from sidekick import import_later

    np = import_later('numpy')           # a proxy to the numpy module
    array = import_later('numpy:array')  # proxy to the array function in the module


Lazy imports can dramatically decrease the initialization time of your python
modules, specially when heavy weights such as numpy, and pandas are used.

.. autofunction:: sidekick.import_later


Proxy and deferred objects
==========================

Sidekick also provides two similar kind of deferred objects: :cls:`sidekick.Deferred`
and :cls:`sidekick.Delayed`. They are both initialized from a callable with
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
>>> b = delayed(User, name='Me', age=42)

The main difference between deferred and delayed, is that Delayed instances
assume the type of the result, while deferred objects are proxies that
simply mimic the interface of the result.

>>> a
Deferred(User(name: 'Me', age: 42))
>>> b
User(name: 'Me', age: 42)

We can see that proxy instances do not change class, while deferred instances
do:

>>> type(a), type(b)
(<class 'sidekick.deferred.Deferred'>, <class 'User'>)

This limitation makes delayed objects much more limited. The delayed execution cannot
return any type that has a different C layout as regular Python objects. This
excludes all builtin types, C extension classes and even Python classes that
define __slots__. On the plus side, deferred objects fully assume
the properties of the delayed result, including its type and can replace them
in almost any context.

A slightly safer version of delayed can specify the return type of the object.
This allows delayed to work with a few additional types (e.g., types that
use __slots__) and check if conversion is viable. In order to do so, just use
the output type as an index:

>>> delayed[record](record, x=1, y=2)
record(x=1, y=2)
