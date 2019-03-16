from .extended_semantics import extract_predicate_function

nullfunc = lambda *args, **kwargs: None
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


class predicate:  # noqa: N801
    """
    A predicate function.
    """

    # __slots__ = ('_sk_function_', '__dict__')

    def __init__(self, function):
        self._sk_function_ = extract_predicate_function(function)

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

    def __getattr__(self, attr):
        return getattr(self._sk_function_, attr)


class cond:  # noqa: N801
    """
    Conditional pipeline.

    It creates a function that takes a predicate and a true and false
    branches. The resulting function executes either branch depending on the
    value of the predicate.

    Examples:
        >>> from sidekick import cond, placeholder as _
        >>> collatz = cond(is_even) \
        ...     .true(_ // 2) \
        ...     .false((3 * _) + 1)
        >>> [collatz(1), collatz(2), collatz(3), collatz(4)]
        [4, 1, 10, 2]
    """

    # noinspection PyShadowingNames
    def __init__(self, predicate, true=nullfunc, false=nullfunc):
        self.predicate = predicate
        self.if_true = true
        self.if_false = false

    def __call__(self, x):
        if self.predicate(x):
            return self.if_true(x)
        else:
            return self.if_false(x)

    def __rshift__(self, other):
        true, false = self.if_true, self.if_false
        return cond(self.predicate, lambda x: other(true(x)), lambda x: other(false(x)))

    def __rrshift__(self, other):
        true, false = self.if_true, self.if_false
        return cond(self.predicate, lambda x: true(other(x)), lambda x: false(other(x)))

    def __ror__(self, other):
        return self.__call__(other)

    def true(self, true):
        """
        Sets the function for the True branch of the pipeline.
        """
        return cond(self.predicate, true, self.if_false)

    def false(self, false):
        """
        Sets the function for the False branch of the pipeline.
        """
        return cond(self.predicate, self.if_true, false)


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
        return x._sk_function_
    raise TypeError("can only compose with other predicate functions")
