from collections import deque
from itertools import islice

from .iter import generator, iter as sk_iter
from ..functions import fn
from ..typing import Seq, T, NOT_GIVEN, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk


@fn.curry(2)
@generator
def cons(x: T, seq: Seq[T]) -> Seq[T]:
    """
    Construct operation. Add x to beginning of sequence.

    Examples:
        >>> sk.cons(0, range(1, 6))
        sk.iter([0, 1, 2, 3, 4, 5])

    See Also:
        :func:`uncons`
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
        >>> head, tail = sk.uncons(range(6))
        >>> head
        0
        >>> tail
        sk.iter([1, 2, 3, 4, 5])

    See Also:
        :func:`cons`
        :func:`first`
        :func:`rest`
    """
    seq = iter(seq)
    try:
        return next(seq), sk_iter(seq)
    except StopIteration:
        if default is NOT_GIVEN:
            raise ValueError("Cannot deconstruct empty sequence.")
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
        >>> sk.first("abcd")
        'a'

    See Also:
        :func:`second`
        :func:`last`
        :func:`nth`
        :func:`rest`
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
        >>> sk.second("abcd")
        'b'

    See Also:
        :func:`first`
        :func:`last`
        :func:`nth`
    """
    try:
        it = iter(seq)
        next(it)
        return next(it)
    except StopIteration:
        return _assure_given(default)


@fn.curry(1)
def last(seq: Seq[T], default=NOT_GIVEN, n=None) -> T:
    """
    Return last item (or items) of sequence.

    Args:
        seq:
            Input sequence
        default:
            If given, and sequence is empty, return it. An empty sequence with
            no default value raises a ValueError.
        n:
            If given, return a tuple with the last n elements instead. If default
            is given and sequence is not large enough, fill it with the value,
            otherwise raise a ValueError.

    Examples:
        >>> sk.last("abcd")
        'd'

    Notes:
        If you don't want to raise errors if sequence is not large enough, try
        the following recipe:

        >>> from collections import deque
        >>> tuple(deque("abc", 2))
        ('b', 'c')
        >>> tuple(deque("abc", 5))  # No error!
        ('a', 'b', 'c')
        >>> sk.last("abc", n=5, default="-")
        ('-', '-', 'a', 'b', 'c')

    See Also:
        :func:`first`
        :func:`second`
        :func:`nth`
        :func:`init`
    """
    if n is None:
        x = default
        for x in seq:
            pass
        return _assure_given(x)
    else:
        try:
            out = tuple(seq[-n:])
        except (TypeError, IndexError):
            out = tuple(deque(seq, n))

        if len(out) == n:
            return out
        elif default is NOT_GIVEN:
            raise ValueError("sequence is smaller than n")
        else:
            m = n - len(out)
            return (default,) * m + out


@fn.curry(2)
def nth(n: int, seq: Seq, default=NOT_GIVEN) -> T:
    """
    Return the nth element in a sequence.

    Return the default if sequence is not large enough or raise a ValueError if
    default is not given.

    Warnings:
        If seq is an iterator, consume the first n items.

    Examples:
        >>> sk.nth(2, "abcd")
        'c'

    See Also:
        :func:`first`
        :func:`second`
        :func:`last`
    """
    try:
        return next(islice(seq, n, n + 1))
    except StopIteration:
        return _assure_given(default)


#
# Special slices
#
@generator
def init(seq: Seq) -> Seq:
    """
    Returns an iterator with all elements of the sequence but last.

    Return an empty iterator for empty sequences.

    Examples:
        >>> sk.init(range(6))
        sk.iter([0, 1, 2, 3, 4])

    See Also:
        :func:`first`
        :func:`rest`
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


@generator
def rest(seq: Seq) -> Seq:
    """
    Skips first item in the sequence, returning iterator starting just after it.

    A shortcut for drop(1, seq). Return an empty iterator for empty sequences.

    Examples:
        >>> sk.rest(range(6))
        sk.iter([1, 2, 3, 4, 5])

    See Also:
        :func:`first`
        :func:`init`
    """
    seq = iter(seq)
    try:
        next(seq)
    except StopIteration:
        pass
    else:
        yield from seq


#
# Testing properties
#
@fn
def is_empty(seq: Seq) -> bool:
    """
    Return True if sequence is empty.

    Warning:
        This function consume first element of iterator. Use this only to assert
        that some iterator was consumed without using it later or create a copy
        with :func:`tee` that will preserve the consumed element.

    Examples:
         >>> nums = iter(range(5))
         >>> sum(nums)  # exhaust iterator
         10
         >>> sk.is_empty(nums)
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
         >>> sk.length(range(10))
         10
    """
    try:
        n = len(seq)
    except TypeError:
        pass
    else:
        return n if limit is None else min(n, limit)

    if limit is None:
        return sum(1 for _ in seq)
    else:
        return sum(1 for _, _ in zip(seq, range(limit)))


def _assure_given(x, not_given=NOT_GIVEN):
    if x is not_given:
        raise ValueError("not enough elements in sequence")
    return x
