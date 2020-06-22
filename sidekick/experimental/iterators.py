from collections import deque
from collections.abc import Iterator

from ..typing import NOT_GIVEN


# noinspection PyPep8Naming
class pushing_iterator(Iterator):
    """
    An iterator that accepts injecting items at the current point of iteration.

    Items can be pushed to iterator using the push() or push_many() methods.

    Args:
        iterator:
            Iterator source.
        default:
            If given, returns an infinite iterator that yields the default
            until some item is pushed to the stream.

    Example:
        Collatz sequence
        >>> it = pushing_iterator([7])
        >>> collatz = []
        >>> for n in it:
        ...     collatz.append(n)
        ...     if n % 2 == 0:
        ...        it.push(n // 2)
        ...     elif n % 2 == 1 and n != 1:
        ...        it.push(3 * n + 1)
        >>> collatz
        [7, 22, 11, 34, 17, 52, 26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1]
    """

    __slots__ = ("_cursor_stack", "_next")

    def __init__(self, iterator, default=NOT_GIVEN):
        self._cursor_stack = []
        self._next = self._next_function(iter(iterator), default)

    def _next_function(self, iterator, default, next=next, not_given=NOT_GIVEN):
        stack = self._cursor_stack
        pop = stack.pop

        def yield_next():
            if stack:
                return pop()
            try:
                return next(iterator)
            except StopIteration:
                if default is not_given:
                    raise
                return default

        return yield_next

    def __next__(self):
        return self._next()

    def push(self, item):
        """
        Push single item to iterator at current point in iteration.

        Calling next() on iterator will return item in the next iterator.
        """
        self._cursor_stack.append(item)

    def push_many(self, values):
        """
        Append a sequence of values to the current iteration point.
        """
        self._cursor_stack.extend(reversed(values))

    def peek(self, steps=0, *, default=NOT_GIVEN):
        """
        Peek next element without consuming iterator.

        Pass the number of steps to check how many steps forward it will peek.

        It raises StopIteration or return the default value if iterator is
        already consumed.
        """
        if steps == 0:
            try:
                value = self._next()
            except StopIteration:
                if default is NOT_GIVEN:
                    raise
                return default
            else:
                self._cursor_stack.append(value)
                return value
        else:
            values = []
            try:
                for _ in range(steps):
                    values.append(self._next())
            except StopIteration:
                if default is NOT_GIVEN:
                    raise
                return default
            finally:
                self.push_many(values)
            return values[-1]


class continuing_iterator(Iterator):
    """
    Similar to continuing_iterator, but push new items at end of sequence
    instead of at the current iteration point.

    Example:
        Cycling
        >>> it = continuing_iterator([1, 2, 3])
        >>> items = []
        >>> for x in sk.take(10, it):
        ...     it.push(x)
        ...     items.append(x)
        >>> items
        [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
    """

    __slots__ = ("_tail_iters", "_next")

    def __init__(self, iterator, default=NOT_GIVEN):
        self._tail_iters = deque()
        self._next = self._generator(iterator, default).__next__

    def __next__(self):
        try:
            return self._next()
        except StopIteration:
            self._next = self._generator((), NOT_GIVEN).__next__
            raise

    def _generator(self, iterator, default):
        queue = self._tail_iters
        pop = queue.popleft

        yield from iterator
        while True:
            while queue:
                yield from pop()
            if default is NOT_GIVEN:
                break
            else:
                yield default

    def push(self, item):
        """
        Push single item to iterator at current point in iteration.

        Calling next() on iterator will return item in the next iterator.
        """
        self._tail_iters.append(iter([item]))

    def push_many(self, values):
        """
        Append a sequence of values to the current iteration point.
        """
        self._tail_iters.append(iter(values))


class prev_iter(Iterator):
    """
    Iterator that stores the value of last iteration.

    Examples:
        >>> fibo = sk.iterate_many((X + Y), [1, 2])
        >>> it = prev_iter(fibo, start=1)
        >>> (x / it.prev for x in it) | L[:50]              # doctest: +ELLIPSIS
        [1.0, 2.0, 1.5, ..., 1.618033988749895, 1.618033988749895]
    """

    __slots__ = ("prev", "_next")

    def __init__(self, iterator, start=None):
        self._next = iter(self.generator(iterator)).__next__
        self.prev = start

    def generator(self, xs):
        for x in xs:
            yield x
            self.prev = x

    def __next__(self):
        return self._next()
