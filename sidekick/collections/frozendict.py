__all__ = ["FrozenDict", "FrozenKeyDict"]


def _forbidden(self, *args, **kwargs):
    name = type(self).__name__
    raise KeyError("cannot add or remove keys of %s." % name)


class FrozenKeyDict(dict):
    """
    Dictionary with a immutable set of keys.

    The values associated to each key can change, but new keys cannot be
    added or deleted.
    """

    __slots__ = ()
    __delitem__ = clear = pop = popitem = _forbidden

    def __setitem__(self, k, v):
        if k in self:
            dict.__setitem__(self, k, v)
        else:
            _forbidden(self)

    def setdefault(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            _forbidden(self)

    def update(self, *args, **kwargs):
        if args:
            data = dict(*args, **kwargs)
        else:
            data = kwargs

        changed = set(data) - self.keys()
        if changed:
            raise KeyError(f"cannot add keys: {changed}")
        super().update(data)

    def __repr__(self):
        name = type(self).__name__
        return f"{name}({super().__repr__()})"


class FrozenDict(FrozenKeyDict):
    """
    Immutable dictionary type.
    """

    __slots__ = ("_cached_hash",)
    __delitem__ = __setitem__ = setdefault = update = _forbidden

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
