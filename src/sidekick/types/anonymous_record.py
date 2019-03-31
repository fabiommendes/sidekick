import collections.abc

from types import SimpleNamespace, MappingProxyType


class _BaseSimpleNamespace(SimpleNamespace):
    # Common methods for record and namespace
    __slots__ = ()
    _meta = property(lambda self: Meta(self))

    def __repr__(self):
        items = sorted(self.__dict__.items(), key=lambda x: x[0])
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join("%s=%r" % item for item in items),
        )

    def __getitem__(self, key):
        return self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__.items())

    def __init__(self, *args, **kwargs):
        if args:
            data, = args
            kwargs = dict(data, **kwargs)
        super().__init__(**kwargs)

    def __json__(self):
        return dict(self.__dict__)


class record(_BaseSimpleNamespace):  # noqa: N801
    """
    A anonymous record type.
    """

    __slots__ = ()

    def __hash__(self):
        return hash(tuple(self.__dict__.values()))

    def __setattr__(self, attr, value):
        raise AttributeError("cannot set attribute: immutable type")

    M = property(lambda self: MapView(self))


class namespace(_BaseSimpleNamespace):
    """
    A mutable record type.
    """

    __slots__ = ()
    M = property(lambda self: MutableMapView(self))


class MapView(collections.abc.Mapping):
    """
    A dict-like interface for record objects.
    """

    __slots__ = ('_record',)

    def __init__(self, data):
        self._record = data

    def __iter__(self):
        return iter(self._record._meta.fields)

    def __getitem__(self, key):
        if not (isinstance(key, str) and not key.startswith("_")):
            raise KeyError(key)
        try:
            return getattr(self._record, key)
        except AttributeError:
            raise KeyError(key)

    def __len__(self):
        return len(self._record._meta.fields)

    def __repr__(self):
        return repr(dict(self._record))


class MutableMapView(MapView, collections.abc.MutableMapping):
    """
    MapView that accepts mutation.
    """

    __slots__ = ()

    def __setitem__(self, key, value):
        setattr(self._record, key, value)

    def __delitem__(self, key):
        self._record.__delattr__(key)


class MetaMixin:
    """
    Common implementations of Meta for anonymous and class based records.
    """
    __slots__ = ()

    def __iter__(self):
        raise NotImplementedError

    def as_dict(self, obj):
        """
        Convert a record instance as a Python dictionary
        """
        return {k: getattr(obj, k) for k in self}

    def as_tuple(self, obj):
        """
        Convert record to tuple of values.
        """
        return tuple(getattr(obj, k) for k in self)

    def items(self, obj):
        """
        An iterator over all (field_name, value) pairs of a record.
        """
        return ((k, getattr(obj, k)) for k in self)


class Meta(MetaMixin):
    """
    Implements the _meta attribute of anonymous records.
    """
    defaults = MappingProxyType({})
    fields = property(lambda self: tuple(self))
    types = property(lambda self: {k: object for k in self})

    def __init__(self, data):
        self._data = data

    def __iter__(self):
        yield from self._data.__dict__
