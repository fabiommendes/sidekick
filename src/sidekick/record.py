from collections import OrderedDict
from types import SimpleNamespace


NOT_GIVEN = object()

#
# Simple record types for one-of uses.
#
class record(SimpleNamespace):
    """
    A anonymous record type.
    """

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % item for item in self.__dict__.items())
        )

    def __hash__(self):
        return hash(tuple(self.__dict__.values()))
    
    def __setattribute__(self, attr, value):
        raise TypeError('cannot set attribute: immutable type')


namespace = SimpleNamespace    


#
# The structured Record type and associated types
#
class field:
    """
    A class that holds information from a field of a record type.
    """

    @property
    def has_default(self):
        return self.default is not NOT_GIVEN

    def __init__(self, type=None, default=NOT_GIVEN):
        self.default = default
        self.type = type


class RecordMeta(type):
    """
    Metaclass for Record types.
    """

    _record_base = None

    def __new__(cls, name, bases, ns, mutable=False):
        if cls._record_base is None:
            return super().__new__(cls, name, bases, ns)        
        else:
            bases = tuple(x for x in bases if x is not cls._record_base)
            ns = _update_namespace(cls, ns)

            if mutable:
                del ns['__hash__']
                
            return type(name, bases, ns)

    def __init__(cls, name, bases, ns, mutable=False):
        pass

    def __prepare__(cls, bases, mutable=False):
        return OrderedDict()


class Record(metaclass=RecordMeta):
    """
    Base class for Record types.

    A records is a lightweight class that have only a fixed number of
    attributes. It is analogous to a C struct type. 

    Record types can be used to hold data or as a basis for a no-boilerplate 
    class.
    """

    __slots__ = ()


RecordMeta._record_base = Record


#
# Private factory functions
#
def _update_namespace(cls, ns):
    """
    Update Record class namespace with default implementations.
    """
    
    fields = [(k, v) for k, v in ns.items() if isinstance(v, field)]
    methods = {k: v for k, v in ns.items() if not isinstance(v, field)}

    namespace = dict(
        # Meta information
        _fields=fields,
        _fields_map=dict(fields),

        # Creation methods
        __slots__=tuple(k for k, v in fields),
        __init__=_init_function_factory(fields),

        # Other useful dunder methods
        __repr__=lambda self:
            '%s(%s)' % (
                self.__class__.__name__,
                ', '.join(
                    repr(getattr(self, x)) for x in self._fields_map
                )
            ),
        __hash__=lambda self: hash(tuple(self._iter())),
        __eq__=_eq_function_factory(fields),

        # Private mapping interface
        _getitem=lambda self, item: self._field_getters(item)(self),
        _iter=lambda self: iter(self._fields_map),
        _keys=lambda self: iter(self._fields_map),
        _values=lambda self: (getattr(self, x) for x in self._iter()),
        _items=lambda self: zip(self._keys(), self._values()),
        _get=lambda self, attr, default=None: getattr(self, attr, default),
    )
    return dict(namespace, **methods)


def _init_function_factory(fields):
    """
    Create a init function from a list of (name, field) tuples.
    """

    # Create argument list
    args = ', '.join(
        ('%s=%s_default' % (name, name) if f.has_default else name)
        for name, f in fields
    )
    
    # Body of the __init__ function
    body = '\n    '.join(
        'self.%s = %s' % (name, name)
        for name, f in fields
    )
    
    # Complete source for the __init__ function 
    code = (
        'def __init__(self, {args}):\n'
        '    {body}'
    ).format(args=args, body=body or 'pass')

    # Initialize defaults
    ns = {
        '%s_default' % name: f.default 
        for name, f in fields if f.has_default 
    }
    
    exec(code, ns, ns)
    return ns['__init__']


def _eq_function_factory(fields):
    """
    Create a __eq__ method from a list of (name, field) tuples.
    """

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(
                x == y for x, y in zip(self._values(), other._values())
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
    return dict(record._items())

