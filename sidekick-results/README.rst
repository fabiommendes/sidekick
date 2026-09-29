====================
``sidekick.results``
====================

Return types for functions that encode errors, nullable values and more.


Installation
============

::
    pip install sidekick-results


Usage
=====

This library implements the classical Maybe and Result types often seen functional programming
languages. Those are type safe ways of representing computations that may fail and
can be seen as type safe alternatives to using exceptions or the null value.


None problem?
-------------

Python uses None as a representation of a null value. This is a prevalent idiom in many 
programming languages, but it is not without issues. The null value has even been 
considered the million dollars mistake by its creator, #TODO.

Python's None is considerably safer than the classical null pointer of C and other low level 
languages. It is much harder to exploit for security breaches because None is not a pointer. It 
still carries many of the original problems: Nones do not compose well with other 
types and require lots of checks that can be easily missed and hide subtle bugs.

Consider the example:

>>> def compute_answer(nullify: bool) -> int | None:
...     if nullify:
...         return None
...     return 42

Users of this functions will probably require to check for Nones
in almost all call sites. The "None" part of a nullable type shares only the most 
trivial pieces of API with its alternatives (the ``int`` value, in this case), and perhaps 
the only useful thing we can do with the result of this function without 
checking its type is to pass it downstream to another function that 
expect nullables. 

Functional languages often solve this problem using a return type that can be in two
states: ``Just(x)``, when data is present or ``Nothing``, when we would otherwise 
return a ``None``. Those two possibilities are instances of ``Maybe``, and the crucial
difference from simply returning a None in case of failure is that both ``Just(x)`` 
and ``Nothing`` share a common API that can be used with very few, if any 
at all, explicit null checks.

Our example function, rewritten using Maybe would be like

>>> from sidekick.results import Maybe, Just, Nothing
>>> def compute_answer(nullify: bool) -> Maybe[int]:
...     if nullify:
...         return Nothing
...     return Just(42)

Now we can use results without explicit checks and the Maybe type will handle
the nullability for us.

>>> answer = compute_answer(nullify=False)
>>> answer + 2
Just(44)

Maybes forward all computations to the inner value or propagate Nothings in the 
null case. We don't have to check if computation succeed or not: Maybe 
check it for us!

>>> answer = compute_answer(nullify=True)
>>> answer + 2
Nothing

Maybes replicate this behavior with all operators, but it does not expose all 
of the inner type's API. This could be confusing, specially if it shared some
method names with the Maybe type itself.

However, we can easily call methods and access attributes of the inner value, 
always keeping the Maybe wrapping.

>>> Just(42).method.bit_length()
Just(6)
>>> Nothing.method.bit_length()
Nothing

Notice the ``.method.*`` namespace used for accessing the methods of the inner value. 
The same functionality can be accessed using an alternative form of function call:

>>> Just(42).method("bit_length")
Just(6)

A similar API also exists for attributes

>>> Just(42).attr.imag
Just(0)

If you need to leave "Maybe" land to a more traditional Python nullable type, the
``.value`` attribute will return the wrapped value or None, if it
is in the Nothing state. It is also possible to ensure that we are in a Just case 
using ``unwrap()``. It extracts the value or raise an exception if the Maybe 
is null.

>>> x = Just(42)  # We could also use Maybe.from_value(42)
>>> x.value == x.unwrap() == 42
True

The difference between both approaches is how they handle the Nothing case:

>>> x = Nothing  # We could also use Maybe.from_optional(None)
>>> x.value is None
True
>>> x.unwrap()
Traceback (most recent call last):
...
ValueError: Maybe is in an error state.

We can also explicitly check the state of the Maybe value using attributes,

>>> data = Just(42)
>>> if data.is_just:
...     do_something(data.value)

or a match statement,

>>> match data:
...     case Maybe.Just(x):
...         do_something(x)
...     case Maybe.Nothing:
...         do_something_else()

We must write the pattern expressions in a way that triggers enum or "class" semantics. 
The code above works fine, but writing the full path to each case (i.e., Maybe.Just and 
Maybe.Nothing) may feel bit too verbose. Consider the expression bellow

>>> match data:
...     case Just(x):  # This branch works fine
...         do_something("yay! :D")
...     case Nothing:  # This is not so great
...         do_something_else("bleh :/")

