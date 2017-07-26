def flip(func):
    """
    Flip function arguments.
    """
    return lambda x, y: func(y, x)


def identity(x):
    """
    The identity function.
    """
    return x


def const(x):
    """
    Return a function that always return x when called with any number of 
    arguments.
    """
    return lambda *args, **kwargs: x


class ConstructMeta(type):
    """
    Metaclass for the construct object.
    """
    _constructors = {}

    def __getitem__(cls, param):
        try:
            return cls._constructors[param]
        except KeyError:
            ns = {'null': param}
            new = type('constructor[%r]' % param, (construct,), ns)
            cls._constructors[param] = new
            return new


class construct(metaclass=ConstructMeta):
    """
    Define a constructor for an object that 
    """

    __slots__ = ('function', 'args', 'kwargs')
    null = None

    def __init__(self, function, *args, **kwargs):
        if not callable(function):
            value = function
            function = lambda: value
        self.function = function
        self.args = args
        self.kwargs = kwargs
    
    def __ror__(self, value):
        if value is None:
            return self.function(*self.args, **self.kwargs)
        return value

    __or__ = __ror__



x = None
x = x | construct(len, [1, 2, 3])
x = x | construct[0](len, [1, 2, 3])
