import collections
import functools

from .list import List, Nil, linklist


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
        result = func(self.to_list(), *args)
        return self.__class__(result) if isinstance(result, List) else result

    return method


class Queue(collections.Sequence):
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
    >>> from fn.immutable import Queue
    >>> q = Queue()
    >>> q1 = q.push_right(10)
    >>> q2 = q1.push_right(20)
    >>> value, tail = q2.pop_left()
    >>> value
    10
    >>> tail.pop_left()
    (20, <fn.immutable.list.Queue object at 0x1055554d0>)

    [1] http://en.wikipedia.org/wiki/Double-ended_queue
    Implementation details are described here:
    "Confluently Persistent Deques via Data Structural Bootstrapping"
    [2] https://cs.uwaterloo.ca/~imunro/cs840/p155-buchsbaum.pdf
    xxx: TBD
    """

    __slots__ = ("_left", "_right")

    def __init__(self, left=Nil, right=Nil):
        self._left = List(left)
        self._right = List(right)

    def __iter__(self):
        yield from self._left
        yield from self._right.reversed()

    def __bool__(self):
        return self._left is not Nil or self._right is not Nil

    def __len__(self):
        return len(self._left) + len(self._right)

    def __getitem__(self, i):
        if isinstance(i, int):
            if i > 0:
                for idx, x in enumerate(self):
                    if idx == i:
                        return x
            raise IndexError(i)
        raise TypeError(i)

    def __contains__(self, value):
        return value in self._left or value in self._right

    def push_right(self, value):
        """
        Puts element in the end of queue and return a new queue.
        """
        if len(self._left) >= len(self._right):
            return self.__class__(self._left, self._right.push_left(value))

        left = self.to_list()
        right = List.cons(value, Nil)
        return self.__class__(left, right)

    def push_left(self, value):
        """
        Puts element in the begining of queue and return a new queue.
        """
        return self.__class__(self._left.push_left(value), self._right)

    def pop_left(self):
        """
        Remove first element and return (value, queue).

        If queue is empty, raises ValueError.
        """
        if self._left is not Nil:
            value, left = self._left.pop_left()
            right = self._right
        elif self._right is not Nil:
            value, left = self._right.reversed().pop_pair()
            right = Nil
        else:
            raise ValueError("Queue is empty")

    def pop_right(self):
        """
        Remove last element and return (value, queue).

        If queue is empty, raises ValueError.
        """
        if self._right is not Nil:
            value, right = self._right.pop_left()
            left = self._left
        elif self._left is not Nil:
            value, right = self._left.reversed().pop_pair()
            left = Nil
        else:
            raise ValueError("Queue is empty")

    def to_list(self):
        """
        Convert queue to list.
        """
        return linklist(iter(self))

    def reversed(self):
        """
        Reversed copy of queue.
        """
        return self.__class__(self._right.reversed(), self._left.reversed())

    def is_empty(self):
        """
        Return True if queue is empty.
        """
        return self._left is Nil and self._right is Nil

    map = on_parts(List.map)
    maybe_map = on_parts(List.maybe_map)
    index_map = on_parts(List.index_map)
    filter = on_parts(List.filter)
    __lt__ = as_list(List.__lt__)
    __gt__ = as_list(List.__gt__)
    __le__ = as_list(List.__le__)
    __ge__ = as_list(List.__ge__)
    __eq__ = as_list(List.__eq__)
