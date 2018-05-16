from .fn import fn
from .placeholder import Placeholder

nullfunc = lambda *args, **kwargs: None


class predicate:  # noqa: N801
    """
    A predicate function.
    """

    __slots__ = ('_', '__dict__')

    def __init__(self, function):
        if isinstance(function, (fn, Placeholder, predicate)):
            function = function._
        self._ = function

    def __call__(self, x):
        return bool(self._(x))

    def __or__(self, other):
        f = self._
        other = _other_pred(other)
        return predicate(lambda x: f(x) or other(x))

    def __and__(self, other):
        f = self._
        other = _other_pred(other)
        return predicate(lambda x: f(x) and other(x))

    def __invert__(self):
        f = self._
        return predicate(lambda x: not f(x))

    def __getattr__(self, attr):
        return getattr(self._, attr)


class cond:  # noqa: N801
    """
    Conditional pipeline.

    It creates a function that takes a predicate and a true and false
    branches. The resulting function executes either branch depending on the
    value of the predicate.

    Examples:
        >>> from sidekick import cond, placeholder
        >>> half = cond(
        ...     is_even,
        ...     true=placeholder // 2,
        ...     false=(placeholder + 1) // 2,
        ... )
        >>> [half(1), half(2), half(3), half(4)]
        [1, 1, 2, 2]
    """

    def __init__(self, predicate, true=nullfunc, false=nullfunc):
        self.predicate = predicate
        self._true = true
        self._false = false

    def __call__(self, x):
        if self.predicate(x):
            return self._true(x)
        else:
            return self._false(x)

    def __rshift__(self, other):
        true, false = self._true, self._false
        return cond(
            self.predicate,
            lambda x: other(true(x)),
            lambda x: other(false(x)),
        )

    def __rrshift__(self, other):
        true, false = self._true, self._false
        return cond(
            self.predicate,
            lambda x: true(other(x)),
            lambda x: false(other(x)),
        )

    def __ror__(self, other):
        return self(other)

    def true(self, true):
        """
        Sets the function for the True branch of the pipeline.
        """
        return cond(self.predicate, true, self._false)

    def false(self, false):
        """
        Sets the function for the False branch of the pipeline.
        """
        return cond(self.predicate, self._true, false)


#
# Predicate factories
#
def type_of(cls):
    """
    Return a predicate function that checks if argument is an instance of a
    class.
    """
    return predicate(lambda x: isinstance(x, cls))


def value_of(value):
    """
    Return a predicate function that checks if the argument is equal to
    the given value.
    """
    return predicate(lambda x: x == value)


def identity_of(value):
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
is_none = identity_of(None)
is_true = identity_of(True)
is_false = identity_of(False)

# Numeric
is_odd = predicate(lambda x: x % 2 == 1)
is_even = predicate(lambda x: x % 2 == 0)
is_positive = predicate(lambda x: x >= 0)
is_negative = predicate(lambda x: x <= 0)
is_nonzero = predicate(lambda x: x != 0)
is_zero = predicate(lambda x: x == 0)


#
# Auxiliary functions
#
def _other_pred(x):
    if isinstance(x, predicate):
        return x._
    raise TypeError('can only compose with other predicate functions')
