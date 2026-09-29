from __future__ import annotations
from collections import deque

import itertools
import operator
from functools import wraps
from typing import (
    Iterable,
    overload,
    Any,
    Callable,
    Iterator,
    NoReturn,
    Tuple,
    TYPE_CHECKING,
)

from .util import hashable, num, c, b, BinOp, FoldOp, Pred, NOT_GIVEN, P, a, Raisable

if TYPE_CHECKING:
    from sidekick import api as sk  # noqa: F401
    import sidekick.seq as lib

safe_repr = repr

_iter = iter


class iter(Iterator[a]):
    """
    Base sidekick iterator class.

    This class extends classical Python iterators with many extra operators.
    Sidekick iterators accepts slicing, indexing, concatenation (with the + sign)
    repetition (with the * sign) and pretty printing.

    Operations that return new iterators (e.g., slicing, concatenation, etc)
    consume the data stream. Operations that simply peek at data execute the
    generator (and thus may produce side-effects), but cache values and do not
    consume data stream.
    """

    __slots__ = ("_iterator", "_size_hint")
    _iterator: Iterator[a]
    _size_hint: int | None

    def __new__(cls, iterator: Iterable[a], size_hint: int | None = None) -> iter[a]:
        if isinstance(iterator, iter):
            return iterator

        new = object.__new__(cls)
        new._iterator = _iter(iterator)
        new._size_hint = size_hint
        return new

    def __next__(self, _next=next) -> a:
        return _next(self._iterator)

    def __iter__(self) -> Iterator[a]:
        return self._iterator

    def __repr__(self) -> str:
        try:
            head = [*itertools.islice(self._iterator, 6)]
        except Exception as ex:
            error = f"{type(ex).__name__}{ex!r})"
            return f"sk.iter(<error: {error}>)"
        finally:
            self._iterator = itertools.chain(head, self._iterator)

        elements = [*map(safe_repr, head)]
        if len(elements) == 6:
            elements[-1] = "..."
        args = ", ".join(elements)
        return f"sk.iter([{args}])"

    @overload
    def __getitem__(self, item: int) -> a:
        ...

    @overload
    def __getitem__(self, item: slice) -> iter[a]:
        ...

    @overload
    def __getitem__(self, item: list[bool] | list[int]) -> list[a]:
        ...

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._get_item_at(item)
        elif isinstance(item, slice):
            return self._get_slice(item)
        elif isinstance(item, list):
            return self._select_indexes(item)
        # elif callable(item):
        #     return Iter(filter(item, self._iterator), self._size_hint)
        # else:
        #     size = operator.length_hint(item, -1)
        #     size = None if size == -1 else size
        #     return Iter(compress_or_select(item, self._iterator), size)
        raise TypeError(type(item))

    def _get_item_at(self, idx: int) -> a:
        if idx >= 0:
            head = []
            for i, x in enumerate(self._iterator):
                head.append(x)
                if i == idx:
                    self._iterator = itertools.chain(head, self._iterator)
                    return x
            else:
                self._iterator = _iter(head)
                self._size_hint = len(head)
                raise IndexError(idx)
        else:
            raise IndexError("negative indexes are not supported")

    def _get_slice(self, slice: slice) -> iter[a]:
        a, b, c = slice.start, slice.step, slice.stop
        return iter(itertools.islice(self._iterator, a, b, c))

    def _select_indexes(self, selector: list[int] | list[bool]) -> list[a]:
        if not selector:
            return []
        if isinstance(selector[0], bool):
            self._iterator, seq = itertools.tee(self._iterator, 2)
            return [x for key, x in zip(selector, seq) if key]
        elif isinstance(selector[0], int):
            self._iterator, seq = itertools.tee(self._iterator, 2)
            data = [*itertools.islice(seq, max(selector) + 1)]
            return [data[i] for i in selector]
        else:
            raise TypeError("index must contain only integers or booleans")

    def __add__(self, other: iter[a]):
        if hasattr(other, "__iter__"):
            return iter(itertools.chain(self._iterator, other))
        return NotImplemented

    def __radd__(self, other: iter[a]):
        if hasattr(other, "__iter__"):
            return iter(itertools.chain(other, self._iterator))
        return NotImplemented

    def __iadd__(self, other: iter[a]):
        self._iterator = itertools.chain(self._iterator, other)

    def __mul__(self, other: int):
        if isinstance(other, int):
            if other < 0:
                raise ValueError("cannot multiply by negative integers")
            return iter(cycle_n(self._iterator, other))
        try:
            data = _iter(other)
        except TypeError:
            return NotImplemented
        return iter(itertools.product([self._iterator, data]))

    def __rmul__(self, other: int):
        if isinstance(other, int):
            return self.__mul__(other)
        try:
            data = _iter(other)
        except TypeError:
            return NotImplemented
        return iter(itertools.product([data, self._iterator]))

    def __rmatmul__(self, func):
        if callable(func):
            return iter(map(func, self._iterator), self._size_hint)
        return NotImplemented

    def __length_hint__(self):
        if self._size_hint is None:
            return operator.length_hint(self._iterator)
        return self._size_hint

    #
    # API
    #
    def copy(self) -> iter[a]:
        """
        Return a copy of iterator. Consuming the copy do not consume the
        original iterator.

        The copy method is simply an alias to iter.tee(1)[0]

        Internally, this method uses itertools.tee to perform the copy. If you
        known that the iterator will be consumed, it is faster and more memory
        efficient to convert it to a list and produce multiple iterators.
        """
        return self.tee(1)[0]

    def tee(self, n=1) -> Tuple[iter[a], ...]:
        """
        Split iterator into n additional copies.
        """
        self._iterator, *rest = itertools.tee(self._iterator, n + 1)
        n = self._size_hint
        return tuple(iter(it, n) for it in rest)

    def peek_n(self, n: int) -> Tuple[a, ...]:
        """
        Peek the first n elements without consuming the iterator.
        """
        data = tuple(itertools.islice(self._iterator, n))
        self._iterator = itertools.chain(data, self._iterator)
        return data

    def peek(self) -> a:
        """
        Peek the first element without consuming the iterator.
        """
        x, iterator = lib.peek(self)
        self._iterator = _iter(iterator)
        return x

    #
    # Augmenting
    #
    def interpose(self, elem: a) -> iter[a]:
        """
        Introduce element between each pair of elements.

        See also:
            :func:`interpose`.
        """
        return lib.interpose(elem, self)

    def pad(
        self, value: a, /, *, size: int = NOT_GIVEN, step: int = NOT_GIVEN
    ) -> iter[a]:
        """
        Fill resulting sequence with value after the first sequence terminates.

        See also:
            :func:`pad`.
        """
        return lib.pad(value, self, size=size, step=step)

    def pad_with(
        self, func: Callable[[a], a], /, nargs=1, default=NOT_GIVEN
    ) -> iter[a]:
        """
        Pad sequence iterating the last item with func.

        See also:
            :func:`pad_with`.
        """
        return lib.pad_with(func, self, nargs=nargs, default=default)

    def append(self, elem: a) -> iter[a]:
        """
        Return a new sequence with element appended to the end.

        See also:
            :func:`append`.
        """
        return lib.append(elem, self)

    def insert(self, idx: int, value: a, /) -> iter[a]:
        """
        Return sequence that inserts value at the given index.

        See also:
            :func:`insert`
        """
        return lib.insert(idx, value, self)

    #
    # Basic
    #
    def prepend(self, x: a, /) -> iter[a]:
        """
        Add x to beginning of sequence.

        See also:
            :func:`cons`
        """
        return lib.cons(x, self)

    def uncons(self, *, default: a = NOT_GIVEN) -> tuple[a, Iterable[a]]:
        """
        De-construct sequence. Return a pair of (``first``, ``*rest``) of sequence.

        If default is given and if seq is an empty sequence return
        (default, empty_sequence), otherwise raise a ValueError.

        See also:
            :func:`uncons`
        """
        return lib.uncons(self, default=default)

    def only(self, *, default: a = NOT_GIVEN) -> a:
        """
        Consume and return the single element of sequence or raise an error.

        See also:
            :func:`only`
        """
        return lib.only(self, default=default)

    def first(self, *, default: a = NOT_GIVEN) -> a:
        """
        Consume and return the first element of sequence.

        Raise ValueError or return the given default if sequence is empty.

        See also:
            :func:`first`
        """
        return lib.first(self, default=default)

    def second(self, *, default: a = NOT_GIVEN) -> a:
        """
        Consume and return the second element of sequence.

        Raise ValueError or return the given default if sequence is too short.

        Examples:
            >>> sk.second("abcd")
            'b'

        See also:
            :func:`second`
        """
        return lib.second(self, default=default)

    def last(self, *, default: a = NOT_GIVEN) -> a:
        """
        Consume sequence and return last item.

        See also:
            :func:`last`
        """
        return lib.last(self, default=default)

    def last_n(self, n: int, *, default: a = NOT_GIVEN) -> list[a]:
        """
        Consume and return the last n items of sequence as a list.

        See also:
            :func:`last_n`
        """
        return lib.last_n(n, self, default=default)

    def nth(self, n: int, *, default: a = NOT_GIVEN) -> a:
        """
        Return the nth element in a sequence, consuming it.

        Return the default if sequence is not large enough or raise a ValueError if
        default is not given.

        See also:
            :func:`last_n`
        """
        return lib.nth(n, self, default=default)

    def find(self, pred: Pred[a], /) -> tuple[int, a]:
        """
        Return the (position, value) of first element in which predicate is true.

        Raise ValueError if sequence is exhausted without a match.

        See also:
            :func:`find`
        """
        return lib.find(pred, self)

    def is_empty(self) -> bool:
        """
        Return True if sequence is empty, consuming an element.

        See also:
            :func:`is_empty`
        """
        return lib.is_empty(self)

    def length(self, *, limit: int = NOT_GIVEN) -> int:
        """
        Return length of sequence, consuming the iterator.

        If limit is given, consume sequence up to the given limit. This is useful
        to test if sequence is longer than some given size but without necessarily
        consuming the whole iterator.

        See also:
            :func:`length`
        """
        return lib.length(self, limit=limit)

    def consume(self) -> None:
        """
        Consume iterator for its side-effects and return None.
        """
        return lib.consume(self)

    def first_repeated(self, key: Pred[a], *, default: a = NOT_GIVEN) -> tuple[int, a]:
        """
        Return the index and value of first repeated element in sequence by predicate.

        Raises a ValueError if no repeated element is found.

        See also:
            :func:`length`
        """
        return lib.first_repeated(key, self, default=default)

    #
    # Combining iterators
    #
    def concat(self, *args: Iterable[a]) -> iter[a]:
        """
        Concatenates all iterators after self.

        See also:
            :func:`concat`
        """
        return lib.concat(self, *args)

    def interleave(*seqs: Iterable[a], aligned: bool = False) -> iter[a]:
        """
        Interleave sequence of sequences.

        See also:
            :func:`interleave`
        """
        return lib.interleave(*seqs)

    def zip_aligned(
        *seqs: Iterable[a], error: Callable[[], Raisable] = NOT_GIVEN
    ) -> iter[a]:
        """
        Zip and raises an error if sizes do not match.

        Similar to the zip built-in, but raises an UnalignedZipError if one sequence
        terminates before the others.

        See also:
            :func:`zip_aligned`
        """
        kwargs = {} if error is NOT_GIVEN else {"error": error}
        return lib.zip_aligned(*seqs, **kwargs)

    def diff(
        *seqs: Iterable[a], key: Callable[[a], b] = NOT_GIVEN, default=NOT_GIVEN
    ) -> iter[tuple[a, a]]:
        """
        Return those items that differ in a pairwise comparison between sequences.

        See also:
            :func:`diff`
        """
        return lib.diff(*seqs, key=key, default=default)

    def merge_sorted(*seqs: Iterable[a], key: Callable[[a], a] = NOT_GIVEN) -> iter[a]:
        """
        Merge and sort a collection of sorted collections.

        See also:
            :func:`merge_sorted`
        """
        return lib.merge_sorted(*seqs, key=key)

    #
    # Creation of new iterables
    #
    def cycle(self, *, n: int = NOT_GIVEN) -> iter[a]:
        """
        Return elements from the iterable until it is exhausted.
        Then repeat the sequence n times or indefinitely.

        See also:
            :func:`cycle`
        """
        return lib.cycle(self, n=n)

    def repeat(self, obj: a, /, *, times: int = NOT_GIVEN) -> iter[a]:
        """
        Append a sequence that returns the object for the specified number of times.

        If not specified, returns the object endlessly.

        See also:
            :func:`repeat`
        """
        return self.concat(lib.repeat(obj, times=times))

    def repeatedly(self, func: Callable[..., a], /, *args, **kwargs) -> iter[a]:
        """
        Append sequence that makes infinite calls to a function with the given arguments.

        End sequence if func() raises StopIteration.

        See also:
            :func:`repeatedly`
        """
        return self.concat(lib.repeatedly(func, *args, **kwargs))

    def iterate(
        self, func: Callable[..., a], n: int = 1, default: a = NOT_GIVEN
    ) -> iter[a]:
        """
        Repeatedly apply a function func to last n elements of sequence and
        generate an infinite sequence.

        Raises value error if sequence is smaller then the number of arguments of
        func.
        """
        if n == 0:
            return self.repeatedly(func)
        elif n == 1:
            return iter(iterate_1(self, func, default))
        else:
            return iter(iterate_n(self, n, func, default))

    #
    # Grouping elements
    #
    def group_by(self, key: Callable[[a], b]) -> dict[b, list[a]]:
        """
        Group collection by the results of a key function.

        See also:
            :func:`group_by`
        """
        return lib.group_by(key, self)

    def chunks(
        self, n: int | Iterable[int], /, *, pad: a = NOT_GIVEN, drop: bool = False
    ) -> iter[tuple[a, ...]]:
        """
        Partition sequence into non-overlapping tuples of length n.

        See also:
            :func:`chunks`
        """
        return lib.chunks(n, self, pad=pad, drop=drop)

    # TODO: better typing
    def chunks_by(self, func, /, *, how="values"):
        """
        Partition sequence into chunks according to a function.

        It creates a new partition every time the value of func(item) changes.

        See also:
            :func:`chunks_by`
        """
        return lib.chunks_by(func, self, how=how)

    def window(self, n: int, /) -> iter[tuple[a, ...]]:
        """
        Return a sequence of overlapping sub-sequences of size n.

        ``n == 2`` is equivalent to a pairwise iteration.

        See also:
            :func:`window`
        """
        return lib.window(n, self)

    def pairs(
        self, /, *, prev: a = NOT_GIVEN, next: a = NOT_GIVEN
    ) -> iter[tuple[a, a]]:
        """
        Returns an iterator of a pair adjacent items.

        This is similar to window(2), but accept a fill value specified either
        with ``prev`` or ``next`` to select if it will form pairs with the preceding
        of the following value.

        See also:
            :func:`pairs`
        """
        return lib.pairs(self, prev=prev, next=next)

    def partition(self, key: int | Pred[a]) -> tuple[iter[a], iter[a]]:
        """
        Partition sequence in two.

        Returns a sequence with elements before and after the key separator.

        See also:
            :func:`partition`
        """
        return lib.partition(key, self)

    def distribute(self, n: int) -> tuple[iter[a], ...]:
        """
        Distribute items of seq into n different sequences.

        See also:
            :func:`distribute`
        """
        return lib.distribute(n, self)

    def inits(self) -> Iterable[a]:
        """
        Lazily return all sub-sequences at beginning of seq.

        See also:
            :func:`inits`
        """
        return lib.inits(self)

    #
    # Reductions and folds
    #
    def fold(self, func: Callable[[b, a], b], init: b, /) -> b:
        """
        Perform a left reduction of sequence.

        See also:
            :func:`fold`
        """
        return lib.fold(func, init, self)

    def reduce(self, func: Callable[[a, a], a], /, default: a = NOT_GIVEN) -> a:
        """
        Like fold, but does not require initial value.

        See also:
            :func:`reduce`
        """
        return lib.reduce(func, self, default=default)

    def acc(self, func: Callable[[a, a], a], /) -> iter[a]:
        """
        Like :func:`scan`, but uses first item of sequence as initial value.

        See also:
            :func:`acc`
        """
        return lib.acc(func, self)

    def scan(self, func: Callable[[b, a], b], init: b, /) -> iter[b]:
        """
        Returns a sequence of the intermediate folds of seq by func.

        See also:
            :func:`scan`
        """
        return lib.scan(func, init, self)

    def fold_by(
        self, key: Callable[[a], c], op: Callable[[b, a], b], init: b, /
    ) -> dict[c, b]:
        """
        Reduce each sequence generated by a group by.

        More efficient than performing separate operations since it does not
        store intermediate groups.

        See also:
            :func:`fold_by`
        """
        return lib.fold_by(key, op, init, self)

    def reduce_by(self, key: Callable[[a], hashable], op: BinOp[a], /) -> dict[hashable, a]:
        """
        Similar to fold_by, but only works on non-empty sequences.

        Initial value is taken to be the first element in sequence.

        See also:
            :func:`reduce_by`
        """
        return lib.reduce_by(key, op, self)

    def fold_together(self, **kwargs: tuple[FoldOp[b, a], b]) -> dict[str, b]:
        """
        Folds using multiple functions simultaneously.

        See also:
            :func:`fold_together`
        """
        return lib.fold_together(self, **kwargs)

    def reduce_together(self, **kwargs: Callable[[a, a], a]) -> dict[str, a]:
        """
        Similar to fold_together, but only works on non-empty sequences.

        Initial value is taken to be the first element in sequence.

        See also:
            :func:`reduce_together`
        """
        return lib.reduce_together(self, **kwargs)

    @overload
    def scan_together(
        self, **kwargs: tuple[Callable[[b, a], b], b]
    ) -> iter[dict[str, b]]:
        ...

    @overload
    def scan_together(
        self,
        arg: tuple[Callable[[b, a], b], b],
        /,
        *args: tuple[Callable[[b, a], b], b],
    ) -> iter[tuple[b, ...]]:
        ...

    def scan_together(self, *args, **kwargs):
        """
        Folds using multiple functions simultaneously.

        See also:
            :func:`scan_together`
        """
        return lib.scan_together(self, *args, **kwargs)

    @overload
    def acc_together(self, **kwargs: Callable[[b, a], b]) -> iter[dict[str, b]]:
        ...

    @overload
    def acc_together(
        self, arg: Callable[[b, a], b], /, *args: Callable[[b, a], b]
    ) -> iter[tuple[b, ...]]:
        ...

    def acc_together(self, *args, **kwargs):
        """
        Similar to fold_together, but only works on non-empty sequences.

        Initial value is taken to be the first element in sequence.

        See also:
            :func:`scan_together`
        """
        return lib.scan_together(self, *args, **kwargs)

    def product(self: iter[num], /, init: num = 1) -> num:
        """
        Multiply all elements of sequence.

        See also:
            :func:`product`
        """
        return lib.product(self, init=init)

    def sum(self: iter[num], /, init: num = 0) -> num:
        """
        Sum all arguments of sequence.

        See also:
            :func:`sum`
        """
        return lib.sum(self, init=init)

    def products(self: iter[num], *, init: num = 1) -> iter[num]:
        """
        Return a sequence of partial products.

        See also:
            :func:`products`
        """
        return lib.products(self, init=init)

    def sums(self: iter[num], *, init: num = 0) -> iter[num]:
        """
        Return a sequence of partial sums.

        See also:
            :func:`sums`
        """
        return lib.sums(self, init=init)

    def all_by(self, pred: Pred[a], /) -> bool:
        """
        Return True if all elements of seq satisfy predicate.

        See also:
            :func:`all_by`
        """
        return lib.all_by(pred, self)

    def any_by(self, pred: Pred[a], /) -> bool:
        """
        Return True if any elements of seq satisfy predicate.

        See also:
            :func:`any_by`
        """
        return lib.any_by(pred, self)

    def top_k(self, k: int, /, *, key: Callable[[a], b] = NOT_GIVEN) -> tuple[a, ...]:
        """
        Find the k largest elements of a sequence.

        See also:
            :func:`top_k`
        """
        return lib.top_k(k, self, key=key)

    #
    # Selecting elements
    #
    def filter(self, pred: Pred[a]) -> iter[a]:
        """
        Return an iterator yielding those items of iterable for which function(item)
        is true.

        See also:
            :func:`filter`
        """
        return lib.filter(pred, self)

    def remove(self, pred: Pred[a]) -> iter[a]:
        """
        Opposite of filter. Return those items of sequence for which pred(item)
        is False

        See also:
            :func:`remove`
        """
        return lib.remove(pred, self)

    def separate(
        self, pred: Pred[a], /, *, consume: bool = False
    ) -> tuple[iter[a], iter[a]]:
        """
        Split sequence it two. The first consists of items that pass the
        predicate and the second of those items that don't.

        Similar to (filter(pred, seq), remove(pred, seq)), but only evaluate
        the predicate once per item.

        See also:
            :func:`separate`
        """
        return lib.separate(pred, self, consume=consume)

    def drop(self, key: int | Pred[a], /) -> iter[a]:
        """
        Drop items from the start of iterable.

        If key is a number, drop at most this number of items for iterator. If it
        is a predicate, drop items while key(item) is true.

        See also:
            :func:`drop`
        """
        return lib.drop(key, self)

    def rdrop(self, key: int | Pred[a], /) -> iter[a]:
        """
        Drop items from the end of iterable.

        See also:
            :func:`rdrop`
        """
        return lib.rdrop(key, self)

    def drop_at(self, indices: set[a] | Iterable[a], /) -> iter[a]:
        """
        Drop all elements in the given positions.

        Indices can be a set or a (possibly infinite) **sorted** iterable.

        See also:
            :func:`drop_at`
        """
        return lib.drop_at(indices, self)

    def take(self, key: int | Pred[a]) -> iter[a]:
        """
        Return the first entries iterable.

        If key is a number, return at most this number of items for iterator. If it
        is a predicate, return items while key(item) is true.

        See also:
            :func:`take`
        """
        return lib.take(key, self)

    def rtake(self, key: int | Pred[a], /) -> iter[a]:
        """
        Return the last entries iterable.

        See also:
            :func:`rtake`
        """
        return lib.rtake(key, self)

    def take_at(self, indices: set[a] | Iterable[a], /) -> iter[a]:
        """
        Return a sequence with values in the positions specified by indices.

        Indices must be any non-decreasing (and possibly infinite) sequence.

        See also:
            :func:`take_at`
        """
        return lib.take_at(indices, self)

    def strip(
        self,
        prefix: Iterable[a],
        partial: bool = False,
        cmp: Callable[[a, a], bool] = NOT_GIVEN,
    ) -> iter[a]:
        """
        If seq starts with the same elements as in prefix, remove them from
        result.

        See also:
            :func:`strip`
        """
        return lib.strip(prefix, self, partial=partial, cmp=cmp)

    def unique(
        self,
        /,
        *,
        key: Callable[[a], b] = NOT_GIVEN,
        exclude: Iterable[a] = (),
        slow: bool = False,
    ) -> iter[a]:
        """
        Returns the given sequence with duplicates removed.

        Preserves order. If key is supplied map distinguishes values by comparing
        their keys.

        See also:
            :func:`unique`
        """
        return lib.unique(self, key=key, exclude=exclude, slow=slow)

    def dedupe(self, *, key: Callable[[a], b] = NOT_GIVEN) -> iter[a]:
        """
        Remove duplicates of successive elements.

        See also:
            :func:`dedupe`
        """
        return lib.dedupe(self, key=key)

    def converge(self, pred: Pred[a], /) -> iter[a]:
        """
        Test convergence with the predicate function by passing the last two items
        of sequence. If pred(penultimate, last) returns True, stop iteration.

        See also:
            :func:`converge`
        """
        return lib.converge(pred, self)

    def random_sample(self, prob: float, *, random_state=None) -> Iterable[a]:
        """
        Choose with probability ``prob`` each element of seq to include in the
        output sequence.

        See also:
            :func:`random_sample`
        """
        return lib.random_sample(prob, self, random_state=random_state)

    def indexed(
        self,
        transform: Callable[
            [Callable[[tuple[int, a]], c], Iterable[tuple[int, a]]],
            Iterable[tuple[int, a]],
        ],
        func: Callable[[a], c],
        /,
        *,
        start: int = 0,
    ) -> Iterable[tuple[int, a]]:
        """
        Take a function that receives a predicate with a sequence and transform it
        to operate on an indexed sequence.

        See also:
            :func:`indexed`
        """
        return lib.indexed(transform, func, self, start=start)

    def map(self, func: Callable[[a], b], /, index=None) -> iter[b]:
        """
        Evaluate function at elements of sequences.

            self.map(func) ==> f(x[0]), f(x[1]), ...

        See also:
            :func:`map`
        """
        return lib.map(func, self, index=index)

    def map_if(
        self,
        pred: Callable[[a], bool],
        func: Callable[..., a],
        /,
        index: int | Iterable[b] | bool = NOT_GIVEN,
    ) -> iter[a]:
        """
        Applies func in the elements in which pred(elem) is True.

        See also:
            :func:`map_if`
        """
        return lib.map_if(pred, func, self, index=index)

    def zip_map(
        self,
        funcs: Iterable[Callable[..., b]],
        index: int | Iterable[b] | bool = NOT_GIVEN,
    ) -> iter[b]:
        """
        Apply sequence of functions to sequences of arguments.

        Generalizes map to receive a stream of functions instead of a single one.

        See also:
            :func:`zip_map`
        """
        return lib.zip_map(funcs, self, index=index)

    #
    # Conversion to collections
    #
    def to_list(self) -> list[a]:
        """
        Convert iterator to list consuming iterator.

        Infinite operators do not terminate.
        """
        return list(self)

    def to_tuple(self) -> tuple[a, ...]:
        """
        Convert iterator to tuple consuming iterator.

        Infinite operators do not terminate.
        """
        return tuple(self)

    def to_set(self) -> set[a]:
        """
        Convert iterator to tuple consuming iterator.

        Infinite operators do not terminate.
        """
        return set(self)

    def to_frozenset(self) -> frozenset[a]:
        """
        Convert iterator to tuple consuming iterator.

        Infinite operators do not terminate.
        """
        return frozenset(self)

    def to_str(self: iter[str]) -> str:
        """
        Convert iterator to string consuming iterator and concatenating
        elements.

        Infinite operators do not terminate.
        """
        return "".join(self)

    def to_bytes(self: iter[bytes]) -> bytes:
        """
        Convert iterator to bytes consuming iterator and concatenating
        elements.

        Infinite operators do not terminate.
        """
        return b"".join(self)


