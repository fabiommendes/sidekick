from functools import lru_cache

from ..utils import snake_case

__all__ = ['union']


class Meta:
    """
    Meta-information about Union type hierarchies.
    """

    def __init__(self, cls):
        self.union = cls
        self.cases = {}

    def add_case(self, name, case):
        self.cases[name] = case


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
    _meta: Meta

    def __new__(mcs, *args, **kwargs):
        # Prepare arguments
        name, *args = args
        bases, *args = args if args else ((),)
        ns, = args if args else ({},)
        ns.setdefault('__slots__', ())
        mcs.check_bases(bases)
        kwargs.update(ns.get('__annotations__', {}))

        # Construct union type tree
        new = mcs.create_base_type(name, bases, ns, kwargs)
        [new.add_case(*item) for item in kwargs.items()]
        return new

    @classmethod
    def create_base_type(mcs, name, bases, ns, cases) -> 'union':
        """
        Create base class of a union type.
        """

        new = type.__new__(mcs, name, bases, ns)
        for name in cases:
            set_default_attr(new, query_name(name), False)
        new._meta = Meta(new)
        return new

    @classmethod
    def check_bases(mcs, bases):
        pass

    def create_case_type(cls, name, base):
        """
        Create case class with given base for a union type.
        """

        metaclass = case_metaclass(type(base))
        new = metaclass(name, (base, cls), {'__slots__': ()})
        set_default_attr(new, query_name(name), True)
        return new

    def add_case(cls, name, base):
        """
        Add case to the union type.
        """
        case = cls.create_case_type(name, base)
        cls._meta.add_case(name, case)
        setattr(cls, name, case)
        return case

    def __init__(cls, *args, **kwargs):
        super().__init__(*args)

    def __call__(cls, *args, **kwargs):
        raise TypeError(
            "cannot instantiate abstract class. "
            "Please instantiate one of the concrete cases"
        )


class CaseMeta(union):
    """
    Metaclass for cases.
    """

    def __new__(mcs, name, bases, ns):
        return super().__new__(mcs, name, bases, ns)

    __call__ = type.__call__


# ------------------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------------------

@lru_cache(None)
def case_metaclass(typ):
    """
    Creates a compatible metaclass for the given type.
    """
    if typ is type:
        return CaseMeta
    return type('CaseMeta', (CaseMeta, typ), {})


def query_name(name):
    name = 'is_' + snake_case(name)
    if not name.isidentifier() or not name:
        raise ValueError('invalid python identifier' + name)
    return name


def set_default_attr(obj, attr, value, own=True):
    """Set attribute if it does not exist in object."""
    if own:
        if not attr in obj.__dict__:
            setattr(obj, attr, value)
    else:
        if not hasattr(obj, attr):
            setattr(obj, attr, value)
