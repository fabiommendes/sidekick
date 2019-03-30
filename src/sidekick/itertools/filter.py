import itertools

import typing

from ..core import fn, extract_function, Func, Pred, Seq

try:
    import cytoolz as toolz
except ImportError:
    import toolz

_filter = filter

__all__ = [
    # Filtering
    *["drop_while", "random_sample", "remove", "take_while", "top_k",
      "unique", "until_convergence", "without", "without_idx"],

    # Extracting items
    *["but_last", "consume", "drop", "get", "last", "nth", "peek", "tail",
      "take", "take_nth"],
]


#
# Filtering functions
#
@fn.annotate(2)
def drop_while(pred: Pred, seq: Seq) -> Seq:
    """
    Drop items from the iterable while predicate(item) is true.
    Afterwards, return every element until the iterable is exhausted.

    drop_while(pred, seq) ==> seq[n], seq[n + 1], ...

    in which n is determined by the first element that pred(seq[n]) == False.
    """
    return itertools.dropwhile(extract_function(pred), seq)


@fn.annotate(2)
def random_sample(prob: float, seq: Seq, *, random_state=None) -> Seq:
    """
    Choose with probability ``prob`` if each element of seq will be included in
    the output sequence.

    See Also:
        :func:`tools.random_sample`.
    """
    return toolz.random_sample(prob, seq, random_state=random_state)


@fn.annotate(2)
def remove(pred: Pred, seq: Seq) -> Seq:
    """
    Return those items of sequence for which pred(item) is False

    See Also:
        :func:`tools.remove`.
    """
    return toolz.remove(extract_function(pred), seq)


@fn.annotate(2)
def take_while(pred: Pred, seq: Seq) -> Seq:
    """
    Return successive entries from an iterable as long as the
    predicate evaluates to true for each entry.

    take_while(pred, seq) => seq[0], seq[1], ..., seq[n - 1]

    in which n is determined by the first element that pred(seq[n]) == False.
    """
    return itertools.takewhile(extract_function(pred), seq)


@fn.annotate(2)
def top_k(k: int, seq: Seq, *, key: Func = None) -> tuple:
    """
    Find the k largest elements of a sequence.
    """
    return toolz.topk(k, seq, key)


@fn
def unique(seq: Seq, *, key: Func = None, exclude: Seq = ()) -> Seq:
    """
    Returns the given sequence with duplicates removed.

    Preserves order. If key is supplied map distinguishes values by comparing
    their keys.

    Args:
        seq:
            Iterable of objects.
        key:
            Optional key function.
        exclude:
            Optional sequence of keys to exclude from seq.

    Note:
        Elements of a sequence or their keys should be hashable, otherwise it
        uses a slow path.
    """
    seen = set(exclude)
    add = seen.add
    pred = extract_function(key)

    for x in seq:
        key = pred(x)
        if key not in seen:
            try:
                add(key)
            except TypeError:
                seen = list(seen)
                add = seen.append
                add(key)
            yield x


@fn.curry(2)
def until_convergence(pred: Pred, seq: Seq) -> Seq:
    """
    Test convergence with the predicate function by passing the last two items
    of sequence. If pred(penultimate, last) returns True, stop iteration.
    """
    seq = iter(seq)
    x = next(seq)
    yield x
    for y in seq:
        yield y
        if pred(x, y):
            break
        x = y


@fn.annotate(2)
def without(items, seq: Seq) -> Seq:
    """
    Returns sequence without items specified. Preserves order.

    Hint: pass items as a set for greater performance.

    >>> list(without({2, 3, 5, 7}, range(10)))
    [0, 1, 4, 6, 8, 9]
    """
    for x in seq:
        if x not in items:
            yield x


@fn.annotate(2)
def without_idx(indexes, seq):
    """
    Returns sequence without the specified indexes.

    Hint: pass items as a set for greater performance.

    >>> ''.join(without_idx([3, 4, 5], 'foobazbar'))
    'foobar'
    """
    try:
        indexes = set(indexes)
    except TypeError:
        pass

    for i, x in enumerate(seq):
        if i not in indexes:
            yield x


@fn.annotate(2)
def filter_idx(func: Pred, seq: Seq) -> Seq:
    """
    Similar to :func:`filter`, but return selected indexes instead of values.
    """
    func = extract_function(func)
    return (i for (i, x) in enumerate(seq) if func(x))


