from sidekick.core.base_fn import extract_predicate_function, extract_function
from .base_fn import SkFunction

__all__ = [
    "predicate",
    "cond",
    "any_of",
    "all_of",
    "is_equal",
    "is_identical",
    "is_instance_of",
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
]


# noinspection PyPep8Naming
class predicate(SkFunction):  # noqa: N801
    """
    A predicate function.
    """

    __slots__ = ()
    _normalize_function = staticmethod(extract_predicate_function)

    def __call__(self, x):
        return bool(self._sk_function_(x))

    def __or__(self, other):
        f = self._sk_function_
        other = _other_pred(other)
        return predicate(lambda x: f(x) or other(x))

    def __and__(self, other):
        f = self._sk_function_
        other = _other_pred(other)
        return predicate(lambda x: f(x) and other(x))

    def __invert__(self):
        f = self._sk_function_
        return predicate(lambda x: not f(x))


def cond(test, then, else_):
    """
    Conditional evaluation.

    Return a function that tests the argument with the cond function, and then
    executes either the "then" or "else_" branches.

    Examples:
        >>> from sidekick import cond, placeholder as _
        >>> collatz = cond(is_even, _ // 2, (3 * _) + 1)
        >>> [collatz(1), collatz(2), collatz(3), collatz(4)]
        [4, 1, 10, 2]
    """
    test = extract_predicate_function(test)
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
def is_instance_of(cls):
    """
    Return a predicate function that checks if argument is an instance of a
    class.
    """
    return predicate(lambda x: isinstance(x, cls))


def is_equal(value):
    """
    Return a predicate function that checks if the argument is equal to
    the given value.
    """
    return predicate(lambda x: x == value)


def is_identical(value):
    """
    Return a predicate function that checks if the argument has the same
    identity of the given value.
    """
    return predicate(lambda x: x is value)


def any_of(*predicates):
    """
    Return a new predicate that performs an logic AND to all predicate
    functions.
    """
    return predicate(lambda x: any(f(x) for f in predicates))


def all_of(*predicates):
    """
    Return a new predicate that performs an logic ALL to all predicate
    functions.
    """
    return predicate(lambda x: all(f(x) for f in predicates))


#
# Predicate functions
#
is_none = is_identical(None)
is_true = is_identical(True)
is_false = is_identical(False)

# Numeric
is_odd = predicate(lambda x: x % 2 == 1)
is_even = predicate(lambda x: x % 2 == 0)
is_positive = predicate(lambda x: x >= 0)
is_negative = predicate(lambda x: x <= 0)
is_strictly_positive = predicate(lambda x: x > 0)
is_strictly_negative = predicate(lambda x: x < 0)
is_nonzero = predicate(lambda x: x != 0)
is_zero = predicate(lambda x: x == 0)


#
# Auxiliary functions
#
def _other_pred(x):
    if isinstance(x, predicate):
        # noinspection PyProtectedMember
        return x._sk_function_
    raise TypeError("can only compose with other predicate functions")
