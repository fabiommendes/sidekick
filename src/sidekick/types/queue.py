import collections.abc
import functools

from sidekick import lazy
from .linkedlist import List, Nil


def on_parts(func):
    """
    Distribute methods on left and right parts.
    """

    @functools.wraps(func)
    def method(self, *args):
        left = func(self._left, *args)
        right = func(self._right, *args)
        return self.__class__(left, right)

    return method


def as_list(func):
    """
    Apply method as if queue was a list and return queue with only the right
    side.
    """

    @functools.wraps(func)
    def method(self, *args):
        result = func(list(self), *args)
        return self.__class__(result) if isinstance(result, List) else result

    return method


class Queue(collections.abc.Sequence):
    """
    A queue is a particular kind of collection in which the entities in the
    collection are kept in order and the principal operations on the collection
    are the addition of entities to the rear terminal position, known as
    push_right, and removal of entities from the front terminal position,
    known as pop_left.

    Queue data structure description on Wikipedia:
    [1] http://en.wikipedia.org/wiki/Queue_(abstract_data_type)
    Implementation based on two linked lists (left and right). Enqueue operation
    performs cons on right list (the end of the queue). Dequeue peeks first
    element from the left list (when possible), if left list is empty we
    populate left list with element from right one-by-one (in natural reverse
    order). Complexity of both operations are O(1). Such implementation is also
    known as "Banker's Queue" in different papers, i.e. in Chris Okasaki,
    "Purely Functional Data Structures"

    Usage:
    >>> q = Queue()
    >>> q1 = q.extend_right([1, 2, 3, 4])
    >>> q2 = q1.push_right(5)
    >>> q2.pop_left()
    (1, Queue([2, 3, 4, 5]))

    [1] http://en.wikipedia.org/wiki/Double-ended_queue
    Implementation details are described here:
    "Confluently Persistent Deques via Data Structural Bootstrapping"
    [2] https://cs.uwaterloo.ca/~imunro/cs840/p155-buchsbaum.pdf
    xxx: TBD
    """

    __slots__ = ("_left", "_right", "__dict__")
    _left: List
    _right: List
    _left_size = lazy(lambda x: len(x._left))
    _right_size = lazy(lambda x: len(x._right))

    def __init__(self, left=(), right=()):
        self._left = List(left)
        self._right = List(right)
        self.__dict__ = {}

    def __iter__(self):
        yield from self._left
        yield from reversed(self._right)

    def __bool__(self):
        return self._left or self._right

    def __len__(self):
        return self._left_size + self._right_size

    def __getitem__(self, i):
        if isinstance(i, int):
            if i > 0:
                for idx, x in enumerate(self):
                    if idx == i:
                        return x
            raise IndexError(i)
        raise TypeError(i)

    def __repr__(self):
        return f'Queue({list(self)})'

    def __contains__(self, value):
        return value in self._left or value in self._right

    def push_right(self, value):
        """
        Puts element in the end of queue and return a new queue.
        """
        return self.__class__(self._left, self._right.cons(value))

    def push_left(self, value):
        """
        Puts element in the begining of queue and return a new queue.
        """
        return self.__class__(self._left.cons(value), self._right)

    def extend_right(self, seq):
        """
        Extend queue to the right.
        """
        right = self._right
        i = 0
        for i, x in enumerate(seq):
            right = right.cons(x)
        if i:
            new = self.__class__(self._left, right)
            new._right_size += i
            return new
        else:
            return self

    def extend_left(self, seq):
        """
        Extend queue to the left.
        """
        left = self._left
        i = 0
        for i, x in enumerate(seq):
            left = left.cons(x)
        if i:
            new = self.__class__(self._left, left)
            new._left_size += i
            return new
        else:
            return self

    def pop_left(self):
        """
        Remove first element and return (value, queue).

        If queue is empty, raises ValueError.
        """
        if self._left is not Nil:
            value, left = self._left.uncons
            right = self._right
        elif self._right is not Nil:
            value, left = self._right.reversed().uncons
            right = Nil
        else:
            raise ValueError("Queue is empty")
        return value, Queue(left, right)

    def pop_right(self):
        """
        Remove last element and return (value, queue).

        If queue is empty, raises ValueError.
        """
        if self._right is not Nil:
            value, right = self._right.parts
            left = self._left
        elif self._left is not Nil:
            value, right = self._left.reversed().parts
            left = Nil
        else:
            raise ValueError("Queue is empty")
        return value, Queue(left, right)

    def reversed(self):
        """
        Reversed copy of queue.
        """
        return self.__class__(self._right.reversed(), self._left.reversed())

    def is_empty(self):
        """
        Return True if queue is empty.
        """
        return not self

    map = on_parts(List.map)
    __lt__ = as_list(List.__lt__)
    __gt__ = as_list(List.__gt__)
    __le__ = as_list(List.__le__)
    __ge__ = as_list(List.__ge__)
    __eq__ = as_list(List.__eq__)
