from collections.abc import Iterator

from ..functools import call
from ..core import fn
from .union import Union

__all__ = ['Maybe', 'Just', 'Nothing', 'maybe', 'mapply', 'mpipe', 'mpipeline', 'mfilter']

flip = lambda f: lambda x, y: f(y, x)
this = None


class Maybe(Union):
    """
    A Maybe type.
    """

    is_success = is_failure = False

    def map(self, func, *funcs):
        """
        Apply function if object is in the Just state and return another Maybe.
        """
        if self:
            if funcs:
                return mpipe(self.value, func, *funcs)
            else:
                return maybe(func(self.value))
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
        return self.value if self else default

    def method(self, method, *args, **kwargs):
        """
        Call the given method of value and promote result to a Maybe.

        Examples:
            >>> Just(1 + 2j).method('conjugate')
            Just((1-2j))
        """
        if self:
            method = getattr(self.value, method)
            return maybe(method(*args, **kwargs))
        else:
            return self

    def attr(self, attr):
        """
        Retrieves attribute as a Maybe.

        Examples:
            >>> Just(1 + 2j).attr('real')
            Just(1.0)
        """
        return self and maybe(getattr(self.value, attr))

    def iter(self):
        """
        Iterates over content.

        It returns an empty iterator in the Nothing case.
        """
        if self:
            it: Iterator = self.value
            yield from it

    def to_result(self, err=Exception()):
        """
        Convert Maybe to Result.
        """
        return Ok(self.value) if self else Err(err)

    def to_maybe(self):
        """
        Return itself.

        This function exists so some algorithms can work with both Maybe's and
        Result's using the same interface.
        """
        return self


class Nothing(Maybe):
    """
    State of absence of a value.
    """

    value = None
    is_failure = True
    __bool__ = lambda _: False


class Just(Maybe):
    """
    A computation with definite value.
    """
    value: object
    is_success = True
    __bool__ = lambda _: True


#
# Module functions.
#
@call(Maybe.Just, Maybe.Nothing, type)
def maybe(just, nothing, type_):
    # Define maybe() inside a closure for a small performance gain.
    # noinspection PyShadowingNames
    def maybe(obj):
        """
        Coerce argument to a Maybe:

            maybe(maybe_obj) -> maybe_obj
            maybe(None)      -> Nothing
            maybe(x)         -> Just(x)
        """
        if obj is None or obj is nothing:
            return nothing
        elif type_(obj) is just:
            return obj
        else:
            return just(obj)

    return maybe


def mapply(func, *args, **kwargs):
    """
    Execute function with all given Maybe values unwrapping all positional
    arguments and return ``Just(result)`` or ``Nothing`` if result is None.

    If any positional argument is a Nothing, returns Nothing. None values and
    keyword arguments do not propagate the Nothing state.

    Examples:
        >>> mapply(max, Just(1), Just(2), Just(3))
        Just(3)
        >>> mapply(max, Nothing, Just(1), Just(2), Just(3))
        Nothing
    """
    arg_values = []
    append = arg_values.append

    for arg in args:
        if arg is None or arg is Nothing:
            return Nothing
        elif arg.__class__ is Just:
            append(arg.value)
        else:
            append(arg)
    return maybe(func(*arg_values, **kwargs))


def mpipeline(*funcs):
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
    application after the first Nothing/None is encountered. It performs implicit
    conversion to maybes treating None as Nothing and any other value x as
    Just(x).

    It also accepts an strict version that does not perform any implicit
    converstion and runs slightly faster using ``mpipe.strict(obj, ...)``.

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


def _mpipe_strict(obj, *funcs):
    for func in funcs:
        if obj:
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


# Result
from .result import Ok, Err  # noqa: E402

mpipe.strict = fn(_mpipe_strict)
mpipeline.strict = fn(lambda *funcs: fn(lambda obj: _mpipe_strict(obj, *funcs)))
