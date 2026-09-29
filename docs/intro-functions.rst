======================================
Introduction to functional programming
======================================

Functional programming, as the name implies, leans heavily towards using functions
for solving problems. This contrasts with other approaches as, for instance,
organizing code around classes and objects or even relying too much on standard control 
flow structures such as ``for``, ``if``'s, ``with``, etc.

Python is a multi-paradigm language that allows functional programming but was not
conceived specifically for it. Functional programming is only practical if we have
means of easily creating new functions and using them in cooperation. This usually means that
functional code tends to be littered with many small functions that are passed to
other (high order) functions to accomplish some elaborate task. Think of those functions
as Lego bricks: they are simple, easy to grasp and tend to fit nicely with each other. 
They are rather unimpressive on their own, but when used in conjunction can create beautiful and elaborate 
structures.

Creating functions in Python usually involves ``def`` statements and ``lambdas`` [#lambda]_.
This approach is perhaps a little bit clumsy for everyday
FP use because the syntax is a little bit heavy, and lambdas are highly constrained in Python. 
Sidekick provides more efficient ways to construct new functions on top of standard 
Python idioms. Those approaches can be split into 3 basic ideas:

1) Specialization_: constrain a generic function by fixing some of its arguments.
2) Creation_: construct commonly used lambdas with a better syntax.
3) Composition_: join two or more functions to generate a new function that inherit behaviors of both.

We will discuss those ideas in detail in the next sections.

