===========
Union types
===========

Union types represent values that can be in one of a series of different states.
Many functional languages implement Union types (a.k.a. variant types, or
algebraic data types) instead of classical object oriented inheritance, as one
of the main ways for creating composite types. Sidekick brings them to Python.

Let us start with a classic example of a Union type: Haskell's Maybe. Consider,
for instance, that we want to fetch some value (from a db, for instance), but
that value is not guaranteed to exist. In Python we probably would return a
value in case of success and would either return None or raise an exception in
case of failure.

The problem with this approach is that the failure case and the success case have
completely different interfaces and this forces us to fill our code with lots
of ifs (or worst yet, with lots of try/except blocks). In a statically typed
language such as Haskell, the situation would be even worst: a computation must
have a predictable type and the compiler cannot
accept a function that can have different output types depending on the path of
computation. Some static languages "solve" this problem by sneakingly accepting
None (or null) as a valid value for any type. Tony Hoare, who pioneered this
approach in Algol W latter acknowledged that null references were a terrible
idea and called it his "billion dollar mistake".

In Haskell, that is solved using the Maybe type: this is a type that explicitly
encodes the two different success/error states:

    Nothing -- No value was produced.
    Just(x) -- Produced "just" x.

Since the type is "Maybe something", we can treat the result for any of the two
states with an uniform interface and compose it nicely with other functions that
understand maybes.

Here is a simple example in Python of a sqrt function that returns a Maybe
result:

    def sqrt(x: float) -> Maybe[float]:
        if x < 0:
            return Nothing

        # Quick and dirty Babylonian method for finding square roots
        y = x
        for _ in range(10):
            y = 0.5 * (y + x/y)
        return Just(y)


This puts exceptions out of the way and we can use it to compose with functions
that understand maybe types

.. ignore-next-block
.. code-block:: python

    values = [func_that_receive_maybes(sqrt(x)) for x in list]

A typical implementation of a ``func_that_receive_maybes`` would propagate
Nothings and apply some transformation to the Just values. No exceptions
involved.

How could we achieve that in Python?

The approach employed by sidekick is typical for object oriented languages: we
create the union type as a class hierarchy. Let us start from scratch:

.. code-block:: python

    class Maybe:
        pass

    class Just(Maybe):
        def __init__(self, value):
            self.value = value

    class Nothing(Maybe):
        """
        This probably should be a singleton.
        """

    # We create shortcuts to use the constructors from the base class
    Maybe.Just = Just
    Maybe.Nothing = Nothing

In the hierarchy above, both instances of Just and Nothing would be Maybes and
should present the same interface (unless you do something funny with those
sub-classes). This approach, however, is verbose and error prone. Sidekick has
an easier way:

.. code-block:: python

    from sidekick import Union, opt

    class Maybe(Union):
        Nothing = opt()
        Just = opt(value=object)

        # Additional methods can come in here...

The :func:`sidekick.opt` function is used to declare the names and types of all
arguments required by each case constructor. The Union metaclass is responsible
for creating the Just and Nothing subclasses that can be accessed as Maybe.Just
and Maybe.Nothing. If we need more control, specially for declaring different
methods and implementations in each case class, it is possible to declare each
case as inner classes that inherit from the base union type:

.. code-block:: python

    class Maybe(Union):
        class Just(Maybe, args=opt(object)):
            def some_method(self):
                return 'called from a Just({})'.format(self.value)

            def a_method_for_the_just_state(self):
                return "I really should'd do that"

        class Nothing(Maybe):
            def some_method(self):
                return 'called from a Nothing'


In OO parlance, Maybe is an abstract base class that cannot have any instances.
We create instances using one of the valid constructors "Just" or "Nothing":

>>> x = Maybe.Just(42)
>>> x
Just(42)

States that do not take parameters behave as an special kind of singleton that
do not use an explicit function call for initialization

>>> y = Maybe.Nothing; y
Nothing
>>> isinstance(y, Maybe)
True

Notice we could declare the case classes Just and Nothing outside the body of
the base class Maybe. This is often convenient if a lot of tweaking on those
child classes is necessary. Sidekick allows that, but prevents subclassing
outside the module that defines the base class. This makes Union types "final"
and prevents arbitrary levels of inheritance. The reason for this restriction is
that many algorithms rely on knowing beforehand all possible case classes of a
union type. Adding new cases can lead to bugs and inconsistencies for those
algorithms. If you really need arbitrary subclassing, you probably should model
your data as a standard object oriented inheritance.


Usage
=====

Class declaration
-----------------

Sidekick provides several ways to construct union types. The best case depends
on the complexity of your case classes and if you want to support any Python
version before 3.6. Let us start simple:

Explicit options
................

.. code-block:: python

    class Maybe(Union):
        Nothing = opt()
        Just = opt(object)

This create the Just state with a default .value attribute holding an arbitrary
Python object and the Nothing singleton.