def cycle_n(seq: Iterable[a], n: int) -> Iterator[a]:
    data = list[a]()
    store = data.append
    consumed = False

    while n > 0:
        if consumed:
            yield from data
        else:
            for x in seq:
                store(x)
                yield x
            if data:
                consumed = True
            else:
                return
        n -= 1


def compress(keys: Iterable[bool], seq: Iterable[a]) -> Iterator[a]:
    for x, pred in zip(seq, keys):
        if pred:
            yield x


def select(keys: Iterable[int], seq: Iterable[a]) -> Iterator[a]:
    data = list[a]()
    for i in keys:
        try:
            yield data[i]
        except IndexError:
            data.extend(itertools.islice(seq, i - len(data) + 1))
            yield data[i]


def compress_or_select(
    keys: Iterable[int] | Iterable[bool],
    seq: Iterable[a],
) -> Iterator[a]:
    keys = _iter(keys)
    seq = _iter(seq)

    try:
        key = next(keys)
        if key is True:
            func = compress
            yield next(seq)
        elif key is False:
            func = compress
            next(seq)
        elif isinstance(key, int):
            func = select
            keys = itertools.chain([key], keys)
        else:
            raise TypeError(f"invalid key: {key!r}")

    except StopIteration:
        return

    yield from func(keys, seq)


