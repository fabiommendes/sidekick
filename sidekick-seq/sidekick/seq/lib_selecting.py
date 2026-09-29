import itertools
import operator as op
from collections import deque
from typing import Callable, Iterable, TYPE_CHECKING
from itertools import filterfalse, dropwhile, takewhile, islice

from .iter import iter
from .lib_basic import uncons
from .util import toolz, to_callable, c, b, a, Pred, NOT_GIVEN

if TYPE_CHECKING:
    from sidekick import api as sk  # noqa: F401
    from sidekick.api import X, Y  # noqa: F401

_filter = filter
_snd = op.itemgetter(1)


def filter(pred: Pred[a], seq: Iterable[a]) -> iter[a]:
    """
    Return an iterator yielding those items of iterable for which function(item)
    is true.

    Behaves similarly to Python's builtin filter, but accepts anything
    convertible to callable using :func:`sidekick.functions.to_callable` as predicate
    and return sidekick iterators instead of regular ones.


    filter(pred, seq) ==> seq[a], seq[b], seq[c], ...

    in which a, b, c, ... are the indexes in which pred(seq[i]) == True.

    Examples:
        >>> sk.filter((X % 2), range(10))
        sk.iter([1, 3, 5, 7, 9])

    See also:
        :func:`remove`
        :func:`separate`
    """
    pred = to_callable(pred)
    return iter(_filter(pred, seq))


def remove(pred: Pred[a], seq: Iterable[a]) -> iter[a]:
    """
    Opposite of filter. Return those items of sequence for which pred(item)
    is False

    Examples:
        >>> sk.remove((X < 5), range(10))
        sk.iter([5, 6, 7, 8, 9])

    See also:
        :func:`filter`.
        :func:`separate`
    """
    return iter(filterfalse(to_callable(pred), seq))


def separate(
    pred: Pred[a], seq: Iterable[a], /, *, consume: bool = False
) -> tuple[iter[a], iter[a]]:
    """
    Split sequence it two. The first consists of items that pass the
    predicate and the second of those items that don't.

    Similar to (filter(pred, seq), filter(!pred, seq)), but only evaluate
    the predicate once per item.

    Args:
        pred:
            Predicate function
        seq:
            Iterable of items that should be separated.
        consume:
            If given, fully consume the iterator and return two lists. This is
            faster than separating and then converting each element to a list.

    Examples:
        >>> sk.separate((X % 2), [1, 2, 3, 4, 5])
        (sk.iter([1, 3, 5]), sk.iter([2, 4]))

    See also:
        :func:`filter`
        :func:`remove`
    """
    pred = to_callable(pred)
    if consume:
        ok_lst = list[a]()
        bad_lst = list[a]()
        add_a = ok_lst.append
        add_b = bad_lst.append
        for x in seq:
            (add_a if pred(x) else add_b)(x)
        return iter(ok_lst), iter(bad_lst)
    else:
        seq1, seq2 = itertools.tee((x, pred(x)) for x in seq)
        return (
            iter(x for x, keep in seq1 if keep),
            iter(x for x, keep in seq2 if not keep),
        )


def drop(key: int | Pred[a], seq: Iterable[a], /) -> iter[a]:
    """
    Drop items from the start of iterable.

    If key is a number, drop at most this number of items for iterator. If it
    is a predicate, drop items while key(item) is true.

        drop(key, seq) ==> seq[n], seq[n + 1], ...

    n is either equal to key, if its a number or is the index for the first
    item in which key(item) is false.

    Examples:
        >>> sk.drop((X < 5), range(10))
        sk.iter([5, 6, 7, 8, 9])

        >>> sk.drop(3, range(10))
        sk.iter([3, 4, 5, 6, 7, 8, ...])

    See also:
        :func:`take`
        :func:`rdrop`
        :func:`strip`
    """
    if isinstance(key, int):
        return iter(islice(seq, key, None))
    else:
        return iter(dropwhile(to_callable(key), seq))


def rdrop(key: int | Pred[a], seq: Iterable[a], /) -> iter[a]:
    """
    Drop items from the end of iterable.

    Examples:
        >>> sk.rdrop(2, [1, 2, 3, 4])
        sk.iter([1, 2])

        >>> sk.rdrop((X >= 2), [1, 2, 4, 1, 2, 4])
        sk.iter([1, 2, 4, 1])

    See also:
        :func:`drop`
        :func:`rtake`
    """
    return iter(_rdrop(key, iter(seq)))


def _rdrop(key, seq):
    if isinstance(key, int):
        n: int = key
        out = deque(take(n, seq), n)
        for x in seq:
            yield out[0]
            out.append(x)

    else:
        pending = []
        wait = pending.append
        clear = pending.clear

        for x in seq:
            if key(x):
                wait(x)
            else:
                yield from pending
                yield x
                clear()


