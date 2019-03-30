========
Sidekick
========

Sidekick is a library that gives you functional superpowers.

.. image:: https://travis-ci.org/fabiommendes/sidekick.svg?branch=master
    :target: https://travis-ci.org/fabiommendes/sidekick
.. image:: https://codecov.io/gh/fabiommendes/sidekick/branch/master/graph/badge.svg?
    :target: https://codecov.io/gh/fabiommendes/sidekick
.. image:: https://codeclimate.com/github/fabiommendes/sidekick/badges/gpa.svg?
    :target: https://codeclimate.com/github/fabiommendes/sidekick
.. image:: https://codeclimate.com/github/fabiommendes/sidekick/badges/issue_count.svg?
    :target: https://codeclimate.com/github/fabiommendes/sidekick


Sidekick implements a functional standard library of functions and types that
make functional programming more pleasant in Python. It uses modern Python
features and requires at least Python 3.6+.


Quick start
===========

Install it from pip

::

    $ pip install sidekick

Now import the most important names

>>> from sidekick.all import sk, op, L

Sidekick emphasizes working with immutable types and iterators. It also
introduces a special embedded syntax for handling function composition and
easy creation of new functions.

Walk through the examples bellow to get a taste of what you can do with
sidekick.

**Fibonacci numbers**

Easily generate sequences of infinite Fibonacci numbers

>>> fibonacci = sk.iterate_past(2, op.add, [1, 1])
>>> fibonacci | L[:10]
[1, 1, 2, 3, 5, 8, 13, 21, 34, 55]


**Golden ratio**

We just consumed the first 10 Fibonacci numbers. We can continue to walk the
sequence to find the golden ratio.

>>> ratios = sk.map(op.rdiv.splice, sk.window(2, fibonacci))
>>> sk.until_convergence(op.eq, ratios) | sk.last
1.618033988749895


**Euler number**

We are using Taylor formula to compute the Euler number from exp(1)

>>> factorials = sk.iterate_indexed(op.mul, 1, start=1)
>>> sk.last(sk.until_convergence(op.eq,
...                              sk.sums(sk.map(op.div(1), factorials))))
2.7182818284590455


**Sieve of Eratosthenes**

For each prime we find, we remove it from the infinite sequence of integers

>>> def sieve(nums):
...     p, nums = sk.uncons(nums, default=None)
...     if p is not None:
...         yield p
...         yield from sieve(n for n in nums if n % p != 0)
>>> primes = sieve(sk.seq[2, ...])
>>> primes | L[:10]
[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


See also
========

Sidekick is heavily inspired by other libraries and functional programming
languages. Most notably

* `toolz`_: excellent utility library for handling iterators.
* `placeholder`_, `fn.py`_, `funcy`_, `Pyrsistent`_: other functional programming libraries for Python.
* `Haskell`_: great inspiration. If you want to learn Haskell, I recommend learning `Elm`_ first.
* `Clojure`_ and `Elixir`_: inspiration for part of the API.
* `Lodash`_: a practical functional Javascript library. Also inspired a few functions.


.. _toolz: https://toolz.readthedocs.io/en/latest/
.. _placeholder: https://placeholder.readthedocs.io/en/latest/
.. _fn.py: https://pypi.org/project/fn/
.. _funcy: https://funcy.readthedocs.io/en/latest/
.. _Pyrsistent: https://pyrsistent.readthedocs.io/en/latest/
.. _Haskell: http://hackage.haskell.org/package/base-4.12.0.0/docs/Data-Data.html
.. _Elm: https://elm-lang.org/
.. _Clojure: https://clojuredocs.org/clojure.core
.. _Elixir: https://hexdocs.pm/elixir/Kernel.html
.. _Lodash: https://lodash.com/