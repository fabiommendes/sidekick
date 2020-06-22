from collections import deque
from itertools import islice

from .iter import generator, iter as sk_iter
from ..functions import fn, to_callable
from ..typing import Seq, T, NOT_GIVEN, TYPE_CHECKING, Pred

if TYPE_CHECKING:
    from .. import api as sk
    from ..api import X


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
def only(seq: Seq[T], default=NOT_GIVEN) -> T:
    """
    Return the single element of sequence or raise an error.

    Args:
        seq:
            Input sequence.
        default:
            Optional default value, returned if sequence is empty.

    Examples:
        >>> sk.only([42])
        42
        >>> sk.only([], default=42)
        42
        >>> sk.only([42, 43])
        Traceback (most recent call last):
        ...
        ValueError: sequence is too long
    """
    seq = iter(seq)
    x = first(seq, default=default)
    if is_empty(seq):
        return x
    raise ValueError("sequence is too long")


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
    Return the second element of sequence.

    Raise ValueError or return the given default if sequence has last than 2
    elements.

    Examples:
        >>> sk.second("abcd")
        'b'

    See Also:
        :func:`first`
        :func:`last`
        :func:`nth`

    Notes:
        There is no third, fourth, etc, because we can easily create those
        functions using nth(n). Sidekick implements first/second to help
        selecting items of a pair, which tends to appear frequently when working
        with dictionaries.
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
        If you don't want to raise errors if sequence is not large enough, use
        :func:`rtake`:

        >>> tuple(sk.rtake(5, "abc"))  # No error!
        ('a', 'b', 'c')
        >>> sk.last("abc", n=5, default="-")
        ('-', '-', 'a', 'b', 'c')

    See Also:
        :func:`first`
        :func:`second`
        :func:`nth`
        :func:`init`
        :func:`rtake`
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


@fn.curry(2)
def find(pred: Pred, seq: Seq[T]) -> (int, T):
    """
    Return the (position, value) of first element in which predicate is true.

    Raise ValueError if sequence is exhausted without a match.

    Examples:
        >>> sk.find((X == 11), [2, 3, 5, 7, 11, 13, 17])
        (4, 11)
    """
    pred = to_callable(pred)
    for i, x in enumerate(seq):
        if pred(x):
            return i, x
    raise ValueError("did not encounter any matching items.")


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


def _assure_given(x, error=None, not_given=NOT_GIVEN):
    if x is not_given:
        error = error or ValueError("not enough elements in sequence")
        raise error
    return x


@fn.curry(1)
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
        >>> sk.consume(it)
        1
        2
        3
    """
    for default in seq:
        pass
    return default
