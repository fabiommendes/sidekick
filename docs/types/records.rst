=======
Records
=======

.. module:: sidekick

.. invisible-code-block:: python

    from sidekick import Record, Namespace, record, namespace
    import sidekick as sk

Records (or structs) are a simple data structure that implements a collection of
named fields. While there are many record-like structures in Python, each of them
seems to have its own set of quirks. Sidekick aims to make using records more
effective so users can avoid to rely on custom classes to define simple types for
data aggregation.

A new record type can be created using the :func:`Record.define`
function, which works similarly to :class:`collections.namedtuple`:

>>> Point = Record.define('Point', ['x', 'y'])

It asks a name and a list of field names to create a new record type.
Sidekick takes care of implementing the default constructor and a few useful
methods:

>>> u = Point(1, 2)
>>> v = Point(x=2, y=1)
>>> u
Point(1, 2)
>>> v.x
2

As we can see, record instances are already nicely printed (not that ugly
``<Point 0x...>`` line noise). They also implement hashing and the ``==``
operator.

Sidekick distinguishes mutable and immutable records types. In fact, we call
mutable records "namespaces", and they are appropriately created using
the :func:`Record.namespace` function:

>>> MutablePoint = Record.namespace('MutablePoint', ['x', 'y'])
>>> w = MutablePoint(x=1, y=1)
>>> w.y = 2  # this will not raise an error!
>>> w
MutablePoint(1, 2)

They behave similarly to records, but cannot be hashed (and hence used as keys
of a dictionary).


Anonymous records
=================

Sometimes we just want to instantiate a record on-the-fly without going
through the trouble of creating a new record type. Sidekick offers
the :func:`record` and :func:`namespace` functions that do
just that. Notice that anonymous records are less safe (e.g., you can introduce
subtle bugs because it does not know the correct name of all fields) and slightly
less efficient than regular record types. Nevertheless they are a good fit to
replace dictionaries in many situations:

>>> artist = record(name='John Lennon', band='Beatles')
>>> artist.name
'John Lennon'

Anonymous records have a few tweaks over regular records to make it more
interoperable with dictionaries and are heavily inspired on Javascript objects.
Records can be created from dictionaries and support the getitem interface:

>>> artist = record({'name': 'John Lennon', 'band': 'Beatles'})
>>> artist['name']
'John Lennon'
>>> dict(artist)
{'name': 'John Lennon', 'band': 'Beatles'}

We intentionally *did not* make records fully compatible with standard Python
mappings since that would pollute the API with many methods such as
``.items()``, ``.values()``, etc. This could generate unexpected results in some
situations. For instance, if ``x = record(items=[1, 2])``, what should
``x.items`` do?

That said, records are compatible enough to be able to replace dictionaries in
a few important cases. One non-trivial example is loading JSON data with Python's
builtin :mod:`sidekick.json` module:

>>> import json
>>> json.loads('{"name": "John Lennon", "band": "Beatles"}', object_hook=record)
record(band='Beatles', name='John Lennon')

We can't automatically serialize record types, but Sidekick provides a encoder
class that can be used instead of the default one:

>>> from sidekick.json import JSONEncoder
>>> json.dumps(artist, cls=JSONEncoder)
'{"name": "John Lennon", "band": "Beatles"}'

:mod:`sidekick.json` since it provides the same API of the builtin ``JSON``
module (i.e., :func:`json.load`, :func:`json.dump`, etc), but it understands
Sidekick's types.


Class based interface
=====================

Records/Namespaces are lightweight classes. It is very common to outgrow simple
record type and start requiring methods and additional properties. Records can
also be declared as classes and provide any functionality available to regular
classes. This interface allows further customizations such as setting default
values and types for the record fields.

>>> class Point(Record):
...      x: int
...      y: int = 0

This declares x as a required argument of the Point constructor and y as an
optional value with a default value of 0. Notice that the type hint are required
even if you don't want to enforce a type on the field values. In that case,
just annotate the field with with ``attr : object``.

Records declared this way behave just regular records.

>>> u = Point(1, 2)
>>> u
Point(1, 2)


Conversions and introspection
=============================

Dictionaries associate a set of keys to their corresponding values. In Python,
this is often abused as a mean of data aggregation: a string with a field name
is then associated with the corresponding field value. Dictionaries are
also extensively used internally in many places and any decent
Python programmer must have a good grasp of how to use
dictionaries and probably know most of its API.

For data aggregation, however, records offer a few advantages

1 Records are safer and cannot introduce silent bugs from typos in field names.
2 The obj.attr syntax reads and writes better than obj['attr'].
3 Records can be made reasonably type safe.

On the other hand,

4 Dictionaries are easier to introspect
5 Dictionaries is a standard language feature

While we can't do nothing about #5, Sidekick offer a few introspection
capabilities to dictionaries under the record's `_meta` and `_view` attributes.

>>> artist._view.keys()
KeysView({'name': 'John Lennon', 'band': 'Beatles'})


Record._view/Record._meta
-------------------------

The record `_view` field offers a Mapping interface to a record and support
all expected dictionary methods (e.g., keys, values, items, etc). Record types
preserve the order of key declaration, and behave like OrderedDict's.

>>> for k, v in u._view.items():
...     print('%s: %s' % (k, v))
x: 1
y: 2

The `_meta` field is class-bound and provides information about the record type

**Field names (in order of definition)**

>>> Point._meta.fields
('x', 'y')

**Default values**

>>> Point._meta.defaults
{'y': 0}

**Field types**

>>> Point._meta.types
(<class 'int'>, <class 'int'>)


Conversions
-----------

Records iterate as a sequence of (key, value) pairs and thus can be
converted to regular dictionaries using the standard dict(record) method.

>>> dict(u)
{'x': 1, 'y': 2}

We can convert a dictionary to a record using the standard unpacking syntax:

>>> Point(**{'x': 1, 'y': 2})
Point(1, 2)