def separate(func, seq):
    """
    Similar to the built-in filter() function, but returns two sequences with
    the (filtered in, filtered out) values.

    Examples:
        >>> separate(lambda x: x % 3, [1, 2, 3, 4, 5, 6])
        ([1, 2, 4, 5], [3, 6])

        Respect the type of input sequence just as the filter() function

        >>> separate(lambda x: x.islower(), 'FoobAR')
        ('oob', 'FAR')
    """
    func = bool if func is None else func
    L1, L2 = [], []

    # Filter elements
    for x in seq:
        (L1 if func(x) else L2).append(x)

    # Return the right type
    if isinstance(seq, str):
        return ''.join(L1), ''.join(L2)
    elif isinstance(seq, tuple):
        return tuple(L1), tuple(L2)
    else:
        return L1, L2


def separate_idx(func, seq):
    """
    Similar to separate(), but return lists of indexes instead of values.
    """

    func = bool if func is None else func
    L1, L2 = [], []

    for i, x in enumerate(seq):
        (L1 if func(x) else L2).append(i)
    return L1, L2


#
# Extract items from sequence
#
@fn
def but_last(seq: Seq) -> Seq:
    """
    Returns an iterator with all elements of the sequence but last.
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
def consume(seq: Seq, *, default=None) -> Seq:
    """
    Consume iterator for its side-effects and return last value or None.

    Args:
        seq:
            Any iterable
        default:
            Fallback value returned for empty sequences.
    """
    for default in seq:
        pass
    return default


@fn.annotate(2)
def drop(n: int, seq: Seq) -> Seq:
    """
    Return the sequence following the first n elements.
    """
    return toolz.drop(n, seq)


@fn.annotate(2)
def first_repeated(key: Func, seq: Seq):
    """
    Return the index and value of first repeated element in sequence.

    Raises a ValueError if no repeated element is found.

        >>> first_repeated(None, [1, 2, 3, 1])
        (3, 1)
    """

    key = extract_function(key)
    seen = set()
    add = seen.add
    for i, x in enumerate(seq):
        tag = key(x)
        if tag in seen:
            return i, x
        add(tag)
    raise ValueError('no repeated element in sequence')


@fn.annotate(2)
def get(idx, seq: Seq, **kwargs):
    """
    Get element (or elements, if idx is a list) in a sequence or dict.
    """
    return toolz.get(idx, seq, **kwargs)


@fn
def last(seq: Seq):
    """
    Return last item of sequence.
    """
    return toolz.last(seq)


@fn.annotate(2)
def nth(n: int, seq: Seq):
    """
    Return the nth element in a sequence.

    If seq is an iterator, consume the first n items.
    """
    if n == 0:
        return toolz.first(seq)
    else:
        return toolz.nth(n, seq)


@fn.annotate(3)
def find(pred: Pred, seq: Seq) -> (int, object):
    """
    Return the (position, value) of first element in which predicate is true.

    Raise ValueError if sequence is exhausted without a match.
    """
    pred = extract_function(pred)
    for i, x in enumerate(seq):
        if pred(x):
            return i, x
    raise ValueError('did not encounter any matching items.')


@fn
def peek(seq: Seq) -> typing.Tuple[object, Seq]:
    """
    Retrieve the next element and retrieve a tuple of (elem, seq).

    The resulting sequence *includes* the retrieved element.
    """
    return toolz.peek(seq)


@fn
def rest(seq: Seq) -> Seq:
    """
    Skips first item in the sequence, returning iterator starting just after it.
    A shortcut for drop(1, seq).
    """
    seq = iter(seq)
    next(seq)
    yield from seq


@fn.annotate(2)
def tail(n: int, seq: Seq) -> tuple:
    """
    Return the last n elements of a sequence.
    """
    return toolz.tail(n, seq)


@fn.annotate(2)
def take(n: int, seq: Seq) -> Seq:
    """
    Return (at most) the first n elements of a sequence.
    """
    return toolz.take(n, seq)


@fn.annotate(2)
def take_nth(n: int, seq: Seq) -> Seq:
    """
    Return every nth item in sequence.
    """
    return toolz.take_nth(n, seq)
