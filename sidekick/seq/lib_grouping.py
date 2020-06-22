from itertools import tee, chain, takewhile, dropwhile, islice

from .iter import iter as sk_iter
from .._toolz import partition_all, partition as _partition, sliding_window, partitionby
from ..functions import fn, to_callable
from ..typing import Seq, NOT_GIVEN, TYPE_CHECKING, Union, Pred, Func, Tuple

_next = next
if TYPE_CHECKING:
    from .. import api as sk
    from ..api import X

    p = ""


@fn.curry(2)
def chunks(n: int, seq: Seq, *, pad=NOT_GIVEN, drop=False) -> Seq:
    """
    Partition sequence into non-overlapping tuples of length n.

    Args:
        n:
            Number of elements in each partition.
        seq:
            Input sequence.
        pad:
            If given, pad a trailing incomplete partition with this value until
            it has n elements.
        drop (bool):
            If True, drop the last partition if it has less than n elements.

    Examples:
        Too see the difference between padding, dropping and the regular
        behavior.

        >>> sk.chunks(2, range(5))
        sk.iter([(0, 1), (2, 3), (4,)])

        >>> sk.chunks(2, range(5), pad=None)
        sk.iter([(0, 1), (2, 3), (4, None)])

        >>> sk.chunks(2, range(5), drop=True)
        sk.iter([(0, 1), (2, 3)])

    See Also:
        :func:`chunks_by`
        :func:`window`
    """
    # TODO: implement functionality from more_itertools.split_into if n is not
    #       an integer.
    if drop:
        return sk_iter(_partition(n, seq))
    elif pad is not NOT_GIVEN:
        return sk_iter(_partition(n, seq, pad))
    else:
        return sk_iter(partition_all(n, seq))


@fn.curry(2)
def chunks_by(func: Func, seq: Seq) -> Seq:
    """
    Partition sequence into chunks according to a function.

    It creates a new partition every time the value of func(item) changes.

    Args:
        func:
            Function used to control partition creation
        seq:
            Input sequence.

    Examples:
        >>> sk.chunks_by((X // 3), range(10))
        sk.iter([(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)])

    See Also:
        :func:`chunks`
        :func:`partition`
    """
    # TODO: implement functionality from more_itertools.split_at, split_after and
    #       split before by passing extra keyword arguments
    return sk_iter(partitionby(to_callable(func), seq))


@fn.curry(2)
def window(n: int, seq: Seq) -> Seq:
    """
    Return a sequence of overlapping sub-sequences of size n.

    ``n == 2`` is equivalent to a pairwise iteration.

    Examples:
        Pairwise iteration:

        >>> [''.join(p) for p in sk.window(2, "hello!")]
        ['he', 'el', 'll', 'lo', 'o!']

    See Also:
        :func:`pairs`
    """
    return sliding_window(n, seq)


@fn.curry(1)
def pairs(seq: Seq, *, prev=NOT_GIVEN, next=NOT_GIVEN) -> Seq:
    """
    Returns an iterator of a pair adjacent items.

    This is similar to window(2), but requires a fill value specified either
    with ``prev`` or ``next`` to select if it will form pairs with the preceeding
    of the following value.

    It must specify either prev or next, never both.

    Args:
        seq:
            Input sequence.
        prev:
            If given, fill this value in the first item and iterate over all
            items preceded with the previous value.
        next:
            If given, fill this value in the last item and iterate over all
            items followed with the next value.

    Examples:
        >>> [''.join(p) for p in sk.pairs("hello!", prev="-")]
        ['-h', 'he', 'el', 'll', 'lo', 'o!']
        >>> [''.join(p) for p in sk.pairs("hello!", next="!")]
        ['he', 'el', 'll', 'lo', 'o!', '!!']

    See Also:
        :func:`window`
    """
    if prev is NOT_GIVEN and next is NOT_GIVEN:
        raise TypeError("must specify either prev or next keyword arguments")
    elif prev is NOT_GIVEN:
        a, b = tee(seq)
        _next(b, None)
        return sk_iter(zip(a, chain(b, [next])))
    elif next is NOT_GIVEN:
        return sk_iter(_pairs_prev(seq, prev))
    else:
        raise TypeError("must specify either prev or next keyword arguments, not both")


def _pairs_prev(seq, prev):
    seq = iter(seq)
    for x in seq:
        yield (prev, x)
        prev = x


@fn.curry(2)
def partition(key: Union[int, Pred], seq: Seq) -> Tuple[Seq, Seq]:
    """
    Partition sequence in two.

    Returns a sequence with elements before and after the key separator.

    Args:
        key:
            An integer index or predicate used to partition sequence.
        seq:
            Input sequence.

    Examples:
        >>> a, b = sk.partition(2, [5, 4, 3, 2, 1])
        >>> a
        sk.iter([5, 4])
        >>> b
        sk.iter([3, 2, 1])

        >>> a, b = sk.partition((X == 3), [1, 2, 3, 4, 5])
        >>> a
        sk.iter([1, 2])
        >>> b
        sk.iter([3, 4, 5])
    """
    if isinstance(key, int):
        a, b = tee(seq)
        return sk_iter(islice(a, key)), sk_iter(islice(b, key, None))
    else:
        pred = to_callable(key)
        a, b = tee((pred(x), x) for x in seq)
        value = lambda x: x[1]
        return (
            sk_iter(map(value, takewhile(lambda x: not x[0], a))),
            sk_iter(map(value, dropwhile(lambda x: not x[0], b))),
        )


@fn
def distribute(n: int, seq: Seq) -> Tuple[Seq, ...]:
    """
    Distribute items of seq into n different sequences.

    Args:
        n:
            Number of output sequences.
        seq:
            Input sequences.

    Examples:
        >>> a, b = sk.distribute(2, [0, 1, 2, 3, 4, 5, 6])
        >>> a
        sk.iter([0, 2, 4, 6])
        >>> b
        sk.iter([1, 3, 5])
    """
    results = tee(seq, n)
    return tuple(sk_iter(islice(it, i, None, n)) for i, it in enumerate(results))
