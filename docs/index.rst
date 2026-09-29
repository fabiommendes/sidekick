========================
Sidekick's documentation
========================

.. include:: warning.rst

Overview
========

Sidekick is a library of functions and types designed
to make functional programming more pleasant in Python. It emphasizes working
with simple functions, immutable and data-centric types and iterators.

Sidekick uses (or maybe abuses) Python expressiveness to introduce some specific
domain syntax and idioms that make functional programming more natural, easy to
use and still somewhat Pythonic. This approach distinguishes Sidekick from other projects like
`toolz`_, which explicitly aim to provide "low-tech" solutions based on common idioms. 

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

Functional programs value correctness, composability and ease of testing by 
using simple functions and data types as the main 
building blocks of code. There are many approaches for achieving this. A 
theoretically-oriented language like Haskell imposes restrictions on 
mutability and implement a rich and sofisticated type system. Other approaches, 
like LISP, are more pragmatic and just emphasize passing functions 
and data around.

Functional programming (FP) therfore means different things to different people. 
Sidekick is an experiment to create a practical and type-safe library within the confines 
of Python's (somewhat limited) type system. 

Contents
========

.. toctree::
   :maxdepth: 3

   intro-functions.rst
   intro-seqs.rst
   api-guide.rst
   lib-evil.rst
   lib-functions.rst
   lib-op.rst
   lib-pred.rst
   lib-properties.rst
   lib-proxy.rst
   lib-seq.rst
   references.rst
   faq.rst
   license.rst
   changelog.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