def drop_at(indices: set[a] | Iterable[a], seq: Iterable[a], /) -> iter[a]:
    """
    Drop all elements in the given positions.

    Indices can be a set or a (possibly infinite) **sorted** iterable.

    Examples:
        >>> "".join(drop_at({1, 2, 4, 10}, "foobar"))
        'fbr'

    See also:
        :func:`drop`
        :func:`take_at`
    """
    if isinstance(indices, set):
        return iter(x for i, x in enumerate(seq) if i not in indices)
    return iter(_drop_at_lazy(iter(indices), iter(seq)))


def _drop_at_lazy(indices, seq):
    idx = next(indices, None)
    if idx is None:
        return
    for i, x in enumerate(seq):
        if i == idx:
            try:
                idx = next(indices)
            except StopIteration:
                break
        elif i > idx:
            raise ValueError("non-decreasing sequence of indices")
        else:
            yield x
    yield from seq


def take(key: int | Pred[a], seq: Iterable[a], /) -> iter[a]:
    """
    Return the first entries iterable.

    If key is a number, return at most this number of items for iterator. If it
    is a predicate, return items while key(item) is true.

        take(key, seq) ==> seq[0], seq[1], ..., seq[n - 1]

    n is either equal to key, if its a number or is the index for the first
    item in which key(item) is false.

    This function is a complement of :func:`drop`. Given two identical iterators
    ``seq1`` and ``seq2``, ``take(key, seq1) + drop(key, seq2)`` yields the
    original sequence of items.

    Examples:
        >>> sk.take((X < 5), range(10))
        sk.iter([0, 1, 2, 3, 4])

    See also:
        :func:`drop`
    """
    if isinstance(key, int):
        return iter(islice(seq, key))
    else:
        return iter(takewhile(to_callable(key), seq))


def rtake(key: int | Pred[a], seq: Iterable[a], /) -> iter[a]:
    """
    Return the last entries iterable.

    Examples:
        >>> sk.rtake(2, [1, 2, 3, 4])
        sk.iter([3, 4])

        >>> sk.rtake((X >= 2), [1, 2, 4, 1, 2, 4])
        sk.iter([2, 4])

    See also:
        :func:`take`
        :func:`rdrop`
    """
    return iter(_rtake(key, iter(seq)))


def _rtake(key, seq):
    if isinstance(key, int):
        yield from deque(seq, key)
    else:
        tail = []
        wait = tail.append
        clear = tail.clear

        for x in seq:
            if key(x):
                wait(x)
            else:
                clear()
        yield from tail


def take_at(indices: set[a] | Iterable[a], seq: Iterable[a], /) -> iter[a]:
    """
    Return a sequence with values in the positions specified by indices.

    Indices must be any non-decreasing (and possibly infinite) sequence.

    If you want to pass a list of non-ordered indices, use the builtin sorted()
    function before sending to this function. It raises a ValueError if a
    non-decreasing sequence is detected.

    Examples:
        >>> ''.join(take_at([0, 1, 1, 1, 4, 5, 10], "foo bar baz"))
        'fooobaz'

    See also:
        :func:`get`
        :func:`drop_at`
    """
    return iter(_take_at(iter(indices), seq))


def _take_at(indices, seq):
    idx = next(indices, None)
    if idx is None:
        return
    for i, x in enumerate(seq):
        if i == idx:
            yield x
            for idx in indices:
                if i == idx:
                    yield x
                else:
                    break
        elif i > idx:
            raise ValueError("non-decreasing sequence of indices")


def strip(
    prefix: Iterable[a],
    seq: Iterable[a],
    partial: bool = False,
    cmp: Callable[[a, a], bool] = NOT_GIVEN,
) -> iter[a]:
    """
    If seq starts with the same elements as in prefix, remove them from
    result.

    Args:
        prefix:
            Prefix sequence to possibly removed from seq.
        seq:
            Sequence of input elements.
        partial:
            If True, remove partial matches with prefix.
        cmp:
            If given, uses as a comparison function between elements of prefix
            and sequence. It removes elements that cmp(x, y) returns True.

    Examples:
        >>> ''.join(strip("ab", "abcd"))
        'cd'
        >>> strip(sk.repeat(3), range(6), partial=True, cmp=(X > Y))
        sk.iter([3, 4, 5])
    """
    if partial:
        cmp = NOT_GIVEN.resolve(cmp, op.eq)
        return iter(_strip_partial(iter(prefix), iter(seq), cmp=cmp))
    elif cmp is NOT_GIVEN:
        return iter(_strip_full(tuple(prefix), iter(seq)))
    else:
        return iter(_strip_full_cmp(tuple(prefix), iter(seq), cmp))


