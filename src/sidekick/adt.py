import operator as op

flip = lambda f: (lambda x, y: f(y, x))


# A sugar for creating state instances.
# This is the default entry point for constructing Union types
class _Opt:
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)

        if not name[0].isupper():
            raise TypeError(
                'Union state names must be CamelCase, got: %s' % name
            )
        return State(name)


opt = _Opt()


class State:
    """
    Represents a state of a union type. This type is used as an intermediate
    step to construct Union types and to hold meta information about each 
    state.

    State instances are not instantiated in user code after class creation.
    """

    property_name = property(lambda x: x.name.lower())
    args_name = property(lambda x: x.name.lower() + '_args')

    def __init__(self, name: str, *argtypes: type):
        if len(argtypes) == 1 and isinstance(argtypes[0], int):
            argtypes = (object,) * argtypes[0]

        self.name = name
        self.argtypes = argtypes

    def __call__(self, *argtypes):
        return State(self.name, *argtypes)

    def __eq__(self, other):
        if isinstance(other, State):
            return self.name == other.name and self.argtypes == other.argtypes
        return NotImplemented

    def __or__(self, other):
        if isinstance(other, State):
            return UnionMeta._from_states([self, other])
        elif other is None or other is ...:
            return UnionMeta._from_states([self])
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, UnionMeta):
            return UnionMeta._from_states(list(other._states) + [self])
        return NotImplemented


class UnionMeta(type):
    """
    Metaclass for Union types.
    """

    def __new__(meta, name, bases, ns, states=None):
        union_bases = [base for base in bases if isinstance(base, UnionMeta)]

        # Check if bases are valid. We only accept a single Union base. 
        # It is necessary to make an exception to the Union type itself, since
        # it must be created with zero bases.
        if len(union_bases) == 0:
            return type.__new__(meta, name, bases, ns)
        elif len(union_bases) >= 2:
            raise TypeError('Type must have a single Union base')

        # Now that we have a single Union type base, we must check if it is
        # final or not. We forbid multiple levels of inheritance since it
        # would make singleton states ambiguous. However we must allow a single
        # level of inheritance to accomodate for types that customize the
        # default union type
        base, = union_bases
        if states is None:
            if getattr(base, '_is_final', False):
                raise TypeError('%s classes are final' % base.__name__)
            else:
                ns.setdefault('_is_final', True)
                bases = tuple(
                    (Union if isinstance(cls, UnionMeta) else cls)
                    for cls in bases
                )
                ns = dict(meta._namespace(base._states), **ns)

        return type.__new__(meta, name, bases, ns)

    def __init__(cls, name, bases, ns, states=None):
        super().__init__(name, bases, ns)
        states = states or cls._states

        # Collect all state constructors and associated attributes
        new = {}
        for id_, state in enumerate(states):
            new[state.name] = _state_constructor_factory(cls, state, id_)
            new[state.property_name] = _state_checker_factory(id_)
            new[state.args_name] = _state_args_factory(id_)

        # We do apply to the class if they are defined explicitly on the 
        # namespace
        new = {k: v for k, v in new.items() if k not in ns}
        for k, v in new.items():
            setattr(cls, k, v)

    def __or__(cls, other):
        if other is None or other is ...:
            return cls
        return NotImplemented

    @classmethod
    def _from_states(meta, states):
        """
        Create a new Union type from a list of states.
        """
        states = tuple(states)
        name = 'Union(%s)' % ('|'.join(state.name for state in states))
        return meta(name, (Union,), meta._namespace(states), states=states)

    @classmethod
    def _namespace(meta, states: tuple):
        """
        Return the class namespace from a list of states. 
        """
        ns = dict(
            __slots__=(),
            _states=states,
            _names_set={x.property_name for x in states},
            _id_to_names={id: x.property_name for id, x in enumerate(states)},
        )
        return ns

    def match_fn(cls, **kwargs):
        """
        Returns a function that performs pattern matching.

        Usage:

        >>> func = Maybe.match_fn(
        ...     nothing=lambda: 
        ...         42,
        ... 
        ...     just=lambda x: 
        ...         2 * x,
        ... )

        func can be executed to perform a pattern match.

        >>> func(Maybe.Just("just"))
        'justjust'
        >>> func(Maybe.Nothing)
        42
        """

        names = cls._names_set
        id_to_names = cls._id_to_names
        keys = set(kwargs.keys())

        if len(keys) > len(names):
            raise ValueError('invalid patterns: %s' % (keys - names))
        elif len(keys) < len(names):
            raise ValueError('missing patterns: %s' % (names - keys))
        elif keys != names:
            raise ValueError('wrong pattern names: %s' % keys)

        def fn(x):
            name = id_to_names[x._id]
            func = kwargs[name]
            return func(*x._args)

        return fn


