import itertools

import toolz
from typing import Union

from ..core import fn, Seq, Func, extract_function

__all__ = ['window', 'with_next', 'with_prev',
           'zipper', 'rzipper', 'zip_with']


@fn.curry(2)
def window(n: int, seq: Seq) -> Seq:
    """
    Return a sequence of overlapping sub-sequences of size n.

    ``n == 2`` is equivalent to a pairwise iteration.
    """
    return toolz.sliding_window(n, seq)


@fn
def with_prev(seq: Seq, *, fill=None) -> Seq:
    """
    Returns an iterator of a pair of each item with one preceding it.

    Generate fill or None as preceding element for first item.
    """

    prev = fill
    for x in seq:
        yield (prev, x)
        prev = x


@fn
def with_next(seq: Seq, fill=None) -> Seq:
    """
    Returns an iterator of a pair of each item with one next to it.

    Yields fill or None as next element for last item.
    """
    a, b = itertools.tee(seq)
    next(b, None)
    return zip(a, itertools.chain(b, [fill]))


def zipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **left** of the given sequences.
    """
    seqs = tuple(seqs[0] if len(seqs) == 1 else seqs)
    return fn(lambda seq: zip(seq, *seqs))


def rzipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **right** of the given sequences.
    """
    seqs = tuple(seqs[0] if len(seqs) == 1 else seqs)
    return fn(lambda seq: zip(*(seqs + (seq,))))


def zip_aligned(*args):
    """
    Similar to the zip built-in, but raises an ValueError if one sequence
    terminates before the others.
    """
    args = tuple(map(iter, args[0] if len(args) == 1 else args))
    yield from zip(*args)
    for idx, it in enumerate(args):
        try:
            next(it)
        except StopIteration:
            pass
        else:
            raise ValueError('the %s-th iterator is still running' % idx)


# noinspection PyIncorrectDocstring
@fn.curry(2)
def zip_with(func: Union[Func, Seq], *seqs: Seq) -> Seq:
    """
    Apply each tuple of element obtained from zipping seqs as arguments to the
    function.

    If func is a sequence of functions, each tuple of arguments is applied to
    their corresponding function.

    >>> incr = lambda n: lambda x: x + n
    >>> zip_with([incr(1), incr(2), incr(3)], [1, 2, 3]) | L
    [2, 4, 6]

    Args:
        func (iterable):
            A function or an iterable of functions
        seqs (iterable arguments):
            Values that will be passed as arguments to functions. If seq is larger than
            funcs, the remaining values are passed as is.

    Returns:
        An iterator.
    """
    arg_items = zip(*seqs)
    try:
        func = extract_function(func)
    except TypeError:
        to_func = extract_function
        yield from (to_func(f)(*args) for f, args in zip(func, arg_items))
    else:
        yield from (func(*args) for args in arg_items)