Inner classes
.............

.. code-block:: python

    class Maybe(Union):
        class Nothing(Maybe):
            pass

        class Just(Maybe):
            args = opt(object)


You can mix both syntax (i.e., define some cases as inner classes and other
cases as opt() values), however we advice to choose a single way and keep it
consistent.

Inner classes with annotations
..............................

If you only cares about the latest and shinny Python (3.6+), use type
annotations for classes instead of opt(). Sidekick understands them just fine:

.. code-block:: python

    class Maybe(Union):
        class Nothing(Maybe):
            pass

        class Just(Maybe):
            value: object

External classes
................

The case classes can be moved outside the base union type body if they are
still declared on the same module. Sidekick forbids arbitrary subclassing any
union type outside the module it was declared:

.. code-block:: python

    class Maybe(Union):
        """
        Maybe type.
        """

    class Nothing(Maybe):
        """
        The Nothing case.
        """

    class Just(Maybe):
        """
        The Just case.
        """
        args = opt(object)


Case expressions
----------------

When using union types we often want to check in which state a variable is and
then proceed accordingly. This can be easily done with an instance check:

.. code-block:: python

    if isinstance(x, Maybe.Just):
        print("value: ", x.value)
    else:
        print("nothing")

This pattern gets boring really fast. Sidekick offers a "case" syntax that can
declare a pattern matching expression that associates specific variants with a
corresponding handling function:

.. code-block:: python

    result = case[x](
        Just=lambda value: "value: {}".format(value),
        Nothing=lambda: "empty",
    )

    # x is Just(42)!
    assert result == 'value: 42'

We used lambdas here, but this pattern tends to be neater when we combine with
other functions. Sidekick has a nice library of small composable functions that
can go a long way to simplify your case expressions:

.. code-block:: python

    from sidekick import const

    result = case[x](
        Just=str,
        Nothing=const("---"),
    )
    assert result == '42'

Each function in the case expression must accept the same number of arguments
as the constructor of its associated case. In our example, the Just case expects
a function that receives a single argument, while the Nothing case requires a
function that receives zero arguments. Notice that those case functions **do not
receive an instance** as argument, but rather the arguments necessary to
construct the corresponding instance.

The case expression asserts that we treat exhaustively all required cases.
Sometimes we may want a *catch-all* case, specially when dealing with Union types
with many different variants. Sidekick understands the ``else_`` clause in case
expressions:

.. code-block:: python

    result = case[y](
        Just=str,
        else_=const('---'),
    )
    # y is nothing
    assert result == '---'

The ``else_`` case must be associated with a function that receives a single
parameter corresponding to the input itself.


Case functions
--------------

Case expressions have a non-trivial runtime overhead. We can reduce this overhead
by declaring case functions and reusing them several times. For classes with
a large number of variants, case functions may be even faster then if statements.

.. invisible-code-block:: python

    Maybe = type(x)._meta.base_class  # we redefined maybe so many times...

.. code-block:: python

    func = case_fn[Maybe](
        Just=str,
        else_=const('---'),
    )
    assert func(x) == '42'
    assert func(y) == '---'

Case functions may take more than one argument, but they dispatch only on
the first one.

.. code-block:: python

    add = case_fn[Maybe](
        Just=lambda x, y: x + y,
        Nothing=lambda y: y,
    )
    assert add(x, 1) == 43
    assert add(y, 1) == 1

Sometimes case functions are just too complicated to fit inside small lambdas
or generic composable functions. Union types with a very large number of
variants also makes the above syntax hard to read. Sidekick offers the
:func:`sidekick.casedispatch` decorator that works similarly to
:func:`functools.singledispatch` and is a better fit for those cases.

.. code-block:: python

    @casedispatch(Maybe.Just)
    def add(x, y):
        """
        Adds a Maybe[Number] with a number. The first argument must be a Maybe
        and the second is a Number. It returns the sum of the two values
        treating Nothing as zero.
        """
        return x + y

    @add.register(Maybe.Nothing)
    def _(y):
        return y


This creates a function add(x, y) that performs the same operations as the
case_fn defined before.

.. code-block:: python

    # just as before...
    assert add(x, 1) == 43
    assert add(y, 1) == 1

A drawback with this notation is that the register mechanism adds a lot of line
noise in the form of ``@add.register(Base.Case)`` decorators. We provide a
third way and cleaner way to produce a case function from any object that
define a namespace. The target object could be a model or even a SimpleNamespace
instance, but the default way is to decorate a class.

.. code-block:: python

    @casedispatch.from_namespace(Maybe)
    class add:
        """
        Adds a Maybe[Number] with a number. The first argument must be a Maybe
        and the second is a Number. It returns the sum of the two values
        treating Nothing as zero.
        """

        def Just(x, y):
            return x + y

        def Nothing(y):
            return y

    assert add(x, 1) == 43
    assert add(y, 1) == 1



