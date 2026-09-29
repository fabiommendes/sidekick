=============================
Function composition patterns
=============================

Object oriented programmers often rely on *Project Patterns* to help on how to structure
and define the architecture of a software system. The famous book "Design Patterns: Elements 
of Reusable Object-Oriented Software" by the "Gang of Four" provides some reusable 
patterns that can be applied to a programming language like Java or C++ (with some bits 
relevant to Python, with the necessary adaptations).  

Functional programming is all about functions and tend to value and recognize patterns
on how functions compose and the relations between functions and their types and between
generics and their concrete types. Compared to the classical object oriented programming
patterns, functional patterns tend to be much more formal e mathematically precise 
concepts.

It is useful to recognize some of those patterns and develop a
consistent and recognizable interfaces to work with them. Let us start with perhaps the
most simple type of function composition, which I call the "power" pattern. I don't think 
it is necessarily a very powerful pattern, but it will help us to develop the intuition
and nomenclature to discuss more interesting concepts.

Any single-argument function that returns a value of the same type of its input
value can be recognized in this pattern. It is a function that can compose with
itself, i.e., we can compute f(x), f(f(x)), f(f(f(x))), and so on. In order for this
to work, f should have an specific type signature: ``f(x: T) -> T`` for some type T.

Any function with this property can be fed to :func:`sidekick.functions.power` or
:func:`sidekick.seq.iterate` to produce either the result of n applications of f
or the infinite sequence of progressive applications starting with some initial
argument.


**A note about types**

This section talks a lot about types, but "types" in Python must be understood
with some caution. The runtime type of an object in Python is given by ``type(obj)``.
Python also allows sub-types, abstract types, protocols and many other complications 
and we can check compliance using ``isinstance(obj, T)``. This is **not** what we are 
interested here.

Starting with Python 3.5, Guido introduced the ``typing`` module to the standard lib
and made it the official way to describe type hints. From this work, we have types 
such as list[int], dict[str, Callable[..., T]], etc which are abstractions that
cannot be checked at runtime (i.e., ``isinstance([1, 2, 3], list[int])`` fails),
and the Python interpreter completely ignore them, happily executing mistyped
code. They exist so that code editors and static analysis tools such as MyPy
can analyze code and find probable errors.

We adopt the same nomenclature as the typing module, but we choose to be a little
bit vague and informal about types and adopt the pragmatic view that if it duck types
correctly (i.e., it runs successfully), than it is correct. While some mathematical
guarantee would be good, Python offers none: the compiler is ignorant about type
errors and even MyPy can be easily confused by the kind of dynamic and functional
code commonly associated with sidekick. Also, we can annotate code with "# type: ignore"
or "cast(typ, expression)" that overrides the type checker, possibly (but we have no
guarantees, to nudge the type checker to the correct direction on hard to analyze situations).

At any case, talking about types is important to identify some patterns of function
composition. We already talked about single argument functions of type ``T -> T``.
Those functions can be successively applied to their outputs and this can be explored
by many algorithms. The following sections will cover functions with two arguments
and some patterns of how data structures can interact with functions.


Semigroups and binary operators
===============================

Consider the humble ``add(x, y) = x + y`` function, expressible both in operator or
functional forms. It can be composed in different ways that arbitrary functions of two 
arguments simply cannot. First, we can make chains of additions:

>>> a + b + c + d

This is only possible because ``add`` preserves types: add(x: T, y: T) -> T. A binary
function that return a different type than its arguments or one that receive
arguments of different types would not allow this kind of indefinite chaining.

Not only that, but addition is associative, and this implies that we can
rewrite chains of summations in various ways

>>> a + b + c  == (a + b) + c  == a + (b + c)

This flexibility in placing the parenthesis makes the operator form so
convenient. We known  that it is always possible to add extra terms ``... + x``
without being too much concerned on how to group them in a chain (The fact that
addition is commutative, means that we can even reorder the terms without affecting
the results, but that is another story).

