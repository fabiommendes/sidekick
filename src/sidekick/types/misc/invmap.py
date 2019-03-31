from collections.abc import MutableMapping

from sidekick import lazy

__all__ = ['InvMap']


class InvMap(MutableMapping):
    """
    A dictionary-like object with both a direct and inverse mapping.

    ``InvMap`` implements a invertible dictionary that can access `values`
    from `keys` as a regular dictionary, but it can also map `keys` to `values`.
    The inverse relation, which is also an ``InvMap`` instance, can be
    accessed from the ``inv`` attribute of the dictionary.

    Notes:
        Inspired on Josh Bronson's ``bidict`` module
        (http://pypi.python.org/pypi/bidict)
    """
    EMPTY = object()

    @classmethod
    def named(cls, class_name, direct, inverse):
        """
        Returns a ``InvMap`` subclass that have specially named attributes for
        direct and inverse access of the mapping relation.

        Examples:
            >>> Kings = InvMap.named('Kings', 'kings', 'realms')
            >>> x = Kings({'Pele': 'soccer', 'Elvis': "rock'n'roll"})
            >>> x.kings
            Kings({'Pele': 'soccer', 'Elvis': "rock'n'roll"})
            >>> x.realms
            InvMap({'soccer': 'Pele', "rock'n'roll": 'Elvis'})
        """
        ns = {direct: property(lambda x: x),
              inverse: property(lambda x: x.inv)}
        return type(class_name, (InvMap,), ns)

    @lazy
    def inv(self):
        inv = object.__new__(InvMap)
        inv._direct, inv._inverse = self._inverse, self._direct
        inv.inv = self
        return inv

    def __init__(self, *args, **kwds):
        self._direct = dict(*args, **kwds)
        self._inverse = invert_map(self._direct)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, repr(self._direct))

    def __getitem__(self, key):
        return self._direct[key]

    def __len__(self):
        return len(self._direct)

    def __iter__(self):
        return iter(self._direct)

    def __setitem__(self, key, value):
        old_value = self.pop(key, self.EMPTY)

        if value in self._inverse:
            self._direct[key] = old_value
            self._inverse[old_value] = key
            raise ValueError('value exists: %s' % value)
        else:
            self._direct[key] = value
            self._inverse[value] = key

    def __delitem__(self, key):
        old_value = self._direct.pop(key, self.EMPTY)
        self._inverse.pop(old_value, self.EMPTY)

    def copy(self):
        new = object.__new__(type(self))
        new._direct, new._inverse = self._direct.copy(), self._inverse.copy()
        return new


def invert_map(map):
    """
    Inverts map. Raises ValueError if map is not invertible.
    """
    inv = {v: k for k, v in map.items()}
    if len(inv) != len(map):
        raise ValueError('map not invertible!')
    return inv
