import collections
import keyword

from types import SimpleNamespace

from .utils import opt, Opts


#
# Metatype for Union types. Most of the action happens here as the metatype +
# auxiliary functions construct a new ADT and each associated case.
#
class UnionMeta(type):
    """
    Metaclass for Union types
    """

    @classmethod
    def __prepare__(meta, name, bases, **kwargs):  # noqa: N804
        namespace = {'__slots__': 'args'}
        new = type.__new__(meta, name, bases, namespace)
        base = new._check_inheritance(bases)

        # Save initial meta information regarding the role of the class
        # in the Union type  hierarchy: abstract, base or case class
        meta_info = {
            'is_abstract': kwargs.get('is_abstract', False),
            'is_case': False, 'is_base': False
        }
        if not meta_info['is_abstract']:
            meta_info['is_base'] = base._meta.is_abstract
            meta_info['is_case'] = base._meta.is_base
        new._meta = new._create_meta(**meta_info)
        new.__is_closed = False

        # Save all attributes to namespace and inject the class the metaclass
        # name and as a 'this' alias.
        namespace['this'] = namespace[name] = new
        return collections.OrderedDict(namespace)

    def __new__(meta, name, bases, namespace, **kwargs):  # noqa: N804
        # Fetch new from namespace or create a new instance
        new = namespace.pop(name, None)
        namespace.pop('this', None)
        if new is None:
            new = type.__new__(meta, name, bases, namespace)
            new._check_inheritance(bases)
        new._name = name
        new.__is_closed = False

        # Handle abstract base classes such as Union and Singleton. Those
        # classes have no instances and no concrete case sub-classes.
        # A class must be tagged explicitly as abstract, otherwise it will
        # think it is a base class
        is_abstract = kwargs.pop('is_abstract', False)
        if is_abstract:
            new._init_abstract_class(name, bases, namespace, **kwargs)
            return new

        # The next step is a base union class. This is also technically an
        # abstract type since it has no instances. However, base classes can
        # only have concrete subclasses
        base, = (base for base in bases if isinstance(base, UnionMeta))
        is_base = base._meta.is_abstract
        if is_base:
            new._init_base_class(name, bases, namespace, **kwargs)
            return new

        # Finally, the class must be a case class.
        new._init_case_class(name, bases, namespace, **kwargs)
        return new

    def __init__(cls, *args, **kwargs):  # noqa: N805
        pass

    def _new_case_class(cls, name, opts):  # noqa: N805
        """
        Create new clase class from opts.
        """
        bases = (cls,)
        ns = UnionMeta.__prepare__(name, bases)
        return UnionMeta(name, bases, ns, args=opts)

    def _init_abstract_class(cls, name, bases, namespace):  # noqa: N805
        """
        Create new abstract Union type class. Those classes are basis for
        other Union sub-types, e.g., Union, Singleton.
        """

        cls._update_dict(namespace)
        cls._meta = cls._create_meta(is_abstract=True)

    def _init_base_class(cls, name, bases, namespace,  # noqa: N805
                         disable_singleton=False):
        """
        A base class is a Union subclass that have inner case classes.
        """

        cases = {}
        cls._meta = cls._create_meta(is_base=True, cases=cases)
        cls._meta.disable_singleton = disable_singleton

        # Update namespace with opt-based cases and register case classes
        for name, value in namespace.items():
            if isinstance(value, Opts):
                value = cls._new_case_class(name, value)

            if isinstance(value, type) and issubclass(value, cls):
                cls._register_case_class(value, name, disable_singleton)

        # Update methods
        cls._update_dict(namespace)
        cls._contribute_case_methods()
        cls.__is_closed = True

    def _init_case_class(cls, name, bases, namespace, args=None):  # noqa: N805
        """
        Concrete Union classes.
        """

        mk_property = (lambda i: property(lambda x: x.args[i]))

        if args is None and 'args' in namespace:
            args = opt(namespace.pop('args'))
        elif args is None:
            args = opt(namespace.get('__annotations__', ()))
        if 'args' in namespace:
            raise TypeError('cannot define an args attribute for class')

        # Add all value getter properties
        for i, (attr, argtype) in enumerate(args.items()):
            namespace.setdefault(attr, mk_property(i))

        # Sets the is_<name> attribute to True
        query_attr_name = 'is_' + name.lower()
        if namespace.get(query_attr_name, True) is not True:
            raise TypeError('%r must be set to True' % query_attr_name)
        namespace.setdefault(query_attr_name, True)

        # End registration
        cls._meta = cls._create_meta(is_case=True, args=opt(args))
        cls._check_case_args(args)
        cls._contribute_case_init()
        cls._update_dict(namespace)
        cls.__is_closed = True

        # Register to base class
        base = cls._meta.base_class
        if base.__is_closed:
            base._register_case_class(cls, name, base._meta.disable_singleton)

    def _register_case_class(cls, subclass, name=None,  # noqa: N805
                             disable_singleton=False):
        """
        Register a case subclass to the base class.
        """

        name = name or subclass.__name__
        cases = cls._meta.cases
        cases[name] = subclass

        # Save class as attribute of base class
        if subclass._meta.is_singleton and not disable_singleton:
            bases = (SingletonMixin,) + subclass.__bases__
            subclass.__bases__ = bases
            setattr(cls, name, subclass())
        else:
            setattr(cls, name, subclass)

        # Contribute the is_<name> = False attribute for the base class
        query_attr_name = 'is_' + name.lower()
        if getattr(cls, query_attr_name, False) is not False:
            msg = '%r must be set to False on base class' % query_attr_name
            raise TypeError(msg)
        setattr(cls, query_attr_name, False)

    def __instancecheck__(cls, value):  # noqa: N805
        # This tweak makes it possible for singleton values to be at the same
        # time instances and subclasses of Union types.
        result = super().__instancecheck__(value)
        if not result and isinstance(value, UnionMeta):
            return cls is Union or cls is value.__bases__[0]
        return result

    def _create_meta(cls, **kwargs):  # noqa: N805
        kwargs.setdefault('is_abstract', False)
        kwargs.setdefault('is_case', False)
        kwargs.setdefault('is_base', False)
        kwargs.setdefault('cases', None)
        kwargs.setdefault('args', None)
        kwargs.setdefault('base_class', None)
        kwargs.setdefault('disable_singleton', False)
        meta = SimpleNamespace(**kwargs)
        meta.is_singleton = meta.is_case and not meta.args

        if meta.is_base:
            meta.base_class = cls
            meta.cases = meta.cases or {}
        elif meta.is_case:
            meta.base_class, = (base
                                for base in cls.__bases__
                                if isinstance(base, UnionMeta))

        return meta

    def _update_dict(cls, data=(), **kwargs):  # noqa: N805
        class_dict = cls.__dict__
        for k, v in dict(data, **kwargs).items():
            if k not in class_dict:
                setattr(cls, k, v)

    #
    # Basic checks and factories
    #
    def _check_inheritance(cls, bases):  # noqa: N805
        bases = tuple(base for base in bases if isinstance(base, UnionMeta))

        # Cannot inherit from more than one Union subclass
        if len(bases) >= 2:
            msg = 'Multiple inheritance of Union types is not allowed'
            raise TypeError(msg)

        elif len(bases) == 1:
            base, = bases

            # Case classes
            if base._meta.is_case:
                msg = 'Cannot inherit from case classes'
                raise TypeError(msg)

            # Closed classes
            if base.__is_closed and base.__module__ != cls.__module__:
                raise TypeError('cannot inherit from %s' % base)

            return base
        return cls

    def _check_case_args(cls, opts):  # noqa: N805
        blacklist = {
            # Sideckick specific
            'args',

            # Python keywords that might not be present on the keyword module
            'async', 'await', 'nonlocal',
        }
        blacklist.update(keyword.kwlist)

        for name in blacklist.intersection(opts):
            msg = 'case classe cannot have an %r attribute.'
            raise TypeError(msg % name)

    def _contribute_case_init(cls, use_kwargs=False):  # noqa: N805
        """
        Concrete init method for case classes.
        """

        types = list(cls._meta.args.values())
        if use_kwargs:
            names = list(cls._meta.args.keys())
            cls.__init__ = make_init_kwargs(cls, types, names)
        else:
            cls.__init__ = make_init_args(cls, types)

    def _contribute_case_methods(cls):  # noqa: N805
        """
        Distribute the implementation of all methods implemented as a
        CaseFn.method instance.
        """

        for k, v in cls.__dict__.items():
            if hasattr(v, 'dispatch'):
                cls._register_case_method(k, v)

    def _register_case_method(cls, name, method):
        from .case_syntax import casedispatch

        # Delayed creation for non-closed types
        if method.dispatch is ...:
            try:
                closed = cls.__is_closed
                cls.__is_closed = True

                if method.base != cls:
                    raise TypeError('case dispatch for a different class.')
                method = casedispatch.from_namespace(cls, method.namespace)
            finally:
                cls.__is_closed = closed

        for case_name, case_cls in cls._meta.cases.items():
            impl = method.dispatch(case_cls)
            setattr(case_cls, case_name, impl)
        setattr(cls, name, method)


