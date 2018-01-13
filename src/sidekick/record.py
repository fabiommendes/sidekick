import collections
from types import SimpleNamespace
import keyword

NOT_GIVEN = object()


#
# Record and namespace type
#
class RecordMeta(type):
    """
    Metaclass for Record types.
    """

    _record_base = None

    def __new__(cls, name, bases, ns, **kwargs):
        if cls._record_base is None:
            return super().__new__(cls, name, bases, ns)
        else:
            fields = [(k, v) for (k, v) in ns.items() if isinstance(v, field)]
            ns = dict(ns)
            for k, _ in fields:
                del ns[k]
            return cls.new_from_fields(name, bases, fields, ns, **kwargs)

    @classmethod
    def new_from_fields(meta, name, bases, fields, ns=None, **kwargs):
        meta_info = Meta(fields)

        bases = tuple(x for x in bases if x is not meta._record_base)
        base_ns = meta._record_namespace(meta_info, **kwargs)
        namespace = dict(base_ns, **(ns or {}))
        namespace['_meta'] = meta_info

        # Create class and update the init method
        cls = type.__new__(meta, name, bases, namespace)
        init = _mk_init(cls)

        if '_init' not in namespace:
            cls._init = init
        if '__init__' not in namespace:
            cls.__init__ = init
        return cls

    def __init__(cls, name, bases, ns, mutable=False):  # noqa: N805
        pass

    def __prepare__(cls, bases, **kwargs):  # noqa: N805
        return collections.OrderedDict()

    @staticmethod
    def _record_namespace(meta, mutable=False, invalid_names=False):
        fields = meta.fields

        # Check if any name is invalid
        if not invalid_names and any(map(keyword.iskeyword, fields)):
            for name in fields:
                if keyword.iskeyword(name):
                    raise ValueError('%s is an invalid field name' % name)
            raise ValueError('Invalid field names')

        namespace = dict(
            __slots__=tuple(fields),
            __eq__=_mk_eq_function(fields),

            # Representation and serialization
            __repr__=lambda self:
            '%s(%s)' % (
                self.__class__.__name__,
                ', '.join(
                    repr(getattr(self, x)) for x in fields
                )
            ),
            __getstate__=lambda self: tuple(self._view.values()),
            __setstate__=lambda self, state: self.__init__(*state),
            __json__=lambda self: dict(self._view),

            # Support conversion to dict through iteration
            __iter__=lambda self:
            ((field, getattr(self, field)) for field in fields),

            # Views
            _view=property(RecordView),
        )

        # Final adjustments
        if not mutable:
            namespace['__setattr__'] = \
                record.__setattr__
            namespace['__hash__'] = \
                lambda self: hash(tuple(self._view.values()))
        return namespace


class Record(metaclass=RecordMeta):
    """
    Base class for Record types.

    A records is a lightweight class that have only a fixed number of
    attributes. It is analogous to a C struct type.

    Record types can be used to hold data or as a basis for a no-boilerplate
    class.
    """

    __slots__ = ()


class Namespace(metaclass=RecordMeta, mutable=True):
    """
    A mutable record-like type.
    """

    __slots__ = ()


RecordMeta._record_base = Record


def make_record(name, attrs, invalid_names=False):
    """
    Return a new record type with the given name and attributes.

    Usage:

        >>> Point = make_record('Point', ['x', 'y'])
        >>> Point(1, 2)
        Point(1, 2)
    """
    return _make_record(name, attrs, Record, invalid_names)


def make_namespace(name, attrs, invalid_names=False):
    """
    Like make_record(), but return a mutable Namespace type.
    """
    return _make_record(name, attrs, Namespace, invalid_names, mutable=True)


def _make_record(name, attrs, base, invalid_names=False, mutable=False):
    fields = [(attr, field()) for attr in attrs]
    kwargs = {'invalid_names': invalid_names, 'mutable': mutable}
    return RecordMeta.new_from_fields(name, (base,), fields, {}, **kwargs)


#
# Simple record types for single-time uses.
#

class BaseSimpleNamespace(SimpleNamespace):
    # Common methods between record and namespace
    __slots__ = ()

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
        return self.__dict__

    _view = property(lambda self: AnonymousRecordView(self))


