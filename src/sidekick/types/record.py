import collections.abc
import keyword
from types import SimpleNamespace

NOT_GIVEN = object()
__all__ = ['Record', 'Namespace', 'record', 'record_to_dict', 'namespace', 'field']


#
# Record and namespace type
#
class RecordMeta(type):
    """
    Metaclass for Record types.
    """

    _record_base = None
    _meta = None

    def __new__(mcs, name, bases, ns, use_invalid=False, **kwargs):
        if mcs._record_base is None:
            return super().__new__(mcs, name, bases, ns)
        else:
            fields = extract_fields(ns)
            return new_record_type(name, fields, bases, ns, **kwargs)

    def __init__(cls, name, bases, ns, **kwargs):
        super().__init__(name, bases, ns)

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    def define(self, name, fields, bases=(), ns=None, use_invalid=False):
        """
        Declare a new record class.

        Args:
            name:
                The name of the
            fields:
                A list of field names or field declarations using the
                func:`sidekick.field` function.
            bases:
                An optional list of base classes for the derived class. By
                default, it has a single base of :cls:`sidekick.Record`.
            ns:
                An optional dictionary of additional methods and properties
                the resulting record class declares.
            use_invalid:
                If True, accept invalid Python names as record fields. Those
                fields are still available from the getattr() and setattr()
                interfaces but are very inconvenient to use.

        Usage:

            >>> Point = Record.define('Point', ['x', 'y'])
            >>> Point(1, 2)
            Point(1, 2)


        Returns:
            A new Record subclass.
        """
        bases = (Record,) if bases is None else tuple(bases)
        return new_record_type(name, fields, bases, ns or {}, use_invalid)

    def namespace(self, name, fields, bases=(), ns=None, use_invalid=False):
        """
        Like meth:`sidekick.Record.define`, but declares a mutable record
        (a.k.a, namespace).
        """
        bases = (Namespace,) if bases is None else tuple(bases)
        ns = ns or {}
        return new_record_type(name, fields, bases, ns, use_invalid, is_mutable=True)



def extract_fields(ns):
    """
    Extract a list of field values from a namespace dictionary.
    """

    fields = [(k, v) for (k, v) in ns.items() if isinstance(v, field)]
    for i, (name, value) in enumerate(fields):
        if value.name is None:
            fields[i] = field(name, value.type, value.default)
        del ns[name]
    return fields


def new_record_type(name: str, fields: list, bases: tuple, ns: dict,
                    use_invalid=False, is_mutable=False):
    """
    Worker function for Record.declare and Record.declare_namespace.
    """
    clean_fields = []
    for f in fields:
        if isinstance(f, str):
            f = field(f, object)
        elif not isinstance(f, field):
            msg = 'fields must be strings or field instances, got: %r'
            raise TypeError(msg % f.__class__.__name__)

        if f.name is None:
            raise TypeError('must use named fields: %s' % f)
        clean_fields.append(f)
    meta_info = Meta(clean_fields)

    bases = tuple(x for x in bases if x is not RecordMeta._record_base)
    base_ns = make_record_namespace(meta_info, use_invalid, is_mutable)
    ns = dict(base_ns, **ns)
    ns['_meta'] = meta_info

    # Create class and update the init method
    cls: RecordMeta = type.__new__(RecordMeta, name, bases, ns)
    init = make_init_function(cls)
    if not hasattr(cls, '_init'):
        cls._init = init
    if not '__init__' in ns:
        cls.__init__ = init
    return cls


def make_record_namespace(meta_info, use_invalid=False, is_mutable=False):
    fields = meta_info.fields

    # Check if any name is invalid
    if not use_invalid:
        for name in fields:
            if keyword.iskeyword(name):
                raise ValueError('%s is an invalid field name' % name)

    ns = dict(__slots__=tuple(fields), **RECORD_NAMESPACE)
    if not is_mutable:
        hash_function = (lambda self: hash(tuple(self)))
        ns['__hash__'] = hash_function
        ns['__setattr__'] = record.__setattr__
    return ns


