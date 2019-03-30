===========================
Extended function interface
===========================

Python functions have a somewhat minimalist interface: we can introspect and
call them. Sidekick functions extends standard Python's functions interfaces
with a few useful methods and operators.


Function operators
==================

Composition
...........

Bitwise shift (``>>`` and ``<<``) are resignified as function composition
operators. The argument flows through the composed function in the same
direction that bit shift points to:

>>> from sidekick.math import abs, sqrt
>>> safe_sqrt = abs >> sqrt  # same as lambda x: sqrt(abs(x))
>>> safe_sqrt(-4)
2

It could be defined equivalently as

>>> safe_sqrt = sqrt << abs

Obviously only sidekick-enabled functions accept that syntax. We can support
arbitrary Python callables by prefixing the pipeline with the fn object:

>>> incr = lambda x: x + 1
>>> incr_pos = fn >> incr >> abs  # (or fn << abs << incr)

fn works as if it was an identity function in the pipeline.

Our evil master plan, of course, is to make this (or a similar) syntax official,
so there would be no separation between sidekick functions and regular Python
functions. You can invoke some arcane magic to make it so:

.. code-block:: python

    from sidekick.evil import forbidden_powers

    forbidden_powers(spell='i now summon the great powers of lambda!')

    function = (lambda x: 2 * x) >> (lambda x: x + 1)
    print(function(x))

Voilá! A working implementation! But seriously, please never use it in
production ;)


Logical combinations
....................

Bitwise operators ``| & ~`` compose predicate functions. That is, ``f | g``
returns a function that produces the logical OR between f(x) and g(x).
Evaluation is done in a "short circuit" fashion: ``g`` is only evaluated if
f returns a "falsy" value like Python's ``or`` operator.

Logical composition of predicate functions is specially useful in methods such
as filter, take_while, etc, that receive predicates.

>>> from sidekick.pred import divisible_by
>>> list(filter(divisible_by(3) | divisible_by(4), range(10)))
[0, 3, 4, 6, 8]

The ``&`` stands for logical conjunction (the AND operation) and ``!`` for
negation:

>>> divisible_by_10 = divisible_by(2) & divisible_by(5)
>>> divisible_by_10(5), divisible_by_10(100)
(False, True)

>>> odd = ~divisible_by(2)
>>> odd(2), odd(3)
(False, True)

The bitwise xor ``^`` is interpreted as the power operator: ``f ^ n`` is ``f``
applied to itself n times.

>>> from sidekick import op
>>> incr = op.add(1)
>>> incr_by_3 = incr ^ 3  # an awful, but correct implementation
>>> incr_by_3(39)
42

The evil module activates this functionality for regular functions, but, again,
use it with care (or, better yet, not at all).


Mapping
.......

Mapping is an important operation that also has a syntactic sugar. The ``@``
operator in ``f @ x`` tries to call the ``x.map(f)``, and if x doesn't have this
method, it tries one of the following:

* list, tuple, set: apply function to each element, preserving the type.
* dict: apply function to values.
* strings: apply function to each character, joining the result.
* other: call :sidekick:`functor_map(f, x)` singledispatch function. Users can
  register implementations of arbitrary types in this function.

The default implementation of `functor_map` also does this:

* if object is a mapping, return the generator ``((k, f(v)) for k, v in obj.items())``.
* if object is iterable, return the generator ``(f(x) for x in obj)``.


Attributes
==========

#TODO: arity?

Consider the function

>>> @fn
... def add(x, y):
...     return x + y

sidekick functions expose standard function introspection facilities and also
play well with the ``inspect`` module.

>>> add.__name__
'add'

The wrapped function is accessible

>>> add.__wrapped__
<add ....>

>>> add.arity
2

>>> add.argspec
...


>>> add.signature
...



Methods
=======

# TODO: partial?
>>> nums = range(1, 6)
>>> fold(op.add, 0)(nums)
15
>>> fold.partial(op.mul, 1)(nums)
120
>>> fold.rpartial(0, range(5))(op.sub)  # ((0 - 1) - 2) - 3 ...)
-15
>>> fold.single(op.add, _, nums)(1)
16