def iterate_1(seq, func, default):
    for x in seq:
        yield x
    try:
        start = x
    except NameError:
        if default is NOT_GIVEN:
            raise ValueError("trying to iterate from an empty sequence")
        start = default
    yield from lib.iterate(func, start)


def iterate_n(seq, n, func, default):
    args = deque(maxlen=n)
    for x in seq:
        yield x
        args.append(x)

    if len(args) < n and default is NOT_GIVEN:
        raise ValueError(f"sequence smaller than {n} elements")
    while len(args) < n:
        args.appendleft(default)

    yield from lib.iterate(func, *args)


def generator(func: Callable[P, Iterator[a]]) -> Callable[P, iter[a]]:
    """
    Decorates generator function to return a sidekick iterator instead of a
    regular Python generator.

    Examples:
        >>> @sk.generator
        ... def fibonacci():
        ...     x = y = 1
        ...     while True:
        ...         yield x
        ...         x, y = y, x + y
        >>> fibonacci()
        sk.iter([1, 1, 2, 3, 5, 8, ...])
    """

    @wraps(func)
    def gen(*args, **kwargs):
        return iter(func(*args, **kwargs))

    return gen


def stop(x: Any = None) -> NoReturn:
    """
    Raise StopIteration with the given argument.
    """
    raise StopIteration(x)


def yield_and_raise(data, exc):
    """
    Return content from data and then raise exception afterwards.
    """
    yield from data
    raise exc


def __getattr__(attr):
    if attr == "lib":
        import sidekick.seq as lib

        globals()["lib"] = lib
        return lib

    raise AttributeError(attr)
