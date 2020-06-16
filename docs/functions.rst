====================================
A library for functional programming
====================================

Functional programming, as the name implies, leans heavily towards using functions
for solving problems. This contrasts with other approaches as, for instance,
organizing code with classes or even relying too much on standard control flow
structures such as ``for``, ``if``'s, ``with``, etc.

Python is a multi-paradigm language that allows functional programming but was not
conceived specifically for it. Functional programming is only practical if we have
means of easily creating new functions and using them in cooperation. This means that
functional code tends to be littered with many small functions that are passed to
other (high order) functions to accomplish some elaborate task. Think of those functions
This is just like Lego bricks: they are simple, easy to grasp, tend to fit nicely
with each other, but when used in conjunction can create elaborate structures.

Creating functions in Python usually means lots of ``def`` statements
and ``lambdas`` [#lambda]_. This approach is perhaps a little bit clumsy for everyday
use, hence Sidekick provides more efficient ways to construct new functions by
implementing some new functionality on top of standard Python idioms. Those novel
approaches follow from one of 4 ideas:

1) Specialization_: constrain a function by fixing some of its arguments.
2) Composition_: join two or more functions to generate a new function that inherit behaviors of both.
3) Transformations_: transform functions to obtain new functions with slightly different behavior.
4) Creation_: provide easy ways to construct commonly used lambdas.

We will discuss those ideas in detail in the next sections.

