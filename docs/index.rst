========================
Sidekick's documentation
========================

.. include:: warning.rst

Overview
========

Sidekick is a functional library of functions and types designed
to make functional programming more pleasant in Python. It emphasizes working
with simple functions, immutable and data-centric types and iterators.

Sidekick uses (or maybe abuses) Python expressiveness to introduce some specific
domain syntax and idioms that makes functional programming more natural, easy to
use and still somewhat Pythonic. This approach distinguishes Sidekick from other projects like
`toolz`_, which explicitly aim to provide "low-tech" solutions based on common idioms or
other libraries that simply port ideas and libraries from other programming languages to
Python (even when that means alien Haskell-isms).

There are obvious limitations of what we can do syntax-wise as a library, and
more so in what we can provide that will still play nicely with the rest of Python
ecosystem. Sidekick is just one proposal in trying to find a nice balance between
practicality and theoretical purity, between expressiveness and familiarity. There are
many other excellent libraries in this landscape which can also be used alongside
with Sidekick, and we certainly want to encourage you to explore other options
in Python and in other programming languages as well.

.. _toolz: https://toolz.readthedocs.io/en/latest/


So, what's up with functional programming?
------------------------------------------

Since functional programming (FP) means different things to different people, it is perhaps
necessary to point out where we want to go with Sidekick. People often point at
correctness, composability and ease of debugging and testing as major motivations.
Those are certainly worthy goals when trying to design any system and functional
programming offers some guidelines that help us to stay on track. Those ideas are
fundamental to grasp real FP languages like Haskell, but are also useful in generic
multi-paradigm languages such as Python.


Contents
========

.. toctree::
   :maxdepth: 3

   intro-functions.rst
   api-guide.rst
   lib-functions.rst
   lib-seq.rst
   references.rst
   faq.rst
   license.rst
   changelog.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