class Record(metaclass=RecordMeta):
    """
    Base class for Record types.

    A records is a lightweight class that have only a fixed number of
    attributes. It is analogous to a C struct type.

    Record types can be used to hold data or as a basis for a no-boilerplate
    class.
    """

    __slots__ = ()

    _view = property(lambda self: View(self))
    _meta = None

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(repr(getattr(self, x)) for x in self._meta.fields)
        )

    def __eq__(self, other):
        if isinstance(other, (type(self), record, namespace)):
            return len(self) == len(other) and \
                   all(getattr(self, k) == getattr(other, k)
                       for k in self._meta.fields)
        return NotImplemented

    def __getstate__(self):
        return tuple(self._view.values())

    def __setstate__(self, state):
        # noinspection PyArgumentList
        self.__init__(*state)

    def __json__(self):
        return dict(self._view)

    def __hash__(self):
        return hash(tuple(self))

    def __len__(self):
        return len(self._meta.fields)

    # Support conversion to dict through iteration in (attr, value) pairs.
    def __iter__(self):
        return ((f, getattr(self, f)) for f in self._meta.fields)


class Namespace(metaclass=RecordMeta, is_mutable=True):
    """
    A mutable record-like type.
    """

    __slots__ = ()


RECORD_NAMESPACE = dict(Record.__dict__.items())
del RECORD_NAMESPACE['__module__']
del RECORD_NAMESPACE['__slots__']
del RECORD_NAMESPACE['__doc__']

RecordMeta._record_base = Record


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
        return dict(self.__dict__)

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

    has_default = property(lambda self: self.default is not NOT_GIVEN)
    has_name = property(lambda self: self.name is not None)

    def __init__(self, *args, default=NOT_GIVEN):
        if len(args) == 3:
            if default is not NOT_GIVEN:
                msg = 'cannot pass default as positional and keyword argument'
                raise TypeError(msg)
            name, tt, default = args
        elif len(args) == 2:
            name, tt = args
        elif len(args) == 1:
            arg, = args
            if isinstance(arg, str):
                name, tt = arg, object
            else:
                name, tt = None, arg
        elif len(args) > 3:
            n = len(args)
            msg = 'field accept at most 3 positional arguments, %s given' % n
            raise TypeError(msg)
        else:
            name, tt = None, object

        self.name = name
        self.default = default
        self.type = tt

    def __repr__(self):
        if self.type is object:
            tt = ''
        else:
            tt = self.type.__name__
        if self.default is NOT_GIVEN:
            default = ''
        else:
            default = ', ' + repr(self.default)
        return 'field(%s%s)' % (tt, default)


class Meta:
    def __init__(self, fields):
        self.fields = []
        self.types = []
        self.defaults = {}
        for f in fields:
            if f.name is None:
                raise TypeError('cannot create class with anonymous fields')
            self.fields.append(f.name)
            self.types.append(f.type)

            if f.has_default:
                self.defaults[f.name] = f.default

        self.fields = tuple(self.fields)
        self.types = tuple(self.types)

    def as_dict(self, obj):
        """
        Convert a record instance as a Python dictionary
        """
        return {k: getattr(obj, k) for k in self.fields}

    def as_tuple(self, obj):
        """
        Convert record to tuple.
        """
        return tuple(getattr(obj, k) for k in self.fields)

    def items(self, obj):
        """
        An iterator over all (field_name, value) pairs of a record.
        """
        return {(k, getattr(obj, k)) for k in self.fields}


class View(collections.abc.Mapping):
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


class AnonymousRecordView(View):
    def __iter__(self):
        return iter(self._data.__dict__)

    def __len__(self):
        return len(self._data.__dict__)

    def __getitem__(self, key):
        return self._data.__dict__[key]


#
# Utility functions
#
def record_to_dict(obj: Record):
    """
    Converts a record/namespace to a dictionary.

    Notes:
        If you want to convert a dict to a record, simply call ``record(**D)``.
    """
    if isinstance(obj, SimpleNamespace):
        return dict(obj.__dict__)
    return dict(obj._view.items())


#
# Private factory functions
#
def make_init_function(cls):
    """
    Create a init function from a list of field names, their respective types
    and a dictionary of defaults.
    """

    # noinspection PyProtectedMember
    meta = cls._meta
    fields = meta.fields
    defaults = meta.defaults
    slots = {f: getattr(cls, f) for f in fields}

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
    ns = {}
    for name, value in defaults.items():
        safe_name = safe_names[name]
        ns['_%s_default' % safe_name] = value
    for name, slot in slots.items():
        safe_name = safe_names[name]
        ns['_%s_getter' % safe_name] = slot.__get__
        ns['_%s_setter' % safe_name] = slot.__set__

    exec(code, ns, ns)
    return ns['__init__']


def make_eq_function(fields):
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
