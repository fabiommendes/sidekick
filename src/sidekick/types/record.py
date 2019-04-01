import collections.abc
import keyword
from types import MappingProxyType
from typing import Mapping

from .anonymous_record import MutableMapView, MapView, record, namespace, MetaMixin

NOT_GIVEN = object()
Field = collections.namedtuple('Field', ['name', 'type', 'default'])


# ------------------------------------------------------------------------------
# Record meta type
# ------------------------------------------------------------------------------

class RecordMeta(type):
    """
    Metaclass for Record types.
    """

    _meta: 'Meta' = NOT_GIVEN

    def __new__(mcs, name, bases, ns, use_invalid=False, **kwargs):
        if Namespace is NotImplemented:
            return super().__new__(mcs, name, bases, ns)
        else:
            fields = extract_fields_from_annotations(bases, ns)
            return new_record_type(name, fields, bases, ns, mcs=mcs, **kwargs)

    def __init__(cls, name, bases, ns, **kwargs):
        super().__init__(name, bases, ns)

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    def define(self, name: str, fields: list, bases=(), ns: dict = None, use_invalid=False):
        """
        Declare a new record class.

        Args:
            name:
                The name of the
            fields:
                A list of field names or a tuples with (name, type) or even
                (name, type, default). If fields is a mapping, it is treated
                as sequence of (name, type) pairs if values are types or
                (name, default) pairs if values are instances.
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
        if Record not in bases:
            bases = (*bases, Record)
        return new_record_type(name, fields, bases, ns or {}, use_invalid)

    def namespace(self, name: str, fields: list, bases=(), ns: dict = None, use_invalid=False):
        """
        Like meth:`sidekick.Record.define`, but declares a mutable record
        (a.k.a, namespace).
        """
        if Namespace not in bases:
            bases = (*bases, Namespace)
        kwargs = {'use_invalid': use_invalid, 'is_mutable': True}
        return new_record_type(name, fields, bases, ns or {}, **kwargs)


def new_record_type(name: str, fields: list, bases: tuple, ns: dict,
                    use_invalid=False, is_mutable=False, mcs: type = RecordMeta) -> type:
    """
    Create new record type.
    """
    if isinstance(fields, collections.abc.Mapping):
        fields = list(normalize_field_mapping(fields))
    meta_info = Meta([clean_field(f, use_invalid) for f in fields])
    initial_ns = make_record_namespace(bases, meta_info, is_mutable)
    ns = dict(initial_ns, **ns)

    # Create class and update the init method
    cls = type.__new__(mcs, name, bases, ns)
    cls._meta = meta_info
    init = make_init_function(cls)
    if not hasattr(cls, "_init"):
        cls._init = init
    if "__init__" not in ns:
        cls.__init__ = init
    return cls


def clean_field(field, use_invalid=False):
    """
    Coerce argument to a Field instance.
    """
    tt = object
    default = NOT_GIVEN
    if isinstance(field, str):
        name = field
    elif isinstance(field, Field):
        return field
    elif len(field) == 1:
        name, = field
    elif len(field) == 2:
        name, tt = field
    else:
        name, tt, default = field
    if not use_invalid and not is_valid_name(name):
        raise ValueError("%s is an invalid field name" % name)
    return Field(name, tt or object, default)


def normalize_field_mapping(fields):
    """
    Normalize each declaration in a field mapping.
    """
    for name, value in fields.items():
        if isinstance(value, type):
            yield Field(name, value, NOT_GIVEN)
        else:
            if value in (None, ..., NotImplemented):
                yield Field(name, object, value)
            else:
                yield Field(name, type(value), value)


def is_valid_name(name: str) -> bool:
    """
    True if name is a valid attribute name.
    """
    return name.isidentifier() and not keyword.iskeyword(name)


def safe_names(names):
    """
    Receive a list of names and return a map from names to the corresponding
    safe name to use as a Python variable.
    """
    safe_names = {}
    for name in names:
        safe_names[name] = name + "_" if keyword.iskeyword(name) else name
    if len(safe_names) != len(set(safe_names.values())):
        msg = "collision between escaped field names and given field names"
        raise ValueError(msg + ": %s" % names)
    return safe_names


def make_record_namespace(bases, meta_info, is_mutable=False):
    fields = meta_info.fields
    ns = {'__slots__': tuple(fields)}

    if not is_mutable:
        ns.setdefault("__hash__", lambda self: hash(tuple(self)))
        ns["__setattr__"] = record.__setattr__
    return ns


def extract_fields_from_annotations(bases, ns):
    annotations = {}
    annotations.update(ns.get('__annotations__', ()))
    for base in bases:
        if isinstance(base, RecordMeta):
            step = base.__dict__.get('__annotations__', {})
            step.update(annotations)
            annotations = step

    fields = []
    for name, tt in annotations.items():
        try:
            default = ns.pop(name)
        except KeyError:
            default = getattr_from_bases(bases, name, NOT_GIVEN)

        fields.append(Field(name, tt, default))
    return fields


def getattr_from_bases(bases, attr, default):
    for base in bases:
        try:
            return getattr(base, attr)
        except AttributeError:
            pass
    return default


def make_init_function(cls: RecordMeta):
    """
    Create a init function from a list of field names, their respective types
    and a dictionary of defaults.
    """

    # noinspection PyProtectedMember
    meta = cls._meta
    slots = {f: get_slot(cls, f) for f in meta.fields}
    names_map = safe_names(meta.fields)

    # Initialize defaults
    ns = {}
    for name, value in meta.defaults.items():
        safe_name = names_map[name]
        ns["_%s_default" % safe_name] = value
    for name, slot in slots.items():
        safe_name = names_map[name]
        ns["_%s_getter" % safe_name] = slot.__get__
        ns["_%s_setter" % safe_name] = slot.__set__

    code = make_init_function_code(names_map, meta.defaults)
    exec(code, ns, ns)
    return ns["__init__"]


def make_init_function_code(names_map: dict, defaults: Mapping) -> str:
    """
    Return a string with source code for the init function.
    """

    args = []
    for name, safe_name in names_map.items():
        if name in defaults:
            args.append("%s=_%s_default" % (safe_name, safe_name))
        else:
            args.append(safe_name)
    args = ", ".join(args)

    body = []
    for name, safe_name in names_map.items():
        slot_name = "_%s_setter" % safe_name
        body.append("%s(self, %s)" % (slot_name, safe_name))
    body = "\n    ".join(body)

    template = "def __init__(self, {args}):\n    {body}"
    return template.format(args=args, body=body or "pass")


def make_eq_function(fields):
    """
    Create a __eq__ method from a list of (name, field) tuples.
    """

    fields = tuple(fields)

    def __eq__(self, other):  # noqa: N802
        if isinstance(other, self.__class__):
            return all(getattr(self, f) == getattr(other, f) for f in fields)
        return NotImplemented

    return __eq__


def get_slot(cls, name):
    try:
        return getattr(cls, name)
    except AttributeError:
        return property(lambda x: x.__dict__[name],
                        lambda x, v: x.__dict__.__setitem__(name, v))


class Meta(MetaMixin):
    __slots__ = ('fields', 'types', 'defaults')

    def __init__(self, fields):
        self.fields = tuple(f.name for f in fields)
        self.types = tuple(f.type for f in fields)
        self.defaults = MappingProxyType(
            {f.name: f.default for f in fields if f.default is not NOT_GIVEN})

    def __iter__(self):
        yield from self.fields


# ------------------------------------------------------------------------------
# Record classes
# ------------------------------------------------------------------------------
Record = Namespace = NotImplemented


class RecordMixin:
    __slots__ = ()
    _meta: Meta = NOT_GIVEN
    M: Mapping

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(repr(getattr(self, x)) for x in self._meta.fields),
        )

    def __eq__(self, other):
        if isinstance(other, (type(self), record, namespace)):
            return len(self) == len(other) and all(
                getattr(self, k) == getattr(other, k) for k in self._meta.fields
            )
        return NotImplemented

    def __getstate__(self):
        return tuple(self.M.values())

    def __setstate__(self, state):
        # noinspection PyArgumentList
        self.__init__(*state)

    def __json__(self):
        return dict(self.M)

    def __hash__(self):
        return hash(tuple(self))

    def __len__(self):
        return len(self._meta.fields)

    def __iter__(self):
        # Support conversion to dict through iteration in (attr, value) pairs.
        return ((f, getattr(self, f)) for f in self._meta.fields)


# noinspection PyRedeclaration
class Record(RecordMixin, metaclass=RecordMeta):
    """
    Base class for Record types.

    A records is a lightweight class that have only a fixed number of
    attributes. It is analogous to a C struct type.

    Record types can be used to hold data or as a basis for a no-boilerplate
    class.
    """

    __slots__ = ()

    M = property(lambda self: MapView(self))


# noinspection PyRedeclaration
class Namespace(RecordMixin, metaclass=RecordMeta, is_mutable=True):
    """
    A mutable record-like type.
    """

    __slots__ = ()
    M = property(lambda self: MutableMapView(self))
