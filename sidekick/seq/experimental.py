import itertools
import operator
import typing
from collections import deque
from functools import reduce, partial
from operator import itemgetter

import toolz

from ..functions import fn, to_callable
from ..typing import Pred, T, NOT_GIVEN
from ..typing import Seq, Func

identity = lambda x: x
_first_item = itemgetter(0)
_second_item = itemgetter(1)
_map = lambda pred: lambda seq: map(pred, seq)


@fn.curry(2)
def random_sample(prob: float, seq: Seq, *, random_state=None) -> Seq:
    """
    Choose with probability ``prob`` if each element of seq will be included in
    the output sequence.

    See Also:
        :func:`tools.random_sample`.
    """
    return toolz.random_sample(prob, seq, random_state=random_state)


@fn.curry(2)
def select_positions(indices: Seq, seq: Seq, *, silent=False) -> Seq:
    """
    Return a sequence with values in the positions specified by indices.

    Indices must be any non-decreasing increasing sequence. If you have a list
    of non-ordered indices, use the builtin sorted() function.

    Use get() if you want access random positions. Differently from get(), this
    function accepts infinite iterators as indices.

    Examples:
        >>> "".join(select_positions([0, 1, 1, 1, 4, 5, 10], "foo bar baz"))
        'fooobaz'

    See Also:
        get
        drop_positions
    """
    indices = iter(indices)
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
        elif i > idx and not silent:
            raise ValueError("non-decreasing sequence of indices")


@fn.curry(2)
def drop_positions(indices: Seq, seq: Seq, *, silent=False) -> Seq:
    """
    Drop all elements in the given positions. Similarly to :func:select_positions`,
    it requires a (possibly infinite) sorted sequence of indices.

    Use ``exclude(fn(set(indices)), seq)`` if the indices are a finite sequence
    in random order.

    Examples:
        >>> "".join(drop_positions([1, 2, 4, 10], "foobar"))
        'fbr'

    See Also:
        exclude
        select_positions
    """
    indices = iter(indices)
    seq = iter(seq)
    idx = next(indices, None)
    if idx is None:
        return
    for i, x in enumerate(seq):
        if i == idx:
            try:
                idx = next(indices)
            except StopIteration:
                break
        elif i > idx and not silent:
            raise ValueError("non-decreasing sequence of indices")
        else:
            yield x
    yield from seq


@fn.curry(2)
def first_repeated(key: Func, seq: Seq):
    """
    Return the index and value of first repeated element in sequence.

    Raises a ValueError if no repeated element is found.

    Examples:
        >>> first_repeated(None, [1, 2, 3, 1])
        (3, 1)
    """

    key = to_callable(key)
    seen = set()
    add = seen.add
    for i, x in enumerate(seq):
        tag = key(x)
        if tag in seen:
            return i, x
        add(tag)
    raise ValueError("no repeated element in sequence")


@fn.curry(2)
def get(idx, seq: Seq, **kwargs):
    """
    Get element (or elements, if idx is a list) in a sequence or dict.

    Examples:
        >>> get([3, 2, 1], [2, 3, 5, 7, 11, 13, 17])
        (7, 5, 3)
    """
    return toolz.get(idx, seq, **kwargs)


@fn.curry(2)
def take_nth(n: int, seq: Seq) -> Seq:
    """
    Return every nth item in sequence.

    Examples:
        >>> take_nth(2, [1, 2, 3, 4, 5]) | L
        [1, 3, 5]

    See Also:
        take
    """
    return toolz.take_nth(n, seq)


_map = map
_enumerate = enumerate


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
    pred = to_callable(pred)
    pred_ = lambda x: pred(_second_item(x))
    return selector(pred_, enumerate(seq, start))


def zipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **left** of the given sequences.

    Examples:
        >>> zip10 = zipper(range(1, 11))
        >>> dict(zip10('abc'))
        {'a': 1, 'b': 2, 'c': 3}
    """
    seqs = tuple(seqs)
    return fn(lambda seq: zip(seq, *seqs))


def rzipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **right** of the given sequences.

    Examples:
        >>> enumerate10 = rzipper(range(1, 11))
        >>> dict(enumerate10('abc'))
        {1: 'a', 2: 'b', 3: 'c'}
    """
    seqs = tuple(seqs)
    return fn(lambda seq: zip(*seqs, seq))


@fn.curry(2)
def strip(prefix, seq):
    """
    If seq starts with the same elements as in prefix, remove them from
    result.

    Examples:
        >>> ''.join(strip("ab", "abcd"))
        'cd'
    """
    seq = iter(seq)
    prefix = tuple(prefix)
    elems = tuple(toolz.take(len(prefix), seq))
    if elems == prefix:
        yield from seq
    else:
        yield from elems
        yield from seq


