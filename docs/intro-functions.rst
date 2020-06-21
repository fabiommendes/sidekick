======================================
Introduction to functional programming
======================================

Functional programming, as the name implies, leans heavily towards using functions
for solving problems. This contrasts with other approaches as, for instance,
organizing code with classes or even relying too much on standard control flow
structures such as ``for``, ``if``'s, ``with``, etc.

Python is a multi-paradigm language that allows functional programming but was not
conceived specifically for it. Functional programming is only practical if we have
means of easily creating new functions and using them in cooperation. This means that
functional code tends to be littered with many small functions that are passed to
other (high order) functions to accomplish some elaborate task. Think of those functions
as Lego bricks: they are simple, easy to grasp, tend to fit nicely with each other,
but when used in conjunction can create elaborate structures.

Creating functions in Python usually means lots of ``def`` statements
and ``lambdas`` [#lambda]_. This approach is perhaps a little bit clumsy for everyday
FP use, hence Sidekick provides more efficient ways to construct new functions by
implementing some new functionality on top of standard Python idioms. Those
approaches can be split into 3 basic ideas:

1) Specialization_: constrain a generic function by fixing some of its arguments.
2) Creation_: provide easy ways to construct commonly used lambdas.
3) Composition_: join two or more functions to generate a new function that inherit behaviors of both.

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
public API, in which you probably want to declare all those properties, this is a
very efficient syntax.