.. [#lambda] The name "lambda" has roots in lambda calculus, an area of theoretical 
   computer science. The lambda keyword was (perhaps regrettably) borrowed from LISP,
   in which the authors of the language really wanted to make the association with
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


This simple function declaration in reality it does a few
more things: it gives the function a name, defines its documentation string, create
type hints and sets an implicit scope for global variables. This is a
very efficient syntax For top level functions of our public APIs, in which we 
probably want to declare all those properties.

Put the same function in a different context and ``def's`` start to feel verbose [#map]:

.. code-block:: python

    def increment_seq(numbers):
        """
        Increment all elements of a sequence by one.
        """
        def succ(n):
            return n + 1

        return map(succ, numbers)

.. [#map] For those who do not remember, the builtin map function takes a function
   and a sequence as arguments and apply the function in all elements of the
   sequence, returning an iterator over the new sequence. 

Not only this code spends two lines to define such a trivial throwaway function, it
forces us to explicitly come up with a name which does not clarify its intent
anymore than seeing ``n + 1`` in the body of the function. `Naming is hard`_,
and we should avoid doing it if does not help making a piece of code
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

A mathematical function receives a single parameter and return a single value.
In Python, and in most programming languages, the "function interface" can be
considerably more complicated: the function might receive several parameters,
keyword arguments, ``*args`` and ``**kwargs`` expansions, and it might
even produce side effects outside of what is visible from the inputs and
outputs.

It is often convenient to consider an idealized world
in which all functions receive a single argument and return a single value. In
fact, it is not hard to transform real world functions to alternatives in this
idealized version. Consider the function bellow:

.. testcode:: default

    def add(x, y):
        return x + y

This "complicated" two argument function can be easily simplified into a
single argument function by passing x and y as a tuple, as such:

.. testcode:: default

    def add_tuple(args):
        return args[0] + args[1]

    add_tuple((1, 2))  # Returns 3

A second approach is to conceive a multi-argument function is just a function
that returns a second function that receives the remaining arguments. The function
is evaluated only after the last argument is passed. This strange encoding is called
*"currying"* after the computer scientist Haskell Curry, and is a very important
idea in a foundational field of computer science called `Lambda calculus`_.

.. _Lambda calculus: https://en.wikipedia.org/wiki/Lambda_calculus

The curried version of the "add" function is shown bellow.

.. testcode:: default

    def add_curried(x):
        return lambda y: x + y

As strange as ``add_curried`` might look, it is so powerful that some languages
adopt it as their standard way of calling functions. This does not work
very nicely Python, however, because the syntax becomes ugly and execution
inefficient:

>>> add(1, 2) == add_tuple((1, 2)) == add_curried(1)(2) == 3
True

A nice middle ground between the standard multi-argument function and the fully
curried version is the technique of "auto-currying": we execute the function normally if
the caller passes all arguments, but curry it if some of them are missing. An auto-curried
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
incomplete set of arguments allowing ``add`` to be a convenient factory of functions.

Even for only two arguments, implementing auto-currying this way already
seems like a lot of trouble. Fortunately, the :func:`sidekick.functions.curry` decorator
automates this whole process and we can implement auto-curried functions
with very little extra work:

.. testcode:: default

    import sidekick.api as sk

    @sk.curry(2)  # The 2 stands for the number of arguments
    def add(x, y):
        return x + y

Ok, it is good that we can automatically curry functions. But why would anyone
want to do that in any real world situation?

Remember when we said that the increment function (``lambda x: x + 1``) was just
a special case of addition when one of the arguments is fixed to 1? This kind of
"specialized" functions are trivial to create using curried functions: just apply
the arguments you want to fix and the result will be a specialized version
of the original function:

>>> incr = add(1)  # Fix first argument of add to 1
>>> incr(41)
42

The ability to do that makes it very easy to compose little functions with other
higher level functions to build powerful functional pipelines.


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

Sidekick implements a clever approach that appeared in Python in popular
functional programming libraries such as `fn.py`_ and `placeholder`_. It exposes
the "magic argument object" ``X`` that creates those simple one-liners using a
very straightforward syntax: every operation we do with the magic object,
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
module, but provide a more flexible and perhaps a more intuitive interface.
But just as `operator` has its share of oddities and caveats (e.g., division is
called truediv, it does not expose have reverse operations such as radd,
rsub, etc). There are some limitations of what the magic X and Y can do.

Some operations **do not** work with those objects. Those are intrinsic
limitations of Python syntax and runtime and will *never* be fixed in Sidekick.
Bellow is a list of operations that fail with the magic arguments.

* **Short circuit operators:** ``(X or Y)`` and ``(X and Y)``. Use :func:`sidekick.op.or_` and
  :func:`sidekick.op.and_` instead.
* **Identity checks:** ``(X is value)`` or ``(X is not value)``. Use
  :func:`sidekick.pred.is_identical` or its negative ``~sk.is_identical(value)`` instead.
* **Assignment operators:** ``(X += value)``. Assignment operators are statements and
  cannot be assigned to values. This includes item deletion and item assignment for the
  same reason.
* **Containment check**: ``(X in seq)`` or ``(value in X)``. Use :func:`sidekick.op.contains`
  instead.
* **Method calling**: ``X.attr`` immediately returns a function that retrieves the
  ``.attr`` attribute of its argument. It is not possible, therefore, to specify the arguments
  of a method like the builtin `operator.methodcaller`_ function. For those situations,
  :func:`sidekick.functions.method` can produce method callers with an specialized syntax.

.. _operator.methodcaller: https://docs.python.org/3/library/operator.html#operator.methodcaller


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

More details in the :mod:`sidekick.op` documentation page.


Placeholder
-----------





.. _Composition:

Composing functions
===================

.. currentmodule:: sidekick.functions

Good functional code behave like LEGO bricks: they
can easily fit with each other and we can organize them in countless and creative ways.
The most common form of composition has the shape of a pipeline: starting with
some data, pass it through a series of functions to obtain the final
result. Sidekick captures that idea in the :func:`pipe` function.

>>> sk.pipe(10, op.mul(4), op.add(2))
42

The data flow from the first argument from left to right: i.e., ``10`` is passed to
``op.mul(4)``, resulting in ``40``, which is then passed to ``op.add(2)`` to
obtain ``42``. Notice we are relying on the fact that functions in :mod:`sidekick.op`
are all auto-curried.

It is often desirable to extract the operations in a pipe without mentioning the 
initial data. This is a done with the :func:`pipeline` sister function.

>>> func = sk.pipeline(op.mul(4), op.add(2))
>>> func(10)
42

Attentive readers might realize that ``pipeline(*funcs)`` is equivalent to
``lambda x: pipe(x, *funcs)``.

Pipelining is a simple form of function composition: the result of a function is 
passed as the argument of the next. In mathematics, the standard
notation for function composition passes the arguments in the opposite direction, 
from the right to the left. For this reason, we also define a separate ``compose(*funcs)``
using this convention.

>>> func = sk.compose(op.add(2), op.mul(4))
>>> func(10)
42

``sk.compose(*funcs)`` is equivalent to ``sk.pipeline(*reversed(funcs))``.


Composition syntax
------------------

Many functional languages have special operators dedicated to function composition.
Python doesn't, but that do not prevent us from being creative. Most sidekick
functions are not real Python functions, but rather instances of an special
class :class:`fn` that extend regular functions in a number of interesting ways.

The first and perhaps more fundamental change is that fn-functions accept bitwise shift
operators (``>>`` and ``<<``) to represent function composition. The argument flows
through the composed function in the same direction that bit shift arrows
points to:

>>> f = op.mul(4) >> op.add(2)  # First multiply by 4, then add 2
>>> f(10)
42

Obviously only sidekick-enabled functions accept this syntax. We can create a 
pipeline of arbitrary Python callables by prefixing it with the fn object, making
it behave essentially as an identity function

>>> succ = lambda x: x + 1
>>> incr_positive = fn >> abs >> succ  # (or fn << succ << abs)
>>> incr_positive(-41)
42

The other bitwise operators ``| ^ & ~`` are re-purposed to compose logical operations
on predicate functions. That is, ``f | g`` returns a function that produces the
logical OR between f(x) and g(x), ``f & g`` produces the logical AND and so on.
Evaluation is done in a "short circuit" fashion: ``g`` is only evaluated if
f returns a "falsy" value like Python's ``or`` operator.

Logical composition of predicate functions is specially useful in methods such
as filter, take_while, etc, that receive predicates.

>>> sk.filter(sk.is_divisible_by(3) | sk.is_divisible_by(5), range(10, 100))
sk.iter([10, 12, 15, 18, 20, ...])

The pipe operator ``|`` represents the standard or, while ``^`` is interpreted
as exclusive or.

>>> sk.filter(sk.is_divisible_by(3) ^ sk.is_divisible_by(5), range(10, 100))
sk.iter([10, 12, 18, 20, 21, ...])

:class:`fn` also extend regular functions with additional
methods and properties, but we refer to the class documentation for more details.


Argument piping syntax
----------------------

Bitwise operators compose fn-functions. Sidekick also provides a syntax to
apply arguments to those functions. Ideally, we would like to mimic some
established syntax. Many functional languages adopt F#'s function
application operation, i.e.,

.. code-block:: F#

    (x |> function) == (function <| x) == function(x)

This is not valid Python and it could only be implemented
changing the core language, not as a mere library feature. The next best
thing would be to re-purpose existing operators. Unfortunately, we do not
have very good options here: bitwise operators such as ``|`` are already taken, comparison
operators like ``>`` or ``<`` do not work well in chained operations [#chain]_ and arithmetic
operators have a high precedence which makes them somewhat annoying to use.

.. [#chain] Python translates chains like ``x > f > g`` to ``x > f and f > g``.
   This breaks the chain of function application and makes those operators
   fragile for this task.

Given those limitations, sidekick makes the following (admittedly less
than ideal) choices:

.. doctest::

    f ** arg == f < arg == f(arg)
    arg // f == arg > f == f(arg)
    f @ arg  == sk.apply(f, arg)  # This is the applicative version, more on this later!


We do not really encourage the use of those operators, but they exist
just to explore how the language would look like if we can really squeeze our eyes
and pretend that ``>`` and ``<``  are actually ``|>`` and ``<|``.
In practical terms, overloading ``>``, ``<``, ``**`` and ``//`` to represent
function application just save us the annoyance of wrapping a long argument in parenthesis when we
want to do a quick function application in a terminal section. This is acceptable
for "throw away code" but it is highly discouraged in production code.
That is why sidekick comes with a ``evil`` module that helps to control when this
extended interface should be enabled or not. By default, it is enabled in interactive
sections and disabled otherwise.

We can execute :func:`sidekick.evil.no_evil` and :func:`sidekick.evil.do_evil` to explicitly
control this behavior. If you are feeling lucky, however, :func:`sidekick.evil.forbidden_powers`
extend those operators to regular Python functions. It uses ugly hacks and
obfuscated code, so we could not stress more to **never** use it in anything
remotely serious. A ``from sidekick import evil`` statement in production code
should make it clear that life is now very dangerous :P.


Applicative mapping
...................

You might have heard computer science theorists talking about applicative functors,
monads and whatnot. In Sidekick, those concepts were adapted to Python and
were given less intimidating names and definitions.

The ``sk.apply(func, col)`` is a special function that applies `func` to
elements of a collection, preserving its type. Each collection must
therefore implement this "mapping interface", a.k.a Functor, for those that like
fancy names. Depending on the kind of collection, it may come in two
flavors. The first behaves mostly like a regular mapping:

>>> sk.apply(op.mul(2), [1, 2, 3])
[2, 4, 6]

Notice how the result is a list, not an iterator. This is implemented
by instances of the :class:`sidekick.functions.Apply` class.

>>> issubclass(list, sk.Apply)
True

The second flavor accepts more parameters and automatically knows
how to broadcast values according to the type of the first
argument. Again, each type that implements this interface defines
its own behavior. In the case of lists and most sequence types,
it executes the function in all tuples formed by combining the
arguments and flattening the result.

>>> sk.apply(op.mul, [1, 2, 3], [1, 2])
[1, 2, 3, 2, 4, 6]

This special kind of function application has its own operator.
If ``f`` is a sidekick function, ``f @ x`` is the same as ``sk.apply(f, x)``.

We will not discuss the intricacies of how does it work and how to
support new types. It suffices to say that :func:`sidekick.functions.apply`
also knows how to coerce the additional arguments into the proper
context application. In the case of lists, it simply wraps non-sequence types into
a singleton list. So we would just have called it like

>>> sk.apply(op.mul, [1, 2, 3], 2)
[2, 4, 6]

The first argument after the application function determines the behavior
of apply and therefore specifies the return type. In many situations, sidekick
accepts mixing arguments of different types, but it is usually considered to be 
a poor style. For instance, these two very similar applications produce 
results of different types:

>>> sk.apply(op.mul, [1, 2, 3], {2})
[2, 4, 6]
>>> sk.apply(op.mul, {1, 2, 3}, [2])
{2, 4, 6}


It is possible to support ``sk.apply`` in your own types and even
to implement support for third party classes. This is described in the
documentation of the :class:`Apply` class. Incidentally, the ability
to support third party classes is essential to support lists,
sets and other built-in types internally in Sidekick.


Sidekick function API and semantics
===================================

Functions have a somewhat minimalist interface: we can introspect and
call them. This section shows how sidekick functions extends functions
with a few useful methods and operators. We call those sidekick-enabled function
as fn-functions, since they are created using the fn decorator:

.. testcode::

    @sk.fn
    def add(x, y):
        return x + y


Extended function semantics
---------------------------

Most sidekick functions that expect function arguments actually accept some
other Python types and interpret them as functions. This idea is taken from
the builtin ``filter`` function that interprets ``None`` as the identity function
(actually, the documentation mentions that None is equivalent to bool, which
in the context of filter has the same effect as the identity function).

We extend this idea quite a bit further to also accept dicts, sets, and
strings as function representations. The first two have strong mathematical
basis: in the most basic mathematical definition, functions **are** mappings and 
sets are just maps from values to booleans.


**Maps**

Using a map in a place that expects a function has the same
effect as wrapping it in a ``lambda x: mapping.get(x, x)``.

>>> sk.map({3: 'fizz', 5: 'buzz'}, range(10))  # not a correct fizz-buzz!
sk.iter([0, 1, 2, 'fizz', 4, 'buzz', ...])

In fact, there are many ways to convert a mapping into a Python function,
considering different strategies for handling invalid values. We chosen this
one (i.e., returning missing values as-is) since it is the least convenient
to express with one-liners. In mathematical jargon, we are extending the
domain of the map with the identity function. Not performing this extension
would force us to select one of two other obvious possibilities:

* Raise errors for missing keys
* Return null values for missing keys

Either way is easy to implement with one-liners. Raising errors,

>>> dic = {3: 'fizz', 5: 'buzz'}
>>> next(sk.map(dic.__getitem__, range(10)))
Traceback (most recent call last):
...
KeyError: 0

or returning ``None``s,

>>> sk.map(dic.get, range(10))
sk.iter([None, None, None, 'fizz', None, 'buzz', ...])


**Sets**

Sets are explicitly enumerated containment functions, they return
``True`` for elements in the set and ``False``, otherwise.

>>> sk.remove({1, 2, 3}, range(10))
sk.iter([0, 4, 5, 6, 7, ...])


**None and Ellipsis**

``None`` and ``...`` represent identity functions. The difference
is in the way both handle multiple arguments. None is a simple
identity: it simply returns its single argument. The ellipsis
is what identity would be if multiple arguments were passed as
tuples.

To see the difference, let us wrap those with to_callable to
produce real functions:

>>> id_none = sk.to_callable(None)
>>> id_ellipsis = sk.to_callable(...)

When called with a single argument, both are equal:

>>> x = 42
>>> id_none(x) == id_ellipsis(x) == x
True

``id_none`` does not accept multiple arguments and id_ellipsis treats
them as tuples

>>> id_ellipsis(1, 2, 3)
(1, 2, 3)
>>> id_none(1, 2, 3)
Traceback (most recent call last):
...
TypeError


**Strings**

Finally, sidekick accept strings that represent very simple functions.
They come in three flavors:

1) Operators:

>>> sk.reduce('+', [1, 2, 3])
6

2) Lambdas

>>> sk.map('x: x + 1', [1, 2, 3])
sk.iter([2, 3, 4])

3) Regex match

>>> sk.filter(r'/\w+/', ['foo', 'foo bar'])
sk.iter(['foo'])

4) Regex replacement

>>> sk.map(r"/\w+/a $0/", ['foo', 'foo bar'])
sk.iter(['a foo', 'a foo a bar'])


Fn-function methods
...................

Most functions in the :mod:`sidekick.functions` module are also exposed
as methods of fn-functions, when it makes sense. The documentation
for :class:`sidekick.functions.fn` shows a complete list, but a little
guesswork can go a long way finding how functions are exposed as methods.

Consider the ``div`` function bellow

.. testcode::

    @sk.fn
    def div(x: float, y: float) -> float:
        return x / y

All introspection functions such as :func:`sk.signature`, :func:`sk.arity`,
:func:`sk.stub`, etc, have the corresponding methods,

>>> div.signature()
<Signature (x: float, y: float) -> float>

Functions that receive a function and return a modified version are also
exposed. When it makes sense, they call the transformed function directly
instead of returning a new function.

This is the behavior of ``flip``, ``background``, ``result``, and others.

>>> div.flip(2, 4)  # Attention: 4 / 2, since arguments are flipped
2.0

Other functions return new functions since the immediate execution
would not make much sense.

>>> half = div.single(X, 2)
>>> half(10)
5.0
