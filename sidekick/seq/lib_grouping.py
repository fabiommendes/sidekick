from itertools import tee, chain, takewhile, dropwhile, islice

from toolz import groupby

from .iter import iter as sk_iter
from .lib_basic import uncons
from .._toolz import partition_all, partition as _partition, sliding_window, partitionby
from ..functions import fn, to_callable
from ..typing import (
    Seq,
    NOT_GIVEN,
    TYPE_CHECKING,
    Union,
    Pred,
    Func,
    Tuple,
    Iterable,
    T,
)

_next = next
if TYPE_CHECKING:
    from .. import api as sk
    from ..api import X, Y

    p = ""


@fn.curry(2)
def group_by(key: Func, seq: Seq) -> dict:
    """
    Group collection by the results of a key function.

    Examples:
        >>> sk.group_by((X % 2), range(5))
        {0: [0, 2, 4], 1: [1, 3]}

    See Also:
        :func:`reduce_by`
        :func:`fold_by`
    """
    return groupby(key, seq)


@fn.curry(2)
def chunks(
    n: Union[int, Iterable[int]], seq: Seq[T], *, pad=NOT_GIVEN, drop=False
) -> Seq[Tuple[T, ...]]:
    """
    Partition sequence into non-overlapping tuples of length n.

    Args:
        n:
            Number of elements in each partition. If n is a sequence, it selects
            partitions by the sequence size.
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

        Using sequences, we can create more complicated chunking patterns.

        >>> sk.chunks(sk.cycle([2, 3]), range(10))
        sk.iter([(0, 1), (2, 3, 4), (5, 6), (7, 8, 9)])

        A trailing ellipsis consumes the rest of the iterator.

        >>> sk.chunks([1, 2, 3, ...], range(10))
        sk.iter([(0,), (1, 2), (3, 4, 5), (6, 7, 8, 9)])

    See Also:
        :func:`chunks_by`
        :func:`window`
    """
    if isinstance(n, int):
        if drop:
            return sk_iter(_partition(n, seq))
        elif pad is not NOT_GIVEN:
            return sk_iter(_partition(n, seq, pad))
        else:
            return sk_iter(partition_all(n, seq))
    elif drop:
        return sk_iter(_chunks_sizes_ex(n, seq, True, None))
    elif pad:
        return sk_iter(_chunks_sizes_ex(n, seq, False, pad))
    else:
        return sk_iter(_chunks_sizes(n, seq))


def _chunks_sizes(ns, seq):
    for n in ns:
        if n is ...:
            yield tuple(seq)
            break
        else:
            yield tuple(islice(seq, n))


def _chunks_sizes_ex(ns, seq, drop, pad):
    buf = []
    clear = buf.clear
    fill = buf.extend
    seq = iter(seq)

    for n in ns:
        if n is ...:
            yield tuple(seq)
            break
        else:
            clear()
            try:
                fill(next(seq) for _ in range(n))
                yield tuple(buf)
            except (RuntimeError, StopIteration):
                if drop or not buf:
                    return
                m = n - len(buf)
                fill([pad] * m)
                yield tuple(buf)
                break


@fn.curry(2)
def chunks_by(func: Func, seq: Seq, how="values") -> Seq:
    """
    Partition sequence into chunks according to a function.

    It creates a new partition every time the value of func(item) changes.

    Args:
        func:
            Function used to control partition creation
        seq:
            Input sequence.
        how (str):
            Control how func is used to create new chunks from iterator.

            * 'values' (default): create a new chunk when func(x) changes value
            * 'pairs': create new chunk when func(x, y) for two successive values
               is True.
            * 'left': create new chunk when func(x) is True. x is put in the
               chunk to the left.
            * 'right': create new chunk when func(x) is True. x is put in the
              chunk to the right.
            * 'drop': create new chunk when func(x) is True. x dropped from output
               sequence. It behaves similarly to str.split.

    Examples:
        Standard chunker

        >>> sk.chunks_by((X // 3), range(10))
        sk.iter([(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)])

        Chunk by pairs

        >>> sk.chunks_by((Y <= X), [1, 2, 3, 2, 4, 8, 0, 1], how='pairs')
        sk.iter([(1, 2, 3), (2, 4, 8), (0, 1)])

        Chunk by predicate. The different versions simply define in which chunk
        the split location will be allocated

        >>> sk.chunks_by(sk.is_odd, [1, 2, 3, 2, 4, 8], how='left')
        sk.iter([(1,), (2, 3), (2, 4, 8)])
        >>> sk.chunks_by(sk.is_odd, [1, 2, 3, 2, 4, 8], how='right')
        sk.iter([(1, 2), (3, 2, 4, 8)])
        >>> sk.chunks_by(sk.is_odd, [1, 2, 3, 2, 4, 8], how='drop')
        sk.iter([(), (2,), (2, 4, 8)])

    See Also:
        :func:`chunks`
        :func:`partition`
    """
    if how == "values":
        return sk_iter(partitionby(to_callable(func), seq))
    elif how == "pairs":
        return sk_iter(_chunks_pairs(func, seq))
    elif how == "left":
        return sk_iter(_chunks_left(func, seq))
    elif how == "right":
        return sk_iter(_chunks_right(func, seq))
    elif how in ("drop", "split"):
        return sk_iter(_chunks_split(func, seq))
    else:
        raise ValueError(f"invalid method: {how!r}")


def _chunks_pairs(pred, seq):
    try:
        x, it = uncons(seq)
    except StopIteration:
        return

    buf = [x]
    add = buf.append
    clear = buf.clear

    for y in it:
        if pred(x, y):
            yield tuple(buf)
            clear()
        add(y)
        x = y
    yield tuple(buf)


def _chunks_right(pred, seq):
    buf = []
    add = buf.append
    clear = buf.clear

    for x in seq:
        if pred(x) and buf:
            yield tuple(buf)
            clear()
        add(x)
    yield tuple(buf)


def _chunks_left(pred, seq):
    buf = []
    add = buf.append
    clear = buf.clear

    for x in seq:
        add(x)
        if pred(x) and buf:
            yield tuple(buf)
            clear()
    if buf:
        yield tuple(buf)


def _chunks_split(pred, seq):
    buf = []
    add = buf.append
    clear = buf.clear

    for x in seq:
        if pred(x):
            yield tuple(buf)
            clear()
        else:
            add(x)
    yield tuple(buf)


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