.. [#lambda] The name "lambda" has roots in lambda calculus, but do not expect
   beginners to make any sense of this. The lambda syntax was borrowed from LISP,
   in which the author of the language really wanted to make the association with
   lambda calculus explicit.


.. _Specialization:

Creating functions by specialization
====================================

Consider a simple function:

.. code-block:: python

    def succ(n: int) -> int:
        """
        Return the next integer after n.
        """

        return n + 1


It seems like it is only a function declaration, but in reality it does a few
more things: it gives the function a name, defines its documentation string and
sets an implicit scope for global variables. For top level functions of your
public API, in which it is recommended to declare all those properties, this is an
efficient syntax.

Put the same function in a different context and ``def`s` start to feel verbose:

.. code-block:: python

    def increment_all(numbers):
        def succ(n):
            return n + 1

        return map(succ, numbers)

Not only this code spends two whole lines to define such a trivial function, it
forces us to explicitly come up with a name which does not clarify its intent
anymore than seeing ``n + 1`` in the body of the function. `Naming is hard`_,
and we should avoid doing it if it has no purpose in making some piece of code
more readable or comprehensible.

.. _Naming is hard: https://martinfowler.com/bliki/TwoHardThings.html

Lambdas are a much better fit for this case:

.. code-block:: python

    def increment_all(numbers):
        return map(lambda x: x + 1, numbers)


But even that definition can be improved. ``lambda x: x + 1`` is just a
special case of addition in which one of the arguments is one. Indeed, that
notion that we can create new functions by "specializing" more generic functions
is very a common functional programming idiom. Python does not have
have a builtin system for doing that, but we can use a few functions from the
standard lib for the same effect.

.. code-block:: python

    from functools import partial
    from operator import add

    def increment_all(numbers):
        return map(partial(add, 1), numbers)


I wouldn't say it provides any tangible advantage over the previous case, but
this code illustrates a powerful technique that can be really useful in other
situations. We now want to take the good ideas from this example and make
them more idiomatic and easy to use.


Currying
--------

When analyzing programs, it is useful to assume that all functions receive a
single argument and return a single result. There
are two common ways to convert any multi-argument function to one that receive
a single argument and return a single value. The most obvious, perhaps, is
to think that arguments are passed as a single tuple, so a function of two
arguments becomes equivalent to a function that receive a tuple with two
elements and return some value.

The second approach is to think that a multi-argument function is just a function
that returns a second function that receives the remaining arguments. The function
is evaluated only after the last argument is passed. This strange encoding is called
*"currying"* after the computer scientist Haskell Curry, and is a very important
idea in a foundational field of computer science called `Lambda calculus`_.

.. _Lambda calculus: https://en.wikipedia.org/wiki/Lambda_calculus

Bellow we convert the "add" function using both approaches:

.. code-block:: python

    def add_tuple(args):
        return args[0] + args[1]

    def add_curried(x):
        return lambda y: x + y

As crazy as ``add_curried`` may look, it is so powerful that some languages
adopt it as their standard way of calling functions. This does not work
very nicely Python, however, because the syntax becomes ugly and execution
inefficient:

>>> add(1, 2) == add_tuple((1, 2)) == add_curried(1)(2) == 3
True

A nice middle ground between the standard multi-argument function and the fully
curried version is called "auto-currying": we execute the function normally if
the callee passes all arguments, but curry it if some of them are missing. An auto-curried
``add`` function is implemented like this:

.. code-block:: python

    def add(x, y=None):
        # y was not given, so we curry!
        if y is None:
            return lambda y: x + y

        # y was given, hence we compute the sum
        else:
            return x + y

>>> add(1)(2) == add(1, 2)
True

One nice thing about auto-currying is that it doesn't break preexisting
interfaces. This new add function continues to be useful in contexts that the
standard implementation would be applied, but it now also accepts receiving an
incomplete set of arguments transforming add in a convenient factory.

Even for only two arguments, implementing auto-currying this way already
seems like a lot of trouble. Fortunately, the :func:`sk.curry` decorator
automates this whole process and we can implement auto-curried functions
with very little extra work:

.. code-block:: python

    import sidekick.api as sk

    @sk.curry(2)  # The 2 stands for the number of arguments
    def add(x, y):
        return x + y

Ok, it is good that we can automatically curry functions. But why would anyone
want to do that in any real world programming problem?

Remember when we said that the increment function (``lambda x: x + 1``) was just
a special case of addition when one of the arguments is was fixed to 1? This kind of
"specialized" functions are trivial to create using curried functions: just apply
the arguments you want to fix and the result will be a specialized version
of the original function:

>>> incr = add(1)  # Fix first argument of add to 1
>>> incr(41)
42

While the magic X object created a way of declaring simple "specializations"
of standard Python operators, currying opens this possibility for any ordinary
function. Indeed, most of sidekick's functions are curried and we also provide
curried versions of Python's builtins and some modules from the standard
library.


The magic X,Y
-------------

Operators like ``+, -, *, /``, etc are functions recognized as being so useful
that they deserve an special syntax. They are obvious candidates for creating a
library of factory functions such as:


.. code-block:: python

    def incrementer(n):
        return lambda x: x + n

    def multiplier(n):
        return lambda x: x * n

    ...


While there is no denying that those functions might be useful, such a library
probably is not. It is hard to advocate for this approach when it is easier to
define those simple one-liners on the fly than actually remembering
their names.

Sidekick implements a clever approach that first appear in Python in popular
functional programming libraries such as `fn.py`_ and `placeholder`_. It exposes
the "magic argument object" ``X`` that creates
those simple one-liners using a very straightforward syntax: every operation
we do with the magic object X, returns a function that would perform the same
operation if X was the argument. For instance, to tell the X object to create a
function that adds some number to its argument, just add this number to X:

.. code-block:: python

    from sidekick.api import X

    incr = X + 1  # same as lambda x: x + 1

.. _placeholder: https://pypi.org/project/placeholder/
.. _fn.py: https://pypi.org/project/fn/

#TODO: limitations, function calling, attributes, recipes, remove the call function?
#TODO: bitwise operators?

In a similar spirit, there is a second operator Y for creating functions of
two arguments:

.. code-block:: python

    from sidekick import X, Y

    div  = X / Y  # same as lambda x, y: x / y
    rdiv = Y / X  # same as lambda x, y: y / x

Y is consistently treated as the second argument of the function, even if the
expression does not involve X. Hence,

>>> incr = Y + 1  # return lambda x, y: y + 1
>>> incr("whatever", 41)
42




+===============+==========================+
| Python Module | Sidekick                 |
+---------------+--------------------------+
| `operator`_   | :mod:`sidekick.op`       |
+---------------+--------------------------+
| `math`_       | :mod:`sidekick.math`     |
+---------------+--------------------------+
| `builtins`_   | :mod:`sidekick.builtins` |
+---------------+--------------------------+

.. _operator: https://docs.python.org/3/library/operator.html
.. _math: https://docs.python.org/3/library/math.html
.. _builtins: https://docs.python.org/3/library/builtins.html