Put the same function in a different context and ``def`s` start to feel verbose [#map]:

.. code-block:: python

    def increment_seq(numbers):
        def succ(n):
            return n + 1

        return map(succ, numbers)

.. [#map] For those who do not remember, the builtin map function takes a function
   and a sequence as arguments and apply the function in all elements of the
   sequence. The code above thus increment each element in a sequence of numbers
   by one.

Not only this code spends two whole lines to define such a trivial function, it
forces us to explicitly come up with a name which does not clarify its intent
anymore than seeing ``n + 1`` in the body of the function. `Naming is hard`_,
and we should avoid doing it if it has no purpose in making some piece of code
more readable or comprehensible.

.. _Naming is hard: https://martinfowler.com/bliki/TwoHardThings.html

Lambdas are a much better fit for this case:

.. code-block:: python

    def increment_seq(numbers):
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

    def increment_seq(numbers):
        return map(partial(add, 1), numbers)


I wouldn't say it provides any tangible advantage over the previous case, but
this code illustrates a powerful technique that can be really useful in other
situations. We now want to take the good ideas from this example and make
them more idiomatic and easy to use.


Currying
--------

A simple function receives one single parameter and return a single value.
In Python and most programming languages, the "function interface" can be
considerably more complicated: the function might receive several parameters,
keyword arguments, splicing (the *args and **kwargs expansions), and it might
even produce side effects outside of what is visible from the inputs and
outputs of the function.

If is often convenient for computer scientists to pretend in an idealized world
in which all functions receive a single argument and return a single value. In
fact, it is not even hard to transform some of those real world functions in this
idealized version. Consider the function bellow:

.. testcode:: default

    def add(x, y):
        return x + y

This "complicated" two argument function can be easily simplified into a
single argument function by passing x and y as values in a tuple, as such:

.. testcode:: default

    def add_tuple(args):
        return args[0] + args[1]


A second approach is to think that a multi-argument function is just a function
that returns a second function that receives the remaining arguments. The function
is evaluated only after the last argument is passed. This strange encoding is called
*"currying"* after the computer scientist Haskell Curry, and is a very important
idea in a foundational field of computer science called `Lambda calculus`_.

.. _Lambda calculus: https://en.wikipedia.org/wiki/Lambda_calculus

The curried version of the "add" funtion is show bellow.

.. testcode:: default

    def add_curried(x):
        return lambda y: x + y

As crazy as ``add_curried`` may look, it is so powerful that some languages
adopt it as their standard way of calling functions. This does not work
very nicely Python, however, because the syntax becomes ugly and execution
inefficient:

>>> add(1, 2) == add_tuple((1, 2)) == add_curried(1)(2) == 3
True

A nice middle ground between the standard multi-argument function and the fully
curried version is the technique of "auto-currying": we execute the function normally if
the callee passes all arguments, but curry it if some of them are missing. An auto-curried
``add`` function is implemented like this:


.. testcode:: default

    def add(x, y=None):
        # y was not given, so we curry!
        if y is None:
            return lambda y: x + y

        # y was given, hence we compute the sum
        else:
            return x + y

>>> add(1)(2) == add(1, 2)
True

One nice thing about auto-currying is that it doesn't (usually) break preexisting
interfaces. This new add function continues to be useful in contexts that the
standard implementation would be applied, but it now also accepts receiving an
incomplete set of arguments transforming add in a convenient factory.

Even for only two arguments, implementing auto-currying this way already
seems like a lot of trouble. Fortunately, the :func:`sk.curry` decorator
automates this whole process and we can implement auto-curried functions
with very little extra work:

.. testcode:: default

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


.. _Creation:

Quick lambdas
=============

Operators like ``+, -, *, /``, etc are functions recognized as being so useful
that they deserve an special syntax in the language. They are obvious candidates
for creating a library of factory functions such as the example:


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


Magic X, Y
----------

Sidekick implements a clever approach that first appear in Python in popular
functional programming libraries such as `fn.py`_ and `placeholder`_. It exposes
the "magic argument object" ``X`` that creates those simple one-liners using a
very straightforward syntax: every operation we do with the magic object X,
returns a function that would perform the same operation if X was the argument.
For instance, to tell the X object to create a function that adds some number
to its argument, just add this number to X:

.. doctest:: default

    from sidekick.api import X

    incr = (X + 1)  # same as lambda x: x + 1

.. _placeholder: https://pypi.org/project/placeholder/
.. _fn.py: https://pypi.org/project/fn/

In a similar spirit, there is a second operator Y for creating functions of
two arguments:

.. doctest:: default

    from sidekick import X, Y

    div  = (X / Y)  # same as lambda x, y: x / y
    rdiv = (Y / X)  # same as lambda x, y: y / x

Y is consistently treated as the second argument of the function, even if the
expression does not involve X. Hence,

>>> incr = (Y + 1)  # return lambda x, y: y + 1
>>> incr("whatever", 41)
42

This magic object is great to create one-liners on the fly without having to
remember names and function signatures. Functions created with the magic X
and Y work very nicely when creating elaborate functional pipelines.

>>> nums = range(1000)
>>> squares = map((X * X), nums)
>>> odds = filter(X % 2, nums)

We will create more interesting examples later using other sidekick functions
and operators.

The X and Y special objects cover most functionality in Python's ``operator``
module, but provides a more flexible and perhaps a more intuitive interface.
But just as `operator` has its share of oddities and caveats (e.g., division is
called truediv, it does not expose have reverse operations such as radd,
rsub, etc). There are some limitations of what the magic X and Y can do.

Some operations **do not** work with those magic objects. Those are intrinsic
limitations of Python syntax and runtime and will *never* be fixed in Sidekick.

* **Short circuit operators:** ``(X or Y)`` and ``(X and Y)``. There is no perfect way to
  reproduce short circuit evaluation with functions, hence sidekick does
  not provide any real alternative.
* **Identity checks:** ``(X is value)`` or ``(X is not value)``. Use
  :func:`sk.is_identical` or its negative ``~sk.is_identical(value)`` instead.
* **Assignment operators:** ``(X += value)``. Assignment operators are statements and
  cannot be assigned to values. This includes item deletion and item assignment for the
  same reason.
* **Containment check**: ``(X in seq)`` or ``(seq in X)``. Use :func:`sk.contains`
  instead.
* **Method calling**: ``X.attr`` immediately returns a function that retrieves the
  ``.attr`` attribute of its argument. We cannot specify a method to obtain a
  behavior similar to :func:`operator.methodcaller`. :func:`sk.method` function has
  can produce method callers. Similarly, :func:`sk.attr` expose some functionality
  of :func:`operator.attrgetter` that cannot be expressed with those magic objects.

``sidekick.op`` module
----------------------

Most functions that would be created with the X and Y magical objects are present
in Python's own operator module, which exposes Python operators and special methods
as regular functions. Sidekick provides a copy of this module that exposes curried
versions of those functions. It is convenient to create simple one-liners via partial
application

>>> from sidekick import op
>>> succ = op.add(1)
>>> succ(41)
42

.. TODO:
    Create a proper documentation

.. TODO:
    Placeholder section


.. _Composition:

Composing functions
===================

We mentioned before that good functional code behave like LEGO bricks: they
can easily fit each other and we can organize them in countless and creative ways.
The most common form of composition has the shape of a pipeline: we start with
some piece of data and pass it through a series of functions to obtain the final
result. Sidekick captures that idea in the :func:`sidekick.api.pipe` function.

>>> sk.pipe(10, op.mul(4), op.add(2))
42

The data flow from the first argument from left to right: i.e., ``10`` is passed to
``op.mul(4)``, resulting in ``40``, which is then passed to ``op.add(2)`` to
obtain ``42``. Notice we are relying on the fact that functions in :mod:`sidekick.op`
are all auto-curried.

It is often desirable to abstract the operations in a pipe without mentioning data.
That is, we want to extract the transformations into a function and pass data
later at call site. This is responsibility of the :func:`pipeline` function.

>>> func = sk.pipeline(op.mul(4), op.add(2))
>>> func(10)
42

Attentive readers might realize that ``pipeline(*funcs)`` is equivalent to
``lambda x: pipe(x, *funcs)``.

Pipelining is a simple form of function composition. In mathematics, the standard
notation for function composition passes the arguments in opposite direction
(i.e., data flows from the right to the left)

>>> func = sk.compose(op.add(2), op.mul(4))
>>> func(10)
42

``sk.compose(*funcs)`` is equivalent to ``sk.pipeline(*reversed(funcs))``.


Composition syntax
------------------

Many functional languages have special operators dedicated to function composition.
Python don't, but that does not prevent us from being creative. Most sidekick
functions are not actually real functions, but rather instances of an special
class :class:`sidekick.functions.fn`. fn-functions extend regular functions in a
number of interesting ways.

The first and perhaps more fundamental change is that fn-functions accept bitwise shift
operators (``>>`` and ``<<``) to represent function composition. The argument flows
through the composed function in the same direction that bit shift arrows
points to:

>>> f = op.mul(4) >> op.add(2)  # First multiply by 4, then add 2
>>> f(10)
42

Obviously only sidekick-enabled functions accept this syntax. We can support
arbitrary Python callables by prefixing the pipeline with the fn object, making
it behave essentially as an identity function

>>> succ = lambda x: x + 1
>>> incr_pos = fn >> abs >> succ  # (or fn << incr << abs)
>>> incr_pos(-41)
42

The other bitwise operators ``| ^ & ~`` are re-purposed to compose logical operations
on predicate functions. That is, ``f | g`` returns a function that produces the
logical OR between f(x) and g(x), ``f & g`` produces the logical AND and so on.
Evaluation is done in a "short circuit" fashion: ``g`` is only evaluated if
f returns a "falsy" value like Python's ``or`` operator.

Logical composition of predicate functions is specially useful in methods such
as filter, take_while, etc, that receive predicates.

>>> sk.filter(sk.is_divisible_by(3) | sk.is_divisible_by(2), range(10))
sk.iter([0, 2, 3, 4, 6, 8, ...])

The pipe operator ``|`` represents the standard or, while ``^`` is interpreted
as exclusive or.

>>> sk.filter(sk.is_divisible_by(3) ^ sk.is_divisible_by(2), range(10))
sk.iter([2, 3, 4, 8, 9])

:class:`sidekick.functions.fn` also extend regular functions with additional
methods and properties, but we refer to the class documentation for more details.


Applicative syntax
------------------

Bitwise operators compose fn-functions. Sidekick also provides a syntax to
apply arguments into functions. Ideally, the syntax should be equal to
F#'s function application operation, i.e.,

::

    x |> function == function <| x == function(x)

Unfortunately, this is not valid Python and it could only be implemented
changing the core language, not as a mere library feature. The next best
thing would be to re-purpose existing operators. Unfortunately, we do not
have very good options here: bitwise operators are already taken (hence,
we can't use the pipe ``|`` operator), comparison operators do not work
well in chained operations [#chain]_ and arithmetic operators have a
high precedence which makes the annoying to use.

.. [#chain] Python translates chains like ``x > f > g`` to ``x > f and f > g``.
   This breaks the chain of function application and makes those operators
   unusable for this task.

Sidekick makes the following (admittedly less than ideal) choices:

.. doctest::

    f ** arg == f < arg == f(arg)
    arg // f == arg > f == f(arg)
    f @ arg  == sk.apply(f, arg)  # This is the applicative version, more on this later!


We do not really encourage the use of those operators, but they are here
just to explore how the language would look like if it had dedicated
operators like ``g <| f <| x`` and ``x |> f |> g``. In practical terms,
overloading ``>``, ``<``, ``**`` and ``//`` to represent function application just
save us the annoyance of wrapping a long argument in parenthesis when we
want to do function application. This is acceptable in interactive sessions,
but it is highly non advisable in production code. That is why sidekick comes
with a ``evil`` module to control when the extended interface should be
enabled.

By default, fn-functions accept ``>``, ``<``, ``**`` and ``//`` to perform
function application. We can execute :func:`sidekick.evil.no_evil` to disable
this behavior. If you are feeling lucky, however, :func:`sidekick.evil.forbidden_powers`
extend this behavior even to regular Python functions. It uses ugly hacks and
obfuscated code, so we could not stress more to never use it in production code.
