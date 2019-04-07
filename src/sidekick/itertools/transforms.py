from operator import itemgetter

from ..core import Seq, Pred, extract_function, fn

__all__ = ['select_indexed', 'select_indexes']

identity = lambda x: x
_first_item = itemgetter(0)
_second_item = itemgetter(1)
_map = lambda pred: lambda seq: map(pred, seq)


@fn.curry(3)
def select_indexes(selector, pred: Pred, seq: Seq, *, start=0, enter=False) -> Seq:
    """
    Take a selection function such as filter, takewhile, etc, apply it to sequence
    and return the filtered indexes instead of values.

    Examples:
        >>> seq = [5, 10, 2, 3, 25, 42]
        >>> select_indexes(filter, (X >= 10), seq) | L
        [1, 4, 5]

        If selection function return a sequence of sequences, it is necessary
        to pass enter=True keyword argument
        >>> a, b = select_indexes(sk.separate, (X >= 10), seq, enter=True)
        >>> list(a), list(b)
        ([1, 4, 5], [0, 2, 3])

    See Also:
        select_indexed
    """
    filtered = select_indexed(selector, pred, seq, start=start)
    if enter:
        return map(_map(_first_item), filtered)
    else:
        return map(_first_item, filtered)


@fn.curry(3)
def select_indexed(selector, pred: Pred, seq: Seq, *, start=0) -> Seq:
    """
    Take a selection function such as filter, takewhile, etc, apply it to sequence
    and return tuples of (index, value).

    Examples:
        >>> seq = [5, 10, 2, 3, 25, 42]
        >>> select_indexed(filter, (X >= 10), seq) | L
        [(1, 10), (4, 25), (5, 42)]

    See Also:
        select_indexes
    """
    pred = extract_function(pred)
    pred_ = lambda x: pred(_second_item(x))
    return selector(pred_, enumerate(seq, start))