def _state_checker_factory(id_):
    """
    Return a property that returns True if object is of the given ADT state.
    """

    return property(lambda self: self._id == id_)


def _state_args_factory(id_):
    """
    Return a property that returns the args of a given state. 
    
    If object is in a different state, it raises an AttributeError.
    """

    def fget(self):
        if self._id == id_:
            return self._args
        raise AttributeError

    return property(fget)


def _state_constructor_factory(cls, state, id_):
    """
    Return a constructor function for a state with the given type id.
    """

    n = len(state.argtypes)

    def constructor(cls, *args):
        if len(args) != n:
            raise TypeError(
                'constructor expects exactly %s arguments' % n
            )
        return cls(id_, *args)

    constructor.__name__ = state.name
    constructor.__doc__ = (
        "Construct new instances in state %r" % state.name
    )

    if n == 0:
        return constructor(cls)
    return classmethod(constructor)


class Union(metaclass=UnionMeta):
    """
    Union argtypes (Abstract data types) for Python
    """

    __slots__ = '_args', '_id'
    _states = ()
    _names_set = frozenset()
    _id_to_names = {}

    def __init__(self, id, *args):
        self._id = id
        self._args = args

    def __repr__(self):
        name = self._states[self._id].name
        args = self._args

        if args:
            return '%s(%s)' % (name, ', '.join(map(str, args)))
        return name

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self._id == other._id and self._args == other._args
        return NotImplemented

    def __hash__(self):
        return hash((self._id, self._args))

    def match(self, **kwargs):
        """
        Execute pattern match.
        """

        names = self._names_set
        id_to_names = self._id_to_names
        keys = kwargs.keys()

        if keys == names:
            name = id_to_names[self._id]
            func = kwargs[name]
            return func(*self._args)

        if len(keys) > len(names):
            raise ValueError('invalid patterns: %s' % (keys - names))
        else:
            raise ValueError('missing patterns: %s' % (names - keys))


#
# Classical ADTs
#
def _maybe_bin_op(op):
    """
    Creates a binary op method for a Maybe from a binary function.

    It executes the function for two Just instances and propagates any Nothings.
    """

    def binop(x, y):
        if isinstance(y, Maybe):
            if x.just and y.just:
                return Just(op(x.just_value, y.just_value))
            else:
                return Nothing
        elif x.just:
            return Just(op(x.just_value, y))
        else:
            return Nothing

    return binop


class Maybe(opt.Just(object) | opt.Nothing):
    """
    A Maybe type.
    """

    __slots__ = ()

    @property
    def value(self):
        try:
            return self._args[0]
        except IndexError:
            raise AttributeError('maybe instance has no value')

    @property
    def ok(self):
        return self.just

    @classmethod
    def call(cls, func, *args, **kwargs):
        """
        Execute function with all given Just values and return 
        Just(func(*values, **kwargs)). If any positional argument is a Nothing, 
        return Nothing.

        Examples:

        >>> Maybe.call(max, Just(1), Just(2), Just(3))
        Just(3)

        >>> Maybe.call(max, Nothing, Just(1), Just(2), Just(3))
        Nothing
        """

        try:
            args = tuple(x.value for x in args)
        except AttributeError:
            return cls.Nothing
        else:
            return cls.Just(func(*args, **kwargs))

    def then(self, func):
        """
        Apply function if object is in the Just state and return another Maybe. 
        """

        if self.just:
            new_value = func(self.value)
            return Maybe.Just(new_value)
        else:
            return self

    def get(self, default=None):
        """
        Extract value from the Just state. If object is Nothing, return the 
        supplied default or None.

        Examples:

        >>> x = Maybe.Just(42)
        >>> x.get()
        42
        >>> x = Maybe.Nothing
        >>> x.get()
        None
        """

        if self.just:
            return self.value
        else:
            return default

    def to_result(self, err=None):
        """
        Convert Maybe to Result.
        """
        if self.nothing:
            return Err(err)
        else:
            return Ok(self.value)

    # Operators
    __add__ = _maybe_bin_op(op.add)
    __radd__ = _maybe_bin_op(flip(op.add))
    __sub__ = _maybe_bin_op(op.sub)
    __rsub__ = _maybe_bin_op(flip(op.sub))
    __mul__ = _maybe_bin_op(op.mul)
    __rmul__ = _maybe_bin_op(flip(op.mul))
    __truediv__ = _maybe_bin_op(op.truediv)
    __rtruediv__ = _maybe_bin_op(flip(op.truediv))
    __bool__ = lambda x: x.just

    # Reinterpreted bitwise operators
    def __rshift__(self, other):
        if self.just:
            return Just(other(self.value))
        else:
            return Nothing

    def __or__(self, other):
        if isinstance(other, Maybe):
            return self if self.just else other
        elif isinstance(other, Result):
            return self if self.just else other.to_maybe()
        elif other is None:
            return self
        return NotImplemented

    def __and__(self, other):
        if isinstance(other, Maybe):
            return self if self.nothing else other
        elif isinstance(other, Result):
            return self if self.nothing else other.to_maybe()
        elif other is None:
            return Nothing
        return NotImplemented


