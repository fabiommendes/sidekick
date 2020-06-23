from collections import Counter
from math import sqrt

from ..functions import fn, to_callable
from ..typing import Seq, Func, Pred

NOT_GIVEN = object()


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
