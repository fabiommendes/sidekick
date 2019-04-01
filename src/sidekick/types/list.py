import collections.abc
import itertools
import operator as op

from sidekick import pipeline
from .union import Union

flip = lambda f: lambda x, y: f(y, x)
Seq = collections.abc.Sequence


# noinspection PyMethodParameters,PyMethodFirstArgAssignment
class List(Union):
    """
    An immutable singly-linked list.
    """

    @property
    def uncons(self):
        """
        Tuple with (head, tail) of cons cell.
        """
        if self:
            return self.head, self.tail
        else:
            raise ValueError('cannot desconstruct empty list.')

    # Generic implementations
    __contains__ = Seq.__contains__
    __reversed__ = Seq.__reversed__
    index = Seq.index
    count = Seq.count

    @classmethod
    def __union_constructor__(cls, seq):
        """
        Examples:
        >>> List([1, 2, 3])
        List([1, 2, 3])
        """

        if isinstance(seq, List):
            return seq

        # Efficient non-recursive list constructor
        set_head = Cons.head.__set__
        set_tail = Cons.tail.__set__
        new = object.__new__
        cons = Cons

        it = iter(seq)
        try:
            result = last = new(cons)
            set_head(last, next(it))
        except StopIteration:
            return Nil

        for x in it:
            cell = new(cons)
            set_head(cell, x)
            set_tail(last, cell)
            last = cell
        set_tail(last, Nil)
        return result

    # Methods
    def __iter__(lst):  # noqa: N805
        while lst is not Nil:
            yield lst.head
            lst = lst.tail

    def __len__(lst):  # noqa: N805
        return sum(1 for _ in lst)

    def __getitem__(self, idx):  # noqa: N805
        if idx < 0:
            raise IndexError("negative indexes are not supported")

        for i, x in enumerate(self):
            if i == idx:
                return x
        else:
            raise IndexError(idx)

    def __repr__(self):
        data = ", ".join(map(str, self))
        return "List([{}])".format(data)

    # Concatenation
    def __add__(self, other):
        if isinstance(other, List):
            cons = Cons
            for x in reversed(list(self)):
                other = cons(x, other)
            return other
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, int):
            if other == 0:
                return Nil
            elif other == 1:
                return self
            elif other < 0:
                raise ValueError("negative numbers")
            return List(itertools.chain(itertools.repeat(self, other)))

        return NotImplemented

    __rmul__ = __mul__

    # Lexicographical comparisons
    def _cmp(a, b, stop_op, end_op, on_identity):
        nil = Nil
        if isinstance(b, List):
            while a is not nil and b is not nil:
                if a is b:
                    return on_identity
                elif stop_op(a.head, b.head):
                    return False
                a, b = a.tail, b.tail
            return end_op(a, b)
        return NotImplemented

    __eq__ = lambda self, other: self._cmp(self, other, op.ne, op.is_, True)
    __ge__ = lambda self, other: self._cmp(self, other, op.lt, lambda x, y: y is Nil, True)
    __gt__ = lambda self, other: self._cmp(self, other, op.gt, lambda x, y: y is Nil, False)

    #
    # Inserting and removing elements
    #
    def cons(self, x):
        """
        Adds an element to the beginning of the list.
        """
        return Cons(x, self)

    def take(self, n):  # noqa: N805
        """
        Return a list with at most n elements taken from the beginning of the
        list.
        """

        return List(itertools.islice(self, n))

    def drop(lst, n):  # noqa: N805
        """
        Return a list that removes at most n elements from the beginning of the
        list.
        """

        for _ in range(n):
            try:
                lst = lst.tail
            except AttributeError:
                break
        return lst

    #
    # Reorganizing the list
    #
    def reversed(lst) -> "List":  # noqa: N805
        """
        Reversed copy of the list.
        """

        acc = Nil
        while lst:
            x, lst = lst.uncons
            acc = acc.cons(x)
        return acc

    def sorted(self, **kwargs):
        """
        A sorted version of the list.
        """
        return List(sorted(self, **kwargs))

    def partition(lst, pred):
        """
        Partition list on predicate.
        """
        start = []
        append = start.append

        while lst:
            x, lst = lst.uncons
            if pred(x):
                break
            append(x)

        return List(start), lst

    #
    # Monadic interface
    #
    def map(self, func, *funcs):
        """
        Maps function into list.
        """
        if funcs:
            func = pipeline(func, *funcs)
        return List(map(func, self))

    def map_bound(self, func):
        """
        Maps a function that return sequences into the list and flatten all
        intermediate results.
        """

        def iter_all():
            for x in self:
                yield from func(x)

        return List(iter_all())


class Cons(List):
    """
    A link in the linked list.
    """
    head: object
    tail: List
    __bool__ = lambda lst: True


class Nil(List):
    """
    Terminal element in a linked list.

    Represents an empty list.
    """
    __bool__ = lambda x: False
