import sys
from itertools import islice

from .base_magics import DataMagic
from .. import itertools
from ..core import fn, extract_function, Seq


class L(DataMagic, type=list):
    """
    Class for the L magic object.
    """

    def __getitem__(self, item):
        if isinstance(item, slice):
            return fn(lambda obj: self._getslice(obj, item))
        elif isinstance(item, int):
            return fn(lambda obj: self._getindex(obj, item))
        else:
            raise TypeError(f'unsupported type: {type(item).__name__}')

    def _getindex(self, obj, item):
        try:
            return obj[item]
        except TypeError:
            return itertools.nth(item, obj)

    def _getslice(self, obj, s):
        if isinstance(obj, list):
            return obj[s]

        if s.step is not None and s.step < 0:
            result = list(islice(obj, s.start, s.stop, -s.step))
            result.reverse()
            return result

        return list(islice(obj, s.start, s.stop, s.step))

    @staticmethod
    def append(x, lst):
        """Append x to lst *INPLACE* and return lst."""
        lst.append(x)
        return lst

    @staticmethod
    def append_new(x, lst):
        """Return new list with x appended to the end of lst."""
        return [*lst, x]

    @staticmethod
    def clear(lst):
        """Clear list *INPLACE* and return it.

        If input is an iterator, consume it. This obviously doesn't play
        nicely with infinite iterators."""
        try:
            clear = lst.clear
        except AttributeError:
            itertools.consume(lst)
        else:
            clear()
        return lst

    @staticmethod
    def count(value, lst):
        """Count the number of occurrences of value in list."""
        try:
            count = lst.count
        except AttributeError:
            return itertools.count(value, lst)
        else:
            return count(value)

    @staticmethod
    def copy(lst):
        """Return a copy of list. Non-list iterables are converted to lists."""
        if isinstance(lst, list):
            return lst.copy()
        return list(lst)

    @staticmethod
    def extend(self, seq, lst):
        """Extend lst with seq *INPLACE* and return lst."""
        lst.extend(seq)
        return lst

    @staticmethod
    def extend_new(seq, lst):
        """Create new list that extends lst with other."""
        return [*lst, *seq]

    @staticmethod
    def index(value, lst, start=0, stop=sys.maxsize):
        """Return first index of value in lst."""
        try:
            index = lst.index
        except AttributeError:
            return itertools.index(value, lst)
        else:
            return index(value)

    @staticmethod
    def insert(index, obj, lst):
        """Insert obj at given index of lst *INPLACE* and return lst."""
        lst.insert(index, obj)
        return lst

    @staticmethod
    def insert_new(index, obj, lst):
        """Return new list that insert obj at the given position in lst."""
        result = list(lst)
        result.insert(index, obj)
        return result

    @staticmethod
    def pop(idx, lst):
        """Pop element at idx *INPLACE* and return it."""
        idx = -1 if idx is None else idx
        return lst.pop(idx)

    @staticmethod
    def pop_new(idx, lst):
        """Creates a copy of lst and return a tuple of (popped_element, rest)"""
        new = list(lst)
        popped = new.pop(idx)
        return popped, new

    @staticmethod
    def remove(value, lst):
        """Remove first occurrence of value *INPLACE* and return lst"""
        lst.remove(value)
        return lst

    def remove_new(self, value, lst):
        """
        Create a list with the first occurrence of value removed.
        Raises value error if value is not present in list.
        """
        return self.remove(value, list(lst))

    @staticmethod
    def reverse(lst):
        """Reverse list *INPLACE* and return it."""
        lst.reverse()
        return lst

    @staticmethod
    def reverse_new(lst: Seq):
        """Return reversed copy of lst. Alias to the ``reversed`` builtin."""
        return reversed(lst)

    @staticmethod
    def sort(key, lst, *, reverse=False):
        """Sort list with key function *INPLACE* and return it."""
        key = extract_function(key)
        lst.sort(key=key, reverse=reverse)
        return lst

    @staticmethod
    def sort_new(key, lst, *, reverse=False):
        """
        Create new list sorted with key. Equivalent to the ``sorted`` builtin.
        """
        return sorted(lst, key=extract_function(key), reverse=reverse)

    #
    # Extra methods
    #
    def as_list(self, obj, list_type=list):
        """Coerce object to list."""
        return obj if isinstance(obj, list_type) else list_type(obj)

    def discard(self, value):
        def removing(seq):
            res = list(seq)
            try:
                res.remove(value)
            except ValueError:
                pass
            return res

        return removing

    def discard_all(self, value):
        return lambda seq: [x for x in seq if x != value]
