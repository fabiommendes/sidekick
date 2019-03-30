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

>>> ratios = sk.map(op.div.splice, sk.window(2, fibonacci))
>>> sk.until_convergence_by(op.eq, ratios) | sk.last
1.6123242


.. cmt
    >>> factorials = sk.iter_indexed(1, op.mul, start=1)
    >>> 1 + sum(sk.stop_at_convergence(op.eq, sk.map(1 / X, factorials)))
    2.7172727232

.. cmt
    >>> def sieve(nums):
    ...     p = next(nums)
    ...     return sk.cons(p, sieve(sk.filter(X % p, nums))
    >>> primes = sieve(sk.seq[2, ...])
    >>> sk.take(20, primes) | L


See also
========

Sidekick is heavily inspired by other libraries and functional programming
languages. Most notably

* `toolz`_: excellent utility library for handling iterators.
* `placeholder`_, `fn.py`_, `funcy`_, `Pyrsistent`_: other functional programming libraries for Python.
* `Haskell`_: great inspiration. If you want to learn Haskell, I recommend learning `Elm`_ first.
* `Clojure`_ and `Elixir`_: inspiration for part of the API.
* `Lodash`_: a practical functional Javascript library. Also inspired a few functions.




