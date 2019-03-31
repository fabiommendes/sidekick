===============
The Result type
===============

The result type (sans extensions) is defined as:

.. invisible-code-block:: python

    from sidekick import Result, Ok, Err, result
    import sidekick as sk

.. ignore-next-block
.. code-block:: python

    from sidekick import Union, Case


    class Result(Union):
        Err: Case(error=object)
        Ok: Case(value=object)

It has two states: Ok and Err, and both can hold additional data.
:class:`Result`s represent computations that might fail and can be used to
replace try/except idioms in Python.

The main difference between a Result and a Maybe is that the first carries
information about the error (like an error message), while Maybe uses a generic
failure state :class:`sidekick.Nothing` that tells no extra information.

Languages that use native Result types tend to favor strings, numbers or
enumerations to represent error states. In Sidekick, we encourage using exception instances
in order to be more consistent with the rest of Python behavior. Sidekick's
result type has some methods to coerce result instances into exceptions and if
you use generic error values such as strings, ints or enums, the result will
be coerced to a generic ValueError, which is not necessarily what you want.

Using results to handle errors
==============================

Using Result is a departure from the traditional way of doing things in Python.
Python encourages exceptions for control flow (the *"ask forgiveness,
not permission"* pattern). We don't think that it is always a good idea, as
exceptions introduce many problems:

* They obscure control flow, making it non-local.
* Exceptions tend to break function composition.
* The exception interface of a function is rarely well documented, so
  discovering the appropriate exception usually involves some guessing.

Using result types is more explicit and favors function composition better. Let
us start with a simple Python function that may fail the usual way by throwing
an exception.

.. code-block:: python

    def div(x, y):
        if y == 0:
            raise ZeroDivisionError
        else:
            return x / y

We wrap the function execution using :func:`rcall`:

>>> sk.rcall(div, 1, 2)
Ok(0.5)

Errors are converted to results in the Err state:

>>> sk.rcall(div, 1, 0)
Err(ZeroDivisionError())

A result-safe version of div can be easily created using :func:`result_fn` method.

>>> safe_div = sk.result_fn(div)
>>> safe_div(1, 0)
Err(ZeroDivisionError())

Standard fn functions have a result method that wraps the function with a
Result output. Successful computations are returned in the Ok state and any
exceptions are returned as an Err value.

.. code-block:: python

    @fn
    def div(x, y):
        if y == 0:
            raise ZeroDivisionError
        else:
            return x / y

This helps bridging the gap between regular Python and its exception-based
computations and the safer world of Result types. Now we have two options:

>>> div(1, 2)
0.5
>>> div.result(1, 2)
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

>>> sk.rapply(min, x, y)
Ok(4)

If something goes wrong, the error propagates:

>>> sk.rapply(min, x, y, bad)
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

>>> div.result(1, 0)
Err(ZeroDivisionError())

This helps bridging the standard world of errors as exceptions and Sidekick
encoding of the error state in the result types.



API reference
=============

.. autoclass:: Result
    :members:

.. autofunction:: result
.. autofunction:: result
.. autofunction:: catch_exceptions
.. autofunction:: first_error
.. autofunction:: rapply
.. autofunction:: rcall
.. autofunction:: rpipe
.. autofunction:: rpipeline
.. autofunction:: result_fn