def _strip_partial(prefix, seq, cmp):
    for x, y in zip(prefix, seq):
        if cmp(x, y):
            continue
        yield y
        break
    yield from seq


def _strip_full(prefix, seq):
    elems = tuple(islice(seq, len(prefix)))
    if elems == prefix:
        yield from seq
    else:
        yield from elems
        yield from seq


def _strip_full_cmp(prefix, seq, cmp):
    elems = tuple(islice(seq, len(prefix)))
    if all(cmp(x, y) for x, y in zip(elems, seq)):
        yield from seq
    else:
        yield from elems
        yield from seq


def unique(
    seq: Iterable[a],
    /,
    *,
    key: Callable[[a], b] = NOT_GIVEN,
    exclude: Iterable[a] = (),
    slow: bool = False,
) -> iter[a]:
    """
    Returns the given sequence with duplicates removed.

    Preserves order. If key is supplied map distinguishes values by comparing
    their keys.

    Args:
        seq:
            Iterable of objects.
        key:
            Optional key function. It will return only the first value that
            evaluate to a unique key by the key function.
        exclude:
            Optional sequence of keys to exclude from seq
        slow:
            If True, allows the slow path (i.e., store seen elements in a list,
            instead of a hash).

    Examples:
        >>> sk.unique(range(10), key=(X % 5))
        sk.iter([0, 1, 2, 3, 4])

    Note:
        Elements of a sequence or their keys should be hashable, otherwise it
        must use a slow path.

    See also:
        :func:`dedupe`
    """
    return iter(_unique(seq, key, exclude, slow))


def _unique(seq, key, exclude, slow):
    pred = to_callable(key)
    if slow:
        seen = [*exclude] if key is None else [*map(pred, exclude)]
        add = seen.append
    else:
        seen = {*exclude} if key is None else {*map(key, exclude)}
        add = seen.add

    if key is NOT_GIVEN:
        for x in seq:
            if x not in seen:
                add(x)
                yield x
    else:
        for x in seq:
            test = key(x)
            if test not in seen:
                add(test)
                yield x


def dedupe(seq: Iterable[a], *, key: Callable[[a], b] = NOT_GIVEN) -> iter[a]:
    """
    Remove duplicates of successive elements.

    Args:
        seq:
            Iterable of objects.
        key:
            Optional key function. It will yield successive values if their
            keys are different.

    See also:
        :func:`unique`
    """
    return iter(_dedupe(seq, key))


def _dedupe(seq, key):
    try:
        x, rest = uncons(seq)
        yield x
    except ValueError:
        return

    if key is NOT_GIVEN:
        for y in rest:
            if x != y:
                yield y
            x = y
    else:
        key = to_callable(key)
        key_x = key(x)
        for y in rest:
            key_y = key(y)
            if key_x != key_y:
                yield y
            key_x = key_y


def converge(pred: Pred[a], seq: Iterable[a], /) -> iter[a]:
    """
    Test convergence with the predicate function by passing the last two items
    of sequence. If pred(penultimate, last) returns True, stop iteration.

    Examples:
        We start with a converging (possibly infinite) sequence and an explicit
        criteria.

        >>> seq = sk.iterate((X / 2), 1.0)
        >>> conv = lambda x, y: abs(x - y) < 0.01

        Run it until convergence

        >>> it = sk.converge(conv, seq); it
        sk.iter([1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, ...])
        >>> sum(it)
        1.9921875
    """
    return iter(_converge(pred, iter(seq)))


def _converge(pred, seq):
    try:
        x = next(seq)
    except StopIteration:
        return

    yield x
    for y in seq:
        yield y
        if pred(x, y):
            break
        x = y


def random_sample(prob: float, seq: Iterable[a], *, random_state=None) -> Iterable[a]:
    """
    Choose with probability ``prob`` each element of seq to include in the
    output sequence.
    """
    return toolz.random_sample(prob, seq, random_state=random_state)


def indexed(
    transform: Callable[
        [Callable[[tuple[int, a]], c], Iterable[tuple[int, a]]], Iterable[tuple[int, a]]
    ],
    func: Callable[[a], c],
    seq: Iterable[a],
    /,
    *,
    start: int = 0,
) -> Iterable[tuple[int, a]]:
    """
    Take a function that receives a predicate with a sequence and transform it
    to operate on an indexed sequence.

    This is mostly useful for functions like filter, take, drop, etc that loose
    indexing information after the transform.

    Examples:
        >>> seq = [5, 10, 2, 3, 25, 42]
        >>> indexed(filter, (X >= 10), seq)
        sk.iter([(1, 10), (4, 25), (5, 42)])
    """
    func = to_callable(func)
    func_: Callable[[tuple[int, a]], c] = lambda x: func(_snd(x))
    return transform(func_, enumerate(seq, start=start))
