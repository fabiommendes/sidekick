======================
Sequence and iterators
======================

.. module:: sidekick

We already said that good functional code looks like LEGO bricks: it consists of simple
blocks that fit together naturally in various different ways. This flexibility does not
happen by accident: it is a feature of using simple functions associated with flexible
data structures and interfaces. Many functional languages choose some data structure
(e.g., a linked list) as a preferred way to organize data and thus implement many
functions that operate on those structures. Python already has some very useful data
structures like dictionaries, lists and sets, but unfortunately none of them fit
very naturally functional code because using those types often entails mutability.
Perhaps the most versatile builtin type is not even a data structure on its own, but the
*iterator* protocol. Lists, tuples, sets, dictionaries all implement the iterator
protocol and Python even offers additional builtin support in the form of generators
and generator functions.

For this flexibility, we chose the main data-processing module in Sidekick to work
exclusively with iterables. It creates iterables, transform them, consume them,
augment them, etc. This confluence of functional code with iterators is perhaps a
little surprising Functional programming values immutability of data and iterators
are extremely mutable data structures. Almost any useful operation in an iterator
mutate it: item access  mutate it, checking if it is exhausted mutate it, finding
its length mutate it, and so on. This volatile nature of iterators means that we
often transform them using pipelines of functions and any input iterators are
created only to feed the pipeline.

It is generally a bad idea to hold references
to iterators for too long. Avoid saving them as attributes in objects, global
variables or as default values in functions. A nice way to put it: iterators are
not data, they are a recipe to produce data. If you want to store an iterator,
prefer to store a recipe to initialize it rather then the iterator itself. That way
your code has a chance to be reproducible since different invocations will not alter
the state of the iterator and produce different results.


Generators, comprehensions, etc
===============================

LISP, the grandmother of all functional programming languages uses linked lists
as the main data structure in the language. Linked lists are nicely integrated
into the language both syntax-wise and in the standard library of functions.
This tradition of using linked lists is proudly followed by most functional
programming languages.

As much as we can implement a LinkedList class in Python (and we do), it has
no special support in the language, which can make its use a little bit awkward.
Sidekick wants to speak Python and not simply translate LISPy or Haskellian
idioms to the language. That is why we opted for using iterators as the pervasive
data container. Python has tons of support for it and by following it we can expect
Sidekick functions to be useful alongside functions from other libraries and
frameworks. Using our own linked list class would put us in an island.

As much as iterators and iterables are nicely integrated in the language and
are essential in idiomatic Python code, this topic is often treated as "advanced",
so a little refresher should be handy.

Python has "iterables" and "iterators". Iterators are basically objects with a
"iterator.__next__()" method that either returns the next element of the
iterator or raises an StopIteration exception. Iterables are just objects that can
produce iterators by calling its "iterable.__iter__()" method. Iterators are
iterables, since they can simply return themselves in its __iter__() implementation.

As an example, the code bellow produces an iterator that counts from 0 to n:

.. testcode::

    class Counter:
        def __init__(self, n):
            # We save the state of the iterator, the maximum number n
            # and its current value.
            self.n = n
            self.value = 0

        def __iter__(self):
            # Returns an iterator. But since Counter instances are iterators,
            # we return self
            return self

        def __next__(self):
            # That is the main code: return the current value and increment
            # the iterator. If value is greater than n, stop iteration.
            if self.value > self.n:
                raise StopIteration
            else:
                next = self.value
                self.value += 1
                return next


Now our Counter can be used in for loops, to create lists, and any place that
Python expects an iterable.

>>> for i in Counter(3):
...     print(i)
0
1
2
3
>>> list(Counter(3))
[0, 1, 2, 3]

This is obviously too much work for such a simple iterator. It is very rare
that we need (or should) to actually implement iterators using the low level
class interface. Python has much better ways. If the iterator is simple enough,
we can get away with generator expressions: they produce iterables from a
for loop wrapped inside parenthesis:

>>> def counter(n):
...     return (i for i in range(n + 1))
>>> list(counter(5))
[0, 1, 2, 3, 4, 5]

We can check for the existence of the __iter__ and __next__ methods

>>> gen = counter(3)
>>> gen.__iter__() is gen  # the __iter__ method return self!
True
>>> gen.__next__()
0
>>> gen.__next__()
1

