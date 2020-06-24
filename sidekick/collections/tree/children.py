from ...typing import MutableSequence, List, T


class Children(MutableSequence):
    """
    List of children nodes of tree.
    """

    __slots__ = ("_owner", "_data")
    _data: List[T]
    _owner: T

    def __init__(self, owner, data):
        self._data = data
        self._owner = owner

    def __getitem__(self, i):
        return self._data[i]

    def __setitem__(self, i: int, obj: T) -> None:
        if isinstance(i, int):
            obj = self._owner._check_child(obj)
        elif isinstance(i, slice):
            obj = [self._owner._check_child(node) for node in obj]
        else:
            raise TypeError(f"invalid index: {i.__class__.__name__}")
        self._data[i] = obj

    def __delitem__(self, i):
        data = self._data[i]
        if isinstance(i, slice):
            for node in data:
                node._parent = None
        else:
            data._parent = None

        del self._data[i]

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self):
        data = ", ".join(map(repr, self._data))
        return f"[{data}]"

    def insert(self, index: int, obj: T) -> None:
        obj = self._owner._check_child(obj)
        self._data.insert(index, obj)