This simple structure of number addition is seen in so many areas of computation and 
mathematics that it deserves a name and a proper formal definition.
A binary operation that allows this free positioning of parenthesis is called
"associative". A set of values (usually defined by the types allowed within the operation)
with an associative binary function is known in mathematical parlance as a semigroup.

* **Semigroup**: a set of values of type "T" with an operation ``op(x: T, y: T) -> T``
  with the following property::

    op(op(x, y), z) == op(x, op(y, z))

If we think of op abstractly as an infix operator, this condition could be
written as::

    (x `op` y) `op` z == x `op` (y `op` z)

This is obviously not valid Python, and I put backticks to emphasize that
op is some funny abstract binary operation written in an imaginary infix form.
The fact that the placement of parenthesis do not matter, means that we could
omit them and simply write ``x `op` y `op` z``.

Python does not allow arbitrary infix operators. We can circumvent this limitation
and still keep some convenience of use by writing our operator as a function 
that accepts several arguments. That way, a single function call can represent
a whole chain of operations, instead of cluttering the code with many ``op(x, y)`` 
calls. This is how sidekick implement semigroups: semigroup is defined by
a function that accepts variadic arguments and recursively apply the binary
operation when the number of operands is greater than two.

::

    op(x, y, z, ...)  # op implements a sidekick semigroup
    op(x, y, z, ...) == x `op` y `op` z `op` ...

Semigroups are implemented by the :func:`semigroup` function. The function takes two
or more arguments and return the result of combining all elements. For instance,
strings form a semigroup under concatenation. We can just call :func:`semigroup` with 
any number of strings to obtain the result.

>>> semigroup("foo", "bar", "baz")
'foobarbaz'

Similarly, with lists

>>> semigroup([1, 2], [3, 4], [5])
[1, 2, 3, 4, 5]

In some situations, we may choose an explicit implementation for a given type:

>>> semigroup[list]("foo", "bar")
traceback
...
TypeError()

``semigroup[list]`` is the list implementation of a semigroup. It will fail if called
with different types of arguments. Using the explicit type can be faster, since the
the runtime dispatch is only made once and it also tend to make static analysis 
work better.

Some types have more than one natural semigroup implementation. A good example are numbers:
they form semigroups under addition and multiplication. We can select the desired
semigroup asking the ``semigroup`` object by name:

>>> semigroup["+"](1, 2, 3, 4)
10
>>> semigroup["*"](1, 2, 3, 4)
24

Those named semigroups are also registered under the ``semigroup.instances`` namespace.

>>> semigroup.instances.product(1, 2)  # "*" is just a convenient alias to "product"
2

If you are creating a class known to form a semigroup, you can simply inherit 
from :cls:`SemigroupT` and implement the ``combine`` method.

.. code-block:: python

    from sidekick.classes import SemigroupT
    
    class MyStr(SemigroupT, str):
        def combine(self, other):
            return MyStr(f"{self}-{other}")

The semigroup function automatically understands members of this class

>>> semigroup(MyStr("foo"), MyStr("bar"))
"foo-bar"

Another convenient way of creating semigroups uses a binary operation or a reducer function:

>>> my_semigroup = semigroup.from_operator(lambda x, y: "|".join([x, y]))
>>> my_semigroup("foo", "bar")
'foo|bar'

This is handy for registering types that you did not create or that you don't want to 
pollute with a ``combine`` method. It is even possible to associate those 
implementations with types, but be careful to avoid registering conflicting 
implementations.

>>> semigroup[MyStr] = my_semigroup

The :func:`semigroup` function has some additional methods and introspection 
capabilities. 


Monoid
======

There is more to addition than associativity. Very notably, it also has a special
neutral element which can be added to any "summable" element without changing
its value (we are talking, of course, about the zero).

A semigroup with a neutral element is called a monoid. It is important to point
out the monoid property because most semigroups we might want to use
in programming are actually monoids (i.e., if we dig carefully, we can find one
such element that can be combined with other values with no effect). The list
bellow show some examples with the corresponding neutral element of each
operation.

