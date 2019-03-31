from collections.abc import MutableMapping

__all__ = ['IdMap']
dict_delitem = dict.__delitem__
dict_getitem = dict.__getitem__
dict_setitem = dict.__setitem__
dict_contains = dict.__contains__
dict_values = dict.values


class IdMap(MutableMapping, dict):
    """A dictionary that handle keys by identity, not value.

    Keys of an `IdDict` can be non-hashable types. Two keys that have the
    same value, but different identities are considered to be different keys.
    """

    def __init__(self, iterable=(), **kwds):
        dict.__init__(self)
        self.update(iterable, **kwds)

    def __len__(self):
        return dict.__len__(self)

    def __delitem__(self, key):
        id_key = id(key)
        try:
            dict_delitem(self, id_key)
        except KeyError:
            raise KeyError(key)

    def __getitem__(self, key):
        return dict_getitem(self, id(key))[1]

    def __iter__(self):
        yield from (key for key, _ in dict_values(self))

    def __setitem__(self, key, value):
        id_key = id(key)
        dict_setitem(self, id_key, (key, value))

    def __repr__(self):
        name = type(self).__name__
        data = ', '.join('%r: %r' % item for item in self.items())
        return '%s({%s})' % (name, data)

    def __contains__(self, key):
        return dict_contains(self, id(key))
