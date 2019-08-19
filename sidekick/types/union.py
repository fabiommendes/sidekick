import random
from functools import lru_cache

from .record import Record, clean_field, normalize_field_mapping, RecordMeta
from ..utils import snake_case

__all__ = ['union', 'Case', 'Union']


# ------------------------------------------------------------------------------
# UNION TYPE METACLASSES
# ------------------------------------------------------------------------------

class union(type):
    """
    Create the base class of a union consisted of several different case
    classes.

    Args:
        name (str):
            Name of the Union.
        bases:
            Optional tuple of bases. Passed as second positional argument
        namespace:
            Optional namespace dictionary with methods and class attributes.
        cases (sequence):
            List of case classes that composes the union.
        namespace (mapping):
            An optional namespace to inject into the base class.
    """

    def __new__(mcs, *args, **kwargs):
        # Prepare arguments
        name, *args = args
        bases, *args = args if args else ((),)
        ns, = args if args else ({},)
        bases = mcs.check_bases(bases)

        if all(not isinstance(cls, union) for cls in bases):
            ns.setdefault('__slots__', ())
            kwargs.update(ns.get('__annotations__', {}))
            new = mcs.create_root(name, bases, ns, kwargs)
            for item in kwargs.items():
                new.create_case(*item)
            return new
        else:
            return mcs.create_record_case(name, bases, ns, **kwargs)

    @classmethod
    def create_root(mcs, name, bases, ns, cases) -> 'union':
        """
        Create base class of a union type.
        """

        new = type.__new__(mcs, name, bases, ns)
        new._union = Info(new)
        return new

    @classmethod
    def check_bases(mcs, bases):
        if bases == (Union,):
            return ()
        if sum(1 for cls in bases if isinstance(cls, union)) > 1:
            raise TypeError('cannot inherit from different union types')
        return tuple(cls for cls in bases if cls is not Union)

    @classmethod
    def create_record_case(cls, name, bases, ns, **kwargs):
        """
        Create record type as a new case in union class.
        """

        root, = (cls for cls in bases if isinstance(cls, union))
        annotations = ns.get('__annotations__', {})

        # Record-based class
        if annotations:
            ns.setdefault('__slots__', tuple(annotations))
            metaclass = case_metaclass(type(Record))
            new = RecordMeta.__new__(metaclass, name, (*bases, Record), ns, **kwargs)
            result = new

        # Singleton classes
        else:
            ns['__slots__'] = ()
            new = SingletonMeta(name, (*bases, SingletonMixin), ns, **kwargs)
            result = new()

        root._union.add_case(name, new, singleton=isinstance(new, SingletonMeta))
        return result

    def create_case(cls, name, base):
        """
        Create case class with given base for a union type.
        """
        if base is SingletonCase:
            new = CaseType(name, (base, cls), {'__slots__': ()})
        else:
            metaclass = case_metaclass(type(base))
            new = type.__new__(metaclass, name, (base, cls), {'__slots__': ()})

        is_singleton = isinstance(new, SingletonMeta)
        cls._union.add_case(name, new, singleton=is_singleton)
        return new() if is_singleton else new

    def case(cls, base):
        """
        Decorator that adds case from base class. Notice it constructs the
        intermediate class from the base case.
        """
        return cls.create_case(base.__name__, base)

    def __init__(cls, *args, **kwargs):
        super(type, union).__init__(*args)

    def __call__(cls, *args, **kwargs):
        try:
            constructor = cls.__union_constructor__
        except AttributeError:
            raise TypeError(
                "cannot instantiate abstract class. "
                "Please instantiate one of the concrete cases"
            )
        else:
            return constructor(*args, **kwargs)


class Info:
    """
    Meta-information about Union type hierarchies.
    """

    def __init__(self, cls):
        self.union = cls
        self.cases = {}

    def add_case(self, name, case, singleton=False):
        """
        Register case in union class hierarchy.
        """
        self.cases[name] = case
        type_query = query_name(name)
        setattr(self.union, type_query, False)
        setattr(case, type_query, True)
        setattr(self.union, name, case() if singleton else case)


class CaseType(union):
    """
    Metaclass for cases.
    """

    def __new__(mcs, name, bases, ns, **kwargs):
        return super(union, mcs).__new__(mcs, name, bases, ns)

    __call__ = type.__call__


class SingletonMeta(CaseType):
    """
    Metaclass for unit-like special cases.
    """

    _instance = None

    def __init__(cls, *args, **kwargs):
        super().__init__(*args)
        cls._hash = random.randrange(1, 2 ** 32)
        cls._instance = type.__call__(cls)

    __instancecheck__ = lambda cls, other: other is cls._instance

    def __call__(cls):
        return cls._instance


class SingletonMixin:
    """
    Mixin class that is injected into singleton case classes.
    """

    __slots__ = ()
    _hash = random.randrange(1, 2 ** 32)

    __instancecheck__ = lambda self, other: self is other
    __eq__ = lambda self, other: self is other or NotImplemented
    __hash__ = lambda self: self._hash
    __repr__ = lambda self: self.__class__.__name__
    __iter__ = lambda self: iter(())
    __len__ = lambda self: 0


# ------------------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------------------

# noinspection PyPep8Naming
def Case(*args, **kwargs):
    """
    Declare a record base class for a Union case.
    """
    args = list(map(clean_field, args))
    args.extend(normalize_field_mapping(kwargs))
    attrs = tuple(args)
    return fetch_case(attrs)


@lru_cache(None)
def fetch_case(attrs: tuple):
    if not attrs:
        return SingletonMeta('Case', (SingletonMixin,), {})
    return Record.define('Case', list(attrs))


@lru_cache(None)
def case_metaclass(typ):
    """
    Creates a compatible metaclass for the given type.
    """
    assert issubclass(typ, type), f'Not a type: {typ}'
    if issubclass(typ, CaseType):
        return CaseType
    return type(typ.__name__ + 'Case', (CaseType, typ), {})


def query_name(name):
    name = 'is_' + snake_case(name)
    if not name.isidentifier() or not name:
        raise ValueError('invalid python identifier' + name)
    return name


# We have to declare union a generic value since the meta-type constructor
# explicity checks for the presence of a Union base class.
Union = NotImplemented
Union = union('Union')
SingletonCase = Case()