def maybe(obj):
    """
    Coerce argument to a Maybe:

        maybe(None)  -> Nothing
        maybe(obj)   -> Just(obj) 

    Maybe instances:
        maybe(maybe) -> maybe

    Result instances:
        maybe(ok)    -> Just(ok.value)
        maybe(err)   -> Nothing
    """

    if isinstance(obj, Maybe):
        return obj
    elif isinstance(obj, Result):
        return obj.to_maybe()
    return Just(obj) if obj is not None else Nothing


Just = Maybe.Just
Nothing = Maybe.Nothing


#
# Classical ADTs: Result
#

def _result_bin_op(op):
    """
    Creates a binary op method for a Maybe from a binary function.

    It executes the function for two Just instances and propagates any Nothings.
    """

    def binop(x, y):
        if x.ok and y.ok:
            return Ok(op(x.value, y.value))
        else:
            return y if x.ok else x

    return binop


class Result(opt.Ok(object) | opt.Err(object)):
    """
    Represents a result with an Ok and an Err state.
    """

    __slots__ = ()

    @property
    def value(self):
        if self._id == 0:
            return self._args[0]
        else:
            raise AttributeError('result instance has no value')

    @property
    def error(self):
        return self._args[0] if self._id == 1 else None

    @classmethod
    def apply(cls, func, *args):
        """
        Execute function with all given Ok values and return Ok(func(*values)). 
        If any argument is an Error return the first error.

        Examples:

        >>> Result.apply(max, Ok(1), Ok(2), Ok(3))
        Ok(3)

        >>> Result.apply(max, Ok(1), Ok(2), Ok(3), Err("NaN"))
        Err("NaN")
        """

        arg_list = []
        for arg in args:
            if arg.ok:
                arg_list.append(arg.value)
            else:
                return arg

        return cls.Ok(func(*arg_list))

    def then(self, func):
        """
        Apply function if object is in the Ok state and return another Result. 
        """

        if self.ok:
            new_value = func(self.value)
            return self.Ok(new_value)
        else:
            return self

    def map_error(self, func):
        """
        Like the .then(func) method, but modifies the error part of the result.
        """

        if self.err:
            return self.Err(func(self.error))
        else:
            return self

    def get(self, default=None):
        """
        Extract value from the Ok state. If object is an error, return the 
        supplied default or None.

        Examples:

        >>> x = Result.Ok(42)
        >>> x.get()
        42
        >>> x = Result.Err("NaN")
        >>> x.get()
        None
        """

        if self.ok:
            return self.value
        else:
            return default

    def to_maybe(self) -> Maybe:
        """
        Convert result object into a Maybe.
        """
        if self.ok:
            return Just(self.value)
        else:
            return Nothing

    # Operators
    __add__ = _result_bin_op(op.add)
    __radd__ = _result_bin_op(flip(op.add))
    __sub__ = _result_bin_op(op.sub)
    __rsub__ = _result_bin_op(flip(op.sub))
    __mul__ = _result_bin_op(op.mul)
    __rmul__ = _result_bin_op(flip(op.mul))
    __truediv__ = _result_bin_op(op.truediv)
    __rtruediv__ = _result_bin_op(flip(op.truediv))
    __bool__ = lambda x: x.ok

    def __or__(self, other):
        if isinstance(other, Result):
            return self if self.ok else other
        elif isinstance(other, Maybe):
            return self if self.ok else other.to_result()
        return NotImplemented

    def __and__(self, other):
        if isinstance(other, Result):
            return self if self.err else other
        elif isinstance(other, Maybe):
            return self if self.err else other.to_result()

    def __negate__(self, other):
        return Err(self.value) if self.ok else Ok(self.error)


def result(obj):
    """
    Coerce argument to a result:

    Objects and exceptions:
        result(obj)   -> Ok(obj) 
        result(ex)    -> Err(ex)

    Result instances:
        result(ok)    -> ok
        result(err)   -> err
    
    Maybe instances:
        result(Just(x)) -> Ok(x)
        result(Nothing) -> Err(None)
    """

    if isinstance(obj, Result):
        return obj
    elif isinstance(obj, Maybe):
        return obj.to_result(None)
    return Err(obj) if isinstance(obj, Exception) else Ok(obj)


Ok = Result.Ok
Err = Result.Err
