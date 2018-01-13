import collections
import sys

Maybe = Nothing = Just = Result = Err = Ok = None


class Opts(collections.OrderedDict):
    """
    An ordered dictionary.
    """

    def __repr__(self):
        data = ', '.join('%r: %r' % (k, v) for k, v in self.items())
        return 'Opts({%s})' % data


def opt(*args, **kwargs):  # noqa: C901
    """
    Declare argument types and names for case classes. Return an ordered
    mapping from names to types.

    Usage:
        Singleton cases
        >>> opt()
        Opts({})

        Declares a single argument type
        >>> opt(type)
        Opts({'value': type})

        Declares a single argument name
        >>> opt('name')
        Opts({'name': object})

        Declares both name and type
        >>> opt(name=type)
        Opts({'name': type})

        For multiple arguments (requires Python 3.6+)
        >>> opt(arg1=int, arg2=float)
        Opts({'arg1': int, 'arg2': float})

        Declares several types
        >>> opt(int, float)
        Opts({'value1': int, 'value2': float})

        Declares the number of arguments
        >>> opt(2)
        Opts({'value1': object, 'value2': object})

        Declares types and argument names
        >>> opt([('arg1', int), ('arg2', float)])
        Opts({'arg1': int, 'arg2': float})
    """
    if not kwargs and not args:
        args = []
    elif not kwargs and len(args) == 1:
        arg, = args
        if isinstance(arg, str):
            args = [(arg, object)]
        elif isinstance(arg, type):
            args = [('value', object)]
        elif isinstance(arg, int):
            args = (object,) * arg
            return opt(*args)
        else:
            args = arg
    elif args and kwargs:
        msg = 'cannot declare positional and keyword arguments simultaneously'
        raise TypeError(msg)
    elif kwargs:
        if len(kwargs) > 1 and sys.version_info < (3, 6):
            msg = 'Multiple keyword arguments are only supported on Python 3.6+'
            raise TypeError(msg)
        args = kwargs

    return Opts(args)


#
# Auxiliary methods for maybes and just metaclasses
#
def maybe_bin_op(op):
    """
    Creates a binary op method for a Maybe from a binary function.

    It executes the function for two Just instances and propagates any Nothings.
    """

    def binop(x, y):
        if isinstance(y, Maybe):
            if x.is_just and y.is_just:
                return Just(op(x.value, y.value))
            else:
                return Nothing
        else:
            return NotImplemented

    return binop


def result_bin_op(op):
    """
    Creates a binary op method for a Result from a binary function.
    """

    def binop(x, y):
        if isinstance(y, Result):
            if x.is_ok and y.is_ok:
                return Ok(op(x.value, y.value))
            else:
                return y if x.is_ok else x
        else:
            return NotImplemented

    return binop
