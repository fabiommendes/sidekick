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


Sidekick implements a functional standard library of functions and types designed
to make functional programming more pleasant in Python. It uses modern Python
features and requires at least Python 3.6+.

Sidekick emphasizes working with immutable types and iterators. It also
introduces a special embedded syntax for handling function composition and
easy creation of new functions.



Quick start
===========

Install it from pip...

::

    $ pip install sidekick

... and import a few important names

>>> from sidekick.all import sk, op, X, Y, L, N

The examples bellow show a taste of what you can do.



Fibonacci numbers
-----------------

Let us start with the classics. This produces an infinite sequences of
Fibonacci numbers

>>> fibonacci = sk.iterate((X + Y), 1, 1)
>>> fibonacci
sk.iter([1, 1, 2, 3, 5, 8, ...])

**Explanation**

``iterate`` creates an infinite iterator that generates each number
by applying the function in the first argument to the last n elements generated
by the sequence. The sequence is initialized with the following arguments and hence
``n`` in our example is 2. The Fibonacci sequence is created by always adding
the last two elements.

We construct our summation function using the magic objects ``X`` and ``Y``.
They are function factories that return lambdas corresponding to the expression
in which they participate. Hence, ``X + 1`` corresponds to ``lambda x: x +1``
and ``X + Y`` to ``lambda x, y: x + y``. If you are familiar to any language in the
Haskell family, it should resemble the `operator section syntax <https://wiki.haskell.org/Section_of_an_infix_operator>`.

In a similar vein, the ``L`` magic object that wraps many useful operations on lists.
In the example above, L[:10] creates a function that return a list slice
in the range of 0 to 10 (not included). ``L[0]`` would create a function that fetches
the first element, ``L[::2]`` would fetch every two elements, and so on.

Finally, the pipe notation passes the argument on the left to the function on
the right. This only works on sidekick enabled functions and mimics
the pipe in the unix shell. Maybe someday Python can have a native pipe operator
like `other functional languages <https://elm-lang.org/docs/syntax#operators>`.



Golden ratio
------------

The snippet above only consumes the first 10 Fibonacci numbers. Let us continue
to walk the sequence to find a good approximation to the golden ratio.

>>> ratios = (y / x for (x, y) in sk.window(2, fibonacci))
>>> sk.last(sk.until_convergence((X == Y), ratios))
1.618033988749895

**Explanation**

``window`` produces a sliding window of n elements from the
original sequence, e.g., ``sk.window(2, [1, 2, 3, 4])`` ==> ``(1, 2), (2, 3), (3, 4)``.
The generator comprehension then compute ratios using those consecutive elements.

Finally, the second line iterate over a sequence until the predicate function
in the first argument of ``sk.until_convergence`` returns True. Rather than
setting up some small interval of variation, we test for equality and wait
for the difference between two evaluations be smaller than floating point
precision.



Euler number
------------

The following snippet uses Taylor formula for exponentials
$\exp(x) = \sum_{n=0}^{\infty} \frac {x^n} {n!}$to compute the Euler number

>>> factorials = sk.iterate_indexed((X * Y), 1, start=1)
>>> partial_sums = sk.sums(map((1 / X), factorials))
>>> sk.last(sk.until_convergence((X == Y), partial_sums))
2.7182818284590455

**Explanation**

``iterate_indexed`` iterates a function ``f(i, x)`` passing both the index
of iteration and the last evaluation of x to generate the next result. By writing
write down a few examples it is easy to see that the given arguments produce a
sequence of factorials.

The second step creates a sequence of partial sums of the reciprocal of each
factorial. Finally, we iterate until convergence, testing if two consecutive
elements are equal.



Sieve of Eratosthenes
---------------------

The `Sieve of Eratosthenes <https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes>`
is a simple algorithm for selecting all primes in an list of consecutive integers.
The list must start with the first prime p (a.k.a., 2), and proceed by excluding
every p element. The next valid number will be a prime p'. The
procedure is repeated with each new prime until reaching the end of the list.

We will do it like so, except that the initial list of numbers is infinite.

>>> @sk.generator
... def sieve(nums):
...     p, nums = sk.uncons(nums)
...     yield p
...     yield from sieve(n for n in nums if n % p != 0)
>>> sieve(N[2, 3, ...])
sk.iter([2, 3, 5, 7, 11, 13, ...])

**Explanation**

The fist line in the sieve function uses ``uncons`` to extract the first
element and return an iterator over the remaining ones. As we
described before, the first element is a prime, so we just yield it. The
last line of the function applies the sieve to a sequence that excludes every
multiple of p.

Finally, we call sieve with the numbers ``2, 3, ...``. The numbers are created
by the special object `N`, specialized in creating numeric sequences.
It is very flexible, and in the example above it
creates natural numbers starting from 2 and proceed indefinitely in steps
of 1. In fact, we could easily make our code operate twice as fast simply
by initializing the sieve with ``N[2, 3, 5, ...]`` so it would moves in steps
of two rather than one. This would avoid checking even numbers which we known in
advance not be primes.


See also
========

Sidekick is heavily inspired by other libraries and functional programming
languages. Most notably,

* `toolz`_: excellent utility library focused on handling iterators.
* `placeholder`_, `fn.py`_, `funcy`_, `Pyrsistent`_: other functional programming libraries for Python.
* `Haskell`_: an essential inspiration to functional programming. You will see many ideas stolen
  directly from Haskell. If you want to learn Haskell, however, I recommend learning `Elm`_ first ;)
* `Clojure`_ and `Elixir`_: inspiration for many parts of the API.
* `Lodash`_: a practical functional Javascript library.


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