1) Numbers under addition/multiplication: ``0 or 1``
2) Lists/tuples/strings under concatenation: ``[] or () or ""``
3) Sets/dictionaries under union: ``set() or {}``
4) Unary functions under composition: ``lambda x: x``
5) Iterators under chaining: ``iter([])``

And there are many other examples.

Monoids are declared analogously to semigroups. We can use either the ``monoid.from_*`` 
methods or :cls:`MonoidT` base class.

The :func:`monoid` object has an special ``neutral()`` method that yield the 
neutral element of a monoid. Since it is impossible for us to guess which monoid 
is being requested, this only works with the specialized versions of the monoid

>>> monoid[int].neutral()
0
>>> monoid[str].neutral()
""
>>> monoid.neutral()
traceback
...
ValueError

The same consideration applies for calling :func:`monoid` with no arguments or 
with an empty list.


Groups
======

A group is a monoid with an inverse. The inverse finds the element
that would bring its argument back to the neutral element of the group. More
formally, if ``op`` is the binary operation and ``inv`` the inverse,

::

    op(inv(x), x) => e  # e is the neutral element


The inverse operation is implemented as the `inv` method of a group.

>>> group.inv(42)
-42

Like monoids, we can specialize the group definition by type or name and 
we can use either the ``group.from_*`` methods or :cls:`GroupT` base class to
declare new groups.

>>> group["*"](4.0)
0.25



Uniqueness and typing
---------------------

Some languages, like Haskell, associate groups/monoids/semigroups with types. 
This can be handy, because it allows the compiler to decide the implementation from 
the values passed to a function, without the user explicitly deciding the correct 
group or monoid to use.

This behaviour is however somewhat imprecise. For any given type, it is often possible to
conceive many different associative operations that could define a number of different 
(and valid) monoids, groups or semigroups. A notable example are integers, that give rise to
two different groups (and consequently two monoids and two semigroups) under multiplication 
and addition. In fact, there are infinite valid groups for integers, since modular arithmetic 
also form a group and we could use the associative operation ``op(x, y) = x * y % N`` for 
any given N.

That said, that behavior is more a rarity then the norm: most types have multiple (and often infinite) 
valid associative operations, but single "natural" implementation. The others, while formally 
valid, may look somewhat  arbitrary and ad hoc. It is rare that a type has two competing and 
clearly useful definitions of a group or monoid exist for the same type like we saw for integers. 

Take strings, as an example. Concatenation is a "natural" associative
operation, and it is useful to define "the" string semigroup using it. However,
any operation like ``op(x, y) = f(x + y)``, in which f is idempotent and distributes over 
concatenation, i.e., ``f(f(x)) = f(x)`` and ``f(x + y) = f(x) + f(y)``, forms 
a valid semigroup. This is the case for functions like ``f = str.lower``, ``f = str.upper``, 
and many more. Incidentally, while there are many semigroups of this form, the only valid
``f(x)`` that accepts a neutral element (and thus defines a monoid) is ``f(x) = x``.

That said, in sidekick, we decided to allow a many-to-many relationship between types and monoids, however,
each type have a default implementation that can be overridden inside a "with" block, if necessary. 
Here is how it works for monoid (groups and semigroups behave analogously).

>>> # multiplication is the default monoid for int's
>>> monoid(1, 2, 3, 4)  
24

We can extract the monoid implementation explicitly. This is necessary for accessing the neutral element or to reduce empty lists

>>> mul_monoid = monoid[int]  
>>> mul_monoid.neutral()
1
>>> monoid.neutral()
traceback
...
ValueError(...)

The default monoid for a type can be overridden inside a with block using

>>> with monoid.override(int, "add_int"):
...     print(monoid(1, 2, 3, 4))
10

For most functions using monoids and groups, it is advisable to select the implementation 
explicitly, instead of relying on automatic discovery from argument types. This 
is because the function :func:`monoid.neutral` do not receive any argument that would make 
it possible to compute the desired output type. Also, there is a small runtime penalty for 
dispatching by type each time a monoid method is called. As a general rule, it is safer 
and faster to use either ``monoid[type]`` or :func:`monoid.like` to select the desired 
monoid.


