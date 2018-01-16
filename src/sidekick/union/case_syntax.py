from functools import update_wrapper
from types import MappingProxyType, SimpleNamespace

import collections

from .union import Union


#
# Case dispatch
#
def casedispatch(typ):
    """
    Decorator that declares a method that participates in a case dispatch.

    Example::

        @casedispatch(Maybe.Just)
        def incr(x):
            return x + 1

        @incr.register(Maybe.Nothing)
        def _():
            return 1

    The cases can also be defined in a class namespace and used in conjunction
    with the ``@casedispatch.from_namespace`` decorator. This syntax maps the
    implementation for each case with a method with the of the same name::

        @casedispatch.from_namespace(Maybe)
        class incr:
            def Just(x):
                return x + 1

            def Nothing():
                return 1

    This return a casedispatch function and discards the class definition.
    """

    # Handle singleton types
    if not isinstance(typ, type) and issubclass(type(typ), Union):
        typ = type(typ)

    if not isinstance(typ, type) or not issubclass(typ, Union):
        raise TypeError('must dispatch to a Union subclasss')

    if typ._meta.is_abstract:
        raise TypeError('cannot dispatch over abstract union classes')

    base = typ._meta.base_class

    def decorator(func):
        if base is typ:
            return _casedispatch(base, default_method=func)
        else:
            multi_method = _casedispatch(base)
            multi_method.register(typ)(func)
            update_wrapper(multi_method, func)
            return multi_method

    return decorator


def _casedispatch(base, default_method=None):
    registry = {}
    cache = {}

    def error(cls):
        msg = 'invalid type: 1st argument should be a %s, got %s'
        return TypeError(msg % (base.__name__, cls.__name__))

    def dispatch(cls):
        """
        generic_func.dispatch(cls) -> <function implementation>
        """
        try:
            impl = cache[cls]
        except KeyError:
            cases_set = set(registry)
            has_default = default_method is not None
            _check_complete_cases(cases_set, base, has_default)
            try:
                impl = registry[cls]
            except KeyError:
                if issubclass(cls, base) and has_default:
                    impl = default_method
                else:
                    raise error(cls)
            cache[cls] = impl
        return impl

    def register(cls, func=None):
        """
        generic_func.register(cls, func) -> func
        """
        if func is None:
            return lambda f: register(cls, f)

        # Check it it is registering to a valid class
        if not isinstance(cls, type) and cls._meta.is_singleton:
            cls = type(cls)
        if cls is base:
            raise TypeError('cannot register base class twice.')
        elif not issubclass(cls, base):
            raise TypeError('must be a %s subclass.' % base.__name__)

        registry[cls] = wrap_case(cls, func)
        cache.clear()
        return func

    def wrapper(*args, **kwargs):
        impl = dispatch(args[0].__class__)
        return impl(*args, **kwargs)

    def wrap_case(case, func):
        def wrapped(x, *args, **kwargs):
            return func(*(x.args + args), **kwargs)

        return wrapped

    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = MappingProxyType(registry)
    if default_method:
        update_wrapper(wrapper, default_method)
    return wrapper


def _check_complete_cases(cases, base, has_default):
    required = set(base._meta.cases.values())

    def error(msg, cases):
        bad_cases = {bad.__name__ for bad in cases}
        data = ', '.join(bad_cases)
        type_name = base.__name__
        return TypeError(msg % (type_name, data))

    # Defined spurious cases
    if cases - required:
        raise error('invalid cases for %r: %s', cases - required)

    # Missing cases
    if required - cases and not has_default:
        raise error('missing required cases for %r: %s', required - cases)


def from_namespace(base, namespace=None):
    if namespace is None:
        return lambda ns: from_namespace(base, ns)
    if not base._UnionMeta__is_closed:
        return SimpleNamespace(base=base, namespace=namespace, dispatch=...)

    # We gather enough information to create a casedispatch method
    # and return it
    if not (issubclass(base, Union) and base._meta.is_base):
        raise TypeError('expect a union type base class')

    # Extract all methods, but remove values inherited from object
    ns_map = {k: getattr(namespace, k)
              for k in dir(namespace)
              if getattr(namespace, k) != getattr(object, k, None)}

    cases_map = base._meta.cases
    cases = {case for name, case in cases_map.items() if name in ns_map}
    _check_complete_cases(cases, base, has_default='else_' in ns_map)

    # Create the return casedispatch method
    func = _casedispatch(base, ns_map.pop('else_', None))
    func.__doc__ = ns_map.pop('__doc__', '')
    func.__name__ = ns_map.pop('__doc__', 'case_fn')
    blacklist = {'__class__', '__weakref__', '__dict__'}

    # Register methods
    for name, impl in ns_map.items():
        if name in cases_map:
            if isinstance(impl, staticmethod):
                impl = impl.__func__
            cls = cases_map[name]
            func.register(cls, impl)
        elif name.startswith('_'):
            if name not in blacklist:
                setattr(func, name, impl)
        else:
            base_name = base.__name__
            raise TypeError('unknown case for %s: %r' % (base_name, name))

    return func


casedispatch.from_namespace = from_namespace


#
# case_fn[Union](...) syntax
#
class _CaseFnMeta(type):
    def __getitem__(cls, item):
        new = object.__new__(cls)
        if not (issubclass(item, Union) and item._meta.is_base):
            raise TypeError('expect a union base type, got %s.' % item)
        new.type = item
        return new


class case_fn(metaclass=_CaseFnMeta):
    """
    An anonymous case function associated with a specific Union type.

    It implements the following syntax::

        case_fn[UnionSubclass](
            State1=
                lambda value: ...,

            State2=
                lambda value1, value2: ...,

            State3=
                lambda: ...,

            else_=
                lambda obj: ...,
        )

    The case function constructor checks if the
    """
    __slots__ = 'type', 'extra_args'

    def __new__(cls, **kwargs):
        return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            'You must first pass an union type for the case function using the '
            'following syntax:\n'
            '\n'
            '    case_fn[Type](\n'
            '       Case1=\n'
            '               lambda a, b: ...,\n'
            '       Case2=\n'
            '           lambda a: ...,\n'
            '       else_=\n'
            '           lambda x: ...,\n'
            '    )'
        )

    def __call__(self, *args, **kwargs):
        # Accept pure keyword arguments or a single mapping as positional
        # argument
        if args and kwargs:
            raise TypeError(
                'case function accepts either a single positional '
                'argument or a series of arguments'
            )
        if args:
            kwargs, = args
            return self.__call__(**kwargs)

        namespace = SimpleNamespace(**kwargs)
        return casedispatch.from_namespace(self.type, namespace)


#
# case[Union](...) syntax
#
class _CaseMeta(type):
    def __getitem__(cls, item):
        new = object.__new__(cls)
        new.data = item
        return new


class case(metaclass=_CaseMeta):
    """
    A case expression dispatch execution to some state from a collection of
    states. The syntax for a case expression is::

        case[value](
            State1=
                lambda value: ...,

            State2=
                lambda value1, value2: ...,

            State3=
                lambda: ...,

            else_=
                lambda obj: ...,
        )
    """
    __slots__ = 'data'

    def __call__(self, **kwargs):
        data = self.data
        branch = kwargs.get(data._name)
        if branch is None:
            try:
                else_branch = kwargs['else_']
            except KeyError:
                expect = set(data._meta.base_class._meta.cases)
                got = set(kwargs)
                raise TypeError(
                    'case expression is not exhaustive. Expect to have %s,\n'
                    'but got %s' % (expect, got))
            else:
                return else_branch(data)
        return branch(*data.args)
