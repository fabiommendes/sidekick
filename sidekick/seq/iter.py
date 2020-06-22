import itertools
import operator
from functools import wraps

from ..functions import fn
from ..typing import Iterator, Tuple, T, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk

NOT_GIVEN = object()
_iter = iter


class iter(Iterator):
    """
    Base sidekick iterator class.

    This class extends classical Python iterators with a few extra operators.
    Sidekick iterators accepts slicing, indexing, concatenation (with the + sign)
    repetition (with the * sign) and pretty printing.

    Operations that return new iterators (e.g., slicing, concatenation, etc)
    consume the data stream. Operations that simply peek at data execute the
    generator (and thus may produce side-effects), but cache values and do not
    consume data stream.
    """

    __slots__ = ("_iterator", "_size_hint")
    _iterator: Iterator[T]

    def __new__(cls, iterator: Iterator[T], size_hint=NotImplemented):
        if isinstance(iterator, iter):
            return iterator

        new = object.__new__(cls)
        new._iterator = _iter(iterator)
        new._size_hint = size_hint
        return new

    def __next__(self, _next=next):
        return _next(self._iterator)

    def __iter__(self):
        return self._iterator

    def __repr__(self):
        it = self._iterator
        head = []
        for _ in range(7):
            try:
                head.append(next(it))
            except StopIteration:
                display = map(str, head)
                self._iterator = _iter(head)
                self._size_hint = len(head)
                break
        else:
            self._iterator = itertools.chain(_iter(head), it)
            display = [*map(repr, head[:-1]), "..."]
        data = ", ".join(display)
        return f"sk.iter([{data}])"

    def __getitem__(self, item, _chain=itertools.chain):
        if isinstance(item, int):
            if item >= 0:
                head = []
                for i, x in enumerate(self._iterator):
                    head.append(x)
                    if i == item:
                        self._iterator = _chain(head, self._iterator)
                        return x
                else:
                    self._iterator = _iter(head)
                    self._size_hint = len(head)
                    raise IndexError(item)
            else:
                raise IndexError("negative indexes are not supported")

        elif isinstance(item, slice):
            a, b, c = item.start, item.step, item.stop
            return iter(itertools.islice(self._iterator, a, b, c))

        elif callable(item):
            return iter(filter(item, self._iterator), self._size_hint)

        elif isinstance(item, list):
            if not item:
                return []
            if isinstance(item[0], bool):
                self._iterator, data = itertools.tee(self._iterator, 2)
                return [x for key, x in zip(item, data) if key]
            elif isinstance(item[0], int):
                self._iterator, data = itertools.tee(self._iterator, 2)
                data = list(itertools.islice(data, max(item) + 1))
                return [data[i] for i in item]
            else:
                raise TypeError("index must contain only integers or booleans")

        else:
            size = operator.length_hint(item, -1)
            size = None if size == -1 else size
            return iter(compress_or_select(item, self._iterator), size)

    def __add__(self, other, _chain=itertools.chain):
        if hasattr(other, "__iter__"):
            return iter(_chain(self._iterator, other))
        return NotImplemented

    def __radd__(self, other, _chain=itertools.chain):
        if hasattr(other, "__iter__"):
            return iter(_chain(other, self._iterator))
        return NotImplemented

    def __iadd__(self, other, _chain=itertools.chain):
        self._iterator = _chain(self._iterator, other)

    def __mul__(self, other):
        if isinstance(other, int):
            if other < 0:
                raise ValueError("cannot multiply by negative integers")
            return iter(cycle_n(self._iterator, other))
        try:
            data = _iter(other)
        except TypeError:
            return NotImplemented
        return iter(itertools.product([self._iterator, data]))

    def __rmul__(self, other):
        if isinstance(other, int):
            return self.__mul__(other)
        try:
            data = _iter(other)
        except TypeError:
            return NotImplemented
        return iter(itertools.product([data, self._iterator]))

    def __rmatmul__(self, fn):
        if callable(fn):
            return iter(map(fn, self._iterator), self._size_hint)
        return NotImplemented

    def __length_hint__(self, _hint=operator.length_hint):
        if self._size_hint is NotImplemented:
            return _hint(self._iterator, NotImplemented)
        return self._size_hint

    #
    # API
    #
    def copy(self) -> "iter":
        """
        Return a copy of iterator. Consuming the copy do not consume the
        original iterator.

        Internally, this method uses itertools.tee to perform the copy. If you
        known that the iterator will be consumed, it is faster and more memory
        efficient to convert it to a list and produce multiple iterators.
        """
        self._iterator, other = itertools.tee(self._iterator, 2)
        return iter(other, self._size_hint)

    def tee(self, n=1) -> Tuple["iter"]:
        """
        Split iterator into n additional copies.

        The copy method is simply an alias to iter.tee(1)[0]
        """
        self._iterator, *rest = itertools.tee(self._iterator, n + 1)
        n = self._size_hint
        return tuple(iter(it, n) for it in rest)

    def peek(self, n: int) -> Tuple:
        """
        Peek the first n elements without consuming the iterator.
        """

        data = tuple(itertools.islice(self._iterator, n))
        self._iterator = itertools.chain(data, self._iterator)
        return data


def cycle_n(seq, n):
    data = []
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


def compress(keys, seq):
    for x, pred in zip(seq, keys):
        if pred:
            yield x


def select(keys, seq):
    data = []
    for i in keys:
        try:
            yield data[i]
        except IndexError:
            data.extend(itertools.islice(seq, i - len(data) + 1))
            yield data[i]


def compress_or_select(keys, seq):
    keys = _iter(keys)
    seq = _iter(seq)

    try:
        key = next(keys)
        if key is True:
            fn = compress
            yield next(seq)
        elif key is False:
            fn = compress
            next(seq)
        elif isinstance(key, int):
            fn = select
            keys = itertools.chain([key], keys)
        else:
            raise TypeError(f"invalid key: {key!r}")

    except StopIteration:
        return

    yield from fn(keys, seq)


@fn
def generator(func):
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


fn.generator = staticmethod(generator)
