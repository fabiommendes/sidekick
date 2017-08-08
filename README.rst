========
Sidekick
========

Sidekick is a helpful library that gives you functional superpowers.
It implements a few utility functions and types that make functional programming 
more pleasant in Python. It is designed to be self-contained and it wraps most
of the functionality in the toolz library. Of course you can also use it in
conjunction with other functional programming libraries such as funcy, fn.py and
Pyrsistent.

If you are lazy, simply import everything and start to play ;)

>>> from sidekick import *


Function composition
====================

Heavily functional in Python code quickly becomes an unholy mess:

>>> import os
>>> print(
...     '\n'.join(
...         map(
...             lambda x: '%s) %s' % (x[0] + 1, x[1]), 
...             enumerate(
...                 sorted(
...                     filter(
...                         lambda x: x.endswith('.py'),
...                         os.listdir(os.getcwd()), 
...                     ),
...                     key=str.casefold,
...                 )
...             )
...         )    
...     )
... )
1) setup.py
2) tasks.py

We formatted for maximum legibility, but even so that are so many nested 
functions that it is not even funny. The code above reads all files from  
the current directory, keeps only the `.py` files, sort them alphabetically 
(after normalizing case), and finally prints a list of files on the screen.

We can do better with sidekick:

>>> print(
...     os.getcwd() | fn
...         >> os.listdir
...         >> filter(_.endswith('.py'))
...         >> order_by(str.casefold)
...         >> enumerate
...         >> map(lambda x: '%s) %s' % (x[0] + 1, x[1]))
...         >> '\n'.join
... )
1) setup.py
2) tasks.py

Let us unpack all those commands.

**Function pipelines**

The function pipeline operator ``>>`` is used to compose 
functions to form a pipeline where each function passes its results to be 
consumed by the next one. Hence,

>>> pipeline = f1 >> f2 >> f3 >> ...                            # doctest: +SKIP
  
is a function pipeline that calls ``f1()``, than pass the result to ``f2()``, 
which goes to ``f3()``, and so on. The code above is equivalent to the nested 
function definition:

>>> pipeline = lambda x: ...(f3(f2(f1(x))))                     # doctest: +SKIP

The pipeline syntax obviously do not work with regular functions. The 
trick is to use fn() magic object either to create functions that accept 
composition or to mark the beginning of a pipeline:

.. ignore-next-block
.. code-block:: python

    f1 = fn(real_f1)                        # f1 now understands the pipeline!
    pipeline = f1 >> f2 >> f3 >> ...                            
    pipeline = fn >> f1 >> f2 >> f3 >> ...  # this also works!

If you are still not so sure how the pipeline works, consider the more 
self-contained example: 

>>> import math
>>> sqrt = fn(math.sqrt)
>>> safe_sqrt = abs >> sqrt
>>> safe_sqrt(-4)
2.0

In the code above, the argument is passed first to the abs() function and then 
is redirected it to the sqrt(). The order the operators appear is the same 
order in which the functions are applied.

The pipeline can also be constructed backwards, reading right to left:

>>> safe_sqrt = sqrt << abs  
>>> safe_sqrt(-4)
2.0

In either case, the argument flows in the same direction that the pipeline 
operator points to. Read it as an arrow that tells the direction information
flows.


**Filter operator**

Once a pipeline is created, we can feed arguments to it either by calling 
the resulting function or by using the filter (pipe) operator. A filter takes 
the value on the left hand side and passes to the function in the right hand 
side:

>>> 4 | sqrt
2.0

This is equivalent to the more traditional ``sqrt(4)``. Filters can be chained
and mixed with function pipelines

>>> 16 | sqrt | sqrt
2.0
>>> 16 | sqrt >> sqrt
2.0

Filters have a lower precedence than pipelines. This means that the expression
``x | f1 >> f2 | f3``  is interpreted as ``x | (f1 >> f2) | f3``. That is, it 
takes x, passes to the pipeline constructed by composing f1 with f2 and then 
finally passes the result to f3.


**Recapitulation**

Let us recap. Remember the code we started with: 

.. ignore-next-block

>>> print(
...     os.getcwd() | fn
...         >> os.listdir
...         >> filter(_.endswith('.py'))
...         >> order_by(str.casefold)
...         >> enumerate
...         >> map(lambda x: '%s) %s' % (x[0] + 1, x[1]))
...         >> '\n'.join
... )

This should not be a foreign language anymore. This line of code reads the current 
working dir returned by os.getcwd() than passes it through a series of 
transformations:

