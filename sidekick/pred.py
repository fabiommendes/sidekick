from .core import fn, extract_function
from .op import is_ as is_identical, eq as is_equal

__all__ = [
    "cond",
    "any_of",
    "all_of",
    "is_false",
    "is_true",
    "is_none",
    "is_even",
    "is_odd",
    "is_negative",
    "is_positive",
    "is_strictly_negative",
    "is_strictly_positive",
    "is_zero",
    "is_nonzero",
    "is_equal",
    "is_identical",
]


@fn.curry(3)
def cond(test, then, else_):
    """
    Conditional evaluation.

    Return a function that tests the argument with the cond function, and then
    executes either the "then" or "else_" branches.

    Examples:
        >>> collatz = cond(is_even, _ // 2, (3 * _) + 1)
        >>> [collatz(1), collatz(2), collatz(3), collatz(4)]
        [4, 1, 10, 2]
    """
    test = extract_function(test)
    then = extract_function(then)
    else_ = extract_function(else_)
    return (
        lambda *args, **kwargs: then(*args, **kwargs)
        if test(*args, **kwargs)
        else else_(*args, **kwargs)
    )


#
# Predicate factories
#

def any_of(*predicates):
    """
    Return a new predicate that performs a logic AND to all predicate
    functions.
    """
    if len(predicates) == 1:
        predicates = predicates[0]
    return fn(lambda x: any(f(x) for f in predicates))


def all_of(*predicates):
    """
    Return a new predicate that performs an logic ALL to all predicate
    functions.
    """
    if len(predicates) == 1:
        predicates = predicates[0]
    return fn(lambda x: all(f(x) for f in predicates))


#
# Predicate functions
#
is_none = is_identical(None)
is_true = is_identical(True)
is_false = is_identical(False)

# Numeric
is_odd = fn(lambda x: x % 2 == 1)
is_even = fn(lambda x: x % 2 == 0)
is_positive = fn(lambda x: x >= 0)
is_negative = fn(lambda x: x <= 0)
is_strictly_positive = fn(lambda x: x > 0)
is_strictly_negative = fn(lambda x: x < 0)
is_nonzero = fn(lambda x: x != 0)
is_zero = fn(lambda x: x == 0)
divisible_by = fn.curry(2, lambda n, x: x % n == 0)


#
# Auxiliary functions
#
def _other_pred(x):
    if isinstance(x, fn):
        # noinspection PyProtectedMember
        return x.__inner_function__
    raise TypeError("can only compose with other predicate functions")
