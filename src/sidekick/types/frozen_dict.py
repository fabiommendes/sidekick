__all__ = ['FrozenDict', 'FrozenKeyDict']


class FrozenKeyDict(dict):
    """
    Dictionary with a immutable set of keys.

    The values associated to each key can be change, but new keys cannot be
    added or deleted.
    """

    __slots__ = ()

    # noinspection PyUnusedLocal
    def _forbidden_method_error(self, *args, **kwds):
        tname = type(self).__name__
        raise KeyError('cannot add or remove keys of %s.' % tname)

    __delitem__ = clear = pop = popitem = _forbidden_method_error

    def __setitem__(self, k, v):
        if k in self:
            dict.__setitem__(self, k, v)
        else:
            self._forbidden_method_error()

    def setdefault(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            self._forbidden_method_error()

    def update(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        changed = set(data) - self.keys()
        if changed:
            raise KeyError(f'cannot add keys: {changed}')
        super().update(data)

    def __repr__(self):
        tname = type(self).__name__
        return f"{tname}({super().__repr__()})"


class FrozenDict(FrozenKeyDict):
    """
    Immutable dictionary type.
    """

    __slots__ = ('_cached_hash',)
    __delitem__ = __setitem__ = setdefault = update = \
        FrozenKeyDict._forbidden_method_error

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            try:
                items = sorted(self.items(), key=lambda item: hash(item[0]))
                self._cached_hash = hash(tuple(items))
            except TypeError:
                self._cached_hash = -1
                raise
            return self._cached_hash