Beware of Python's syntax for case matching. The first match uses Python "class pattern 
semantics". It verifies if the target expression, i.e., ``data`` is an instance of Just, 
and captures the ``.value`` argument and bind it to the variable ``x``.

The second case triggers the variable capture semantics. It binds the target value to 
a variable named Nothing and proceed to evaluate the body of expression using this binding.
This may work, since generally the second expression will only be triggered when the target
is indeed equal to Nothing. But this is fragile: if data is not a Maybe (due to a bug or 
some other legitimate reason), it will bind some random value to Nothing and possibly triggering
strange bugs downstream. Refactor the code to swap the order of cases, and it will also 
lead to a bug. Now a Just value could be bound to a variable named Nothing and the 
code will handle both cases in the same branch.

The safe way of using match/case expressions with maybes is to always declare the
Nothing case using a dotted name. Doing so forces the interpreter to match the pattern
by value, which is what we want. There are several legitimate ways of doing this

>>> match data:
...     case Just(x):  # This is fine!
...         do_something(x)
...     case Maybe.Nothing:
...         ...  # Nothing was matched by value
...     case Nothing.CTE:
...         ...  # Ditto, as `Nothing.CTE is Nothing`
...     case x if x is Nothing:
...         ...  # More verbose, but it still works
...     case Maybe.Nothing | None:
...         ...  # This way, we can handle Nones in the same branch
...     case _:
...         ... # Wildcard expression works if we know that x is a Maybe.
...             # Otherwise, non-Maybes will also be handled here

On implementing the Maybe class on sidekick, we favor the following pattern:

>>> match data:
...     case Just(x):
...         do_something(x)
...     case _:
...         do_something_else()

It reads better and prevents the type checker from complaining about possibly
missing cases. The catch here is that we must be sure that data is really a Maybe,
otherwise, this code may hide errors when it handles all non-Just objects
as a Nothing. For methods in the Maybe class, this is OK because we know that
self is always a Maybe in a methods definition. For other functions,
it is a little bit more dangerous, and I would probably use this idiom only
in code that is type checked with a tool like MyPy or PyLance (a.k.a., the VSCode
extension).

We refer to the :cls:`Maybe` documentation for a list of methods that can be used
to access or modify the content of the inner value.


Computations with failures
--------------------------

The archetypical motivation for using result is to represent a computation
that may fail, like the function bellow:

>>> def compute_answer(bad: bool) -> int:
...     if bad:
...         raise RuntimeError("something was wrong")
...     return 42

Handling exceptions is even more invasive than null checks as it requires an 
special syntax which is quite verbose. Differently from nullable values,
we cannot pass error results as arguments to other functions. Unhandled exceptions
propagate up in the call stack and may be handled non-locally, which arguably make
exceptions akin to a modern version of the infamous GOTO statement.

Following the footsteps of Maybe, we can propose an alternative to exceptions by 
wrapping the return value in a container that can be either in a success state which
holds the desired result or in a failure state that holds an error. We expand on Maybe
by letting the error state also hold information describing the error condition.

Our new ``compute_answer`` function thus become.

>>> from sidekick.results import Result, Ok, Err
>>> def compute_answer(bad: bool) -> Result[str, int]:
...     if bad:
...         raise Err("something was wrong")
...     return Ok(42)

In many ways, ``Ok(42)`` behaves like ``Just(42)``: we can extract its value,
transform it with some function and apply operators. The main difference 
is that accessing the ``.value`` attribute in an error state triggers an exception 
rather than returning a null value.

>>> Ok(42).value
42
>>> Err("some error").value
Traceback (most recent call last):
...
ValueError: some error

Pattern matching also works, and unlike Maybes we don't have to worry about the error state
being a singleton.

>>> match result:
...     case Ok(x):
...         do_something(x)
...     case Err(err):
...         do_something_else(err)

Results also have some methods for manipulating the error state. They often mirror a 
similar method handing the Ok() state of a result. 

>>> Ok(20).map(lambda x: 2 * x + 2)
Ok(42)
>>> Err(20).map_error(lambda x: 2 * x + 2)
Err(42)

Just like ``.map()`` doesn't affect an ``Err()`` result, ``.map_error()`` does not affect
an ``Ok()`` value. Similar pairs exist for flatmap, flatten, value_or, value_or_call and 
many others. We refer to the :cls:`Result` documentation for more information.