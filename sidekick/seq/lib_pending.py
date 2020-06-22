import typing

from sidekick import fn, Seq, Pred, Func, to_callable


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
        >>> it = map(print, [1, 2, 3])
        >>> consume(it)
        1
        2
        3
    """
    for default in seq:
        pass
    return default


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


@fn.curry(3)
def find(pred: Pred, seq: Seq) -> (int, object):
    """
    Return the (position, value) of first element in which predicate is true.

    Raise ValueError if sequence is exhausted without a match.

    Examples:
        >>> find((X == 11), [2, 3, 5, 7, 11, 13, 17])
        (4, 11)
    """
    pred = to_callable(pred)
    for i, x in enumerate(seq):
        if pred(x):
            return i, x
    raise ValueError("did not encounter any matching items.")


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
