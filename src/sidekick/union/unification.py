import abc
from itertools import chain
from weakref import WeakKeyDictionary

from ..text import snake_case

CASE_CLASSES = WeakKeyDictionary()


def create_union(name, cases, inject_bases=None, abstract=True, namespace=None):
    """
    Create the base class of a union consisted of several different case
    classes.

    Args:
        name (str):
            Name of the Union.
        cases (sequence):
            List of case classes that composes the union.
        inject_bases (bool):
            If True, inject the base class in the list of bases for each case
            type.
        abstract (bool):
            If True (default), create base as an Abstract Base Class.
        namespace (mapping):
            An optional namespace to inject into the base class.
    """

    def __init__(self, *args, **kwargs):
        raise TypeError(
            'cannot instantiate base class {}, please instantiate one of the '
            'concrete case classes'.format(name))

    new_type = abc.ABCMeta if abstract else type
    base = new_type(name, (), {'__init__': __init__, **(namespace or {})})
    unify_classes(base, cases, inject_bases=inject_bases)
    return base


def unify_classes(base, cases, inject_bases=None):
    """
    Unify case classes under the same base class.
    """

    cases = sequence(cases)
    check_cases_do_not_participate_in_other_unions(cases)

    # Save constructors and case query attributes
    unify_case_queries(cases, extra=[base])
    for cls in cases:
        setattr_default(base, cls.__name__, cls)

    # Register abstract classes
    if isinstance(base, abc.ABCMeta):
        for cls in cases:
            base.register(cls)

    # Inject base into __bases__ for each case class
    if inject_bases is not False:
        for cls in cases:
            bases = cls.__bases__
            if bases and bases[-1] is object:
                *bases, obj = bases
                bases = (*bases, base, obj)
            else:
                bases = (*bases, base)

            try:
                cls.__bases__ = bases
            except AttributeError:
                if inject_bases is True:
                    raise TypeError(f'cannot set __bases__ of case class {cls}')

    # Check if base unification was successful
    if not all(issubclass(case, base) for case in cases):
        raise TypeError(
            'could not register all cases as subclasses of the base class. '
            'Try forcing inject_bases=True to fix this.'
        )

    # Unify methods
    unify_methods(base, cases)


def unify_case_queries(classes, extra=()):
    """
    Create attributes such as is_case1, is_case2 for all items in the list
    of classes.

    An extra iterable of classes can be passed to save the resulting case
    queries, but it will not be used to compute the set of valid queries.
    """
    classes = sequence(classes)
    query_names = {cls: 'is_' + snake_case(cls.__name__) for cls in classes}

    for cls in chain(classes, extra):
        for ref, attr in query_names.items():
            setattr_default(cls, attr, cls is ref)


def unify_methods(base, cases):
    """
    Create attributes such as is_case1, is_case2 for all items in the list
    of classes.

    An extra iterable of classes can be passed to save the resulting case
    queries, but it will not be used to compute the set of valid queries.
    """
    cases = sequence(cases)

    # Find common methods and register dispatchers on base
    common_methods = intersection(dir_methods(cls) for cls in cases)
    for method in common_methods:
        if not hasattr(base, method):
            setattr(base, method, dispatch_method(method))

    # Register all methods in base that are not present in case classes
    cases = [cls for cls in cases if base not in cls.mro()]
    for attr, value in vars_methods(base):
        for cls in cases:
            if not hasattr(cls, attr):
                setattr(cls, attr, value)


def dir_methods(obj):
    return iter(attr for attr, _ in vars_methods(obj))


def vars_methods(obj):
    for attr in dir(obj):
        value = getattr(obj, attr)
        if isinstance(value, type):
            continue
        elif hasattr(value, '__get__'):
            yield attr, value


def intersection(sequences):
    """
    Return a set with the intersection of all sequences.
    """
    result = set()
    for seq in sequences:
        result.intersection_update(seq)
    return result


def sequence(obj):
    if isinstance(obj, (list, tuple, str)):
        return obj
    else:
        return list(obj)


def dispatch_method(name):
    def method_(self, *args, **kwargs):
        try:
            method = getattr(self, name)
        except AttributeError:
            cls = type(self)
            msg = 'cannot access method {} of {} instance'.format(name, cls)
            raise AttributeError(msg)
        else:
            return method(*args, **kwargs)

    method_.__name__ = method_.__qualname__ = name
    return method_


#
# Utility functions
#
def setattr_default(obj, attr, value):
    """
    Set attribute to value, if attribute does not exist.
    """
    if not hasattr(obj, attr):
        setattr(obj, attr, value)


def check_cases_do_not_participate_in_other_unions(cases):
    for case in cases:
        if case not in CASE_CLASSES:
            msg = f'{case} is already a case class of {CASE_CLASSES[case]}'
            raise TypeError(msg)
