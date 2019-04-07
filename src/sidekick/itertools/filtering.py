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
    *["drop_while", "random_sample", "remove", "separate", "take_while", "top_k",
      "unique", "until_convergence", "without"],

    # Extracting items
    *["consume", "drop", "get", "peek", "take", "take_nth"],
]


#
# Filtering functions
#
@fn.curry(2)
def drop_while(pred: Pred, seq: Seq) -> Seq:
    """
    Drop items from the iterable while predicate(item) is true.
    Afterwards, return every element until the iterable is exhausted.

    drop_while(pred, seq) ==> seq[n], seq[n + 1], ...

    in which n is determined by the first element that pred(seq[n]) == False.

    Examples:
        >>> drop_while((X < 5), range(10)) | L
        [5, 6, 7, 8, 9]

    See Also:
        drop
        take_while
    """
    return itertools.dropwhile(extract_function(pred), seq)


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
def remove(pred: Pred, seq: Seq) -> Seq:
    """
    Opposite of filter. Return those items of sequence for which pred(item) 
    is False

    Examples:
        >>> remove((X < 5), range(10)) | L
        [5, 6, 7, 8, 9]

    See Also:
        :func:`tools.remove`.
    """
    return toolz.remove(extract_function(pred), seq)


@fn.curry(2)
def take_while(pred: Pred, seq: Seq) -> Seq:
    """
    Return successive entries from an iterable as long as the
    predicate evaluates to true for each entry.

    take_while(pred, seq) => seq[0], seq[1], ..., seq[n - 1]

    in which n is determined by the first element that pred(seq[n]) == False.

    Examples:
        >>> take_while((X < 5), range(10)) | L
        [0, 1, 2, 3, 4]

    See Also:
        take
        drop_while
    """
    return itertools.takewhile(extract_function(pred), seq)


@fn.curry(2)
def top_k(k: int, seq: Seq, *, key: Func = None) -> tuple:
    """
    Find the k largest elements of a sequence.

    Examples:
        >>> top_k(3, "hello world") | L
        ['w', 'r', 'o']
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
            Optional key function. It will return only the first value that
            evaluate to a unique key by the key function.
        exclude:
            Optional sequence of keys to exclude from seq

    Examples:
        >>> unique(range(100), key=(X % 5)) | L
        [0, 1, 2, 3, 4]

    Note:
        Elements of a sequence or their keys should be hashable, otherwise it
        uses a slow path.
    """
    pred = extract_function(key or (lambda x: x))
    seen = set(map(key,exclude))
    add = seen.add

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

    Examples:
        We start with a converging (possibly infinite) sequence and an explicit 
        criteria
        >>> seq = sk.iterate((X / 2), 2.0)
        >>> conv = lambda x, y: abs(x - y) < 0.01

        Run it until convergence
        >>> until_convergence(conv, seq) | L
        [2.0, 1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125]
    """
    seq = iter(seq)
    x = next(seq)
    yield x
    for y in seq:
        yield y
        if pred(x, y):
            break
        x = y

# FIXME: Deprecate?
@fn.curry(2)
def without(items, seq: Seq) -> Seq:
    """
    Return sequence without specified items.

    Hint: pass items as a set for greater performance.

    Examples:
        >>> list(without({2, 3, 5, 7}, range(10)))
        [0, 1, 4, 6, 8, 9]

    See Also:
        without_keys
    """
    return (x for x in seq if x not in items)


# FIXME: Deprecate?
@fn.curry(3)
def without_keys(items, key: Func, seq: Seq) -> Seq:
    """
    Returns sequence without the values in which key(x) are present in items.

    Hint: pass items as a set for greater performance.

    Examples:
        >>> "".join(without_keys('aeiou', str.lower, 'foObaR'))
        'fbR'

    See Also:
        without_keys
    """
    key = extract_function(key)
    return filter(lambda x: key(x) not in items, seq)


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
            raise ValueError('non-decreasing sequence of indices')


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
            raise ValueError('non-decreasing sequence of indices')
        else:
            yield x
    yield from seq


@fn.curry(2)
def separate(pred: Func, seq: Seq) -> (Seq, Seq):
    """
    Split sequence it two. The first consists of items that pass the
    predicate and the second of those items that don't.

    Similar to (filter(pred, seq), filter(!pred, seq)), but only evaluate
    the predicate once per item.

    Examples:
        >>> a, b = separate(X % 2, [1, 2, 3, 4, 5])
        >>> list(a), list(b)
        ([1, 3, 5], [2, 4])
    """
    pred = extract_function(pred)
    a, b = itertools.tee((x, pred(x)) for x in seq)
    return ((x for x, keep in a if keep),
            (x for x, exclude in b if not exclude))


#
# Extract items from sequence
#
@fn
def consume(seq: Seq, *, default=None) -> Seq:
    """
    Consume iterator for its side-effects and return last value or None.

    Args:
        seq:
            Any iterable
        default:
            Fallback value returned for empty sequences.

    Examples:
        >>> consume(print(x) for x in [1, 2, 3])
        1
        2
        3
    """
    for default in seq:
        pass
    return default


@fn.curry(2)
def drop(n: int, seq: Seq) -> Seq:
    """
    Return the sequence following the first n elements.

    Examples:
        >>> drop(3, [1, 2, 3, 4, 5]) | L
        [4, 5]

    See Also:
        take
        drop_while
    """
    return toolz.drop(n, seq)


@fn.curry(2)
def first_repeated(key: Func, seq: Seq):
    """
    Return the index and value of first repeated element in sequence.

    Raises a ValueError if no repeated element is found.

    Examples:
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


@fn.curry(2)
def get(idx, seq: Seq, **kwargs):
    """
    Get element (or elements, if idx is a list) in a sequence or dict.

    Examples:
        >>> get([3, 2, 1], [2, 3, 5, 7, 11, 13, 17])
        (7, 5, 3)
    """
    return toolz.get(idx, seq, **kwargs)


@fn.curry(3)
def find(pred: Pred, seq: Seq) -> (int, object):
    """
    Return the (position, value) of first element in which predicate is true.

    Raise ValueError if sequence is exhausted without a match.

    Examples:
        >>> find((X == 11), [2, 3, 5, 7, 11, 13, 17])
        (4, 11)
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

    Examples:
        >>> seq = (x*x for x in range(1, 6))
        >>> x, seq = peek(seq)
        >>> x, list(seq)
        (1, [1, 4, 9, 16, 25])
    """
    return toolz.peek(seq)


@fn.curry(2)
def take(n: int, seq: Seq) -> Seq:
    """
    Return (at most) the first n elements of a sequence.

    Examples:
        >>> take(3, [1, 2, 3, 4, 5]) | L
        [1, 2, 3]

    See Also:
        drop
        take_while
        take_nth
    """
    return toolz.take(n, seq)


# TODO: rename this?
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
