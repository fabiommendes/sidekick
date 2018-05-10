import collections
import functools
import itertools

from .union import Union, opt

flip = (lambda f: lambda x, y: f(y, x))


class ListMeta(type(Union), type(collections.Sequence)):
    """
    Metaclass for List type.
    """


class List(Union, collections.Sequence, metaclass=ListMeta):
    """
    An immutable singly-linked list.
    """

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
        while lst.is_cons:
            x = lst.head
            lst = lst.tail
            yield x

    def __len__(lst):  # noqa: N805
        size = 0
        while lst.is_cons:
            lst = lst.tail
            size += 1
        return size

    def __getitem__(lst, i):  # noqa: N805
        if i < 0:
            raise IndexError('negative indexes not supported')
        if lst.is_nil:
            raise IndexError(i)
        for idx in range(i + 1):
            try:
                x = lst.head
                lst = lst.tail
            except AttributeError:
                raise IndexError(i)
        return x

    def __eq__(self, other):
        if isinstance(other, List):
            a, b = self, other
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
        Return a list with at most the first n elements.
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
        Return a list that removes at most the first n elements.
        """

        for i in range(n):
            try:
                x, lst = lst.args
            except AttributeError:
                break
        return lst

    def interspace(self, value):
        """
        Interspace list elements with value.
        """

        cons = Cons
        acc = Nil
        lst = self.reverse()
        x, lst = lst.args
        while lst.is_cons:
            acc = cons(value, cons(x, acc))
            x, lst = lst.args
        return cons(x, acc)

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
        return linklist(x for x in self if predicate(x))

    def maybe_map(self, func):
        """
        Apply function that returns a Maybe to list and keep only the valid
        results.
        """
        results = (func(x) for x in self)
        return linklist(x.value for x in results if x.is_just)

    def index_map(self, func):
        """
        Maps a function that the pair (i, value) for value in position i.
        """
        return linklist(func(i, x) for i, x in enumerate(self))

    def foldl(self, func, start):
        """
        Apply function to reduce a list from the left.
        """
        return functools.reduce(func, self, start)

    def foldr(self, func, start):
        """
        Apply function to reduce a list from the right.
        """
        return functools.reduce(flip(func), self.reversed(), start)

    def fold(self, func, start):
        """
        Reduce list with the most efficient implementation, which in case of
        a list is foldl.

        This method should only be used if the function application is
        associative (e.g., func x, y: x * y).
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
        return functools.reduce(scan_func, self.reversed(), cons(start, Nil))

    #
    # Monadic interface
    #
    def map(self, func):
        """
        Maps function into list.
        """
        return linklist(map(func, self))

    def map_bound(self, func):
        """
        Maps a function that returns a list into the list.

        The result is obtained by flatting all intermediate results.
        """

        def iter_all():
            for x in self:
                yield from func(x)

        return linklist(iter_all())


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

    # Fasttrack a few methods to Nil instances
    def __getitem__(self, i):
        raise IndexError(i)

    def interspace(self, value):
        return self


# Fixme: should return a singleton instance
Nil = List.Nil


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
            ls = _link_list_recur(iter(seq))
            print(ls)
            return ls
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