class record(BaseSimpleNamespace):  # noqa: N801
    """
    A anonymous record type.
    """
    __slots__ = ()

    def __repr__(self):
        items = sorted(self.__dict__.items(), key=lambda x: x[0])
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % item for item in items)
        )

    def __hash__(self):
        return hash(tuple(self.__dict__.values()))

    def __setattr__(self, attr, value):
        raise AttributeError('cannot set attribute: immutable type')


class namespace(BaseSimpleNamespace):
    """
    A mutable record type.
    """
    __slots__ = ()


#
# Utility classes
#
class field:  # noqa: N801
    """
    A class that holds information from a field of a record type.
    """

    @property
    def has_default(self):
        return self.default is not NOT_GIVEN

    def __init__(self, type=None, default=NOT_GIVEN):
        self.default = default
        self.type = type

    def __repr__(self):
        if self.type is None:
            type = ''
        else:
            type = self.type.__name__
        if self.default is NOT_GIVEN:
            default = ''
        else:
            default = ', ' + repr(self.default)
        return 'field(%s%s)' % (type, default)


class Meta:
    def __init__(self, fields):
        self.fields = tuple(k for k, _ in fields)
        self.types = tuple(v.type for _, v in fields)
        self.defaults = {k: v.default for k, v in fields
                         if v.default is not NOT_GIVEN}


class RecordView(collections.Mapping):
    """
    A dict-like view of a record object.
    """

    def __init__(self, data):
        self._data = data

    def __iter__(self):
        return iter(self._data._meta.fields)

    def __getitem__(self, key):
        if not (isinstance(key, str) and not key.startswith('_')):
            raise KeyError(key)
        try:
            return getattr(self._data, key)
        except AttributeError:
            raise KeyError(key)

    def __len__(self):
        return len(self._data._meta.fields)

    def __repr__(self):
        return repr(dict(self._data))


class AnonymousRecordView(RecordView):
    def __iter__(self):
        return iter(self._data.__dict__)

    def __len__(self):
        return len(self._data.__dict__)

    def __getitem__(self, key):
        return self._data.__dict__[key]


#
# Private factory functions
#
def _mk_init(cls):
    """
    Create a init function from a list of field names, their respective types
    and a dictionary of defaults.
    """

    fields = cls._meta.fields
    types = cls._meta.types
    defaults = cls._meta.defaults
    slots = {field: getattr(cls, field) for field in fields}

    # Mapping from names to safe names
    safe_names = {}
    for name in fields:
        safe_names[name] = name + '_' if keyword.iskeyword(name) else name
    if len(safe_names) != len(set(safe_names.values())):
        msg = 'collision between escaped field names and given field names'
        raise ValueError(msg + ': %s' % fields)

    # Create argument list
    args = []
    for name in fields:
        safe_name = safe_names[name]
        if name in defaults:
            args.append('%s=_%s_default' % (safe_name, safe_name))
        else:
            args.append(safe_name)
    args = ', '.join(args)

    # Body of the __init__ function
    body = []
    for name in fields:
        safe_name = safe_names[name]
        slot_name = '_%s_setter' % safe_name
        body.append('%s(self, %s)' % (slot_name, safe_name))
    body = '\n    '.join(body)

    # Complete source for the __init__ function
    code = (
        'def __init__(self, {args}):\n'
        '    {body}'
    ).format(args=args, body=body or 'pass')

    # Initialize defaults
    namespace = {}
    for name, value in defaults.items():
        safe_name = safe_names[name]
        namespace['_%s_default' % safe_name] = value
    for name, slot in slots.items():
        safe_name = safe_names[name]
        namespace['_%s_getter' % safe_name] = slot.__get__
        namespace['_%s_setter' % safe_name] = slot.__set__

    exec(code, namespace, namespace)
    return namespace['__init__']


def _mk_eq_function(fields):
    """
    Create a __eq__ method from a list of (name, field) tuples.
    """

    def __eq__(self, other):  # noqa: N802
        if isinstance(other, self.__class__):
            return all(
                getattr(self, f) == getattr(other, f) for f in fields
            )
        return NotImplemented

    return __eq__


#
# Utility functions
#
def record_to_dict(record: Record):
    """
    Converts a record/namespace to a dictionary.

    Notes:
        If you want to convert a dict to a record, simply call ``record(**D)``.
    """
    if isinstance(record, SimpleNamespace):
        return dict(record.__dict__)
    return dict(record._view.items())