True Pythonistas would not call the __next__ method directly, but rather use the
next() function that does just that. The next() function also accepts a second
optional argument that declares a default value to use if the iterator is exhausted.

>>> next(gen)
2
>>> next(gen, None), next(gen, None), next(gen, None)
(3, None, None)

It is hard to argue against the generator expression for the class based definition
in this simple example. The generator expression only works, however, because the
pattern of data generated is so simple that it fits in a single expression inside
the for loop. For more complex cases, Python provides generator functions: those
are special functions that create generators and can stop and resume execution
each time the generator's __next__ method is called. Generator functions distinguishes
from regular functions by using the yield keyword to produce values (and pause execution
until __next__ is called again. Our counter would be implemented like this:

>>> def counter(n):
...     for i in range(n + 1):
...         yield i   # Notice the yield instead of return!

This behaves exactly as the previous implementation using generator expressions.

>>> gen = counter(5)
>>> next(gen), next(gen), next(gen)
(0, 1, 2)

Now that we have the full power of functions at our disposal, it is possible to
produce much more sophisticated patterns. Check the darling of all programmers,
the Fibonacci numbers:

>>> def fibo():
...     x, y = 1, 1
...     while True:
...         yield x
...         x, y = y, x + y
>>> fibs = fibo()
>>> next(fibs), next(fibs), next(fibs), next(fibs), next(fibs), ...
(1, 1, 2, 3, 5, ...)

There are many details not covered here, but this introduction should be enough
to understand the following sections.


The 3 classics
==============

Introductory explanations of what functional programming is about often start with
three functions: :func:`map`, :func:`reduce`, and :func:`filter`. It is no
surprise: those 3 very simple functions encode common control flow patterns
that occur very frequently and are a great example of how functional
programming can abstract control flow and data processing by using functions.

Python has builtin "map" and "filter" and it is possible to import "reduce" from
the "functools" module from the standard lib. Sidekick has drop-in replacements
for those functions with a few additional goodies.

Map and filter are more or less equivalent to the following generator expressions

.. code-block:: python

    sk.map(func, seq)    == (func(x) for x in seq)
    sk.filter(pred, seq) == (x for x in seq if pred(x))

One advantage of generators is that it is easy combine both map and filter
in the same operation and while still keeping a decent level of legibility. This
is specially true if ``func`` and ``pred`` are defined by lambda expressions, which
tends to clutter the syntax.

However, list comprehensions do not compose very well. In sidekick,
map and filter are curried functions, which means that we can easily
create new useful methods by simply omitting the second argument. This
is good not only to create new functions, but also to organize code in
a pipeline of data transformations.

>>> drop_nulls = sk.filter(lambda x: x is not None)
>>> drop_nulls([1, 2, None, 3, None, 4])
sk.iter([1, 2, 3, 4])

Map and filter replace for loops that transform or filter content and
reduce is a functional replacement for a for loop used as an accumulator.
Consider the simple for loop bellow:

.. code-block:: python

    acc = 0
    for x in seq:
        acc = acc + x

We express it functionally using the pattern

>>> seq = range(11)
>>> sk.reduce(lambda x, y: x + y, seq, initial=0)
55

The reduce function uses a binary operator (in this case, the "+" operator) to
accumulate the result of an operation across every element of a sequence. In this
case it is equivalent to ``((((0 + a) + b) + c) + d) + ...)`` where the values
a, b, c, d, etc where taken from the list.

While the imperative version of map/filter/reduce using for loops is often
easier to read and understand, it suffers from some important disadvantages.
First, it is not very much reusable. The code above that sums the elements of
a list is rather a template (or if you want, a pattern) that you can copy and
paste and adapt to any situation in which it is necessary to sum elements of a
list. The functional version has a much more elegant approach for code reuse:
simply partially apply arguments to obtain a sum() function from
``sum = sk.reduce(lambda x, y: x + y, initial=0)``. Besides that, map and filter
do not create concrete results, but rather return a pattern yield a sequence of
elements from an input stream of values. We can pass a mapped or filtered sequence
forward to other data transformation functions and create a very versatile
data transformation pipelines. This is much more complicated with the imperative
version, and usually involves storing values in temporary arrays, which tends
to be cumbersome and memory inefficient.
