====================
``sidekick.lambdas``
====================

Easy and fast quick lambdas with no boilerplate.


Installation
============

::
    pip install sidekick-lambdas


Usage
=====

Quick lambdas come in two flavors. The ``X`` and ``Y`` magic objects and the ``_`` placeholder.
The first two instantly create functions when called with any operator:

>>> from sidekick.lambdas import X, Y
>>> func = X + 1
>>> func(41)
42

This is useful to create throwaway functions to pass to other higher order functions like map and filter.

>>> [*map(2 * X, [1, 2, 3])]
[2, 4, 6]

The difference between ``X`` and ``Y`` is that the first creates functions of a single argument, while the
second creates functions of two arguments. We can easily mix both.

>>> from functools import reduce
>>> reduce(X + Y, [1, 2, 3])
6

One important limitation of those magic objects is that any operation on them automatically 
creates a function. This prevents the use of more complex expressions. If we want to create
a function like ``lambda x: 2 * x + 1``, those quick lambdas will not work. The first part of 
the expression, ``2 * X`` would immediately return a function, which cannot be 
added to the ``1`` term, raising a TypeError.

In order to circumvent this limitation, this library also provides a placeholder object that can 
create arbitrary expressions. The downside is that they require an intermediate 
compilation step to convert the expression tree in an actual function. Calling the placeholder object 
would create an expression that represents a function call, rather than executing the underlying function.

>>> from sidekick.lambdas import _, compile
>>> func = compile(2 * _ + 1)
>>> func(2)  # 2 * 2 + 1  =>  5
5

We can minimize typing by aliasing the ``compile`` function with a shorter name or
using functions that understand placeholder expressions. Fortunately, all functions in the
sidekick api understand it and automatically compile placeholder expressions in places 
that expect a function.

>>> from sidekick.lambdas import _, compile as fn
>>> fn(_.foo + 1)  # slightly shorter than `lambda x: x.foo + 1`

Sidekick functions do the compilation for us automatically, which is very convenient.

>>> from sidekick.seq import iterate
>>> iterate(2 * _ + 1, 1)
sk.iter([1, 3, 7, 15, 31, ...])

Finally, if you want to create functions that support placeholder expressions instead of a callable,
simply wrap the function argument with compile.

.. code-block:: python 

    def call_twice(func, x):
        func = compile(func)
        return func(func(x))

:func:`compile` compiles placeholder expressions and pass any other callables as-is. It is therefore safe to
add this preparation step to existing functions, since regular callables are still going to be supported.

After this modification, all of these expressions become equivalent

>>> call_twice(lambda x: x + 1, 40)
42
>>> call_twice(X + 1, 40)
42
>>> call_twice(_ + 1, 40)
42