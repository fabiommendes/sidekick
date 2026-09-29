from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any, ItemsView, Iterator, KeysView, NoReturn, ValuesView, Type

from .util import k, v

__all__ = ["FrozenDict", "FrozenKeyDict", "InvMap", "FrozenInvMap"]

NOT_GIVEN: Any = object()


def _forbidden(self) -> NoReturn:
    typ = type(self).__name__
    raise KeyError(f"cannot add or remove keys of {typ}.")


class _WrappedDict(Mapping[k, v]):
    """
    Common implementation for FrozenKeyDict and FrozenDict.
    """

    __slots__ = ("_data",)
    _data: dict[k, v]

    def __init__(self, data, **kwargs):
        self._data = dict(data)
        self._data.update(kwargs)

    def __setitem__(self, k, v) -> None:
        if k in self._data:
            self._data[k] = v
        else:
            _forbidden(self)

    def __getitem__(self, key: k) -> v:
        return self._data[key]

    def __iter__(self) -> Iterator[k]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        name = type(self).__name__
        return f"{name}({self._data!r})"

    def __contains__(self, key) -> bool:
        return key in self._data

    def get(self, key, default=None):
        "D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."
        return self._data.get(key, default)

    def keys(self) -> KeysView[k]:
        "D.keys() -> a set-like object providing a view on D's keys"
        return self._data.keys()

    def items(self) -> ItemsView[k, v]:
        "D.items() -> a set-like object providing a view on D's items"
        return self._data.items()

    def values(self) -> ValuesView[v]:
        "D.values() -> an object providing a view on D's values"
        return self._data.values()

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        elif isinstance(other, _WrappedDict):
            return self._data == other._data
        return self._data == dict(other.items())


class FrozenKeyDict(_WrappedDict[k, v]):
    """
    Dictionary with a immutable set of keys.

    The values associated to each key can change, but new keys cannot be
    added or deleted.
    """

    __slots__ = ()

    def setdefault(self, key, default: v | None = None) -> v | None:
        try:
            return self._data[key]
        except KeyError:
            _forbidden(self)

    def update(self, other=(), /, **kwargs) -> None:
        extra = dict(other)
        extra.update(kwargs)
        new_keys = set(extra) - self.keys()
        if new_keys:
            raise KeyError(f"cannot add keys: {new_keys}")
        self._data.update(extra)


class FrozenDict(_WrappedDict[k, v]):
    """
    Immutable dictionary type.
    """

    __slots__ = ("_hash",)

    def __hash__(self) -> int:
        try:
            return self._hash  # type: ignore
        except AttributeError:
            items = sorted((hash(k), v) for k, v in self.items())
            try:
                self._hash = hash(tuple(items))
            except TypeError:
                self._hash = -1
                raise
            return self._hash


class _WrappedInvMap(_WrappedDict[k, v]):
    """
    Common implementations for InvMap and FrozenInvMap
    """

    __slots__ = ("_inverse", "_inv")
    _inverse: dict[v, k]
    _inv: _WrappedInvMap[v, k]

    @classmethod
    def named(cls, name: str, direct: str, inverse: str) -> Type[InvMap]:
        """
        Returns a ``InvMap`` subclass that have specially named attributes for
        direct and inverse access of the mapping relation.

        Examples:
            >>> Kings = InvMap.named('Kings', 'kings', 'realms')
            >>> x = Kings({'Pele': 'soccer', 'Elvis': "rock'n'roll"})
            >>> x.kings
            Kings({'Pele': 'soccer', 'Elvis': "rock'n'roll"})
            >>> x.realms
            Kings({'soccer': 'Pele', "rock'n'roll": 'Elvis'})
        """
        ns = {direct: property(lambda x: x), inverse: property(lambda x: x.inv)}
        return type(name, (cls,), ns)

    @property
    def inv(self) -> _WrappedInvMap[v, k]:
        return self._inv

    def __init__(self, other=(), /, **kwargs):
        super().__init__(other, **kwargs)
        self._inverse = invert_dict(self._data)
        self._register_inverse()

    def _register_inverse(self) -> None:
        inv: _WrappedInvMap[v, k] = object.__new__(type(self))  # type: ignore
        inv._data = self._inverse
        inv._inverse = self._data
        inv._inv = self
        self._inv = inv


class InvMap(_WrappedInvMap[k, v], MutableMapping[k, v]):
    """
    A dictionary-like object with both a direct and inverse mapping.

    :class:`InvMap` implements a invertible dictionary that can access `values`
    from `keys` as a regular dictionary, but it can also map `keys` to `values`.
    The inverse relation, which is also an ``InvMap`` instance, can be
    accessed from the ``inv`` attribute of the dictionary.

    Notes:
        Inspired on Josh Bronson's ``bidict`` module
        (http://pypi.python.org/pypi/bidict)
    """

    __slots__ = ()

    def __setitem__(self, key: k, value: v):
        old_value = self.pop(key, NOT_GIVEN)

        if value in self._inverse:
            self._data[key] = old_value
            self._inverse[old_value] = key
            raise ValueError("value exists: %s" % value)
        else:
            self._data[key] = value
            self._inverse[value] = key

    def __delitem__(self, key):
        value = self._data.pop(key)
        del self._inverse[value]

    def copy(self) -> InvMap[k, v]:
        new = object.__new__(type(self))
        new._data, new._inverse = self._data.copy(), self._inverse.copy()
        new._register_inverse()
        return new


class FrozenInvMap(_WrappedInvMap[k, v]):
    """
    An immutable version of a InvDict.
    """

    __slots__ = ("_hash",)
    __hash__ = FrozenDict.__hash__


def invert_dict(dic: dict[k, v]) -> dict[v, k]:
    """
    Inverts map. Raises ValueError if map is not invertible.
    """
    inv = {v: k for k, v in dic.items()}
    if len(inv) != len(dic):
        raise ValueError("map not invertible!")
    return inv
