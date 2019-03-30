.. module:: sidekick



Handling functions
==================

Functional programming emphasizes small and simple functions that
can be composed together to implement complex computations. In functional
interfaces, we just need to match the input and output argument types of
functions. Usually this means that there is a high likelihood that functions
that manipulate similar data types can be plugged together even they were not
designed specifically yo do so.

Class-based interfaces must conform to ad hoc choices of method names and
behaviours and often do not exhibit this accidental composibility. In OOP, things
usually work together only when they are specifically *designed* to work together. This often
makes OOP code plagued with Adapter and Façade classes that add little to no value in
terms of functionality, but are required to compose different parts of your system.

Of course, functions are not guaranteed to compose nicely. A large part of
creating a composible ecosystem of functions is selecting common data structures
(or common abstract interfaces) and maintain consistency. Sidekick provides
functions to handle common Pythonic types: lists, dictionaries, iterators, strings,
etc.

If all else fails, we often can adjust functions to fit together using simple
transformations. This is the
role of most functions in this module: they take functions as arguments and
create new functions with slightly different functionality so they can receive
data in a format that would not fit the exact original definition.

.. invisible-code-block:: python

    from sidekick import op, L, N
    import sidekick as sk


Partial application
-------------------

Partial function application is a powerful way of creating new functions from
old ones. Consider the functions in the module :mod:`sidekick.op`: they
correspond to functional versions of Python's native operators.

>>> from sidekick import op
>>> op.mul(2, 3)
6

A partial application means that we fix some arguments of the function, and
obtain another function that receives the remaining arguments. The "double" function can
be easily created by partially applying 2 to the multiplication function above:

>>> double = sk.partial(op.mul, 2)
>>> double(21)
42

It is perhaps slightly easier to create "double" by partial application than
by redefining a brand new function with ``def``'s or ``lambda``'s. Since partial
application is so useful, we went one step further: all functions in
the :mod:`sidekick.op` module are **curried**. This means that if the function do not receive all required
arguments, instead of raising an error, we return a partial application of the
given arguments.

Creating a "double" function is therefore as easy the code bellow:

>>> double = op.mul(2)
>>> double(1.5)
3.0

It is possible to Curry arbitrary user-created functions

>>> add = sk.curry(2, lambda x, y: x + y)

When 2-argument function is curried, calling it as f(x, y) is equivalent to
f(x)(y).

>>> add(40, 2) == add(40)(2)
True

We can also use the implicit partial application to create useful functions on
demand:

>>> incr = add(1)
>>> incr(41)
42

:func:`curry` itself is a curried function, hence we can use it like

>>> add = sk.curry(2)(lambda x, y: x + y)

or, equivalently, as a decorator

.. code-block:: python

    import sidekick as sk

    @sk.curry(2)
    def add(x, y):
        return x + y

Currying usually requires functions of fixed number of arguments (the number of
arguments is called the *arity* of a function). We can control how many arguments
participate in the auto-currying by passing the arity number as the first argument to the
:func:`curry` function.

Curry accepts variadic functions, which understands arity as the minimum number
of arguments necessary to invoke the function. The caller can, however, specify
additional arguments.

Let us see it in action:

>>> add = sk.curry(2, lambda x, y, *args: x + y + sum(args))

This is a regular auto-curried function:

>>> add(1, 2) == add(1)(2)
True

But it accepts more than 2 arguments, if needed. (Notice that only the first two
arguments auto-curry.)

>>> add(1, 2, 3, 4)
10

Sometimes we don't known the arity of a function or don't want to think too much
about it. :func:`curry` accepts ``'auto'`` as an arity specifier so it will try
to infer the arity automatically. Under the hood, it just calls the :func:`arity`
function to infer the arity of its argument

>>> sk.arity(lambda x, y: x + y)
2


Currying vs partial application
...............................

It is easy to confuse currying with partial application. Currying is a way to
encode a function that receives several arguments into a series of partial
functions of a single argument. Partial application is just fixing some arguments
of functions that receive several arguments. It is similar, but not quite the
same.

