from itertools import zip_longest

from .functions import fn, quick_fn, to_callable
from .functions import always
from .op import is_ as is_identical, eq as is_equal
from .typing import Callable, overload, NOT_GIVEN, Any, TypeCheck, Seq
from ._toolz import isdistinct, isiterable

__all__ = [
    "cond",
    "any_pred",
    "all_pred",
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
    "is_distinct",
    "is_iterable",
    "is_seq_equal",
    "is_equal",
    "is_identical",
    "is_divisible_by",
    "is_truthy",
    "is_falsy",
    "is_a",
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
    test = to_callable(test)
    then = to_callable(then)
    else_ = to_callable(else_)
    return (
        lambda *args, **kwargs: then(*args, **kwargs)
        if test(*args, **kwargs)
        else else_(*args, **kwargs)
    )


#
# Predicate factories
#
def any_pred(*predicates):
    """
    Return a new predicate function that performs a logic OR to all arguments.

    This behaves in a short-circuit manner and returns the first truthy result,
    if found, or the last falsy result, otherwise.
    """

    if len(predicates) == 0:
        return always(False)
    elif len(predicates) == 1:
        return predicates[0]

    @quick_fn
    def predicate(*args, **kwargs):
        res = False
        for f in predicate:
            res = f(*args, **kwargs)
            if res:
                return res
        return res

    return predicate


def all_pred(*predicates):
    """
    Return a new predicate that performs an logic AND to all predicate
    functions.

    This behaves in a short-circuit manner and returns the first falsy result,
    if found, or the last truthy result, otherwise.
    """

    if len(predicates) == 0:
        return always(True)
    elif len(predicates) == 1:
        return predicates[0]

    @quick_fn
    def predicate(*args, **kwargs):
        res = True
        for f in predicate:
            res = f(*args, **kwargs)
            if not res:
                return res
        return res

    return predicate


#
# Predicate functions
#
is_none = is_identical(None)
is_true = is_identical(True)
is_false = is_identical(False)
is_truthy = fn(bool)
is_falsy = ~is_truthy


@overload
def is_a(cls: TypeCheck) -> Callable[[Any], bool]:
    ...


@overload
def is_a(cls: TypeCheck, x: Any) -> bool:
    ...


@fn.curry(2)
def is_a(cls, x):
    """
    Check if x is an instance of cls.

    Equivalent to isinstance, but auto-curried and with the order or arguments
    flipped.

    Args:
        cls:
            Type or tuple of types to test for.
        x:
            Instance.

    Examples:
        >>> is_int = is_a(int)
        >>> is_int(42), is_int(42.0)
        (True, False)
    """
    return isinstance(x, cls)


# Numeric
is_odd = fn(lambda x: x % 2 == 1)
is_even = fn(lambda x: x % 2 == 0)
is_positive = fn(lambda x: x >= 0)
is_negative = fn(lambda x: x <= 0)
is_strictly_positive = fn(lambda x: x > 0)
is_strictly_negative = fn(lambda x: x < 0)
is_nonzero = fn(lambda x: x != 0)
is_zero = fn(lambda x: x == 0)
is_divisible_by = fn.curry(2, lambda n, x: x % n == 0)


# Sequences
@fn
def is_distinct(seq: Seq) -> bool:
    """
    Test if all elements in sequence are distinct.
    """
    return isdistinct(seq)


@fn
def is_iterable(obj) -> bool:
    """
    Test if argument is iterable.
    """
    return isiterable(obj)


@fn.curry(2)
def is_seq_equal(seq1, seq2):
    """
    Return True if the two sequences are equal.
    """
    return all(x == y for x, y in zip_longest(seq1, seq2, fillvalue=object()))


# Strings
@overload
def has_pattern(pattern: str) -> Callable[[str], bool]:
    ...


@overload
def has_pattern(pattern: str, st: str) -> bool:
    ...


def has_pattern(pattern, st=NOT_GIVEN):
    """
    Check if string contains pattern.

    This function performs a pattern scan. If you want to match the beginning of
    the string, make it start with a "^". Add a "$" if it needs to match the
    end.

    Examples:
        >>> has_pattern("\d{2}", "year, 1942")
        True
        >>> has_pattern("^\d{2}$", "year, 1942")
        False

        This function is also very useful to filter or process string data.

        >>> is_date = has_pattern("^\d{4}-\d{2}-\d{2}$")
        >>> is_date("1917-03-08")
        True
        >>> is_date("08/03/1917")
        False
    """

    import re

    if st is NOT_GIVEN:
        regex = re.compile(pattern)

        def check_pattern(data: str) -> bool:
            return regex.search(data) is not None

        return check_pattern

    else:
        return re.search(pattern, st) is not None


#
# Auxiliary functions
#
def _other_pred(x):
    if isinstance(x, fn):
        # noinspection PyProtectedMember
        return x.__sk_callable__
    raise TypeError("can only compose with other predicate functions")
