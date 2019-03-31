===========
Union types
===========

.. module:: sidekick
.. invisible-code-block:: python

    import sidekick as sk
    from sidekick import Record

Union types represent values that can be in one of a series of different states.
Many functional languages implement Union types (a.k.a. variant types, or
algebraic data types) instead of classical object oriented inheritance, as one
of the main ways for creating composite types. Sidekick implements them in Python.

Let us start with a classic example, the Result type. Consider we want to fetch
some value (from a db?), but that value is not guaranteed to exist or the operation
may fail for some reason. In Python, we probably would return the correct
value in case of success and would either return None or raise an exception in
case of failure.

The problem with this approach is that the failure case and the success case have
completely different interfaces and this forces us to fill our code with lots
of ifs (or worst yet, with lots of try/except blocks). In a statically typed
language such as Haskell, the situation would be even worst: a computation must
have a predictable type and the compiler cannot accept a function that can
have different output types depending on input values or a random state of the
world.

Our proposal is to create a type that can be in two states:

* ``Ok(value)`` -- computation was successful.
* ``Err(error)`` -- computation failed with some message.

Since the type is a "Result", we can treat the result for any of the two
states with an uniform interface and compose it nicely with other functions that
understand Results.

Here is a simple example in Python of a sqrt function that returns a Result
instead of raising exceptions for negative values.

.. ignore-next-block
.. code-block:: python

    def sqrt(x: float) -> Result:
        if x < 0:
            return Err('negative input')

        # Quick and dirty Babylonian method for finding square roots
        y = x
        for _ in range(10):
            y = 0.5 * (y + x/y)
        return Ok(y)


This puts exceptions out of the way and we can use it to compose with functions
that understand Result instances

.. ignore-next-block
.. code-block:: python

    roots = sk.map(sqrt, inputs)
    mean = sk.mean(sk.filter(X.attr('is_ok'), roots))


How would be a Pythonic way of implementing this?

The approach we choose uses is a typical encoding of union types in
an object oriented languages. Union types are created as a class hierarchy from
an abstract base. Let us start from scratch:

.. code-block:: python

    class Result:
        # It is more Pythonic to check cases using attributes rather than
        # isinstance checks. That allows users to test "if res.is_err: ..."
        # rather than using ugly explicit type checks.
        is_ok = False
        is_err = False

        def __init__(self):
            # A result must be in either Ok or Err cases, we should not
            # allow instantiation of bare results.
            raise TypeError('Maybe is an abstract type and cannot have instances')

    class Ok(Result):
        is_ok = True

        def __init__(self, value):
            self.value = value

    class Err(Result):
        is_err = True

        def __init__(self, error):
            self.error = error


    # We also save shortcuts to use the constructors from the base class so
    # users can access all states from a single reference to the base class
    Result.Ok = Ok
    Result.Err = Err

While this is fine, it is a lot of work. Sidekick implements some convenient
factories to declare new types with very little overhead. We might as well
use those resources to ease our task.

The first obvious choice would be to use :cls:`Record`s or namedtuples to
declare the variants. This saves the trouble of declaring ``__init__``,
``__repr__``, ``__eq__`` and probably a few other methods we had missed. Besides
that, the machinery around the ``is_ok``, ``is_err`` attributes can be
easily automated and it seems kind of dull and error prone to do by hand.

The union type constructor does exactly this:

.. code-block:: python

    Result = sk.union(
        'Result',
        Ok=Record.define('Ok', ['value']),
        Err=Record.define('Err', ['err']),
    )

Much better ;)

Now we can enjoy our freshly created Result type:

>>> answer = Result.Ok(42)
>>> if answer.is_ok:
...     print(f'The answer is {answer.value}!')
... else:
...     print("I don't have the answer")
The answer is 42!

Under the hood, it creates the Ok and Err classes by subclassing both Result and
the corresponding record type. It also insert the ``is_ok/err`` attributes and
forbid instantiation of bare Result values.