Self-references
---------------

Union types are very useful to define immutable tree-like data structures.
Consider the declaration of a linked list node bellow:

.. code-block:: python

    class List(Union):
        """
        A traditional LISP-like singly linked list.
        """

        # If you only care about Python 3.6+, declare the cons case as
        # Cons = opt(head=object, tail=List)
        Cons = opt([('head', object), ('tail', List)])
        Nil = opt()

        def cons(self, x):
            "Adds an element to the beginning of the list"
            return self.Cons(x, self)

        def reverse(self, acc=Nil):
            "Reversed copy of the list."

            if self.is_nil:
                return acc
            else:
                x, xs = self.value
                return xs.reverse(acc.cons(x))

Notice that List declaration has a self reference since Cons has a tail attribute
of type List. Attentive users may expect the above declaration to fail since
the Cons case has a reference to a List type that is still being created.
Sidekick uses some metaclass trickery to inject a reference to the newly created
class into its module namespace so that it is accessible from the class body.

While this is completely valid Python, this trick tends to trip static code
analysis. Sidekick also alias the currently created class as "this" so we can
use the following pattern:

.. code-block:: python

    this = Union  # make static code analysis happy!

    class List(Union):
        Cons = opt([('head', object), ('tail', this)])
        Nil = opt()

    ...  # possibly declare other union types

    del this  # clean module namespace


Multimethods
------------

In classical inheritance, a base class have an open number of subclasses
that may override specific parts of the interface. When dealing with union
types, the number of subclasses is known in advance and one may choose between
three strategies for implementing methods that behave differently in each
variant:

* Implement the method in the base class using an if clause or a case expression
  to handle each case explicitly.
* Implement a *catch-all* method in the base class and specialize in each case
  sub-class.
* Implement a function using :func:`sidekick.casedispatch`. If one such function
  is found inside a class body, sidekick automatically distribute each
  implementation to the corresponding method during class creation.

Bellow, we show how to implement a simple recursive "size" method for the List
using each strategy:

**1) Using if statements:**

.. code-block:: python

    class List(Union):
        """
        A classic singly-linked list.
        """

        Cons = opt([('head', object), ('tail', this)])
        Nil = opt()

        def size(self):
            """
            Return the size of a list.
            """
            if self.is_nil:
                # In the Nil state, the list is empty
                return 0
            else:
                # Remember that in the Cons state, instances have a .head
                # attribute that holds the content of the first position and
                # a .tail attribute that is a reference to the list's tail.
                #
                # In the Cons state, we have to compute the size from the
                # size of the tail.
                return 1 + self.tail.size()

**2) Using object oriented specialization**

.. code-block:: python

    class List(Union):
        """
        A classic singly-linked list.
        """

        def size(self):
            """
            Return the size of a list.
            """
            # Usually here goes the catch-all default implementation. We have
            # only two cases and it may be more natural to handle each case
            # in its respective declaration.
            raise NotImplementedError('implemented in case classes')


    class Nil(List):
        args = opt()

        def size(self):
            # We override the parent behavior here.
            return 0


    class Cons(List):
        args = opt([('head', object), ('tail', this)])

        def size(self):
            # Just as before...
            return 1 + self.tail.size()

**3) Using a case method dispatch**

.. code-block:: python

    class List(Union):
        """
        A classic singly-linked list.
        """

        Cons = opt([('head', object), ('tail', this)])
        Nil = opt()

        # In this last alternative, we concentrate the all implementations of
        # the same method in a single place. The class constructor is
        # responsible to distribute each function to the corresponding case
        # class
        @casedispatch.from_namespace(List)
        class size:
            "Returns the size of the list"

            def Cons(x, xs):
                # Each method receive a deconstructed version of the case
                # object
                return 1 + xs.size()

            def Nil():
                # Nil receives no arguments since we pass no attributes to the
                # Nil constructor.
                return 0

In all cases the effect is similar, and the list object gains a size method
that computes the size of a list:

>>> # Same as [1, 2, 3]. A poor way to build a list ;)
>>> lst = List.Cons(1, List.Cons(2, List.Cons(3, List.Nil)))
>>> lst.size()
3

API reference
=============

Union types
-----------

.. autoclass:: sidekick.Union
    :members:

.. autofunction:: sidekick.opt


Case syntax and case dispatch functions
---------------------------------------

.. autoclass:: sidekick.case
.. autoclass:: sidekick.case_fn
.. autofunction:: sidekick.casedispatch
.. autofunction:: sidekick.casedispatch.from_namespace


See also
========

Check the reference for the :class:`sidekick.Maybe`, :sidekick:`Result` and
:sidekick:`List` for implementations of some classic union types.

.. toctree:: Classic union types
    Maybe <maybe.rst>
    Result <result.rst>
    List <list.rst>
