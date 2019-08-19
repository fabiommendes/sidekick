from collections import namedtuple
from collections.abc import MutableSequence

from ..core import extract_function

tagged = namedtuple('tagged', ['value', 'tag'])
NOT_GIVEN = object()


class TagSeq(MutableSequence):
    """
    A list in which each element can be optionally tagged.
    """
    __slots__ = ('tags', 'data', '_default')

    def __init__(self, data=None, default=None):
        self.data = [] if data is None else data
        self.tags = [default for _ in data]
        self._default = default

    def __getitem__(self, idx):
        return self.data[idx]

    def __len__(self):
        return len(self.data)

    def __delitem__(self, idx):
        del self.data[idx]

    def __setitem__(self, idx, value):
        self.data[idx] = value

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.data)

    def append(self, value, tag=NOT_GIVEN):
        tag = self._default if tag is NOT_GIVEN else tag
        self.data.append(value)
        self.tags.append(tag)

    def insert(self, idx, value, tag=NOT_GIVEN):
        tag = self._default if tag is NOT_GIVEN else tag
        self.data.insert(idx, value)
        self.tags.insert(idx, tag)

    def clear(self):
        self.data.clear()
        self.tags.clear()

    def reverse(self):
        self.data.reverse()
        self.tags.reverse()

    def items(self):
        """
        Iterates over all (obj, tag) pairs.
        """

        for x, y in zip(self.data, self.tags):
            yield tagged(x, y)

    def pop_item(self, index=-1):
        """
        Remove and return a tuple with object and tag at index (default last)
        """
        value = self.data.pop(index)
        tag = self.tags.pop(index)
        return tagged(value, tag)

    def set(self, idx, value, tag=NOT_GIVEN):
        """
        Set value in the given index position.
        """
        self.data[idx] = value
        if tag is not NOT_GIVEN:
            self.tags[idx] = tag

    def get_item(self, idx):
        """
        Return (value, tag) at index.
        """
        return tagged(self.data[idx], self.tags[idx])

    def get_tag(self, idx):
        """
        Return tag at index.
        """
        return self.tags[idx]

    def tag_sort(self, key=None, reverse=False, items=False):
        """Stable sort by tag value *IN PLACE*"""

        if items and key is None:
            raise ValueError('must set key function when items=True')
        if items:
            func = lambda x: key(*x)
        else:
            func = lambda x: key(x[1])
        key = extract_function(key)
        full = sorted(zip(self.data, self.tags), key=func, reverse=reverse)
        self.data[:] = [x for x, _ in full]
        self.tags[:] = [y for _, y in full]

    def tag_count(self, *args, **kwargs):
        """
        Count the number of occurrences of the given tag.
        """
        return self.tags.count(*args, **kwargs)

    def tag_index(self, *args, **kwargs):
        """
        Return the index of the first occurrence of tag.
        """
        return self.tags.index(*args, **kwargs)

    def tag_remove(self, tag):
        """
        Remove the fist occurrence of tag.
        """
        idx = self.tags.index(tag)
        del self.data[idx]
        del self.tags[idx]