Functors/Applicative/Monads
===========================

Groups, monoids and semigroups describe relationships between functions and its arguments. 
Now, we want to explore relations between generic types and their type parameters. Take ``list[T]``
as an example: how can we make functions over ``T`` interact with lists of ``T``'s? Can those 
functions compose?

There are many variations to consider (we now call a generic container as ``F[T]``):

* Can functions over elements, ``f(T) -> S``, act on the container ``F[T]``?
* Does it generalize to functions of more than one argument, e.g., ``f(T1, T2) -> S``, and multiple containers ``F[T1]``, and ``F[T2]``?
* If a function returns a container, ``f(T) -> F[S]``, can we apply it to some ``F[T]``?
* Can we generalize to multi-argument functions ``f(T1, T2) -> F[S]`` and multiple input containers?
* What if the function is inside a container already ``F[f(T) -> S]``?

Let us start with the first bullet point. In the jargon of functional programming, 
the kind of interface we are looking for is called a "Functor". In sidekick, the functor interface is implemented via the
"apply" function. It receives a function and a container argument, and applies the
function into the elements of that container using the "functor" mechanism, which
returns a container of the same type.

For lists and most sequences, it applies the function to each element and return
a sequence with the resulting values.

>>> sk.apply(op.add(1), [1, 2, 3])
[2, 3, 4]

In the case of dictionaries, the default implementation takes the input function
and applies it in all values of the dictionary, returning a new dictionary:

>>> sk.apply(op.add(1), {"foo": 41, "bar": 42})
{"foo": 42, "bar": 43}

This interface is so important, that it has an special notation in sidekick:

>>> op.add(1) @ {"foo": 41, "bar": 42}
{"foo": 42, "bar": 43}

This works for fn-enabled functions. And we can always wrap a normal function
in ``fn()`` to make it work:

>>> fn(lambda x: x + 1) @ {"foo": 41, "bar": 42}
{"foo": 42, "bar": 43}

(but perhaps, using sk.apply explicitly is better.)

The :func:`sidekick.interfaces.apply` function checks the type of the second
argument and ask the related functor to execute the function in all elements of
the data structure and return the result.

Each container type has a different mechanism of applying the function into
its elements and reconstructing the resulting data structure. We already shown
how it work for dicts and sequences and this gives an intuition on what ``apply``
can do. However, ``sk.apply`` is more than executing functions on the elements of 
a collection: this transformation can be formulated for any object that references 
a value of generic type ``T``, even when that value is not explicitly stored. 
For instance, functions like ``F[T] = f(X) -> T`` are functors, 
even though they do not store any object of type ``T``, but rather a recipe 
to produce such objects.

>>> func = sk.apply(str, op.add(1))
>>> func(41)
'42'

Before continuing, let us pause for a brief comment on notation. 
The typing module considers ``list[int]`` as a concrete type of lists of integers. 
The generic version, ``list[T]``, acts like a function: give me a type ``T`` and 
I will give you a concrete type of lists of ``T``'s; a function over types rather 
than values. In type theory, those objects are known as **kinds** to distinguish 
from concrete types. 

Using this nomenclature, we can say that ``list[int]`` is a concrete **type**, and 
``list`` (or perhaps ``list[*]``, if we want to make the missing type parameter explicit) 
is a **kind**. A first-order kind, to be more specific, since it requires a single type
parameter to generate a concrete type. Similarly, ``dict[*, *]`` is a second-order
kind, because it requires two type parameters. 

Functor implementations for first-order kinds are unique, when they exist. This 
is an important property proven for Haskell's type system. It is unfortunately not clear
if the proof still holds for Python. We could expect it should, but it could probably
fail if the implementation uses lots of introspection or metaclass trickery. 

This result does not hold for higher order kinds. For instance, ``dict[str, *]`` is a 
first order kind and in principle, could have a different functor implementation than
``dict[int, *]``, ``dict[*, int]`` or even ``* -> dict[*, *]``.

