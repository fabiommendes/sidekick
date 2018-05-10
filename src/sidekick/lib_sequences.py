import itertools
from collections import deque

from .fn import fn
from .lib_utils import (
    toolz, is_seqcont, fn1, fn2, fn2_opt, fn2_key, fn2_predicate, fn2_function, fn3_opt,
)
from sidekick.extended_semantics import as_func, as_predicate_func

NOT_GIVEN = object()

# Cached functions
_tee = itertools.tee
_islice = itertools.islice
_chain = itertools.chain
_takewhile = itertools.takewhile
_dropwhile = itertools.dropwhile
_groupby = itertools.groupby
_map = map
_filter = filter

#
# Create sequences
#
repeat = fn(itertools.repeat)
count = fn(itertools.count)
enumerate = fn(enumerate, doc='''
Iterator for (index, value) pairs of iterable. An fn-enabled version of 
Python's builtin ``enumerate`` function.''')
cycle = fn(itertools.cycle)
iterate = fn2_function(toolz.iterate)


@fn
def repeatedly(f, n=None):
    """
    Make n or infinite calls to a function.
    """
    seq = repeat(None) if n is None else repeat(None, n)
    return (f() for _ in seq)


#
# Item extraction
#
drop = fn2(toolz.drop)
take = fn2(toolz.take)
take_nth = fn2(toolz.take_nth)
first = fn(toolz.first)
second = fn(toolz.second)
nth = fn2(toolz.nth)
get = fn2_opt(toolz.get)
last = fn(toolz.last)
tail = fn2(toolz.tail)
peek = fn(toolz.peek)
getslice = fn(itertools.islice)


@fn
def butlast(seq):
    """
    Returns an iterator of all elements of the sequence but last.
    """
    seq = iter(seq)
    try:
        prev = next(seq)
    except StopIteration:
        return
    else:
        for x in seq:
            yield prev
            prev = x


@fn
def rest(seq):
    """
    Skips first item in the sequence, returning iterator starting just after it.
    A shortcut for drop(1, seq).
    """
    return _islice(seq, 1, None)


@fn
def consume(seq):
    """
    Consume iterator for its side-effects and return last value or None.
    """
    last = None
    for last in seq:
        pass
    return last


#
# Sequence properties
#
count = fn(toolz.count)
countby = fn2_function(toolz.countby)
frequencies = fn(toolz.frequencies)
isdistinct = fn(toolz.isdistinct)  # maybe move to predicate?
isiterable = fn(toolz.isiterable)


@fn2_predicate
def has(pred, seq):
    """
    Return True if sequence has at least one item that satisfy the predicate.
    """
    for x in seq:
        if pred(x):
            return True
    return False


#
# Join sequences
#
cons = fn2(toolz.cons)
interleave = fn(toolz.interleave)
interpose = fn2(toolz.interpose)
mapcat = fn2_function(toolz.mapcat)


@fn2
def append(el, seq):
    """
    Return a new sequence with element el appended to the end.
    """
    yield from seq
    yield el


@fn
def concat(first, *extra):
    """
    Concats several sequence arguments into one and return an iterator.
    """
    if extra:
        return toolz.concatv(first, *extra)
    else:
        return toolz.concat(first)


#
# Transformations
#
map = fn2_function(_map)
accumulate = fn2_opt(toolz.accumulate)


@fn.curried
def order_by(key, sequence):
    """
    Order sequence by the given function.
    """
    key = as_func(key)
    return sorted(sequence, key=key)


#
# Filtering
#
takewhile = fn2_predicate(itertools.takewhile)
dropwhile = fn2_predicate(itertools.dropwhile)
unique = fn(toolz.unique)
remove = fn2_predicate(toolz.remove)
filter = fn2_predicate(_filter)
random_sample = fn2_opt(toolz.random_sample)
topk = fn2_opt(toolz.topk)


@fn
def distinct(seq, key=None):
    """
    Returns the given sequence with duplicates removed.

    Preserves order. If key is supplied map distinguishes values by comparing
    their keys.

    Note:
        Elements of a sequence or their keys should be hashable.
    """
    seen = set()

    if key is None:
        for x in seq:
            if x not in seen:
                seen.add(x)
                yield x
    else:
        pred = as_func(key)
        for x in seq:
            key = pred(x)
            if key not in seen:
                seen.add(key)
                yield x


@fn
def keep(*args):
    """
    A shortcut function that filters and keeps the truthy elements.

        keep(f, seq)  <==> filter(bool, map(f, seq))
        keep(f, None) <==> lambda seq: keep(f, seq)
        keep(seq)     <==> filter(bool, seq)
    """
    if len(args) == 1:
        return _filter(bool, args[0])
    else:
        f, seq = args
        f = as_predicate_func(f)
        if seq is None:
            return lambda seq: keep(f, seq)
        return _filter(bool, _map(f, seq))


@fn2_opt
def without(seq, *items):
    """
    Returns sequence without items specified, preserves order.

    Designed to work with a few items, this allows removing unhashable objects.
    """

    for x in seq:
        if x not in items:
            yield x


