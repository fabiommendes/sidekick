from collections import deque
from itertools import islice

from ..core import fn, Seq, T, NOT_GIVEN
from ..magics import L, N  # used in doctests

__all__ = [
    *['cons', 'uncons'],
    *['first', 'second', 'nth', 'last'],
    *['rest', 'init', 'last_n'],
    *['is_empty', 'length'],
]


@fn.curry(2)
def cons(x: T, seq: Seq[T]) -> Seq[T]:
    """
    Construct operation. Add x to beginning of sequence.

    Examples:
        >>> cons(0, N[1, ..., 5]) | L
        [0, 1, 2, 3, 4, 5]

     See Also:
        uncons
    """
    yield x
    yield from seq


@fn.curry(1)
def uncons(seq: Seq[T], default=NOT_GIVEN) -> (T, Seq[T]):
    """
    De-construct sequence. Return a pair of (first(seq), rest(seq)) of sequence.

    If default is given and if seq is an empty sequence return
    (default, empty_sequence), otherwise raise a ValueError.

    Examples:
        >>> n, seq = uncons(N[1, ..., 5])
        >>> n, list(seq)
        (1, [2, 3, 4, 5])

    See Also:
        cons
        first
        rest
    """
    seq = iter(seq)
    try:
        return next(seq), seq
    except StopIteration:
        if default is NOT_GIVEN:
            raise ValueError('Cannot deconstruct empty sequence.')
        return default, iter(())


#
# Selecting elements
#
@fn.curry(1)
def first(seq: Seq[T], default=NOT_GIVEN) -> T:
    """
    Return the first element of sequence.

    Raise ValueError or return the given default if sequence is empty.

    Examples:
        >>> first("abcd")
        'a'

    See Also:
        second
        last
        nth
        rest
    """
    try:
        return next(iter(seq))
    except StopIteration:
        return _assure_given(default)


@fn.curry(1)
def second(seq: Seq[T], default=NOT_GIVEN) -> T:
    """
    Return the first element of sequence.

    Raise ValueError or return the given default if sequence has last than 2
    elements.

    Examples:
        >>> second("abcd")
        'b'

    See Also:
        first
        last
        nth
    """
    try:
        it = iter(seq)
        next(it)
        return next(it)
    except StopIteration:
        return _assure_given(default)


@fn.curry(1)
def last(seq: Seq[T], default=NOT_GIVEN) -> T:
    """
    Return last item of sequence.

    Raise ValueError or return the given default if sequence is empty.

    Examples:
        >>> last("abcd")
        'd'

    See Also:
        first
        second
        nth
        init
    """
    x = default
    for x in seq:
        pass
    return _assure_given(x)


@fn.curry(2)
def nth(n: int, seq: Seq, default=NOT_GIVEN):
    """
    Return the nth element in a sequence or default if sequence is not large
    enough.

    Warnings:
        If seq is an iterator, consume the first n items.

    Examples:
        >>> nth(2, "abcd")
        'c'

    See Also:
        first
        second
        last
    """
    try:
        return next(islice(seq, n, n + 1))
    except StopIteration:
        return _assure_given(default)


#
# Special slices
#
@fn
def init(seq: Seq) -> Seq:
    """
    Returns an iterator with all elements of the sequence but last.

    Return an empty iterator for empty sequences.

    Examples:
        >>> init(range(6)) | L
        [0, 1, 2, 3, 4]

    See Also:
        first
        rest
    """
    seq = iter(seq)
    try:
        prev = next(seq)
    except StopIteration:
        pass
    else:
        for x in seq:
            yield prev
            prev = x


@fn
def rest(seq: Seq) -> Seq:
    """
    Skips first item in the sequence, returning iterator starting just after it.

    A shortcut for drop(1, seq). Return an empty iterator for empty sequences.

    Examples:
        >>> rest(range(6)) | L
        [1, 2, 3, 4, 5]

    See Also:
        first
        init
    """
    seq = iter(seq)
    try:
        next(seq)
    except StopIteration:
        pass
    else:
        yield from seq


@fn.curry(2)
def last_n(n: int, seq: Seq) -> tuple:
    """
    Return a tuple with the last n elements of sequence.

    Examples:
        >>> last_n(2, "abcd")
        ('c', 'd')
    """
    try:
        return tuple(seq[-n:])
    except (TypeError, IndexError):
        return tuple(deque(seq, n))


#
# Testing properties
#
@fn
def is_empty(seq: Seq) -> bool:
    """
    Return True if sequence is empty.

    Warnings:
        This function consume first element of iterator. Use this only to assert
        that some iterator was consumed without using it later or create a copy
        with :func:`tee` that will preserve the consumed element.

    Examples:
         >>> nums = iter(range(5))
         >>> sum(nums)  # exhaust iterator
         10
         >>> is_empty(nums)
         True
    """
    try:
        next(iter(seq))
    except StopIteration:
        return True
    else:
        return False


@fn.curry(1)
def length(seq: Seq, *, limit=None) -> int:
    """
    Return length of sequence, consuming the iterator.

    If limit is given, consume sequence up to the given limit. This is useful
    to test if sequence is longer than some given size but without consuming the
    whole iterator if so.

    Examples:
         >>> length(range(10))
         10
    """
    if limit is None:
        return sum(1 for _ in seq)
    else:
        return sum(1 for _, _ in zip(seq, range(limit)))


def _assure_given(x, not_given=NOT_GIVEN):
    if x is not_given:
        raise ValueError('not enough elements in sequence')
    return x
