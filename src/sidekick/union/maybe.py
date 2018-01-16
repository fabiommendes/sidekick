import operator as op

from .union import Union, opt
from .utils import maybe_bin_op

flip = lambda f: lambda x, y: f(y, x)


class Maybe(Union):
    """
    A Maybe type.
    """

    class Nothing(Maybe):
        """
        Represents the absence of a value.
        """

    class Just(Maybe, args=opt('value')):
        """
        Represents a computation with a definite type.
        """

    is_ok = property(lambda x: x.is_just)

    @classmethod
    def apply(cls, func, *args, **kwargs):
        """
        Execute function with all given Just values and return
        ``Just(func(*values, **kwargs))``. If any positional argument is a
        Nothing, return Nothing.

        Examples:

        >>> Maybe.apply(max, Just(1), Just(2), Just(3))
        Just(3)

        >>> Maybe.apply(max, Nothing, Just(1), Just(2), Just(3))
        Nothing
        """

        try:
            args = tuple(x.value for x in args)
        except AttributeError:
            return cls.Nothing
        else:
            return cls.Just(func(*args, **kwargs))

    def map(self, func):
        """
        Apply function if object is in the Just state and return another Maybe.
        """

        if self.is_just:
            new_value = func(self.value)
            return Maybe.Just(new_value)
        else:
            return self

    def map_bound(self, func):
        if self.is_just:
            return func(self.value)
        return self

    def get(self, default=None):
        """
        Extract value from the Just state. If object is Nothing, return the
        supplied default or None.

        Examples:

        >>> x = Maybe.Just(42)
        >>> x.get()
        42
        >>> x = Maybe.Nothing
        >>> x.get()
        None
        """

        if self.is_just:
            return self.value
        else:
            return default

    def to_result(self, err=None):
        """
        Convert Maybe to Result.
        """
        if self.is_nothing:
            return Err(err)
        else:
            return Ok(self.value)

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


def maybe(obj):
    """
    Coerce argument to a Maybe:

        maybe(None)  -> Nothing
        maybe(obj)   -> Just(obj)

    Maybe instances:
        maybe(maybe) -> maybe

    Result instances:
        maybe(is_ok)    -> Just(is_ok.value)
        maybe(err)   -> Nothing
    """

    if isinstance(obj, Maybe):
        return obj
    elif isinstance(obj, Result):
        return obj.to_maybe()
    return Just(obj) if obj is not None else Nothing


Just = Maybe.Just
Nothing = Maybe.Nothing
from .result import Result, Ok, Err