Functors represent a relationship between a first-order kind and its free type. 
This relationship is universal for all possibles values of the type parameter. 
The ``list[*]`` functor, for instance, must have the same implementation for all 
types ``T`` and the implementation should not know the type of the parameters (no
``isinstance`` checks are allowed!).  

In the case of dicts, which are second order, it turns out that the correct 
implementation for ``dict[T, *]``  does not depend on ``T``. In other words: the 
functor for ``dict[str, *]`` is the same as the one for ``dict[int, *]`` or any 
other key type. Other higher order kinds can have more complicated stories.


Typing nomenclature
-------------------

Python is notoriously inconsistent in how it name things. Classes should have
CamelCase names, but ``int``, ``str``, ``list``, and most built-ins do not respect this rule.
Values should be lower_case, however ``True``, ``False`` and ``None`` aren't. And so many other
quirks that I guess make sense when you are Dutch or have some particular sense 
of humor. 

This state of things is confusing, specially when we are mixing Python with terse
mathematical notation. From now on, UpperCase names and letters will refer only to types or
kinds and lower case letters will be used as variables representing values or free 
type variables. Thus we known that ``F[a]`` is a type (produced from a first-order 
kind ``F``) and ``fa`` represents an instance of that type or a type variable 
depending on the context.

How can we combine ``F[a]`` with functions that operate either in ``a``'s or ``F[a]``'s?
The most simple situation is a function ``f`` that expects ``F[a]`` and return some other
type, i.e., ``f: F[a] -> b``. The function understands the container directly, hence we 
just pass it as an argument in a regular function call. Nothing new here.

The next case is the functor: from a function that operates in ``a``, ``f: a -> b``, and 
a container ``F[a]``, the functor mechanism (:func:`apply`) executes the function in each 
element of the container and reconstruct the resulting container ``F[b]``. We write the 
type signature as ``apply: (a -> b, F[a]) -> F[b]``.

After the functor, we will consider two more cases. The first is generalize to functions 
of multiple arguments ``f: (a, b) -> c`` to act on multiple containers ``F[a]`` and ``F[b]``. 
This is more complicated than the regular functor, and sometimes it is not possible to 
generalize to multiple arguments. When this is possible, we call the resulting interface an 
applicative functor or monoidal, but don't be dismissive by the scary names: mathematicians 
are not always great at naming things. Applicative functors are powerful and useful in many
practical contexts.

