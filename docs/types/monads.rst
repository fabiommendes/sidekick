==================
Monadic interfaces
==================

Experienced functional programmers may recognize that Result types are monads.
If you never seen this name, don't be scared by the nomenclature: monads are
simply an interface that allows some useful forms of function composition.

All monads can be mapped over, which we recognize by the presence of the .map
method in the Result type. Haskellers and type theorists like to call it a
"Functor". Traditional examples of functors are the Maybe type, the Result type,
and lists. In an ideal world, all functors would have
a .map method that applies a function to its contents. However, it is not
possible to change Python's builtin types and, even when it is possible, it is
probably not a good idea to monkey patch types written by others willy and nilly.
Sidekick provides an :func:`sidekick.fmap` function that performs this "Functor"
mapping over any Functor type.

Half way to a full monad, we have the "Applicative functor" interface: it means
that it has a method that can compose over functions that receive more than
one argument. This is acomplished by the .apply class method of applicative
types. Like before, many builtin Python types could be valid applicative
functors, but we just can't add a new "apply" method in order to provide a
consistent interface. Likewise, sidekick provides a toplevel :func:`sidekick.fapply`
that apply functions to applicative functors arguments.

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