1. List the files
2. Select files with the '.py' extension using a quick lambda (more later...)
3. Sort files by name using casefold to normalize
4. Enumerate the sorted list
5. Maps all items to be a string in the ``"idx) filename'`` format.
6. Join the list of files with new lines
7. Finally, pass the result to the print function.    

Compare it to a more idiomatic Python code::

    dir = os.getcwd()
    files = os.listdir(files)
    py_files = (f for f in files if f.endswith('.py'))
    py_files = sorted(py_files, key=str.casefold)
    lines = ['%s) %s' % item for item in enumerate(files)]
    print('\n'.join(lines))

It all comes to personal taste, but one cannot deny the functional version 
is more compact since it do not require the noise of all those temporary 
variable definitions.


Partial application
===================

The fn object can be used as a decorator to give regular functions 
superpowers. We already mentioned the pipeline and filter operators. Let us see
what else it can give us.

Consider the function:

.. code-block:: python

    @fn
    def g(x, y, z):
        return (x, y, z)

The function ``g`` can now be used as a filter or as a part of a pipeline. 
Like normal Python functions, fn-functions also use parenthesis to make call. 
If a function is called with square brackets, however, it makes a partial 
application:

>>> g2 = g[1, 2]
>>> g2(3)
(1, 2, 3)

By default, partial application respect a auto-currying semantics. We decided to
not make currying the default behavior for standard function calls since 
currying can be confusing on languages that support a variable number
of arguments such as Python. If you never heard this name, autocurrying is the 
process in which a function that do not receive all required arguments simply 
return another function that receives the missing ones. It is an attempt to 
mimick the behavior of curried programming languages define only single-argument
functions (in those languages, e.g., Haskell, a function of two variables is
a function of a single variable that returns another function of one variable).

fn-functions also suports a more explicit and flexible mode of partial function 
application:

>>> gpart = g.partial(1, y=2)

Finally, both partial and the square-brackets notation understands the special 
placeholder object ``_`` as a declaration for the position in which a single
free argument should be used

>>> g[1, 2](3) == g[_, 2, 3](1) == g[1, _, 3](2)
True

If the placeholder is repeated, the same argument is passed to all used 
positions

>>> g[_, _, _](1)
(1, 1, 1)

The fn object offers a few additional goodies. The first is the ``method`` 
attribute, that declares a function to be autocurrying::

>>> g = fn.curried(lambda x, y, z: x + y + z)
>>> g(1, 2, 3) == g(1, 2)(3) == g(1)(2)(3) == 6
True

Secondly, the fn object itself accepts the bracket notation and can be used
to define partial application directly when the function is created::

.. skip-next-block
.. code-block:: python

    g_ = lambda x, y, z: x + y + z
    fn[g]           # the same as fn(g)
    fn[g, 1]        # the same as fn(g)[1]
    fn[g, _, 2, 3]  # the same as fn(g)[_, 2, 3] (you get the idea!)


Quick lambdas
=============

The previous section introduced the placeholder object ``_``. It exists in order
to create quick lambdas for use in functional code. Functional code relies on
lots of short anonymous functions and seems that nobody likes Python 
lambda's syntax: it is ugly, a bit too verbose and not particularly readable. 
Even Javascript did it right with ES6, so why wouldn't we?

Sidekick provides a quick way to define lambdas using the placeholder object. 
Just create an arbitrary Python expression and wrap it with the fn() object. 

>>> inc = fn(_ + 1)
>>> total_cost = fn(_.num_items * _.price)

In the future, we may create additional placeholders such as ``__`` and ``___`` 
to define functions with multiple arguments. For now, use a lambda.


Predicates
==========

Predicates are functions that receive a single argument and return a boolean. 
They are used in many contexts, usually to select elements in an collection. 
Consider Python's builtin filter function:

>>> names = ['foo', 'bar', 'ham']

Sidekick extends the builtin filter function to accept placeholder expressions
and curring.

>>> filtered = filter(_.startswith('f'), names)

The result is a filter object, which we convert to a list using the magic ``| L``
filter notation:

>>> filtered | L
['foo']

In sidekick we can expliclty tell that a quick lambda or a function is a
predicate by wrapping it with the predicate function:

>>> startswith_f = predicate(_.startswith('f'))
>>> filter(startswith_f, names) | L
['foo']

For now it is just the same as using a regular function. Predicate functions,
however, compose nicely under boolean expressions. This makes it easier to
create complex predicates instead of relying on awkward lambda functions:

>>> startswith_b = predicate(_.startswith('b'))
>>> filter(startswith_f | startswith_b, names) | L
['foo', 'bar']


