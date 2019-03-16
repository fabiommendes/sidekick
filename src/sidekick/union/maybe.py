import operator as op

from .union import Union, opt
from .utils import maybe_bin_op
from ..lazy import property

flip = lambda f: lambda x, y: f(y, x)
this = None


class Maybe(Union):
    """
    A Maybe type.
    """

    class Nothing(this):
        """
        Represents the absence of a value.
        """
        value = None

    class Just(this, args=opt('value')):
        """
        Represents a computation with a definite value.
        """

    is_ok = property(lambda self: self.is_just)
    is_just: bool
    is_nothing: bool
    value: object

    def map(self, func):
        """
        Apply function if object is in the Just state and return another Maybe.
        """
        if self.is_just:
            return maybe(func(self.value))
        else:
            return self

    def map_all(self, *funcs):
        """
        Pipe value through all functions.
        """
        if self.is_just:
            return mpipe(self.value, *funcs)
        else:
            return self

    def get_value(self, default=None):
        """
        Extract value from the Just state. If object is Nothing, return the
        supplied default or None.

        Examples:

        >>> Just(42).get_value(0)
        42
        >>> Nothing.get_value(0)
        0
        """
        if self.is_just:
            return self.value
        else:
            return default

    def to_result(self, err=Exception()):
        """
        Convert Maybe to Result.
        """
        if self.is_nothing:
            return Err(err)
        else:
            return Ok(self.value)

    def to_maybe(self):
        """
        Return itself.

        This function exists so some algorithms can work with both Maybe's and
        Result's using the same interface.
        """
        return self

    def method(self, method, *args, **kwargs):
        """
        Call the given method of value and promote result to a Maybe.

        Examples:
            >>> Just(1 + 2j).method('conjugate')
            Just(1 - 2j)
        """
        if self.is_just:
            try:
                method = getattr(self.value, method)
            except AttributeError:
                raise ValueError(f'method {method} does not exist')
            return maybe(method(*args, **kwargs))
        else:
            return self

    def attr(self, attr):
        """
        Retrieves attribute as a Maybe.

        Examples:
            >>> Just(1 + 2j).attr('real')
            Just(1)
        """
        if self.is_just:
            return maybe(getattr(self.value, attr))
        else:
            return self

    def iter(self):
        """
        Iterates over content.

        It returns an empty iterator in the Nothing case.
        """
        if self.is_just:
            yield from iter(self.value)

    # Operators
    __add__ = maybe_bin_op(op.add)
    __radd__ = maybe_bin_op(flip(op.add))
    __sub__ = maybe_bin_op(op.sub)
    __rsub__ = maybe_bin_op(flip(op.sub))
    __mul__ = maybe_bin_op(op.mul)
    __rmul__ = maybe_bin_op(flip(op.mul))
    __truediv__ = maybe_bin_op(op.truediv)
    __rtruediv__ = maybe_bin_op(flip(op.truediv))
    __bool__ = lambda x: x.is_just

    # Reinterpreted bitwise operators
    def __rshift__(self, other):
        if self.is_just:
            return Just(other(self.value))
        else:
            return Nothing

    def __or__(self, other):
        if isinstance(other, Maybe):
            return self if self.is_just else other
        elif other is None:
            return self
        return NotImplemented

    def __ror__(self, other):
        if other is None:
            return self
        else:
            return NotImplemented

    def __and__(self, other):
        if isinstance(other, Maybe):
            return self if self.is_nothing else other
        elif other is None:
            return Nothing
        return NotImplemented

    def __rand__(self, other):
        if other is None:
            return Nothing
        else:
            return NotImplemented


#
# Module functions.
#
def mcall(func, *args, **kwargs):
    """
    Execute function with all given Maybe values unwrapping all positional
    arguments and return ``Just(result)`` or ``Nothing`` if result is None.

    If any positional argument is a Nothing, returns Nothing. None values and
    keyword arguments do not propagate the Nothing state.

    Examples:
        >>> mcall(max, Just(1), Just(2), Just(3))
        Just(3)
        >>> mcall(max, Nothing, Just(1), Just(2), Just(3))
        Nothing
    """
    arg_values = []
    append = arg_values .append

    for arg in args:
        if arg is None:
            return Nothing
        elif isinstance(arg, Just):
            append(arg.value)
        else:
            append(arg)
    return maybe(func(*args, **kwargs))


def mcompose(*funcs):
    """
    Compose functions that return maybes.

    If any function returns Nothing or None, the final result will be Nothing.

    Args:
        *funcs:
            List of functions in application order.

    Returns:
        A function that returns Maybes.

    See Also:
        This is similar to :func:`mpipe`, except that it does not require the
        initial argument passed to the functions.
    """
    return lambda x: mpipe(x, *funcs)


def mpipe(obj, *funcs):
    """
    Pass argument through functions of (a -> Maybe b). It stops function
    application after the first Nothing is encountered. It performs implicit
    conversion to maybes treating None as Nothing and any other value x as
    Just(x).

    Args:
        obj:
            Initial argument passed to all functions.
        *funcs:
            List of functions in application order.

    Returns:
        A Maybe value.

    See Also:
        :func:`strict_mpipe`
    """
    for func in funcs:
        if obj is None or obj is Nothing:
            return Nothing
        elif type(obj) is Just:
            obj = func(obj.value)
        else:
            obj = func(obj)
    return maybe(obj)


def strict_mpipe(obj, *funcs):
    """
    A strict version of mpipe: requires a maybe and functions of (a -> M b)
    and do not perform any implicit conversion. This is safer and slightly
    faster than :func:`mpipe`.

    It can also be accessed as mpipe.strict(obj, func_a, func_b, ...)
    """
    for func in funcs:
        if obj.is_just:
            obj = func(obj.value)
        else:
            break
    return obj


def mfilter(lst):
    """
    Return a sequence of values from a list of Maybes skipping all "Nothing"
    and "None" states.
    """
    for value in lst:
        if value is None or value is Nothing:
            continue
        elif isinstance(value, Just):
            yield value.value
        else:
            yield value


def _mk_maybe(Just, Nothing, type=type):
    """
    Define maybe() inside a closure for a small performance gain.
    """

    def maybe(obj):
        """
        Coerce argument to a Maybe:

            maybe(None)      -> Nothing
            maybe(maybe_obj) -> maybe_obj
            maybe(x)         -> Just(x)
        """
        if obj is None or obj is Nothing:
            return Nothing
        elif type(obj) is Just:
            return obj
        else:
            return Just(obj)

    return maybe


#
# Save class methods and module constants
#

# Aliases
Just = Maybe.Just
Nothing = Maybe.Nothing

# Result
from .result import Ok, Err

maybe = _mk_maybe(Maybe.Just, Maybe.Nothing)
Maybe.new = staticmethod(maybe)
Maybe.call = staticmethod(mcall)
Maybe.compose = staticmethod(mcompose)
Maybe.pipe = staticmethod(mpipe)
Maybe.filter = staticmethod(mfilter)

# Strict functions
mpipe.strict = strict_mpipe
mcompose.strict = (lambda *funcs: lambda obj: strict_mpipe(obj, *funcs))
