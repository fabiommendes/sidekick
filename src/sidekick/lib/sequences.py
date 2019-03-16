import itertools
from collections import deque
from collections.abc import Iterator

import toolz

from ..core import fn, extract_function, extract_predicate_function
from ..core.fn import Fn1, Fn1_, Fn2, Fn2_, Fn3_, Fn2P

NOT_GIVEN = object()

# Cached functions
_tee = itertools.tee
_islice = itertools.islice
_chain = itertools.chain
_takewhile = itertools.takewhile
_dropwhile = itertools.dropwhile
_groupby = itertools.groupby
_count = itertools.count
_map = map
_filter = filter

#
# Create sequences
#
repeat = fn(itertools.repeat)
numbers = fn(itertools.count)
enumerate = fn(enumerate, doc='''
Iterator for (index, value) pairs of iterable. An fn-enabled version of 
Python's builtin ``enumerate`` function.''')
cycle = fn(itertools.cycle)
iterate = Fn2(toolz.iterate)


@fn
def repeatedly(*args, **kwargs):
    """
    Make n or infinite calls to a function.

    Can be called with function or a tuple of (function, repetitions) as the
    first argument. Additional arguments are passed to the function at each
    call.
    """
    f, *args = args
    f, n = f if isinstance(f, tuple) else (f, None)
    seq = _count() if n is None else range(n)
    if not (args or kwargs):
        return (f() for _ in seq)
    else:
        return (f(*args, **kwargs) for _ in seq)


#
# Extract items from sequence
#
drop = Fn2(toolz.drop)
take = Fn2(toolz.take)
take_nth = Fn2(toolz.take_nth)
first = Fn1(toolz.first)
second = Fn1(toolz.second)
nth = Fn2(toolz.nth)
get = Fn2_(toolz.get)
last = Fn1(toolz.last)
tail = Fn2(toolz.tail)
peek = fn(toolz.peek)


@fn
def but_last(seq):
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


@Fn1
def rest(seq):
    """
    Skips first item in the sequence, returning iterator starting just after it.
    A shortcut for drop(1, seq).
    """
    return _islice(seq, 1, None)


@Fn1_
def consume(seq, last=None):
    """
    Consume iterator for its side-effects and return last value or None.
    """
    for last in seq:
        pass
    return last


#
# Sequence properties and predicates
#
count = Fn1(toolz.count)
count_by = Fn2(toolz.countby)
frequencies = fn(toolz.frequencies)  # Do we need this w/ collections.Counter
is_distinct = fn(toolz.isdistinct)  # maybe move to predicate?
is_iterable = fn(toolz.isiterable)


@Fn2
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
cons = Fn2(toolz.cons)
interleave = fn(toolz.interleave)
interpose = Fn2(toolz.interpose)
mapcat = Fn2(toolz.mapcat)


@Fn2
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
map = Fn2(_map)
accumulate = Fn2_(toolz.accumulate)


@Fn2
def order_by(key, sequence):
    """
    Order sequence by the given function.
    """
    key = extract_function(key)
    return sorted(sequence, key=key)


#
# Filtering
#
take_while = Fn2P(itertools.takewhile)
drop_while = Fn2P(itertools.dropwhile)
unique = fn(toolz.unique)
remove = Fn2P(toolz.remove)
filter = Fn2P(_filter)
random_sample = Fn2_(toolz.random_sample)
top_k = Fn2_(toolz.topk)


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
        pred = extract_function(key)
        for x in seq:
            key = pred(x)
            if key not in seen:
                seen.add(key)
                yield x


@fn
def keep(f, seq=None):
    """
    A shortcut function that filters and keeps the truthy elements.

        keep(f, seq)  <==> filter(bool, map(f, seq))
        keep(f)       <==> lambda seq: keep(f, seq)
        keep(seq)     <==> filter(bool, seq)
    """
    if not (f):
        return keep(bool, seq)
    return _filter(bool, _map(extract_predicate_function(f), seq))


@Fn2_
def without(items, seq):
    """
    Returns sequence without items specified. Preserves order.

    Hint: pass items as a set for greater performance.

    >>> list(without({2, 3, 5, 7}, range(10)))
    [0, 1, 4, 6, 8, 9]
    """
    for x in seq:
        if x not in items:
            yield x


#
# Partitioning
#
partition = Fn2_(toolz.partition)
partition_by = Fn2_(toolz.partitionby)
partition_all = Fn2(toolz.partition_all)
sliding_window = Fn2(toolz.sliding_window)
reduce_by = Fn3_(toolz.reduceby, doc='''
Perform a simultaneous group_by and reduction.

The computation ``result = reduce_by(key, binop, seq, init)`` is equivalent to 
the following::

    def reduction(group):           
        return reduce(binop, group, init)

    groups = groupby(key, seq)                                  # doctest: +SKIP
    result = value_map(reduction, groups)                       # doctest: +SKIP

The former does not build the intermediate groups, allowing it to operate in 
much less space.  This makes it suitable for larger datasets that do not fit 
comfortably in memory

The ``init`` keyword argument is the default initialization of the
reduction.  This can be either a constant value like ``0`` or a callable
like ``lambda : 0`` as might be used in ``defaultdict``.

Usage:

    >>> from operator import add
    >>> is_even = (lambda x: x % 2 == 0)
    >>> reduce_by(iseven, add, [1, 2, 3, 4, 5])
    {False: 9, True: 6}
''')
groupby = Fn2(toolz.groupby)


