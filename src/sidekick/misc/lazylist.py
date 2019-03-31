import itertools
from collections.abc import MutableSequence

from typing import Callable

__all__ = ['LazyList']
INF = float('inf')


class LazyList(MutableSequence, list):
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

    __slots__ = ('_iter', '_tail', '_missing')

    def __new__(cls, iterable, *, size=None):
        return list.__new__(cls)

    def __init__(self, iterable, *, size=None):
        list.__init__(self)
        self._iter = iter(iterable)
        self._tail = []
        self._missing = size
        if size == 'inf' or size == float('inf'):
            self._missing = INF
        if self._missing not in [None, INF]:
            self._iter = itertools.islice(self._iter, self._missing)

    @property
    def is_lazy(self):
        return self._iter is not None

    @property
    def can_be_infinite(self):
        if self._missing is INF:
            return True
        elif self._missing is not None:
            return False
        return self._iter is not None

    def _index_operation(self, op: Callable, idx: int, *args):
        if idx < 0 and self._iter is not None:
            try:
                return op(self._tail, idx, *args)
            except IndexError:
                self.consume()
        elif self._iter is not None:
            self.consume_until(idx)
        return op(self, idx, *args)

    def __setitem__(self, idx, value):
        self._index_operation(list.__setitem__, idx, value)

    def __getitem__(self, idx):
        if isinstance(idx, int):
            return self._index_operation(list.__getitem__, idx)
        elif isinstance(idx, slice):
            raise TypeError('slices are not supported yet')
        else:
            raise TypeError

    def __iter__(self):
        yield from list.__iter__(self)
        has_length = self._missing is not None
        if self._iter is not None:
            for x in self._iter:
                list.append(self, x)
                if has_length:
                    self._missing -= 1
                yield x
            self._iter = None
            list.extend(self, self._tail)
            tail = list(self._tail)
            self._tail.clear()
            yield from tail

    def __repr__(self):
        tname = type(self).__name__
        if self._iter is None:
            return f'{tname}({super().__repr__()})'
        else:
            pre_data = list.__repr__(self)[1:-1]
            pos_data = repr(self._tail)[1:-1]
            data = '...' if not pre_data else pre_data + ', ...'
            data = data if not pos_data else '%s, %s' % (data, pos_data)
            return '%s([%s])' % (tname, data)

    def __eq__(self, other):
        if not isinstance(other, list):
            return NotImplemented

        if isinstance(other, LazyList):
            if self._missing is INF or other._missing is INF:
                return False

        a, b = iter(self), iter(other)
        for x, y in zip(a, b):
            if x != y:
                return False
        return is_consumed(a) and is_consumed(b)

    def append(self, value):
        if self._iter is None:
            list.append(self, value)
        else:
            self._tail.append(value)

    def extend(self, iterable):
        if self._iter is None:
            list.extend(self, iterable)
        else:
            self._tail.extend(iterable)

    def __len__(self):
        if self._iter is None:
            return list.__len__(self)
        elif self._missing == INF:
            raise OverflowError('cannot get the size of an infinite iterator')
        elif self._missing is not None:
            return list.__len__(self) + self._missing + len(self._tail)
        else:
            self.consume()
            return list.__len__(self)

    def __delitem__(self, idx):
        return self._index_operation(list.__delitem__, idx)

    def insert(self, idx, value):
        return self._index_operation(list.insert, idx, value)

    def consume(self):
        """
        Consume iterator and save all elements to list.
        """

        if self._iter is not None:
            if self._missing is INF:
                raise OverflowError('cannot consume an infinite iterator')
            list.extend(self, self._iter)
            list.extend(self, self._tail)
            self._tail.clear()
            self._iter = None
            self._missing = 0

    def consume_until(self, n: int):
        """
        Consume iterator until list reaches at most size n.
        """

        head_size = list.__len__(self)
        if n < 0:
            raise ValueError('negative values are not accepted')
        if head_size >= n or self._iter is None:
            return

        values = itertools.islice(self._iter, n - head_size)
        list.extend(self, values)
        try:
            list.append(self, next(self._iter))
        except StopIteration:
            if self._missing is not None:
                self._missing -= list.__len__(self) - head_size
            self.consume()


def is_consumed(it):
    try:
        next(it)
        return False
    except StopIteration:
        return True
