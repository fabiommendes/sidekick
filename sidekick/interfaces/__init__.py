"""
Function composition patterns
=============================

Some functions have properties that permit specific kinds of function
composition. It is useful to recognize some of those patterns and develop a
consistent and recognizable interfaces with them. Let us start with perhaps the
most simple type of function composition, which we call the "power" pattern.

Any single-argument function that returns a value of the same type of its input
value can be recognized in this pattern. It is a function that can compose with
itself, i.e., we can compute f(x), f(f(x)), f(f(f(x))), and so on. In order for this
to work, f should have the specific signature: ``f(x: T) -> T`` for some type T.

Any function with this property can be fed to the :func:`sidekick.functions.power` or
:func:`sidekick.seq.iterate` to produce either the result of n applications of f
or the infinite sequence of progressive applications starting with some initial
argument.

Detour: The Babylonian method
-----------------------------

Many algorithms can be formulated as a sequence of approximations by some
transformation function. We will illustrate with a simple example of computing
square roots, but the general idea can be expanded to many other domains.

Let us recall the Babylon method to compute square roots. Consider R to be the
square root of x. We will approximate R by a sequence of r0, r1, r2, ... etc that
starts with some guess and converges gradually to the correct value by the
formula

    r' = 0.5 * (r + x / r)

This formula was allegedly used by Babylonian mathematicians thousands of years
ago, and can be derived with modern mathematics as an instance of Newton's
method for approximating the root of a function.

Let us define:

>>> x = 2
>>> f = lambda r: 0.5 * (r + x / r)

By iterating f, we obtain progressively better approximations of square root
of x.

>>> sk.iterate(f, x)
sk.iter([2.0, 1.5, ...])

When to stop? There are several workable criteria and we can play around a little
bit. We may fix the number of iterations...

>>> n_iter = 5
>>> sk.iterate(f, x)[:n_iter].last()
1232

... or define a tolerance...
>>> tol = 1e-6
>>> sk.last(sk.take(lambda r: abs(r * r - x) / x < tol, sk.iterate(f, x)))
1232

Or even mix the results by selecting a maximum slice in the output of take.
Either case, those are the building blocks to create a function with a custom
implementation of square roots.

>>> def sqrt(x):
...     f = lambda r: 0.5 * (r + x / r)
...     return sk.iterate(f, x)[:10].last()

Very nice, but this pattern can be generalized further to any function that
can be handled by Newton's method.

>>> @sk.curry(2)
... def newton(next_func, x, maxiter=10):
...     f = sk.partial(next_func, x)
...     return sk.iterate(f, x)[:maxiter].last()

From this, we easily create a collection of functions, reusing bits and pieces

>>> sqrt = newton(lambda x, r: 0.5 * (r + x / r))
>>> acos = newton(lambda x, r: 0.5 * (r + x / r))
>>> atan = newton(lambda x, r: 0.5 * (r + x / r))

This illustrates good features of functional code: we bundle together small
functions and compose them using very simple interfaces. Passing functions to
functions achieve a high degree of flexibility and code reuse without involving
ad hoc abstractions such as classes..


Typing a function
=================

This section talks a lot about types, but types in Python must be interpreted
with some caution. The runtime type of an object in Python is given by ``type(obj)``
and we can check types using ``isinstance(obj, T)``. This is not what we mean.

Starting with Python 3.5(?), Guido introduced the ``typing`` module to the standard lib
and made it the official way module to use with type hints. ``typing`` defines
types such as List[int], Dict[str, Callable], etc which are abstraction that
cannot be checked at runtime (i.e., ``isinstance([1, 2, 3], List[int])`` fails),
and the Python interpreter completely ignore them, happily executing mistyped
code. They exist so that code editors and static analysis tools such as MyPy
can introspect code and find probable errors.

We adopt the same nomenclature as the typing module, but we choose to be a little
bit vague and informal about types and adopt the pragmatic view that if duck type
correctly (i.e., it runs successfully), than it is correct. While some mathematical
guarantee would be good, Python offers none: the compiler is ignorant about type
errors and even MyPy can be easily confused by the kind of dynamic and functional
code commonly associated with sidekick.

At any rate, talking about types is important to identify some patterns of function
composition. We already talked about single argument functions of type ``(T) -> T``.
Those functions can be successively applied to their outputs and this can be explored
by many algorithms. The following sections will cover functions with two arguments
and some patterns of how data structures can interact with functions.


Binary functions
================

Consider our humble ``add`` function, expressible both in operator or
functional forms. It can be composed in
different ways that arbitrary functions of two arguments simply cannot. First,
we can make chains of additions:

>>> a + b + c + d

This is only possible because add preserves types: add(x: T, y: T) -> T. A binary
function that return a different type than its arguments or one that receive
arguments of different types would not allow this kind of indefinite chaining.

Not only that, but the fact that addition is associative means that we can
rewrite chains of summations in various ways

>>> a + b + c  == (a + b) + c  == a + (b + c)

This flexibility in writing the parenthesis makes the operator form so
convenient. We known  that it is always possible to add extra terms ``... + x``
without being too much concerned in how to group them in a chain (The fact that
addition is commutative, means that we can even reorder the terms without affecting
the results).

This simple structure of addition of regular numbers is seen in so many areas of
computation and mathematics that it deserves a name and a proper formal definition.
A binary operation that allows this free positioning of parenthesis is called
"associative". A set of values (usually defined by the types allowed within the operation)
with an associative binary function is known in mathematical parlance as a semi-group.

* **Semigroup**: a set of values of type "T" with an operation ``op(x: T, y: T) -> T``
  with the following property::

    op(op(x, y), z) == op(x, op(y, z))

If we think of op abstractly as an infix operator, this condition would be
written as::

    (x `op` y) `op` z == x `op` (y `op` z)

This is obviously not valid Python, and we put some backticks to emphasize that
op is some funny abstract binary operation written in an imaginary infix form.
Python does not allow arbitrary infix operators, but we may circumvent part
of this limitation by writing our operator as a function that accepts several
arguments. This is how sidekick implement semigroups: semigroup is defined by
a function that accepts variadic arguments and recursivelly apply the binary
operation when the number of operands is greater than two.

::

    op(x, y, z, ...)  # op implements a sidekick semigroup

Semigroups can be created explicitly by decorating a binary operator with
@sk.semigroup. This decorator creates a fn-enabled function with some additional
methods and introspection capabilities. We will discuss those later on. First,
we need to know a close friend of the semigroup, the monoid.


Monoid
======

There is more to addition than associativity. Very notably, it also has a special
neutral element which can be added to any "summable" element without changing
its value (we are talking, of course, about the zero).

A semigroup with a neutral element is called a monoid. It is important to point
out the monoid property because most of the interesting semigroups we might use
in programming are actually monoids (i.e., if we dig carefully, we can find one
such neutral element that can combined with other values with no effect). The list
bellow show some examples with the corresponding neutral element of each
operation.

1) Numbers under addition/multiplication: ``0 or 1``
2) Lists/tuples/strings under concatenation: ``[] or () or ""``
3) Sets/dictionaries under union: ``set() or {}``
4) Unary functions under composition: ``lambda x: x``
5) Iterators under chaining: ``iter([])``

And there are many other examples.

Monoids are declared similarly, but using the @monoid decorator. The decorator
requires us to specify a function that creates an instance of the neutral
element.


Groups
======

A group is a monoid with an inverse operation. The inverse finds the element
that would bring its argument back to the neutral element of the group. More
formally, if ``op`` is the binary operation and ``inv`` the inverse,

::

    op(inv(x), x) => e  # e is the neutral element


Some of the monoids that we mentioned, are actually groups, and we can access
the inverse operation as a method. Addition, for instance, is obviously a group
since we can take the negative of any value x and sum with x to recover the neutral
element zero.

>>> from sidekick.interfaces import Add
>>> Add.inv(42)
-42

Groups are declared with the @group decorator.


Functors/Applicative/Monads
===========================

Sometimes, the sidekick approach of creating iterators, transforming them and
at the end construct some explicit container (such as as a list or tuple)  with the
resulting data can be a little bit annoying. More importantly, some container
types express different relations than that of a "sequence of elements", which
is nicely captured by iterators. If we want to do operations in data stored
in those types, iterators often are of no help to us.

One nice example in Python is the dictionary type. We can``iter`` over a dictionary,
but it destroy its values leaving us only with the keys. While certainly useful,
iteration is not friendly towards data stored in a dictionary. If we want to
transform this data, we are out of luck: ``map(func, dic)`` will transform
only the keys and discard all values, which is probably not what we
want in most cases.

That leave us with the question: is there a generic interface that applies a
function into the elements of any container type? The answer is yes (at least
in the sense "it is possible to implement it very generally"), and sidekick
implements it for several Python builtin types and allow hooks to implement them
for custem types.

In the jargon of functional programming, the kind of interface we are looking for
is called a "Functor". In sidekick, the functor interface is implemented via the
"apply"  function. It receives a function and a container argument, and apply the
function into the elements of that container using the "functor" mechanism, which
returns a container of the same type.

In the case of dictionaries, our default implementation takes the input function
and applies it in all values of the dictionary, returning a new dictionary:

>>> sk.apply(op.add(1), {"foo": 41, "bar": 42})
{"foo": 42, "bar": 43}

This interface is so important, that it has an special notation in sidekick:

>>> op.add(1) @ {"foo": 41, "bar": 42}
{"foo": 42, "bar": 43}

This only works if the function in the left hand side is a sidekick fn-function.

The :func:`sidekick.interfaces.apply` function checks the type of the second
argument and ask the related functor to execute the function in all elements of
the data structure and return the result.

Each container type has a different mechanism of applying the function into
its elements and reconstructing the resulting data structure. We already shown
how does it work for dicts. In the case of lists, tuples, sets, frozen sets, deques
and other builtin sequential types, it behaves very similarly to map, but wraps
the result in the correct data structure

>>> sk.apply(op.add(1), [1, 2, 3])
[2, 3, 4]
>>> sk.apply(op.add(1), {1, 2, 3})
{2, 3, 4}


It might seem that ``sk.apply`` is about collections and mapping functions on
elements of collections. It is actually more than that: this transformation can be
formulated to any object that is related to a value of type a, which can be transformed
into a value of type b. This include :class:`sidekick.types.Result`,
:class:`sidekick.types.Maybe` and even functions.

In the case of Results and Maybes, ``sk.apply`` executes the function in the
successful cases (Just and Ok)  and does nothing in the failure cases (Err and Nothing)

>>> sk.apply(op.mul(2), sk.Ok(21))
Ok(42)
>>> sk.apply(op.mul(2), sk.Err("some error"))
Err('some error')

With some creativity, we may think of Results or Maybes as somewhat analogous to
lists that contain 0 or 1 value. But apply works even with objects that
store no value. One nice example are functions: a function that returns values of
type "a" be mapped into another function from a to b by simple functional
composition.

>>> func = sk.apply(str, op.add(1))
>>> func(41)
'42'

The apply function has a mechanism to register any custom type. But before
implementing any crazy transformation with apply, it is important to understand
how functors should work and how do they fit in the grand scheme of things. Keep
reading...

Typing
======

There are many options for passing F[a]'s to functions. The most simple
case is, of course, a function ``f`` that expects ``F[a]`` and return some other
type. The function understands the container directly, hence we just pass it as
an argument in a regular function call. Nothing new here.

We represent the previous case with the notation ``f: F[a] -> b``. The next
step is the functor: we have a function ``f: a -> b`` and a container F[a]. The
functor mechanism (sk.apply) executes the function in each element of the container
and reconstruct the resulting container F[b]. This is the result of executing
``apply(f, container_of_as)`` to obtain a result F[b]. ``sk.apply`` takes a function
that receives a's and return b's (they can be the same type), and a container of
a's and return a container of b's by executing the function in each element of the
container. It is therefore a function with a signature of ``apply: (a -> b, F[a]) -> F[
b]``.

What if the function takes several arguments like ``f: (a, b) -> c``, but we have
data stored in the corresponding containers ``F[a]`` and ``F[b]``. Apply still
works and we can call it with several arguments. In this case the signature
would be ``apply: ((a, b) -> c, F[a], F[b]) -> F[c]``.

In functional programming, this general version of apply is often known as an
"applicative functor". This is simply a fancy name for a functor that can
generalize to several arguments. It is useful to distinguish both cases because
not all functors can easily generalize to many arguments and this generalization
is not always unique.

The last option in a our tower of abstractions goes by the scary name of a "Monad".
This is essentially a generalization of a functor that can handle transformations
like ``((a, b) -> F[c], F[a], F[b]]) -> F[c]``. Notice the input function
already returns values of the functor type. The corresponding handler must then
be able to flatten those intermediate results when constructing the final result
is therefore we call the function responsible for handling Monads "sk.apply_flat".


Classical functors
------------------

In the last section, we talked about function signatures for functor-like types.
However, simply implementing something with the correct type signatures do not
qualify it as a proper functor. Consider, for instance, these two implementations
of a functors for lists:

.. code-block:: python

    @apply.register(list)
    def good_functor(f, lst):
        return [f(x) for x in lst]

    @apply.register(list)
    def bad_functor(f, lst):
        # We take at most two elements of the list, just because ;)
        return [f(x) for x in lst[:2]]


Both satisfy the required type signatures, but what makes one a good functor and
the other a bad functor? Can we prove that a **bad_functor** not only looks
suspicious, but is indeed **wrong**?

The answer lies on the "functor laws": those are a set of properties that proper
functors should obey. In the case of single-argument functors, the requirements
are:

1) A functor should not change when transformed by the identity function, i.e.,
   ``apply(identity, xs) == xs``
2) It should respect function composition in the sense that the effect of
   transforming by h(x) = f(g(x)) should be equivalent of first transforming by
   g and then by f, i.e., ``apply(compose(f, g), xs) == apply(f, apply(g, xs))``

It is easy to verify that the ``good_functor`` respect both laws and the ``bad_functor``
violates both if the list has more than two elements.

The generalization for multi-argument functors is not that straightforward because
both the identity function and function composition are not well defined for functions
with more than one argument. We need a more indirect approach.

The first important insight is to know that it is possible to generalize apply
to a function of n arguments if we know how to apply function with only two arguments.
Unfortunately, we don't know how to do it yet, but let us understand how this
generalization would be, supposing someone has already figured out what to do
with two arguments. The argument is a little bit brain bending, so you might
want to read this section twice.

Suppose we want to apply::

    apply(f, as, bs, cs) -> ds
    # f: (a, b, c) -> d
    # as: F[a]
    # bs: F[b]
    # cs: F[c]

but there is only support for functions of two arguments. If apply works
for any (consistent) set of types (a, b, c, d), it surely must work for this
curious contraption::

    gs = apply(curry(3, f), as, bs)

This returns a functor gs of type F[c -> d], since the curried version of f, when
called with two arguments will return a function that receives a third argument and
then compute the result. Since gs is a functor of functions, there is nothing that
prevents us to use it as an argument to apply again. We
obtain the final answer by::

    ds = apply(lambda g, c: g(c), gs, cs)

Thus apply will execute each function in the gs functor with the corresponding value
coming from the cs functor. This creates our final result ds. This method can
be easily generalized to functions with any number of arguments, even though it is
not the most efficient method due to the creation of intermediary data structures
and lots of indirection in the creation of partially applied functions.

It is a good check, however, if our generalization for multiple arguments is
consistent. If applying a function of 3 arguments is not consistent with this
method, it is not a correct applicative functor.


FlatApply
=========
"""
# flake8: noqa
from .semigroup import semigroup
from .monoid import monoid, combine, combine_map, times
from .group import group, dual
from .wrapper import Algebraic

__all__ = [
    # Semigroups
    "semigroup",
    # Monoids
    "monoid",
    # Groups
    "group",
    "dual",
]