Consider one particular example. If we partially apply one argument of a function that
requires 3 arguments, it is necessary to pass the missing two arguments in the next
invocation, otherwise it will raise an error.

>>> add_mod = lambda mod, x, y: (x + y) % mod
>>> add_mod10 = sk.partial(add_mod, 10)
>>> add_mod10(5)
Traceback (most recent call last):
...
TypeError: <lambda>() missing 1 required positional argument: 'y'

This behavior differs from a curried function, that would return a new function
that partially applies 9 to ``add_mod10`` (or partially applies 10 and 5 to
``add_mod``).

Partial application can occur from the left (default) or from the right, in
which we fix the rightmost arguments. :func:`rpartial` is similar to partial,
and does exactly that.

The example illustrates the difference between the two:

>>> two_divided_by = sk.partial(op.div, 2)
>>> divided_by_two = sk.rpartial(op.div, 2)
>>> two_divided_by(10)
0.2
>>> divided_by_two(10)
5.0


Functions
.........

.. autofunction:: sidekick.curry
.. autofunction:: sidekick.arity
.. autofunction:: sidekick.partial
.. autofunction:: sidekick.rpartial


Composition
-----------

Most computations can be formulated as the abstract sequence of operations:
1) gather input data, 2) perform some transformation and collect the result.
When the transformation can be decomposed in a series of smaller
transformations, this pattern can be elegantly formulated with :func:`pipe`
function.

The example bellow takes a value and pass it to a function that multiplies it
by four and then another function that adds 2 to the result.

>>> sk.pipe(10, op.mul(4), op.add(2))
42

In some cases, we might want to specify additional arguments passed to functions
in the pipe. This is acomplished by the :func:`thread` and :func:`rthread`
functions.

>>> sk.thread(10, (op.mul, 4), (op.add, 2))
42

:func:`rthread` is similar, but applies the piping argument to the right of
each operation.

It is often desirable to abstract the operations in a pipe without mentioning data.
This is responsibility of the :func:`pipeline` function.

>>> func = sk.pipeline(op.mul(4), op.add(2))
>>> func(10)
42

``pipeline(*funcs)`` is equivalent to ``lambda x: pipe(x, *funcs)``:

Pipelining is a simple form of function composition. In mathematics, the standard
notation for function composition passes the arguments in opposite direction
(i.e., data flows from the right to the left)

>>> func = sk.compose(op.add(2), op.mul(4))
>>> func(10)
42

``sk.compose(*funcs)`` is equivalent to ``sk.pipeline(*reversed(funcs))``.


Functions
.........

.. autofunction:: sidekick.pipe
.. autofunction:: sidekick.compose
.. autofunction:: sidekick.pipeline
.. autofunction:: sidekick.thread
.. autofunction:: sidekick.rthread


Combinators
-----------

Sometimes we just need to create some simple functions to pass to other
functions in functional composition. Consider one of the most important of those
functions:

>>> sk.identity(42)
42

Identity simply return its argument unchanged. In sidekick, we generalized
identity to receive several arguments and return only the first. If you want it
to return the last, use ridentity. This is useful for "sequencing" operations
such as logging before returning some value:

>>> sk.ridentity(print('the answer'), 42)
the answer
42

If you want to capture all positional arguments, use :func:`args` and for keyword
arguments, use :func:`kwargs`:

>>> sk.args(1, 2, 3, foo="bar")
(1, 2, 3)
>>> sk.kwargs(1, 2, 3, foo="bar")
{'foo': 'bar'}

Another useful function is :func:`always`, which creates a function that always
return the same value:

>>> answer = sk.always(42)
>>> answer("what is the answer",
...        "to the ultimate question of life, ",
...        "the universe, and everything?")
42

We can also use combinators that control recursion. Bellow is the famous
Y-combinator, which we call :func:`rec`, standing for recursion. It receives
a function that expects a recursion function and an argument and fix the
recursion to be the function itself.

