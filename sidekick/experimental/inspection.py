from collections import Counter
from itertools import zip_longest
from math import sqrt

from sidekick import to_callable
from .. import _toolz as toolz
from ..functions import fn, Seq, Func, Pred

__all__ = ["count_by", "is_distinct", "is_iterable", "has"]
NOT_GIVEN = object()


@fn.curry(2)
def count_by(key: Func, seq: Seq) -> Counter:
    """
    Count elements of a sequence by a key function.

    See Also:
        group_by
    """
    return Counter(map(to_callable(key), seq))


@fn.curry(2)
def count(pred: Pred, seq: Seq) -> int:
    """
    Count the number of occurrences in which predicate is true.
    """
    pred = to_callable(pred)
    return sum(1 for x in seq if pred(x))


@fn.curry(2)
def has(pred: Pred, seq: Seq) -> bool:
    """
    Return True if sequence has at least one item that satisfy the predicate.
    """
    for x in seq:
        if pred(x):
            return True
    return False


@fn
def is_distinct(seq: Seq) -> bool:
    """
    Test if all elements in sequence are distinct.
    """
    return toolz.isdistinct(seq)


@fn
def is_iterable(obj) -> bool:
    """
    Test if argument is iterable.
    """
    return toolz.isiterable(obj)


@fn.curry(2)
def is_seq_equal(seq1, seq2):
    """
    Return True if the two sequences are equal.
    """
    return all(x == y for x, y in zip_longest(seq1, seq2, fillvalue=object()))


#
# Statistical functions
#
@fn.curry(2)
def moment(func: Func, seq: Seq) -> float:
    """
    Return the generalized moment computed by the mean of func across all
    values in seq.
    """

    func = to_callable(func)
    sum = 0
    count = 0
    for x in seq:
        sum += func(x)
        count += 1
    return sum / count


mean = moment(lambda x: x)
var = moment(lambda x: x * x)
std = var >> sqrt