Record types
============

Classes are often used as a heavy-weight solution to types that behave 
essentially as a bag of values. Python do not have very good builtin solutions 
to this problem: literal string keys of dictionaries are ugly to read and a 
pain to type. ``namedtuples`` have an awkward API and can bring some unwanted 
tuple/sequence semantics in surprising places. Finally, SimpleNamespace fail in 
subtle ways such as not implementing the hash protocol.

Sidekick provides two lightweight functions for creating on-the-fly record 
types: :cls:`record` and :cls:`namespace` that resemble the SimpleNamespace 
type.

Just call ``record()`` with a few named arguments to create a new immutable
value

>>> pt = record(x=1, y=2)

This defines a new record with .x and .y attributes

>>> pt.x, pt.y
(1, 2)

Records are immutable and should be favored when mutability is not strictly 
required. If you need a mutable bag of values, use :cls:`namespace`. It behaves 
similarly to :cls:`record`, but it allows mutation:

>>> pt = namespace(x=1, y=2)


Custom record types
-------------------

While record() and namespace() types can be useful, it is often more prudent to
define the structure of a record type explicitly since it is easy to miss a few
parameters, or to make a typo. In most cases, you should favor custom record
types created deriving from the Record class:

>>> class Point2D(Record):
...     x = field()
...     y = field()

(Of course we could include a few methods, but lets forget about it now).

This is a little bit more work, but it will surely save you from a few bugs
later on. Point2D instances expect to have exactly two attributes named x and y,
and you cannot skip one of them or set a third z coordinate.
Another subtle but useful advantage is that Point2D constructor also accepts
positional arguments, so ``Point2D(1, 2)`` is also a valid way to construct 
an instance.
   
Even if you do not plan to diverge much from OO, Record is a nice starting point 
to defining your own classes. They already implement a few useful methods that
Python does not provide useful default implementations: no need to override
__init__, __repr__, __eq__ and __hash__. Also Record subclasses are immutable
by default. Python classes do not provide a good way for doing this, and with
records you can always opt-out if mutability is required:

>>> class Point2D(Record, mutable=True):
...     x = field()
...     y = field()

Record fields can declare default values and in the future we plan to support
additional features such as type-checking and validation.

>>> class Point2D(Record):
...     x = field()
...     y = field()
...     origin = field(default=(0, 0))


Union types
===========

Union types represent types that can be in one of a series of different states. 
Most functional languages implement Union types (a.k.a. abstract data types), 
as one of the basic ways to create composite types. 


Usage
-----
    
A new Union types is declared using the pipe sintax. We define each state by 
invoking an attribute from the ``opt`` special object: 

>>> Maybe = opt.Just(object) | opt.Nothing

The Maybe type represents values that can either exist in the "Just" state or
be Nothing. Notice that Nothing is a singleton that accepts no argument, while
Just requires a single argument which corresponds to the value held by the
Maybe instance.

We create instances by calling the Just(...) or the Nothing constructors

>>> x = Maybe.Just(42)
>>> y = Maybe.Nothing   # ok, that is technically not calling a constructor...

Maybe types is a functional response to the infamous null pointer. Instead of
having the null value lurking around in every corner, we explicitly model 
nullable objects as instances of the Maybe type. 

Using a maybe almost always requires some sort of pattern matching. This is the 
closest we can get in Python::

    if x.just:
        print('value is:', x.value)
    elif x.nothing:
        print('x is empty')
    
The other possibility is to use the match method::

    # Poor man's version of Haskell's pattern matching
    is_the_answer = x.case_of(
        just=lambda x:
            x == 42,

        nothing=lambda:
            False,
    )

Finally, if an specific pattern matching is used repeatedly, we can define a 
type matching function with the notation::

    is_the_answer_fn = Maybe.case_fn(
       just=lambda x:
            x == 42,

        nothing=lambda:
            False,
    )
    is_the_answer = is_the_answer_fn(x)

This is equivalent to the prior method, but it should be faster if the case 
function is called lots of times.


The Maybe type
--------------

While in real functional languages the Maybe type is usually defined just as 
we shown above, Python is an OO language and it might be more useful to define 
it as a class with a few extra methods. Sidekick's Maybe implements a few 
extra goodies besides the plain definition.


The Result type
---------------

The result type (sans extensions) is defined as::

    Result = opt.Ok(object) | opt.Err(object)

Hence it has two states: Ok and Err that both can hold additional data. Result
is a functional way to represent a computation that may fail. It is used where
in Python one would normally use an exception.

##TODO: specific documentation 