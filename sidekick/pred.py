from itertools import zip_longest

from ._toolz import isdistinct, isiterable
from .functions import always
from .functions import fn, quick_fn, to_callable
from .typing import Callable, overload, Any, TypeCheck, Seq, NOT_GIVEN, TYPE_CHECKING

if TYPE_CHECKING:
    import sidekick.api as sk  # noqa: F401
    from sidekick.api import _  # noqa: F401

__all__ = [
    # Compositions
    "cond",
    "any_pred",
    "all_pred",
    # Value testing
    "is_a",
    "is_equal",
    "is_identical",
    "is_false",
    "is_true",
    "is_none",
    "is_truthy",
    "is_falsy",
    # Numeric tests
    "is_even",
    "is_odd",
    "is_negative",
    "is_positive",
    "is_strictly_negative",
    "is_strictly_positive",
    "is_zero",
    "is_nonzero",
    "is_divisible_by",
    # String tests
    "has_pattern",
    # Sequences
    "is_distinct",
    "is_iterable",
    "is_seq_equal",
]


@fn.curry(3)
def cond(test, then, else_):
    """
    Conditional evaluation.

    Return a function that tests the argument with the cond function, and then
    executes either the ``then`` or ``else_`` branches.

    Examples:
        >>> collatz = sk.cond(sk.is_even, _ // 2, (3 * _) + 1)
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
@fn.curry(2)
def is_identical(x, y):
    """
    Check if ``x is y``.
    """
    return x is y


@fn.curry(2)
def is_equal(x, y):
    """
    Check if ``x == y``.
    """
    return x == y


def _is_identical(
    value,
    name=None,
    render=None,
    doc=None,
    func=None,
    by="by identity",
    ok=None,
    bad=None,
):
    render = render or repr(value)
    name = name or f"is_{render.lower()}"
    ok = ok if ok is not None else f"{value!r}"
    bad = bad if bad is not None else f'"not_{render.lower()}"'
    doc = (
        doc
        or f"""
    Check if argument is {render.replace('_', ' ')}{by}.

    Examples:
        >>> sk.{name}({bad})
        False
        >>> sk.{name}({ok})
        True
    """
    )

    if func is None:

        @fn
        def id_check(x):
            return x is value

    else:
        id_check = fn(func)

    id_check.__name__ = id_check.__qualname__ = name
    id_check.__doc__ = doc
    return id_check


is_none = _is_identical(None)
is_true = _is_identical(True)
is_false = _is_identical(False)


@fn
def is_truthy(x):
    """
    Check if argument is truthy.

    This is the same as calling ``bool(x)``
    """
    return bool(x)


@fn
def is_falsy(x):
    """
    Check if argument is falsy.

    This is the same as calling ``not bool(x)``
    """
    return not bool(x)


@overload
def is_a(cls: TypeCheck) -> Callable[[Any], bool]:
    ...


@overload
def is_a(cls: TypeCheck, x: Any) -> bool:  # noqa: F811
    ...


@fn.curry(2)
def is_a(cls, x):  # noqa: F811
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
        >>> is_int = sk.is_a(int)
        >>> is_int(42), is_int(42.0)
        (True, False)
    """
    return isinstance(x, cls)


# Numeric
_is_numeric = lambda name, func, ok, bad: _is_identical(
    None, render=name, by="", ok=ok, bad=bad, func=func
)
is_odd = _is_numeric("odd", lambda x: x % 2 == 1, 1, 42)
is_even = _is_numeric("even", lambda x: x % 2 == 0, 42, 1)
is_positive = _is_numeric("positive", lambda x: x >= 0, 42, -10)
is_negative = _is_numeric("negative", lambda x: x <= 0, -10, 42)
is_strictly_positive = _is_numeric("strictly_positive", lambda x: x > 0, 42, 0)
is_strictly_negative = _is_numeric("strictly_negative", lambda x: x < 0, -10, 0)
is_nonzero = _is_numeric("nonzero", lambda x: x != 0, 42, 0)
is_zero = _is_numeric("zero", lambda x: x == 0, 0, 42)


@fn.curry(2)
def is_divisible_by(n, x):
    """
    Check if x is divisible by n.

    Examples:
        >>> sk.is_divisible_by(2, 42)  # 42 is divisible by 2
        True
        >>> even = sk.is_divisible_by(2)
        >>> even(4), even(3)
        (True, False)
    """
    return x % n == 0


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
def has_pattern(pattern: str, st: str) -> bool:  # noqa: F811
    ...


def has_pattern(pattern, st=NOT_GIVEN):  # noqa: F811
    r"""
    Check if string contains pattern.

    This function performs a pattern scan. If you want to match the beginning of
    the string, make it start with a "^". Add a "$" if it needs to match the
    end.

    Examples:
        >>> sk.has_pattern(r"\d{2}", "year, 1942")
        True
        >>> sk.has_pattern(r"^\d{2}$", "year, 1942")
        False

        This function is also very useful to filter or process string data.

        >>> is_date = sk.has_pattern("^\d{4}-\d{2}-\d{2}$")
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
