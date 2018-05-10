===============================
Lazy properties and descriptors
===============================

Sidekick encourages the usage of lazy evaluation of code. It has a few
functions that help avoiding eager evaluation in Python.

Properties
==========

Sidekick implements its own :cls:`sidekick.property` decorator that accepts
placeholder expressions and quick lambdas as input functions. This allows
very terse declarations:

.. code-block:: python

    from sidekick import property, _

    class Vector:
        ...

        sqr_radius = property(_.x**2 + _.y**2)


Sidekick's property decorator is a drop-in replacement for Python's builtin
properties.


Lazy attribute
==============

The lazy decorator defines an attribute with deferred initialization::

.. code::python
    import math
    from lazyutils import lazy

    class Vec:
        def __init__(self, x, y):
            self.x, self.y = x, y

        @lazy
        def magnitude(self):
            print('computing...')
            return math.sqrt(self.x**2 + self.y**2)

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

Lazy attributes can be useful either to simplify the implementation of the
``__init__`` method of objects that initialize a great number or variables or as
an optimization that delays potentially expensive computations that are not always
necessary in the object's lifecycle.

.. autoclass:: sidekick.lazy
   :members:


Delegation
==========

The delegate_to() function delegates some attribute or method do an inner
object::

.. code::python

    from lazyutils import delegate_to

    class Arrow:
        magnitude = delegate_to('vector')

        def __init__(self, vector, start=Vec(0, 0)):
            self.vector = vector
            self.start = start

Now, the ``.magnitude`` attribute of ``Arrow`` instances is delegated to
``.vector.magnitude``. Delegate fields are useful in class composition when one
wants to expose a few selected attributes from the inner objects. delegate_to()
handles attributes and methods with no distinction.


>>> a = Arrow(Vec(6, 8))
>>> a.magnitude
computing...
10.0


.. autoclass:: sidekick.lazy
   :members:

.. autoclass:: sidekick.lazy_shared
   :members:


Aliasing
========

Aliasing is a very simple form of delegation. We can create simple aliases for
attributes using the alias() and readonly() functions::

    class MyArrow(Arrow):
        abs_value = readonly('magnitude')
        origin = alias('start')

This exposes two additional properties: "abs_value" and "origin". The first is
just a read-only view on the "magnitude" property. The second exposes read and
write access to the "start" attribute.

