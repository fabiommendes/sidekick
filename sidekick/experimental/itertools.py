import operator
from itertools import chain, cycle, islice, tee

from .._toolz import take, first
from ..core import fn, Pred, Seq, SeqT, extract_function, NOT_GIVEN
from ..itertools import uncons, unique, Func, cons, reduce


@fn.curry(2)
def split_prefix(pred: Pred, seq: SeqT) -> (SeqT, SeqT):
    """
    Returns tuple (a, b) in which ``a`` is the longest prefix (possibly empty) of
    elements that satisfy predicate and ``b`` is the remainder of sequence.

    Examples:
        >>> a, b = split_prefix((X <= 5), range(1, 11))
        >>> list(a), list(b)
        ([1, 2, 3, 4, 5], [6, 7, 8, 9, 10])
    """
    seq = iter(seq)
    pred = extract_function(pred)
    pending_left = []
    pending_right = []

    def head():
        for x in seq:
            if pred(x):
                yield x
            else:
                pending_right.append(x)
                break
        yield from pending_left
        pending_left.clear()

    def tail():
        if not pending_right:
            pending_left.extend(head_iter)
        yield from pending_right
        yield from seq

    head_iter, tail_iter = head(), tail()
    return head_iter, tail_iter


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
    elems = tuple(take(len(prefix), seq))
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
        return first(i for i, y in enumerate(seq) if x == y)
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


def partition_eq(eq, seq):
    """
    Group successive elements that compare positively by the equality function.

    Examples:
        >>> partition_eq(lambda x, y: abs(x - y) == 1, [1, 2, 3, 5, 6, 7]) | L
        [(1, 2, 3), (5, 6, 7)]
    """
    try:
        x, seq = uncons(seq)
    except ValueError:
        return iter(())

    while True:
        term = [x]
        for y in seq:
            if eq(x, y):
                term.append(y)
            else:
                yield tuple(term)
                x = y
                break
            x = y
        else:
            break
    if term:
        yield tuple(term)


def intersect(*seqs, eq=operator.eq):
    """
    >>> intersect([1, 2, 3], [3, 4, 5]) | L
    [3]

    >>> intersect([1, 2, 3], [3, 4, 5], eq=lambda x, y: abs(x - y) <= 1) | L
    [2, 3]
    """

    def reducer(a, b):
        for x in a:
            b, ys = tee(b)
            if any(x for y in ys if eq(x, y)):
                yield x

    return reduce(reducer, seqs)


def list_or_set(seq):
    seq = list(seq)
    try:
        return set(seq)
    except TypeError:
        return seq


def _intersect(a, b):
    b = list(b)


def _intersect_both(a, b):
    ...


def _intersect_key(a, b, key):
    ...


def unique_from(*seqs, key=None, cycle=False):
    """
    >>> unique_from([1, 2, 3], [5, 6, 7], key=(X % 3)) | L
    [1, 2, 3]

    >>> unique_from([1, 2, 3], [5, 6, 7], key=(X % 3), cycle=True) | L
    [1, 5, 6]
    """
    data = round_robin(*seqs) if cycle else chain(*seqs)
    return unique(data, key=key)


def round_robin(*seqs):
    """
    >>> ''.join(round_robin('abc', '123', ',,'))
    'a1,b2,c3'
    """
    n_active = len(seqs)
    nexts = cycle(iter(it).__next__ for it in seqs)
    while n_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            n_active -= 1
            nexts = cycle(islice(nexts, n_active))


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
    seq, disposable = tee(seq)
    func = extract_function(func)
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
    return x, cons(x, seq)
