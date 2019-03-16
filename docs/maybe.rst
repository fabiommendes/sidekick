==============
The Maybe type
==============

Sidekick's Maybe is declared essentially as:

.. code-block:: python

    class Maybe(Union):
        Nothing = opt()
        Just = opt(value=object)



API reference
=============

.. autoclass:: sidekick.Maybe
    :noindex:
.. autofunction:: sidekick.maybe
    :noindex:
