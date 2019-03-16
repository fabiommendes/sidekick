===============
The Result type
===============

The result type (sans extensions) is defined as:

.. code-block:: python

    from sidekick import Union, opt


    class Result(Union):
        Err = opt(error=object)
        Ok = opt(value=object)

Hence it has two states: Ok and Err, and both can hold additional data. :class:`sidekick.Result`
is a functional way to represent a computation that might fail. It can be used
anywhere one would use a try/except block in Python.

The main difference between a Result and a Maybe is that the first carries
information about the error (like an error message), while Maybe uses a generic
failure state :class:`sidekick.Nothing`. Languages that use native Result types
tend to favor the usage of strings, numbers or enumerations in order to
represent error states. In Sidekick, we encourage using exception instances
in order to be more consistent with the rest of Python behavior. Sidekick's
result type has some methods to coerce result instances into exceptions and if
you use generic error values such as strings, ints or enums, the result will
be coerced to a generic ValueError, which is not necessarily what you want.

Using results to handle errors
==============================

Using Result is a departure from the traditional way of doing things in Python.
Python encourages the usage of exceptions as control flow (the *"ask forgiveness,
not permission"* pattern). We don't thing that is always a good idea, since
exceptions may introduce many problems:

* They obscure control flow.
* Exceptions tend to break function composition.
* The exception interface of a function is rarely well documented, so
  discovering the appropriate exception can take some trial and error and
  guessing.

Using result types is more explicit and favors function composition better. Let
us start with a simple Python function that may fail the usual way by throwing
an exception.

.. code-block:: python

    def div(x, y):
        if y == 0:
            raise ZeroDivisionError
        else:
            return x / y

We wrap the result of this function in a Result type by using the :meth:`sidekick.Result.call`
method of the :class:`sidekick.Result` class:

>>> from sidekick import Result
>>> Result.call(div, 1, 2)
Ok(0.5)

Notice that errors are converted to results in the Err state:

>>> Result.call(div, 1, 0)
Err(ZeroDivisionError())

If we want a result-safe version of div, just wrap it with the :meth:`sidekick.Result.safe`
method.

>>> safe_div = Result.safe(div)
>>> safe_div(1, 0)
Err(ZeroDivisionError())

:meth:`sidekick.Result.safe` can be used as a decorator, and it will convert the
decorated function into a safe function. Another alternative is the :meth:`sidekick.Result.with_safe`
decorator that preserves the original implementation, but introduces an
additional safe version under the the .safe attribute:

.. code-block:: python

    @Result.with_safe
    def div(x, y):
        if y == 0:
            raise ZeroDivisionError
        else:
            return x / y

This helps bridging the gap between regular Python and its exception-based
computations and the safer world of Result types. Now we have two options:

>>> div(1, 2)
0.5
>>> div.safe(1, 2)
Ok(0.5)

Combining results
=================

The main advantage of using explicit Result types instead of exceptions is that,
with the later, we can compose functions across error boundaries whereas
exceptions requires special handling in try/except blocks. Sidekick provides a
few utilities to compose functions to better handle result types.

Consider the following result values.

.. code-block:: python

    x = Ok(4)
    y = Ok(38)
    bad = Err(ZeroDivisionError())

The examples bellow show how to handle those results with simple function
compositions that avoids explicit checks with case expressions or if blocks.


Mapping
-------

Consider you have several result values that you want to pass to a regular function
that do not understands result types. We provide the classmethod :meth:`sidekick.Result.apply`
to wrap this computation very easily:

>>> Result.apply(min, x, y)
Ok(4)

If something goes wrong, the error propagates:

>>> Result.apply(min, x, y, bad)
Err(ZeroDivisionError())

If the computation takes a single value, we can use the .map method of the
instance:

>>> from math import sqrt
>>> x.map(sqrt)
Ok(2.0)

Error states are always returned as-is and do not take place on computations.

>>> bad.map(sqrt)
Err(ZeroDivisionError())

You should also take a look at the :meth:`sidekick.Result.chain` method if you
want to map over more than one function.

If the .apply and .map functions encounter any exception, they propagate it as
an error state:

>>> div.safe(1, 0)
Err(ZeroDivisionError())

This helps bridging the standard world of errors as exceptions and Sidekick
encoding of the error state in the result types.


Operators
---------

Most standard operators work with result types. They return a result if the
value of both operands understand the operation or an error case otherwise:

>>> x + y
Ok(42)
>>> x + bad
Err(ZeroDivisionError())


Monadic error handling
----------------------

Experienced functional programmers may recognize that Result types are monads.
If you never seen this name, don't be scared by the nomenclature: monads are
simply an specific interface that some types can have that allows some specific
forms of function composition.

All monads can be mapped over, which we recognize by the presence of the .map
method in the Result type. Haskellers like to call it a "Functor". A functor
is simply something that can be "mapped over". Traditional examples are the
Maybe type, the Result type, and lists. In an ideal world, all functors would have
a .map method that applies a function to its contents. However, it is not
possible to change Python's builtin types and, even when it is possible, it is
probably not a good idea to monkey patch types written by others willy and nilly.
Sidekick provides an :func:`sidekick.fmap` function that performs this "Functor"
mapping over any Functor type.

Half way to a full monad, we have the "Applicative functor" interface: it means
that it has a method that can compose over functions that receive more than
one argument. This is acomplished by the .apply class method of applicative
types. Like before, many builtin Python types can be think of applicative
functors, but we can't just add a new "apply" method in order to provide a
consistent interface. Sidekick provides a toplevel :func:`sidekick.fapply` that
apply functions to applicative functors arguments.

Both Functors and Applicatives make functions that take regular values work with
Result inputs. The monad tries to answer a complementary question: how do we
compose functions that receive regular values, but already return Result
instances? Consider the example bellow:

.. code-block:: python

    import math

    def sqrt(x: float) -> Result:
        if x < 0:
            return Err('smaller than zero')
        else:
            return Ok(math.sqrt(x))

If we already have a Result value (such as x, y, bad), the function above cannot
be used immediately: it is necessary to unwrap the value and select a different
path for the Ok and Err cases (pass the value to sqrt or propagate the error).
A better method is to use the .map monadic interface:

>>> x.map(sqrt)
Ok(2.0)
>>> bad.map(sqrt)
Err(ZeroDivisionError())


API reference
=============

.. autoclass:: sidekick.Result
    :members:
    :noindex:
.. autofunction:: sidekick.result
    :noindex:

