from itertools import tee
from sidekick.beta.misc import fill
from ..core import fn, Func, Seq, extract_function

__all__ = ["order_by", "transform", "transform_map"]


@fn.curry(2)
def order_by(key: Func, seq: Seq) -> list:
    """
    Order sequence by the given function.

    Args:
        key:
            Sort return values of the key function.
        seq:
            Sequence
    """
    key = extract_function(key)
    return sorted(seq, key=extract_function(key))


@fn.curry(2)
def arg_transformer(*args, **kwargs) -> Func:
    """
    Receive a function arguments and return a function that transform the
    given arguments by the corresponding functions.

    Examples:
        >>> transformer = arg_transformer(str.upper, None, str.lower, sep=str.strip)
        >>> args, kwargs = transformer('Foo', 'Bar', 'Baz', 'Eggs', sep=' : ')
        >>> args
        ('FOO', 'Bar', 'baz', 'Eggs')
        >>> kwargs
        {'sep': ':'}
    """
    id_ = lambda x: x
    fargs = tuple(extract_function(f or id_) for f in args)
    fkwargs = {k: extract_function(f or id_) for k, f in kwargs.items()}

    def arg_transformer(*args, **kwargs):
        args = tuple(f(x) for f, x in zip(fill(id_, fargs), args))
        kwargs = {k: fkwargs.get(k, id_)(v) for k, v in kwargs.items()}
        return args, kwargs

    return arg_transformer


def tee_with(func, seq):
    """
    Return a pair of (transformed, seq) in which a copy of seq is transformed
    by function and another copy is returned as a second argument.

    Examples:
        >>> nums = iter([1, 2, 3, 4, 5])
        >>> sqrs, nums = tee_with(sk.map(X * X), nums)
        >>> list(sqrs), list(nums)
        ([1, 4, 9, 16, 25], [1, 2, 3, 4, 5])
    """
    seq_, seq = tee(seq)
    return (func(seq_), seq)
