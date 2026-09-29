import builtins
from collections import deque
from itertools import islice, chain, repeat, tee
from typing import Iterable, Callable, TYPE_CHECKING, overload


from .iter import iter
from .util import hashable, Pred, to_callable, b, a, NOT_GIVEN


if TYPE_CHECKING:
    from sidekick import api as sk  # noqa: F401
    from sidekick.api import X  # noqa: F401


_iter = builtins.iter


def cons(x: a, seq: Iterable[a], /) -> iter[a]:
    """
    Construct operation. Add x to beginning of sequence.

    Examples:
        >>> sk.cons(0, range(1, 6))
        sk.iter([0, 1, 2, 3, 4, 5])

    See also:
        :func:`uncons`
    """
    return iter(_cons(x, seq))


def _cons(x, seq):
    yield x
    yield from seq


def uncons(seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> tuple[a, iter[a]]:
    """
    De-construct sequence. Return a pair of (``first``, ``*rest``) of sequence.

    If default is given and if seq is an empty sequence return
    (default, empty_sequence), otherwise raise a ValueError.

    Examples:
        >>> head, tail = sk.uncons(range(6))
        >>> head
        0
        >>> tail
        sk.iter([1, 2, 3, 4, 5])

    See also:
        :func:`cons`
        :func:`first`
    """
    seq = _iter(seq)
    try:
        return next(seq), iter(seq)
    except StopIteration:
        if default is NOT_GIVEN:
            raise ValueError("Cannot deconstruct empty sequence.")
        return default, iter(_iter(()))


#
# Selecting elements
#
def only(seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> a:
    """
    Consume and return the single element of sequence or raise an error.

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
    x = first(seq := iter(seq), default=default)
    if is_empty(seq):
        return x
    raise ValueError("sequence is too long")


def first(seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> a:
    """
    Consume and return the first element of sequence.

    Raise ValueError or return the given default if sequence is empty.

    Examples:
        >>> sk.first("abcd")
        'a'

    See also:
        :func:`second`
        :func:`last`
        :func:`nth`
    """
    try:
        return next(_iter(seq))
    except StopIteration:
        return _assure_given(default)


def second(seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> a:
    """
    Consume and return the second element of sequence.

    Raise ValueError or return the given default if sequence is too short.

    Examples:
        >>> sk.second("abcd")
        'b'

    See also:
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
        next(seq := _iter(seq))
        return next(seq)
    except StopIteration:
        return _assure_given(default)


def last(seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> a:
    """
    Consume sequence and return last item.

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

    See also:
        :func:`first`
        :func:`second`
        :func:`nth`
        :func:`rtake`
        :func:`last_n`
    """
    x = default
    for x in seq:
        pass
    return _assure_given(x)


def last_n(n: int, seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> list[a]:
    """
    Consume and return the last n items of sequence as a list.

    Args:
        n:
            If given, return a tuple with the last n elements instead. If default
            is given and sequence is not large enough, fill it with the value,
            otherwise raise a ValueError.
        seq:
            Input sequence
        default:
            If given, and sequence is empty, return it. An empty sequence with
            no default value raises a ValueError.

    Examples:
        >>> sk.last_n(2, "abcd")
        ['c', 'd']

    Notes:
        If you don't want to raise errors if sequence is not large enough, use
        :func:`rtake` or set the default argument:

        >>> list(sk.rtake(5, "abc"))  # No error!
        ['a', 'b', 'c']
        >>> sk.last_n("abc", n=5, default="-")
        ['-', '-', 'a', 'b', 'c']

    See also:
        :func:`first`
        :func:`last`
        :func:`second`
        :func:`nth`
        :func:`rtake`
    """
    try:
        out = seq[-n:]  # type: ignore
    except (TypeError, IndexError):
        out = deque(seq, n)

    if len(out) == n:
        return [*out]
    elif default is NOT_GIVEN:
        raise ValueError("sequence is smaller than n")
    else:
        return [*repeat(default, n - len(out)), *out]


def nth(n: int, seq: Iterable[a], /, *, default: a = NOT_GIVEN) -> a:
    """
    Return the nth element in a sequence, consuming it.

    Return the default if sequence is not large enough or raise a ValueError if
    default is not given.

    Warnings:
        If seq is an iterator, consume the first n items.

    Examples:
        >>> sk.nth(2, "abcd")
        'c'

    See also:
        :func:`first`
        :func:`second`
        :func:`last`
    """
    try:
        return next(islice(seq, n, n + 1))
    except StopIteration:
        return _assure_given(default)


def find(pred: Pred[a], seq: Iterable[a], /) -> tuple[int, a]:
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
def is_empty(seq: Iterable[a], /) -> bool:
    """
    Return True if sequence is empty.

    Warning:
        This function consume first element of iterator. Use this only to assert
        that some iterator was consumed without using it later or create a copy
        with `itertools.tee <https://docs.python.org/3/library/itertools.html#itertools
        .tee>`_
        that will preserve the consumed element.

    Examples:
         >>> nums = iter(range(5))
         >>> sum(nums)  # exhaust iterator
         10
         >>> sk.is_empty(nums)
         True
    """
    try:
        next(_iter(seq))
    except StopIteration:
        return True
    else:
        return False


def length(seq: Iterable[a], /, *, limit: int = NOT_GIVEN) -> int:
    """
    Return length of sequence, consuming the iterator.

    If limit is given, consume sequence up to the given limit. This is useful
    to test if sequence is longer than some given size but without necessarily
    consuming the whole iterator.

    Examples:
         >>> sk.length(range(10))
         10
         >>> sk.length(range(10), limit=5)
         5
    """
    try:
        n = len(seq)  # type: ignore
    except TypeError:
        pass
    else:
        return n if limit is NOT_GIVEN else min(n, limit)

    if limit is NOT_GIVEN:
        return sum(1 for _ in seq)
    else:
        return sum(1 for _, _ in zip(seq, range(limit)))


def consume(seq: Iterable[a]) -> None:
    """
    Consume iterator for its side-effects and return None.

    Args:
        seq:
            Any iterable

    Examples:
        >>> it = map(print, [1, 2, 3])
        >>> sk.consume(it)
        1
        2
        3
    """
    for _ in seq:
        pass


@overload
def peek(
    seq: Iterable[a],
    /,
    *,
    key: Callable[[Iterable[a]], b],
    default: a = NOT_GIVEN,
) -> tuple[b, iter[a]]:

    ...


@overload
def peek(
    seq: Iterable[a],
    /,
    *,
    default: a = NOT_GIVEN,
) -> tuple[a, iter[a]]:
    ...


def peek(seq, /, *, key=NOT_GIVEN, default=NOT_GIVEN):
    """
    Retrieve the first element and return a tuple of (elem, iterator).

    The resulting iterator *includes* all elements of the original sequence, including the
    first. If a callable key is given, it is used to partially consume the list and
    produce the returning element.

    Args:
        seq:
            Input sequence.
        key:
            A function that is used to inspect the sequence and produce the
            element returned in the LHS. If key is known to always consume most
            of the sequence, it is usually faster to convert to a list before
            sending to this function.
        default:
            An optional default value to fill if sequence is empty.

    Examples:
        >>> peek((x*x for x in range(1, 101)), key=sk.second)
        (4, sk.iter([1, 4, 9, 16, 25, ...]))
    """
    if key is NOT_GIVEN:
        key = first
    return _peek_key(seq, to_callable(key), default)


def _peek_key(seq, key, default):
    out, dispose = tee(seq)
    if default is not NOT_GIVEN:
        dispose = chain(dispose, repeat(default))
    return key(dispose), iter(out)


def peek_n(
    n: int,
    seq: Iterable[a],
    /,
    *,
    default: a = NOT_GIVEN,
    truncate: bool = False,
) -> tuple[list[a], Iterable[a]]:
    """
    Retrieve the first n elements and return a tuple of (elems, iterator).

    The resulting iterator *includes* all elements of the original sequence, the ones
    returned as the first element of the tuple.

    Args:
        n:
            If given, return the first n elements of seq. Must not be given
            with key.
        seq:
            Input sequence.
        default:
            An optional default value to fill if sequence is not long enough.
        truncate:
            If True, return a list with less then n elements if iterable is
            smaller than n.

    Examples:
        >>> peek_n(2, (x*x for x in range(1, 101)))
        ([1, 4], sk.iter([1, 4, 9, 16, 25, ...]))
    """
    try:
        first_n = seq[:n]  # type: ignore
    except TypeError:
        seq_, seq = tee(seq)
        first_n = islice(seq_, n)

    first_n = list(first_n)
    n_missing = len(first_n) < n

    if n_missing and default:
        first_n.extend([default] * (n - len(first_n)))
    if n_missing and not truncate:
        raise ValueError("sequence is not long enough")
    return first_n, seq


def first_repeated(
    key: Callable[[a], hashable], seq: Iterable[a], /, *, default: a = NOT_GIVEN
) -> tuple[int, a]:
    """
    Return the index and value of first repeated element in sequence by predicate.

    Raises a ValueError if no repeated element is found.

    Args:
        key:
            A key function used to evaluate uniqueness. If None, check the first
            repetition by value.
        seq:
            Input sequence.
        default:
            If given, return this value and the length of the consumed iterator
            instead of raising an exception when no repetitions are found.

    Examples:
        >>> data = [
        ...     {'name': 'John', 'id': 123},
        ...     {'name': 'Paul', 'id': 234},
        ...     {'name': 'John', 'id': 456},
        ... ]
        >>> first_repeated(X['name'], data)
        (2, {'name': 'John', 'id': 456})
    """
    i = 0
    key = to_callable(key)
    seen: set[hashable] = set()
    add_key = seen.add

    for i, x in enumerate(seq):
        if (tag := key(x)) in seen:
            return i, x
        try:
            add_key(tag)
        except TypeError:
            # Slow fallback for non-hashable types
            seen = list(seen)  # type: ignore
            add_key = seen.append  # type: ignore

    if default is NOT_GIVEN:
        raise ValueError("no repeated element in sequence")
    return i, default


def _assure_given(x: a, error=None, not_given=NOT_GIVEN) -> a:
    if x is not_given:
        error = error or ValueError("not enough elements in sequence")
        raise error
    return x
