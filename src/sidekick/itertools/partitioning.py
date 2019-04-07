import itertools
from typing import Union

import toolz

from ..core import fn, Seq, Func, extract_function, Pred

not_given = object()
__all__ = [
    'chunks', 'partition', 'partition_by',
    'fold_by', 'reduce_by', 'group_by', 'partition_at',
]


@fn.curry(2)
def chunks(n: int, seq: Seq) -> Seq:
    """
    Partition sequence into non-overlapping tuples of length n.

    The final tuple might have less than n elements.

    Examples:
        >>> chunks(2, range(5)) | L
        [(0, 1), (2, 3), (4,)]

    See Also:
        partition
        partition_by
        window
    """
    return toolz.partition_all(n, seq)


@fn.curry(2)
def group_by(key: Func, seq: Seq) -> dict:
    """
    Group collection by the results of a key function.

    Examples:
        >>> group_by((X % 2), range(5))
        {0: [0, 2, 4], 1: [1, 3]}

    See Also:
        count_by
        reduce_by
    """
    return toolz.groupby(key, seq)


@fn.curry(2)
def partition(n: int, seq: Seq, *, pad=not_given) -> Seq:
    """
    Partition sequence into tuples of length n.

        partition(2, seq) -> (seq[0], seq[1]), (seq[2], seq[3]), ...

    If seq is not evenly partitioned in groups of ``n``, the final tuple is
    dropped. Specify  ``pad`` to fill it to length ``n``.

    Examples:
        >>> partition(2, range(5)) | L  # no padding
        [(0, 1), (2, 3)]

        >>> partition(2, range(5), pad=None) | L  # padding
        [(0, 1), (2, 3), (4, None)]

    """
    kwargs = {} if pad is not_given else {'pad': pad}
    return toolz.partition(n, seq, **kwargs)


@fn.curry(2)
def partition_by(func: Func, seq: Seq) -> Seq:
    """
    Partition a sequence according to a function. It creates a new partition
    every time the value of func(item) changes.

    Examples:
        >>> partition_by((X // 3), range(10)) | L
        [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)]

    See Also:
        chunks
        partition
    """
    return toolz.partitionby(extract_function(func), seq)


@fn.curry(4)
def fold_by(key: Func, op, init, seq: Seq) -> dict:
    """
    Reduce each sequence generated by a group by.

    More efficient than performing separate operations since it does not
    store intermediate groups.

    Examples:
        >>> fold_by(X % 2, op.add, 0, [1, 2, 3, 4, 5])
        {1: 9, 0: 6}

    See Also:
        fold
        group_by
        reduce_by
    """
    return toolz.reduceby(key, op, seq, init)


@fn.curry(3)
def reduce_by(key: Func, op, seq: Seq) -> dict:
    """
    Similar to reduce_by, but only works on non-empty sequences.

    Initial value is taken to be the first element in sequence.

    Examples:
        >>> reduce_by(X % 2, op.add, [1, 2, 3, 4, 5])
        {1: 9, 0: 6}
    """
    return toolz.reduceby(key, op, seq)


@fn.curry(2)
def partition_at(sep: Union[int, Pred], seq: Seq) -> (Seq, Seq):
    """
    Returning a sequence with elements before and after the separator.

    Separator can be a integer index to separate by position or a predicate
    function.

    Examples:
        >>> a, b = partition_at(2, [5, 4, 3, 2, 1])
        >>> list(a), list(b)
        ([5, 4], [3, 2, 1])

        >>> a, b = partition_at((X == 3), [1, 2, 3, 4, 5])
        >>> list(a), list(b)
        ([1, 2], [3, 4, 5])
    """
    a, b = itertools.tee(seq)
    if isinstance(sep, int):
        return itertools.islice(a, sep), itertools.islice(b, sep, None)
    else:
        pred = extract_function(sep)
        a, b = itertools.tee((pred(x), x) for x in seq)
        value = lambda x: x[1]
        return (map(value, itertools.takewhile(lambda x: not x[0], a)),
                map(value, itertools.dropwhile(lambda x: not x[0], b)))