def make_init_args(cls, types):
    """
    Make init function for case class. Only accept positional arguments.
    """

    def init_args(self, *args):
        if len(args) != len(types):
            n = len(args)
            m = len(types)
            raise TypeError('expected %s arguments, got %s' % (m, n))

        for n, (x, tt) in enumerate(zip(args, types)):
            if not isinstance(x, tt):
                msg = '({base}.{case}) invalid type for arg {n}: got ' \
                      '{tt}, expect {tt_expected}'
                raise TypeError(
                    msg.format(base=cls._meta.base_class.__name__,
                               case=cls.__name__, n=n,
                               tt=type(x).__name__,
                               tt_expected=tt.__name__))

        self.args = args

    return init_args


def make_init_kwargs(cls, types, names):
    """
    Make init function for case class. Accepts positional and keyword arguments.
    """

    init_args = make_init_args(cls, types)

    def init_kwargs(self, *args, **kwargs):
        if kwargs:
            extra = []
            for name in names[len(args):]:
                extra.append(kwargs[name])
            args = args + tuple(extra)

        init_args(self, *args)

    return init_kwargs


#
# Create the base union and singleton classes.
#
class Union(metaclass=UnionMeta, is_abstract=True):
    """
    Base class for all union types.
    """
    __slots__ = 'args'
    __qualname__ = 'Union'
    __module__ = 'sidekick'

    def __init__(self, *args, **kwargs):
        cls = self._meta.base_class
        if type(self) is cls:
            msg = 'cannot instantiate a %s directly, choose an specific case'
            raise TypeError(msg % cls.__name__)
        self.args = args

    def __repr__(self):
        try:
            data = '(%s)' % (', '.join(map(repr, self.args)))
        except Exception:
            data = '(...)'
        return type(self).__name__ + data

    def __eq__(self, other):
        if type(self) is type(other):
            return self.args == other.args
        return NotImplemented

    def __hash__(self):
        return hash((self.args, type(self)))


class SingletonMixin:
    """
    Mixin class that is injected into singleton case classes.
    """

    __slots__ = ()
    args = ()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def __instancecheck__(self, value):
        # The only instance of a Singleton class is the cls itself!
        return self is value

    def __eq__(self, other):
        if type(self) is type(other):
            return True
        return NotImplemented

    def __hash__(self):
        return hash(type(self))

    def __repr__(self):
        return type(self).__name__