If, finally, if the function applied to an element produces a container, 
i.e., ``f: a -> F[b]``, the resulting application ```f(F[a]) -> F[b]`` defines a Monad, 
which is nothing more than a *"monoid in the category of endo-functors"*. Don't let the jargon distract you! 
Monads are very useful and are mostly implemented by the :func:`flatmap` in sidekick.


Classical functors
------------------

In the last section, we talked about function signatures for functor-like types.
However, simply implementing something with the correct type signatures do not
qualify it as a proper functor. Consider, for instance, these two candidate 
implementations of a functor mapping for lists:

.. code-block:: python

    @apply.register_functor(list)
    def good_functor_map(f, lst):
        return [f(x) for x in lst]

    @apply.register_functor(list)
    def bad_functor_map(f, lst):
        # We take at most two elements of the list, just because ;)
        return [f(x) for x in lst[:2]]


Both satisfy the required type signatures, but what makes one a good functor and
the other a bad functor? Can we prove that a **bad_functor_map** not only looks
suspicious, but is indeed **wrong**?

The answer to discard it lies on the "functor laws": those are a set of properties 
that proper functors must obey. It goes beyond type signatures and express some constrains 
on how the apply function should behave. 

1. A functor should not change when transformed by the identity function, i.e.,
   ``apply(identity, xs) == xs``
2. It should respect function composition so the effect of transforming by
   ``h(x) = f(g(x))`` should be equivalent of first transforming by
   ``g`` and then by ``f``
   
Let us write the second point in a more rigorous notation. The fact that 
:func:`apply` is curried  implies that it accepts both type signatures: 
``apply: (a -> b, F[a]) -> F[b]``, and ``apply: (a -> b) -> (F[a] -> F[b])``. The
second case is specially interesting: we can think of it as a procedure 
that lifts a function that acts on elements to a function that acts directly on
the container. That way, if ``f`` is a regular function that acts on elements,
``apply(f)`` is a lifted function that acts on containers.

The second property can thus be written more formally like 

.. code-block:: python

    apply(f >> g) == apply(f) >> apply(g)

where ``>>`` defines function composition using sidekick notation for fn-functions.

It is easy to verify that the ``good_functor_map`` respect both laws and the ``bad_functor_map``
violates both if the list has more than two elements.

Apply is a user-facing and easy to use API for working with functors and applicatives 
(see next section). If you want to create your own implementation for custom types, read 
the documentation for the :cls:`Functor` and :cls:`FunctorInstance` classes.

Similarly to monoid, semigroup and others, apply can be specialized for a given type
using the getitem notation:

>>> map_list = apply[list]  # specialize for lists
>>> map_list(lambda x: x + 1, (1, 2, 3))  # oops, inconsistent types!
[1, 2, 3]


Applicative functors
--------------------

Generalizing :func:`apply` for multi-argument functors is not straightforward because
both the identity function and function composition are not well defined for functions
with more than one argument. We need a more indirect approach.

The first important insight is to know that it is possible to generalize apply
from 2 to n arguments. Let us understand how this generalization works, supposing
someone has already  figured out what to do with two arguments. The argument
is a little bit brain bending, so you might want to read this section twice.

Suppose we want to apply::

    apply(f, fa, fb, fc) -> fd
    
    where
        f: (a, b, c) -> d
        fa: F[a]
        fb: F[b]
        fc: F[c]
        fd: F[d]

but if we know how to ``apply(f', fa', fb') -> fc'`` for any set of
types ``(a', b', c')``, it surely must work for this curious contraption::

    fg = apply(curry(3, f), fa, fb)

This returns a functor ``fg`` of type ``F[c -> d]``, since the curried version of ``f(a, b, c)``, when
called with two arguments will return a function that receives a third argument ``c`` and
then compute the result of type ``d``. Given that ``fg`` is a functor 
(that incidentally contains functions), there is nothing that prevents us 
to use it as an argument to apply again. We obtain the final answer by::

    fd = apply(lambda g, c: g(c), fg, fc)

Thus apply will execute each function in the ``fg`` functor with the corresponding value
coming from the ``fc`` functor. This creates our final result ``fd``. This method can
be easily generalized to functions with any number of arguments, even though it is
not the most efficient mechanism due to the creation of intermediary data structures
and lots of indirection in the creation of partially applied functions.

It is a good check, however, if our generalization for multiple arguments is
consistent. If applying a function of 3 arguments is not consistent with this
method, it is not a correct applicative functor.


Monoidals and applicative laws
..............................

The previous section showed that if we can define apply for 2-argument functions, 
it is possible to generalize to any arity. It does not tell us, however, how could we
employ such generalization and which properties are necessary to do it correctly.
This section introduce the concept of a Monoidal, which is equivalent to an Applicative,
but is perhaps easier to understand and to reason about.

The crucial step for going from one to two arguments is the ability to group
elements of each container in pairs. Something like::

    pairwise(F[a], F[b]) -> F[(a, b)]

For sequences, for instance, there are two obvious ways to do this pairing: we can 
take the cartesian product of the two sequences and produces every possible pair or
zip both data structures, stopping at the smallest sequence.

Having both ``apply(a -> b, F[a])`` and ``pairwise()`` defined above we can easily 
generalize apply to two arguments::

    apply2(f, fa, fb) = apply(lambda args: f(*args), pairwise(fa, fb))

We could also easily define pairwise in terms of ``apply2``, showing that both 
formulations are equivalent::

    pairwise(fa, fb) = apply2(lambda *args: args, fa, fb)

``pairwise(fa, fb)`` is the first part of defining a Monoidal. As the nome suggests, this
is somewhat related to a Monoid and pairwise fills an analogous role as the associative
binary operation for Monoids. To complete a Monoidal, we also need a neutral element. This is 
just a function that produces a Functor with an empty tuple::

    neutral: () -> F[()]

The reason we call it "Monoidal" and not "Applicative Monoid" or something like this 
is because ``pairwise()`` is not really associative.

    pairwise(pairwise(fa, fb), fc): F[((a, b), c)]
    pairwise(fa, pairwise(fb, fc)): F[(a, (b, c))]

Since ``((a, b), c) != (a, (b, c))``, associativity is lost. We can make it truly 
associative by flattening the tuples on both sides (it also requires to 
elide empty tuples terms, and to unwrap a 1-tuple element, as in ``tuple[a] -> a``). 
Some programming languages like Perl, Matlab and Maple implement this behavior by 
default, making Monoidal true monoids. Python and most mainstream programming 
languages, however, don't.

The laws for Monoidals now can be written in terms of these two operations. I will use an infix
notation ``x <> y = pairwise(x, y)`` for brevity:

1. Left identity: ``apply(lambda x, _: x, fa, neutral()) = fa``
2. Right identity: ``apply(lambda _, y: y, neutral(), fb) = fb``
3. Associativity: ``flatten((fa <> fb) <> fc) = flatten(fa <> (fb <> fc))``
4. Naturality: ``apply(fg, fa <> fb) = apply(f, fa) <> apply(g, fb)``, where ``fg(x, y) = (f(x), g(y))``

Here, ``flatten`` is a function that flattens tuples inside a functor container.
The first and second rules are generalizations of the identity rule for functors. 
The left identity, for example, ignore the values of the second argument, 
returning the first unmodified. Apply also requires a "neutral" functor that do 
not affect the shape of the other argument when we make the pairwise association.

Associativity is required if we want that argument position should have no
effect in the results of apply. For instance, if we swap two arguments both in
lifted and non-lifted functions, the result should be the same::

       apply(λ x, y, z: f(x, y, z), fx, fy, fz)
    == apply(λ y, x, z: f(x, y, z), fy, fx, fz)  
    == apply(λ y, z, x: f(x, y, z), fy, fz, fx)

Here we took some liberty on the notation of lambda (λ) functions.

Finally, the naturality law requires that a function that operates independently 
over each argument should not interfere in the pairwise association. That is, we 
could either combine the functors and then apply the function to a pair or modify
each functor by their respective function and then combine both results. 

Like functors, new applicatives can be created by implementing instances of 
:cls:`Applicative` and :cls:`ApplicativeInstance` classes or via a decorators
using :func:`apply.register_pairwise` or some similar decorators.



Monad
=====

We saw that ``apply(f)`` lifts a function that operates over elements to a function
that understands the container. That is, if ``f: a -> b``, then ``apply(f): F[a] -> F[b]``

Since ``sk.apply()`` is a curried function, we pass a single argument of type
`a -> b` (the first argument is a function) and it will return another function
of type `F[a] -> F[b]`.  The function has, therefore, two type signatures:

* `apply((a -> b), F[a]) -> F[b]`
* `apply(a -> b) -> (F[a] -> F[b])`


From this point of view, we say a container is a functor if we can upgrade a
function that acts on values to a function that acts on containers of those
values. It is easy to conceive useful ways to make this upgrade for many container
types such as lists, dicts, sets, etc.

Now the monad. The idea is pretty similar, but now we have a function that already
puts its results into a container:

* `apply_flat((a -> F[b]), F[a]) -> F[b]`
* `apply_flat(a -> F[b]) -> (F[a] -> F[b])`

This can happen frequently with lists and other collections to be useful, but it
really shines with classes that are not traditional containers.


* upgrade(F[a] -> b) -> (F[a] -> F[b])

* downgrade(F[a] -> F[b]) -> (a -> b)
* downgrade(F[a] -> b) -> (a -> b)
* downgrade(a -> F[b]) -> (a -> b)

* mix(F[a] -> F[b]) -> (F[a] -> b)
* mix(F[a] -> F[b]) -> (a -> F[b])
* ...
