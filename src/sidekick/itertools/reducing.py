from functools import reduce as _reduce

import toolz

from ..core import fn, Func, Seq, extract_function

__all__ = [
    *['fold', 'reduce'],  # base reducers
    *['accumulate', 'products', 'sums', 'accumulate', 'scan'],  # special
]


#
# Basic reductions and folds
#
@fn.curry(3)
def fold(func: Func, init, seq: Seq):
    """
    Perform a left reduction of sequence.

    Examples:
        >>> fold(op.add, 0, [1, 2, 3, 4])
        10
    """
    return _reduce(func, seq, init)


@fn.curry(2)
def reduce(func: Func, seq: Seq):
    """
    Like fold, but does not require initial value.

    This function raises a ValueError on empty sequences.

    Examples:
        >>> reduce(op.add, [1, 2, 3, 4])
        10
    """
    return _reduce(func, seq)


#
# Special reductions
#
@fn.annotate(2)
def accumulate(func: Func, seq: Seq) -> Seq:
    """
    Like :func:`scan`, but uses first item of sequence as initial value.
    """
    func = extract_function(func)
    return toolz.accumulate(func, seq)


@fn.annotate(3)
def scan(func: Func, init, seq: Seq) -> Seq:
    """
    Returns a sequence of the intermediate folds of seq by func.

    In other words it yields a sequence like:

        func(init, seq[0]), func(result[0], seq[1]), ...

    in which result[i] corresponds to items in the resulting sequence.
    """
    func = extract_function(func)
    return toolz.accumulate(func, seq, init)


#
# Special reductions
#
@fn
def products(seq, *, init=1):
    """
    Return a sequence of partial products.
    """
    for x in seq:
        init = x + init
        yield init


@fn
def sums(seq, *, init=0):
    """
    Return a sequence of partial sums.
    """
    for x in seq:
        init = x + init
        yield init
