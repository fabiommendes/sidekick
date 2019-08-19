==============
The Maybe type
==============

Sidekick's Maybe is declared essentially as:


.. code-block:: python

    from sidekick import Union, Case

    class Maybe(Union):
        Nothing: Case()
        Just: Case('value')


Some static languages "solve" this problem by sneakingly accepting
None (or null) as a valid value for any type. Tony Hoare, who pioneered this
approach in Algol W latter acknowledged that null references were a terrible
idea and called it his "billion dollar mistake".

In Haskell, that is solved using the Maybe type: this is a type that explicitly
encodes the two different success/error states:

    Nothing -- No value was produced.
    Just(x) -- Produced "just" x.


API reference
=============

.. autoclass:: sidekick.Maybe
    :noindex:
.. autofunction:: sidekick.maybe
    :noindex:


