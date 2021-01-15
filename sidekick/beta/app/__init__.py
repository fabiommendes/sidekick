"""
============
Applications
============

.. module:: sidekick

Sidekick emphasizes function-oriented programming. In this spirit, we believe that
conversion of regular Python functions to full-blown deployed programs should be as
seamless as possible. In that spirit, programs in sidekick are represented by functions
or records of functions and are easily deployed with minimal adaptations through the
backends in sidekick.apps.

Let us create the classic Fibonacci calculator.

.. code-block:: python

    from typing import Iterable

    def fib(n: int = float('inf')) -> Iterable[int]:
        x, y = 1, 1
        for _ in range(n - 1):
            x, y = y, x + y
            yield x

Save it on "fib.py", and execute it by running::

    $ python -m sidekick.beta.app.cli fib.py:fib 10

This should display the 10 first fibonacci numbers. Conversions from arguments to proper
Python values are inferred using the help from optional type hints. The app tries to
reuse information already declared in the string as much as possible, including type
hints, the function name and docstring.

We can invoke the function as an app explicitly passing fib to the :func:`run` function
of the :mod:`sidekick.app.cli` module.

.. code-block:: python

    from sidekick.beta.app.cli import run

    def fib(n: int = float('inf')) -> Iterable[int]:
        ...

    run(fib)


The beautiful thing of functions being this universal representation, is that we can
easily plug our fibonacci function to different backends. It can be anything from a
Google Cloud Function to an Electron app. The process is mostly plug-and-play and we
might simply import a different backend and let sidekick take care of the rest.


.. code-block:: python
    from sidekick.app.flask import run

    def fib(n: int = float('inf')) -> Iterable[int]:
        ...

    run(fib)


Most backends accept apps both as functions or as modules. A module is an object that
stores functions on its attributes. Each backend interpret it in a different fashion.


.. code-block:: python

    from typing import Iterable

    def seqs(n: int = float('inf'), start: int = 1, end: int = 1) -> Iterable[int]:
        x, y = start, end
        for _ in range(n - 1):
            x, y = y, x + y
            yield x


    def fib(n: int = float('inf')) -> Iterable[int]:
        return seqs(n, 1, 1)


    def lucas(n: int = float('inf')) -> Iterable[int]:
        return seqs(n, 1, 3)


    if __name__ == '__main__':
        from sidekick.beta.app.cli import run
        from sidekick.api import record

        return run(record(fib=fib, lucas=lucas))


We could also run the module with the command `python -m sidekick.beta.app.cli 'fib.py' fib 10`.


Backends
========

Cli
---

The CLI backend is based on Typer_ (which is based on click_) with a few additions.

.. _Typer: https://typer.tiangolo.com/
.. _click: https://click.palletsprojects.com/

**API reference**

.. automodule:: sidekick.app.cli
   :members:
   :inherited-members:
"""
from ...proxy import import_later

cli = import_later(".cli", package=__package__)
gcf = import_later(".gcf", package=__package__)
