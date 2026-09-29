from collections.abc import MutableSequence
from collections import deque
import itertools
from typing import Iterable, Iterator, Sized

from .util import a

__all__ = ["LazyList"]
INF = float("inf")


# noinspection PyCallByClass
class LazyList(MutableSequence[a]):
    """
    A list whose members are calculated by consuming a (possibly infinite) iterator
    on-the-fly.

    Args:
        iterable : iterable object
            Any iterable object can be used to construct a list
        size : int
            The length can be specified if it is known beforehand. It can also be
            used to truncate the iterator at some given length. Infinite iterators
            can be explicitly specified by setting length='inf' or
            length=float('inf').
    """

    __slots__ = ("_data", "_parts")
    _data: list[a]
    _parts: deque[tuple[int | float | None, list[a] | Iterator[a]]]

    def __init__(self, iterable=(), *, size=None):
        self._data = []
        self._parts = deque()

        if iterable == ():
            size = 0
        elif size == "inf" or size == float("inf"):
            size = INF
        elif isinstance(size, int):
            iterable = itertools.islice(iterable, size)
        elif isinstance(iterable, LazyList):
            size = iterable._size_fast()
        elif isinstance(iterable, Sized):
            self._data.extend(iterable)
            size = 0
        else:
            size = None
            
        if size != 0:
            self._parts.append((size, iter(iterable)))

    @property
    def is_consumed(self) -> bool:
        """
        True if LazyList has consumed all of its lazy components.
        """
        return self._parts == []
    
    @property
    def is_surely_infinite(self) -> bool:
        """
        True if LazyList is known to be infinite.
        
        Notice that ``lst.is_surely_infinite`` ``lst.is_surely_finite`` 
        can be False at the same time.
        """
        for (n, _) in self._parts:
            if n == INF:
                return True
        return False
    
    @property
    def is_surely_finite(self) -> bool:
        """
        True if LazyList is known to be finite.
        
        Notice that ``lst.is_surely_infinite`` ``lst.is_surely_finite`` 
        can be False at the same time.
        """
        return all(isinstance(n, int) for (n, _) in self._parts)

    def __setitem__(self, idx, value):
        self.consume(idx)
        self._data[idx] = value

    def __getitem__(self, idx):
        self.consume(idx)
        return self._data[idx]

    def __iter__(self):
        yield from self._data

        while self._parts:
            n, data = self._parts[0]

            if isinstance(data, list):
                self._data.extend(data)
                self._parts.popleft()
                yield from data
            elif n is None or n == INF:
                yield from data
                self._parts.popleft()
            else:
                for x in data:
                    yield x
                    n -= 1
                    self._parts[0] = (n, data)    

    def __repr__(self):
        n = len(self._data)
        parts = [*map(repr, itertools.islice(self, n + 3))]
        if len(parts) == n + 3:
            parts.append("...")
        data = ", ".join(parts)
        return f"{type(self).__name__}([{data}])"

    def __len__(self) -> int:
        size = len(self._data)

        for i, (n, seq) in enumerate(self._parts):
            if n is None:
                data = list(seq)
                n = len(data)
                self._parts[i] = (n, data)
            elif n == INF:
                raise OverflowError("cannot get the size of an infinite iterator")
            size += n

        return size

    def __delitem__(self, idx: int | slice):
        self.consume(idx)
        del self._data[idx]

    def append(self, value: a):
        if self._parts and isinstance(self._parts[-1][1], list):
            n, lst = self._parts[-1]
            self._parts[-1] = n + 1, lst
            lst.append(value)
        else:
            self._parts.append((1, [value]))

    def extend(self, iterable: Iterable[a]):
        if isinstance(iterable, Sized):
            n = len(iterable)
            self._parts.append((n, list(iterable)))
        else:
            self._parts.append((None, iterable))

    def insert(self, idx: int, value: a):
        self.consume(idx)
        self._data.insert(idx, value)

    def consume(self, n: int | None | slice = None):
        """
        Consume iterator and save all elements to list.

        If an index is given, consume up to the given index.
        """

        match n:
            case None:
                while self._parts:
                    n, data = self._parts[0]
                    if n == INF:
                        raise OverflowError("cannot consume infinite iterator")
                    elif n is None:
                        for x in data:
                            self._data.append(x)
                    else:
                        self._data.extend(data)
                    self._parts.popleft()

            case int():
                for _ in itertools.islice(self, n):
                    pass

            case slice(stop=n) if n is None or n < 0:
                self.consume()

            case slice(stop=n):
                self.consume(n)

            case _:
                raise TypeError(f"invalid index: {type(n).__name__}")

    def _size_fast(self) -> int | None:
        n = len(self._data)
        for n, _ in self._parts:
            if isinstance(n, int):
                n += 1
            else:
                return None
        return n