@Fn2P
def split(pred, seq):
    """
    Splits sequence items which pass predicate from the ones that don’t,
    essentially returning a tuple filter(pred, seq), remove(pred, seq).
    """
    a, b = _tee((pred(x), x) for x in seq)
    return (x for pred, x in a if pred), (x for pred, x in b if not pred)


@Fn2
def split_at(n, seq):
    """
    Splits sequence at given position, returning a tuple of its start and tail.
    """
    a, b = _tee(seq)
    return _islice(a, n), _islice(b, n, None)


@Fn2P
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


@Fn1
def pairwise(seq):
    """
    Yields pairs of items in seq like (item0, item1), (item1, item2), ....
    """
    a, b = _tee(seq)
    next(b, None)
    return zip(a, b)


@Fn2_
def reductions(f, seq, acc=NOT_GIVEN):
    """
    Returns a sequence of the intermediate values of the reduction of seq by f.

    In other words it yields a sequence like:

        reduce(f, seq[:1], [acc]), reduce(f, seq[:2], [acc]), ...
    """
    seq = iter(seq)
    f = extract_function(f)
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
pluck = Fn2_(toolz.pluck)
merge_sorted = fn(toolz.merge_sorted)


@Fn2
def is_equal(seq1, seq2):
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


def zipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **left** of the given sequences.
    """
    return fn(lambda seq: zip(seq, *seqs))


def rzipper(*seqs):
    """
    Return a function that takes a sequence and zip it with the arguments.

    The input sequence is zipped to the **right** of the given sequences.
    """
    return fn(lambda seq: zip(*(seqs + (seq,))))


# noinspection PyIncorrectDocstring
def zip_with(funcs, *seqs):
    """
    Zip a iterable of functions with one or more iterable of arguments and

    >>> incr = lambda n: lambda x: x + n
    >>> list(zipper([incr(1), incr(2), incr(3)], [1, 2, 3]))
    [2, 4, 6]

    Args:
        funcs (iterable):
            Functions
        seqs (iterable arguments):
            Values that will be passed as arguments to functions. If seq is larger than
            funcs, the remaining values are passed as is.

    Returns:
        An iterator.
    """
    to_func = extract_function
    it = zip(*seqs)
    yield from (to_func(f)(*args) for f, args in zip(funcs, it))


@Fn2
def transform(funcs, seq):
    """
    Similar to zip_with, but accepts only single argument functions. If the
    sequence of arguments is larger than the sequence of functions, the
    remaining values are returned unchanged.

    >>> incr = lambda n: lambda x: x + n
    >>> list(zipper([incr(1), incr(2), incr(3)], [1, 2, 3, 4, 5]))
    [2, 4, 6, 4, 5]

    Args:
        funcs (iterable):
            An iterable of functions
        seq (iterable):
            The respective function arguments

    Returns:
        An iterator.
    """
    to_func = extract_function
    it = iter(seq)
    yield from (to_func(f)(x) for f, x in zip(funcs, it))
    yield from it


# noinspection PyIncorrectDocstring
def transform_map(funcs, mapping, _as_func=extract_function):
    """
    Similar to transform, but instead of receiving a sequence of values, it
    expects maps. The function than apply each function in the map of functions
    to their corresponding values in the second argument.

    >>> transform_map({'foo': str.lower, 'ham': str.upper},
    ...           {'foo': 'Bar', 'ham': 'Spam', 'baz': 'Other'})
    {'foo': 'bar', 'ham': 'SPAM', 'baz': 'Other'}

    Args:
        funcs (Mapping):
            A mapping from arbitrary keys to functions.
        mapping (Mapping):
            Any mapping.

    Returns:
        dict
    """
    result = dict(mapping)
    for k, f in funcs:
        try:
            result[k] = _as_func(f)(result[k])
        except KeyError:
            pass
    return result


#
# Nested structures
#
SEQ_TYPES = (list, tuple, Iterator)

is_seqcont = (lambda x: isinstance(x, SEQ_TYPES))


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
    follow = extract_predicate_function(follow)
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
    follow = extract_predicate_function(follow)
    q = deque([[root]])
    while q:
        node_iter = iter(q.pop())
        for sub in node_iter:
            yield sub
            if follow(sub):
                q.append(node_iter)
                q.append(children(sub))
                break