>>> fat = sk.rec(lambda f, n: 1 if n <= 1 else n * f(f, n - 1))
>>> fat(5)
120

One interesting bit of this implementation is that this version of fat does not
need to be bound to a name for it to work. Standard ways of doing
recursion requires that.


API
...

.. automodule:: identity
.. automodule:: ridentity
.. automodule:: always
.. automodule:: args
.. automodule:: kwargs
.. automodule:: rec


Function calling
----------------

The call function, creates a caller factory. This is a function that receives
other functions and call them with the original arguments passed to call.

>>> even_10 = sk.call(lambda x: x % 2, range(10))
>>> even_10(map) | L
[0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
>>> even_10(filter) | L
[1, 3, 5, 7, 9]

>>> add_mod = lambda mod, x, y: (x + y) % mod
>>> add_mod10 = sk.partial(add_mod, 10)
>>> add_mod10(9, 4)
3

API
...

.. autofunction:: sidekick.call
.. autofunction:: sidekick.call_over
.. autofunction:: sidekick.do
.. autofunction:: sidekick.juxt


Argument filtering
------------------

>>> lst = []
>>> push = sk.call_after(1, lst.append)
>>> push(0); push(1); push(2); push(3)
>>> lst
[1, 2, 3]


>>> lst = [1, 2, 3]
>>> pop = sk.call_at_most(len(lst), lst.pop)
>>> for _ in range(5):
...     print(pop())
3
2
1
1
1

>>> @sk.once
... def initialize():
...     print('starting...')
...     return {'success': True}

>>> initialize()
starting...
{'success': True}

>>> initialize()
{'success': True}


>>> @sk.thunk(10)
... def fibs(n):
...     print('computing fibs...')
...     lst = [1, 1]
...     for _ in range(n - 2):
...         lst.append(lst[-1] + lst[-2])
...     return lst

>>> fibs()
computing fibs...
[1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

>>> fibs()
[1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

API
...

.. autofunction:: sidekick.call_after
.. autofunction:: sidekick.call_at_most
.. autofunction:: sidekick.once
.. autofunction:: sidekick.thunk


Runtime control
---------------

>>> numbers = [1, 2, 3, 4]
>>> func = sk.throttle(1 / 1000, numbers.pop)
>>> func(), func(), func()
(4, 4, 4)

>>> from time import sleep
>>> sleep(1.5 / 1000)
>>> func(), func(), func()
(3, 3, 3)


>>> func = sk.background(lambda x: sleep(1 / 1000) and x)
>>> res = func(42)

>>> res()


API
...

.. autofunction:: sidekick.throttle
.. autofunction:: sidekick.background


Runtime control
---------------

>>> half = sk.flip(op.div)(2)
>>> half(10)
5.0

>>> rdiv = sk.select_args([1, 0], op.div)
>>> rdiv(5, 10)
2.0

>>> sum_but_first = sk.skip_args(1, sk.splice(sum))
>>> sum_but_first(1, 2, 3, 4)
9

>>> mul = sk.keep_args(2, op.mul)
>>> mul(5, 4, 3, 2, 1)
20


API
...

.. autofunction:: flip
.. autofunction:: select_args
.. autofunction:: skip_args
.. autofunction:: keep_args


Error control
-------------

>>> sk.error(ValueError('msg'))
Traceback (most recent call last):
...
ValueError: msg


>>> div = sk.ignore_error(ZeroDivisionError, op.div, handler=sk.always(0))
>>> div(10, 2), div(10, 0)
(5.0, 0)

>>> import random
>>> def likely_to_fail():
...     if random.random() > 0.1:
...         raise ValueError('failure mode')
...     return 42
>>> safe = sk.retry(100, likely_to_fail)
>>> safe()
42


API
...

.. autofunction:: error
.. autofunction:: ignore_error
.. autofunction:: retry


Misc
----

.. autofunction:: force_function

