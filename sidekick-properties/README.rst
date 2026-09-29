=======================
``sidekick.properties``
=======================

Functions in this module are helpers intended to create convenient and
declarative idioms when declaring classes. Perhaps it is not entirely correct
calling them "functional", but since some patterns such as lazy properties
are common in functional libraries, Sidekick has a module for doing that.

This library can be installed independently from the rest of sidekick distribution
using ``pip install sidekick-properties``. Prefer depending on sidekick-properties
if your project only use those functions.

Quick start
===========

.. code-block:: python

    from typing import NamedTuple
    from sidekick.properties import lazy, alias, delegate_to  # or from sidekick.api import *


    class Person(NamedTuple):
        name: str
        age: int
        full_name = alias('name')

    p = Person('Karl Heinrich', age=29)

Now ``p.full_name`` is now an alias to ``p.name``. This usage simply exposes an attribute
under a different name. :py:func:`alias` can be configured in many different ways by choosing mutability
and simple transformations between the exposed alias and the original attribute.

The code bellow creates two delegate attributes that simply redirect access to ``employee.name``
to ``employee.person.name`` (and similarly to ``.age``). Delegate attributes and methods make it
easy to compose elements in a coherent interface using an architecture that favors composition
over inheritance. It is possible to control the mutability and apply simple transformations to 
delegate attributes (see :py:func:`delegate_to` for more).

.. code-block:: python

    class Employee(NamedTuple):
        person: Person
        role: str
        name = delegate_to('person')
        age = delegate_to('person')

        @lazy
        def photo(self):
            return download_from_server(f'http://url.img/employees/{self.name}')
        

Finally, the ``@lazy`` decorator marks a property that is computed lazily at first access.
Differently from regular Python properties, lazy properties only execute the decorated function 
during first access. Lazy initializers can be used for optimization by avoiding an expensive 
computation that may not be necessary or as an architectural choice that decouples attribute 
initialization from object construction.

Be aware that lazy properties can slightly degrade performance for properties that are 
always computed during the lifetime of an object. If squeezing every bit of performance 
is important, compute them in __init__.
  