#
# Partitioning
#
partition = fn2_opt(toolz.partition)
partitionby = fn2_function(toolz.partitionby)
partition_all = fn2(toolz.partition_all)
sliding_window = fn2(toolz.sliding_window)
reduceby = fn3_opt(toolz.reduceby, doc='''
Perform a simultaneous groupby and reduction.

The computation ``result = reduceby(key, binop, seq, init)`` is equivalent to 
the following::

    def reduction(group):           
        return reduce(binop, group, init)

    groups = groupby(key, seq)                                  # doctest: +SKIP
    result = valmap(reduction, groups)                          # doctest: +SKIP

The former does not build the intermediate groups, allowing it to operate in 
much less space.  This makes it suitable for larger datasets that do not fit 
comfortably in memory

The ``init`` keyword argument is the default initialization of the
reduction.  This can be either a constant value like ``0`` or a callable
like ``lambda : 0`` as might be used in ``defaultdict``.

Usage:

    >>> from operator import add
    >>> iseven = (lambda x: x % 2 == 0)
    >>> reduceby(iseven, add, [1, 2, 3, 4, 5])
    {False: 9, True: 6}
''')
groupby = fn2_key(toolz.groupby)


@fn2_predicate
def split(pred, seq):
    """
    Splits sequence items which pass predicate from the ones that don’t,
    essentially returning a tuple filter(pred, seq), remove(pred, seq).
    """
    a, b = _tee((pred(x), x) for x in seq)
    return (x for pred, x in a if pred), (x for pred, x in b if not pred)


@fn2
def split_at(n, seq):
    """
    Splits sequence at given position, returning a tuple of its start and tail.
    """
    a, b = _tee(seq)
    return _islice(a, n), _islice(b, n, None)


@fn2_predicate
def split_by(pred, seq):
    """
    Splits start of sequence, consisting of items passing predicate, from the
    rest of it. Works similar to takewhile(pred, seq), dropwhile(pred, seq),
    but works with iterator seq correctly.
    """
    a, b = _tee(seq)
    return _takewhile(pred, a), _dropwhile(pred, b)


#
# Special iteration
#
@fn
def with_prev(seq, fill=None):
    """
    Returns an iterator of a pair of each item with one preceding it.

    Yields fill or None as preceding element for first item.
    """

    prev = fill
    for x in seq:
        yield (prev, x)
        prev = x


@fn
def with_next(seq, fill=None):
    """
    Returns an iterator of a pair of each item with one next to it.

    Yields fill or None as next element for last item.
    """
    a, b = _tee(seq)
    next(b, None)
    return zip(a, _chain(b, [fill]))


@fn1
def pairwise(seq):
    """
    Yields pairs of items in seq like (item0, item1), (item1, item2), ....
    """
    a, b = _tee(seq)
    next(b, None)
    return zip(a, b)


@fn2_opt
def reductions(f, seq, acc=NOT_GIVEN):
    """
    Returns a sequence of the intermediate values of the reduction of seq by f.

    In other words it yields a sequence like:

        reduce(f, seq[:1], [acc]), reduce(f, seq[:2], [acc]), ...
    """
    seq = iter(seq)
    f = as_func(f)
    if acc is NOT_GIVEN:
        try:
            acc = next(seq)
        except StopIteration:
            return
        yield acc

    for x in seq:
        acc = f(acc, x)
        yield acc


@fn
def sums(seq, acc=0):
    """
    Return a sequence of partial sums.

    Same as reductions(operator.add, seq[, acc]).
    """

    for x in seq:
        acc = x + acc
        yield acc


#
# Multiple sequences
#
diff = fn(toolz.diff)
join = fn(toolz.join)
pluck = fn2_opt(toolz.pluck)
merge_sorted = fn(toolz.merge_sorted)


@fn.curried
def isequal(seq1, seq2):
    """
    Return True if the two sequences are equal.
    """

    seq1, seq2 = iter(seq1), iter(seq2)

    while True:
        try:
            a = next(seq1)
        except StopIteration:
            return next(seq2, NOT_GIVEN) is NOT_GIVEN
        else:
            if a != next(seq2, NOT_GIVEN):
                return False


def zipwith(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the left of the given sequences.
    """
    return fn(lambda seq: zip(seq, *seqs))


def rzipwith(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the right of the given sequences.
    """
    return fn(lambda seq: zip(*(seqs + (seq,))))


#
# Nested structures
#
@fn
def flatten(seq, follow=is_seqcont):
    """
    Flattens arbitrary nested sequence of values and other sequences.

    Second argument determines whether to unpack each item.

    By default it dives into lists, tuples and iterators, see is_seqcont() for further explanation.
    """

    for x in seq:
        if follow(x):
            yield from flatten(x)
        else:
            yield x


# Taken from funcy
@fn
def tree_leaves(root, follow=is_seqcont, children=iter):
    """
    A way to list or iterate over all the tree leaves.

    Args:
        root:
            The nested data structure
        follow:
            A predicate function that decides if a child node should be
            yielded or if it should follow its children.
        children:
            A function to extract the children from the current node.
    """
    follow = as_predicate_func(follow)
    q = deque([[root]])
    while q:
        node_iter = iter(q.pop())
        for sub in node_iter:
            if follow(sub):
                q.append(node_iter)
                q.append(children(sub))
                break
            else:
                yield sub


# Taken from funcy
@fn
def tree_nodes(root, follow=is_seqcont, children=iter):
    """
    A way to list or iterate over all the tree nodes.

    This iterator includes both leaf nodes and branches.
    """
    follow = as_predicate_func(follow)
    q = deque([[root]])
    while q:
        node_iter = iter(q.pop())
        for sub in node_iter:
            yield sub
            if follow(sub):
                q.append(node_iter)
                q.append(children(sub))
                break