@fn
def inits(seq: Seq) -> Seq:
    """
    Return all sub-sequences at beginning of seq.

    Examples:
        >>> inits('abc') | L
        [(), ('a',), ('a', 'b'), ('a', 'b', 'c')]

        We can obtain the ending sub-sequences using the recipe. Notice that
        this consumes the whole iterator and store its contents in memory.

        >>> ends = lambda s: reversed([tuple(x)[::-1]
        ...                            for x in inits(reversed(s))])
        >>> ends('abc') | L
        [('a', 'b', 'c'), ('b', 'c'), ('c',), ()]

    """
    acc = ()
    yield acc
    for x in seq:
        acc = (*acc, x)
        yield acc


def lookup(key, seq, default=NOT_GIVEN):
    for k, v in seq:
        if k == key:
            return v
    if default is NOT_GIVEN:
        raise KeyError(key)
    return default


def lookup_by(pred, seq, default=NOT_GIVEN):
    for x in seq:
        if pred(x):
            return x
    if default is NOT_GIVEN:
        raise KeyError("no elements satisfy predicate")
    return default


def index(x, seq):
    try:
        return toolz.first(i for i, y in enumerate(seq) if x == y)
    except ValueError:
        raise IndexError("element not found in sequence")


def indexes(x, seq):
    return tuple(i for i, y in enumerate(seq) if x == y)


def exclude_n(n, pred, seq):
    if n >= 0:
        for x in seq:
            if pred(x):
                n -= 1
                if n <= 0:
                    break
            else:
                yield x

    yield from seq


def intersect(*seqs, eq=operator.eq):
    """
    >>> intersect([1, 2, 3], [3, 4, 5]) | L
    [3]

    >>> intersect([1, 2, 3], [3, 4, 5], eq=lambda x, y: abs(x - y) <= 1) | L
    [2, 3]
    """

    def reducer(a, b):
        for x in a:
            b, ys = itertools.tee(b)
            if any(x for y in ys if eq(x, y)):
                yield x

    return reduce(reducer, seqs)


def list_or_set(seq):
    seq = list(seq)
    try:
        return set(seq)
    except TypeError:
        return seq


def round_robin(*seqs):
    """
    >>> ''.join(round_robin('abc', '123', ',,'))
    'a1,b2,c3'
    """
    n_active = len(seqs)
    nexts = itertools.cycle(iter(it).__next__ for it in seqs)
    while n_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            n_active -= 1
            nexts = itertools.cycle(itertools.islice(nexts, n_active))


def alternate(*seqs):
    """
    >>> ''.join(alternate('abc', '123', ',,'))
    'a1,b2,'
    """
    nexts = [iter(it).__next__ for it in seqs]
    buffer = []
    append = buffer.append

    while True:
        buffer.clear()
        try:
            for f in nexts:
                append(f())
            yield from buffer
        except StopIteration:
            break


#
# Haskell
#
# span -> prefix
# break -> prefix(~pred)
# group -> partition_by(identity)
# tails -> not feasible
@fn.curry(2)
def peek_with(func: Func, seq: Seq) -> (object, Seq):
    """
    Apply function to seq and return tuple with (result, seq).

    The resulting sequence is not consumed and is duplicated with :func:`tee`
    when necessary.

    This function is useful to retrieve information about sequence from
    functions that would consume or partially consume iterator.

    >>> size, seq = peek_with(sum, range(5))
    >>> size, list(seq)
    (10, [0, 1, 2, 3, 4])
    """
    seq, disposable = itertools.tee(seq)
    func = to_callable(func)
    return func(disposable), seq


@fn
def peek(seq: Seq, default=NOT_GIVEN) -> (object, Seq):
    """
    Same as peek_with(first).

    Peek first element of sequence and return (first, seq).

    >>> fst, seq = peek(range(5))
    >>> fst, list(seq)
    (0, [0, 1, 2, 3, 4])
    """
    try:
        x, seq = uncons(seq)
    except ValueError:
        if default is NOT_GIVEN:
            raise
        return default, iter(())
    return x, toolz.cons(x, seq)


@fn
def peek(seq: Seq) -> typing.Tuple[object, Seq]:
    """
    Retrieve the next element and retrieve a tuple of (elem, seq).

    The resulting sequence *includes* the retrieved element.

    Examples:
        >>> seq = (x*x for x in range(1, 6))
        >>> x, seq = peek(seq)
        >>> x, list(seq)
        (1, [1, 4, 9, 16, 25])
    """
    return toolz.peek(seq)


def scan_together_alt(seq, kwargs):
    # Alternative implementation that yield a dict of iterators instead of an
    # iterator of dicts
    seq = iter(seq)

    def yield_acc(func, pop, y):
        try:
            x = pop()
        except IndexError:
            push(next(seq))
            x = pop()
        return func(x, y)

    res = {}
    deques = []

    def push(x):
        for do in deques:
            do(x)

    for key, (func, x0) in kwargs.items():
        Q = deque()
        deques.append(Q.append)
        res[key] = iterate(partial(yield_acc, func, Q.popleft), x0)
    return res
