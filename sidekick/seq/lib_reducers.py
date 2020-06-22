import warnings
from functools import reduce as _reduce

from .iter import iter as sk_iter, generator
from .._toolz import accumulate as _accumulate, topk as _topk
from ..functions import fn, to_callable
from ..typing import Func, Seq, Pred, TYPE_CHECKING, NOT_GIVEN

if TYPE_CHECKING:
    from .. import api as sk


#
# Basic reductions and folds
#
@fn.curry(3)
def fold(func: Func, init, seq: Seq):
    """
    Perform a left reduction of sequence.

    Examples:
        >>> sk.fold(op.add, 0, [1, 2, 3, 4])
        10

    See Also:
        :func:`reduce`
        :func:`scan`
    """
    func = to_callable(func)
    return _reduce(func, seq, init)


@fn.curry(2)
def reduce(func: Func, seq: Seq, init=NOT_GIVEN):
    """
    Like fold, but does not require initial value.

    This function raises a ValueError on empty sequences.

    Examples:
        >>> sk.reduce(op.add, [1, 2, 3, 4])
        10

    See Also:
        :func:`fold`
        :func:`accumulate`
    """
    if init is not NOT_GIVEN:
        warnings.warn("use the sk.fold() function to set initial values.")
        return fold(func, init, seq)

    func = to_callable(func)
    return _reduce(func, seq)


#
# Special reductions
#
@fn.curry(2)
def accumulate(func: Func, seq: Seq) -> Seq:
    """
    Like :func:`scan`, but uses first item of sequence as initial value.

    See Also:
        :func:`scan`
        :func:`reduce`
    """
    func = to_callable(func)
    return sk_iter(_accumulate(func, seq))


@fn.curry(3)
def scan(func: Func, init, seq: Seq) -> Seq:
    """
    Returns a sequence of the intermediate folds of seq by func.

    In other words it generates a sequence like:

        func(init, seq[0]), func(result[0], seq[1]), ...

    in which result[i] corresponds to items in the resulting sequence.

    See Also:
        :func:`accumulate`
        :func:`fold`
    """
    func = to_callable(func)
    return sk_iter(_accumulate(func, seq, init))


#
# Special reductions
#
@fn
def product(seq: Seq, *, init=1):
    """
    Multiply all elements of sequence.

    Examples:
        >>> sk.product([1, 2, 3, 4, 5])
        120

    See Also:
        :func:`sum`
        :func:`products`
    """
    for x in seq:
        init = x * init
    return init


@fn.curry(1)
@generator
def products(seq: Seq, *, init=1):
    """
    Return a sequence of partial products.

    Examples:
        >>> sk.products([1, 2, 3, 4, 5])
        sk.iter([1, 2, 6, 24, 120])

    See Also:
        :func:`accumulate`
        :func:`sums`
    """
    for x in seq:
        init = x * init
        yield init


@fn
@generator
def sums(seq: Seq, *, init=0):
    """
    Return a sequence of partial sums.

    Same as ``sk.fold((X + Y), seq, 0)``

    Examples:
        >>> sk.sums([1, 2, 3, 4, 5])
        sk.iter([1, 3, 6, 10, 15])

    See Also:
        :func:`accumulate`
        :func:`products`
    """
    for x in seq:
        init = x + init
        yield init


@fn.curry(2)
def all_by(pred: Pred, seq: Seq) -> bool:
    """
    Return True if all elements of seq satisfy predicate.

    ``all_by(None, seq)`` is the same as the builtin ``all(seq)`` function.

    Examples:
        >>> sk.all_by((X % 2), [1, 3, 5])
        True

    See Also:
        :func:`any_by`
    """
    pred = to_callable(pred)
    return all(map(pred, seq))


@fn.curry(2)
def any_by(pred: Pred, seq: Seq) -> bool:
    """
    Return True if any elements of seq satisfy predicate.

    ``any_by(None, seq)`` is the same as the builtin ``any(seq)`` function.

    Examples:
        >>> sk.any_by(sk.is_divisible_by(2), [2, 3, 5, 7, 11, 13])
        True

    See Also:
        :func:`all_by`
    """
    pred = to_callable(pred)
    return any(map(pred, seq))


@fn.curry(2)
def top_k(k: int, seq: Seq, *, key: Func = None) -> tuple:
    """
    Find the k largest elements of a sequence.

    Examples:
        >>> sk.top_k(3, "hello world")
        ('w', 'r', 'o')
    """
    return _topk(k, seq, key)
