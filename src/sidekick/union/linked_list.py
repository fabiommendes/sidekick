import collections.abc
import functools
import itertools

from .union import Union, opt

flip = (lambda f: lambda x, y: f(y, x))


class ListMeta(type(Union), type(collections.abc.Sequence)):
    """
    Metaclass for List type.
    """


# noinspection PyMethodParameters,PyMethodFirstArgAssignment
class List(Union, collections.abc.Sequence, metaclass=ListMeta):
    """
    An immutable singly-linked list.
    """

    is_nil: bool
    is_cons: bool
    head: object
    tail: 'List'

    #
    # Class methods
    #
    @classmethod
    def concat(cls, lists):
        """
        Concatenates a list of lists.
        """
        result = Nil
        for x in reversed(lists):
            result = x + result
        return result

    def __iter__(lst):  # noqa: N805
        while lst is not Nil:
            yield lst.head
            lst = lst.tail

    def __len__(lst):  # noqa: N805
        return sum(1 for _ in lst)

    def __getitem__(lst, i):  # noqa: N805
        if i < 0:
            raise IndexError('negative indexes are not supported')
        if lst is Nil:
            raise IndexError(i)

        x = lst.head
        lst = lst.tail
        for idx in range(i):
            try:
                x = lst.head
                lst = lst.tail
            except AttributeError:
                raise IndexError(i)
        return x

    def __eq__(self, other):
        a = self
        b: List = other

        if isinstance(b, List):
            while a is not Nil and b is not Nil:
                if a is b:
                    return True
                elif a.head != b.head:
                    return False
                a, b = a.tail, b.tail
            return a is b
        return NotImplemented

    def __repr__(self):
        data = ', '.join(map(str, self))
        return 'linklist([{}])'.format(data)

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
                raise ValueError('negative numbers')

            result = self
            for _ in range(other):
                result = result + self
            return result

        return NotImplemented

    __rmul__ = __mul__

    # Lexicographical comparisons
    def __ge__(self, other):
        if isinstance(other, List):
            return list(self) >= list(other)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, List):
            return list(self) <= list(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, List):
            return list(self) > list(other)
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, List):
            return list(self) < list(other)
        return NotImplemented

    #
    # Inserting and removing elements
    #
    def cons(self, x):
        """
        Adds an element to the beginning of the list and return a copy.
        """
        return Cons(x, self)

    def take(lst, n):  # noqa: N805
        """
        Return a list with at most n elements taken from the beginning of the
        list.
        """

        result = Nil
        for i in range(n):
            try:
                x, lst = lst.args
            except AttributeError:
                break
            else:
                result = result.cons(x)
        return result

    def drop(lst, n):  # noqa: N805
        """
        Return a list that removes at most n elements from the beginning of the
        list.
        """

        for i in range(n):
            try:
                x, lst = lst.args
            except AttributeError:
                break
        return lst

    def intersperse(self, value):
        """
        Intersperse list elements with value.
        """
        if self.is_cons:
            cons = Cons
            acc = Nil
            lst = self.reverse()
            x, lst = lst.args
            while lst.is_cons:
                acc = cons(value, cons(x, acc))
                x, lst = lst.args
            return cons(x, acc)
        else:
            return self

    #
    # Reorganizing the list
    #
    def reverse(lst):  # noqa: N805
        """
        Reversed copy of the list.
        """

        acc = Nil
        while lst.is_cons:
            x, lst = lst.args
            acc = acc.cons(x)
        return acc

    def sorted(self, **kwargs):
        """
        A sorted version of the list.
        """
        return linklist(sorted(self, **kwargs))

    def partition(self, predicate):
        """
        Partition list on predicate.
        """

        neg_predicate = lambda x: not predicate(x)
        start = self.__class__(itertools.takewhile(neg_predicate, self))

        end = self
        for _ in start:
            end = end.tail
        return start, end

    #
    # Filtering, mapping and folding
    #
    def filter(self, predicate):
        """
        Return a filtered copy with only the items that satisfy the given
        predicate.
        """
        return _link_list(x for x in self if predicate(x))

    def maybe_map(self, func):
        """
        Apply function that returns Maybes and keep only the valid results.
        """
        results = (func(x) for x in self)
        return _link_list(x.value for x in results if x.is_just)

    def index_map(self, func):
        """
        Maps a function that the pair (i, value) for value in position i.
        """
        return _link_list(func(i, x) for i, x in enumerate(self))

    def foldl(self, func, start):
        """
        Apply function to reduce a list from the left.
        """
        return functools.reduce(func, self, start)

    def foldr(self, func, start):
        """
        Apply function to reduce a list from the right.
        """
        return functools.reduce(flip(func), self.reverse(), start)

    def fold(self, func, start):
        """
        Reduce list with the most efficient implementation, which in case of
        a list is foldl.
        """
        return self.foldl(func, start)

    def scanl(self, func, start):
        """
        Like foldl, but return a list with all intermediate results.
        """
        cons = Cons
        scan_func = lambda x, y: cons(func(x, y.head), y)
        return functools.reduce(scan_func, self, cons(start, Nil))

    def scanr(self, func, start):
        """
        Like foldr, but return a list with all intermediate results.
        """
        cons = Cons
        func = flip(func)
        scan_func = lambda x, y: cons(func(x, y.head), y)
        return functools.reduce(scan_func, self.reverse(), cons(start, Nil))

    #
    # Monadic interface
    #
    def map(self, func):
        """
        Maps function into list.
        """
        return _link_list(map(func, self))

    def map_bound(self, func):
        """
        Maps a function that return sequences into the list and flatten all
        intermediate results.
        """

        def iter_all():
            for x in self:
                yield from func(x)

        return _link_list(iter_all())


class Cons(List):
    """
    A link in the linked list.
    """

    args = opt([('head', object), ('tail', List)])

    __bool__ = lambda x: True


class Nil(List):
    """
    Terminal element in a linked list.

    Represents an empty list.
    """

    __bool__ = lambda x: False

    # Fast-track a few methods to Nil instances
    def __getitem__(self, i):
        raise IndexError(i)

    def intersperse(self, value):
        return self


Nil = List.Nil = Nil()
List.Cons = Cons


def linklist(seq):
    """
    Creates a classical singly-linked List object from sequence.

    >>> linklist([1, 2, 3])
    linklist([1, 2, 3])
    """

    try:
        size = len(seq)
    except TypeError:
        pass
    else:
        if size < 256:
            return _link_list_recur(iter(seq))
    return _link_list(seq)


def _link_list(seq):
    cons = Cons
    xs = List.Nil
    for x in reversed(seq):
        xs = cons(x, xs)
    return xs


def _link_list_recur(seq):
    try:
        x = next(seq)
        print(x)
    except StopIteration:
        return Nil
    else:
        return Cons(x, _link_list_recur(seq))
