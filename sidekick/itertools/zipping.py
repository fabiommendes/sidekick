from typing import Union

from ..functions import fn, to_callable
from ..seq import is_empty
from ..typing import Seq, Func

__all__ = ["zipper", "rzipper", "zip_with"]


def zipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **left** of the given sequences.

    Examples:
        >>> zip10 = zipper(range(1, 11))
        >>> dict(zip10('abc'))
        {'a': 1, 'b': 2, 'c': 3}
    """
    seqs = tuple(seqs)
    return fn(lambda seq: zip(seq, *seqs))


def rzipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **right** of the given sequences.

    Examples:
        >>> enumerate10 = rzipper(range(1, 11))
        >>> dict(enumerate10('abc'))
        {1: 'a', 2: 'b', 3: 'c'}
    """
    seqs = tuple(seqs)
    return fn(lambda seq: zip(*seqs, seq))


def zip_aligned(*args):
    """
    Similar to the zip built-in, but raises an ValueError if one sequence
    terminates before the others.

    Examples:
        If sizes match, it is just like zip.

        >>> zip_aligned((1, 2, 3), (4, 5, 6)) | L
        [(1, 4), (2, 5), (3, 6)]

        But gives an error otherwise.

        >>> zip_aligned((1, 2, 3), (4, 5, 6, 7)) | L
        Traceback (most recent call last):
        ...
        ValueError: non-aligned iterators
    """
    args = tuple(map(iter, args[0] if len(args) == 1 else args))
    yield from zip(*args)
    if not all(map(is_empty, args)):
        raise ValueError("non-aligned iterators")


# noinspection PyIncorrectDocstring
@fn.curry(2)
def zip_with(func: Union[Func, Seq], *seqs: Seq) -> Seq:
    """
    Apply each tuple of element obtained from zipping seqs as arguments to the
    function.

    If func is a sequence of functions, each tuple of arguments is applied to
    their corresponding function.

    Args:
        func (iterable):
            A function or an iterable of functions
        seqs (iterable arguments):
            Values that will be passed as arguments to functions. If seq is larger than
            funcs, the remaining values are passed as is.

    Examples:
        >>> zip_with([(X ** 1), (X ** 2), (X ** 3)], [1, 2, 3]) | L
        [1, 4, 27]
    """
    arg_items = zip(*seqs)
    try:
        func = to_callable(func)
    except TypeError:
        to_func = to_callable
        yield from (to_func(f)(*args) for f, args in zip(func, arg_items))
    else:
        yield from (func(*args) for args in arg_items)
