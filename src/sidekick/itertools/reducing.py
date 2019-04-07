from functools import reduce as _reduce

import toolz

from ..core import fn, Func, Seq, extract_function, Pred

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
    func = extract_function(func)
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
    func = extract_function(func)
    return _reduce(func, seq)


#
# Special reductions
#
@fn.curry(2)
def accumulate(func: Func, seq: Seq) -> Seq:
    """
    Like :func:`scan`, but uses first item of sequence as initial value.
    """
    func = extract_function(func)
    return toolz.accumulate(func, seq)


@fn.curry(3)
def scan(func: Func, init, seq: Seq) -> Seq:
    """
    Returns a sequence of the intermediate folds of seq by func.

    In other words it generates a sequence like:

        func(init, seq[0]), func(result[0], seq[1]), ...

    in which result[i] corresponds to items in the resulting sequence.
    """
    func = extract_function(func)
    return toolz.accumulate(func, seq, init)


#
# Special reductions
#

@fn
def product(seq: Seq, *, init=1):
    """
    Multiply all elements of sequence.

    Examples:
        >>> product([1, 2, 3, 4, 5])
        120

    See Also:
        sum
        product
        all_by
        any_by
    """
    for x in seq:
        init = x * init
    return init


@fn
def products(seq: Seq, *, init=1):
    """
    Return a sequence of partial products.

    Examples:
        >>> products([1, 2, 3, 4, 5]) | L
        [1, 2, 6, 24, 120]

    See Also:
        sum
        all_by
        any_by
    """
    for x in seq:
        init = x * init
        yield init


@fn
def sums(seq: Seq, *, init=0):
    """
    Return a sequence of partial sums.

    Examples:
        >>> sums([1, 2, 3, 4, 5]) | L
        [1, 3, 6, 10, 15]

    """
    for x in seq:
        init = x + init
        yield init


@fn.curry(2)
def all_by(pred: Pred, seq: Seq) -> bool:
    """
    Return True if all elements of seq satisfy predicate.

    Examples:
        >>> all_by((X % 2), [1, 3, 5])
        True
    """
    pred = extract_function(pred)
    return all(map(pred, seq))


@fn.curry(2)
def any_by(pred: Pred, seq: Seq) -> bool:
    """
    Return True if any elements of seq satisfy predicate.

    Examples:
        >>> any_by(pred.divisible_by(2), [2, 3, 5, 7, 11, 13])
        True
    """
    pred = extract_function(pred)
    return any(map(pred, seq))
