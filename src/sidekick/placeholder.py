import operator as op
from functools import partial

from .operators import (
    UNARY, BINARY, COMPARISON, METHODS, KEYWORDS, SYMBOLS
)
from .bare_functions import identity, flip


#
# AST node types
#
OP = 'op'
OP_SINGLE = 'op-single'
CALL = 'call'


#
# Operator factories and registration
#
def register_operators(operators):
    """
    Register a list of operators.
    """

    def decorator(cls):
        for op in operators:
            setattr(cls, op.__name__, op)
        return cls
    return decorator


def unary(op):
    name = '__%s__' % op.__name__.rstrip('_')
    
    def method(self):
        if self is _:
            acc = op
        else:
            f = self._acc
            acc = lambda x: op(f(x)) 
        ast = (OP_SINGLE, op, self)
        return placeholder(ast, acc)

    method.__name__ = name
    return method


def binary(op):
    name = '__%s__' % op.__name__.rstrip('_')
    
    def method(self, other):
        if isinstance(other, placeholder):
            if self is _ and other is _:
                acc = lambda x: op(x, x)
            elif self is _:
                f = other._acc
                acc = lambda x: op(x, f(x))
            else:
                f = self._acc
                acc = lambda x: op(f(x), x)
            
        if self is _:
            acc = lambda x: op(x, other)
        else:
            f = self._acc
            acc = lambda x: op(f(x), other) 
        ast = (OP, op, self, other)
        return placeholder(ast, acc)
    
    method.__name__ = name
    return method


def rbinary(op):
    name = '__r%s__' % op.__name__.rstrip('_')
    
    def method(self, other):
        if self is _:
            acc = partial(op, other)
        else:
            f = self._acc
            acc = lambda x: op(other, f(x)) 
        ast = (OP, op, other, self)
        return placeholder(ast, acc)
    
    method.__name__ = name
    return method


@register_operators(map(unary, UNARY))
@register_operators(map(binary, BINARY + COMPARISON + METHODS))
@register_operators(map(rbinary, BINARY))
class placeholder:
    """
    Placeholder objects represents a variable or expression on quick lambda.
    """

    __slots__ = '_ast', '_acc'

    def __init__(self, ast, acc):
        self._ast = ast
        self._acc = acc

    @property
    def _(self):
        return compile_placeholder(self._ast, self._acc)
    
    @property
    def __name__(self):
        return self.__repr__()

    def __repr__(self):
        ast = self._ast
        if ast is None:
            return '_'

        head = ast[0]
        if head is OP:
            op = op_symbol(ast[1]) 
            return '(%r%s%r)' % (ast[2], op, ast[3])
        elif head is OP_SINGLE:
            raise NotImplementedError
        else:
            return '<quick lambda>'

    def __getattr__(self, attr):
        acc = op.attrgetter(attr)
        return placeholder((OP, op.attrgetter, attr, self), acc)

    def __call__(self, *args, **kwargs):
        ast = (CALL, self._ast, args, kwargs)
        func = self._acc
        acc = lambda x: \
            func(x)(
                *((e._acc(x) if isinstance(e, placeholder) else e) 
                    for e in args),
                **{k: (e._acc(x) if isinstance(e, placeholder) else e)
                    for k, e in kwargs.items()},
            )
        return placeholder(ast, acc)

def F(func, *args, **kwargs):
    """
    A helper object that can be used to define function calls on a placeholder
    object.
    """
    ast = (CALL, func, args, kwargs)
    acc = lambda x: \
        func(
            *((e._acc(x) if isinstance(e, placeholder) else e) 
                for e in args),
            **{k: (e._acc(x) if isinstance(e, placeholder) else e)
                for k, e in kwargs.items()},
        )
    return placeholder(ast, acc)


def compile_placeholder(ast, acc):
    """
    Compile a placeholder expression and return the corresponding anonymous 
    function.
    """

    if ast is None:
        return lambda x: x
    elif acc:
        return acc
    else:
        raise NotImplementedError(ast)


#
# Rendering
#
OP_SYMBOLS = {k: ' %s ' % v for k, v in SYMBOLS.items()}
OP_SYMBOLS[op.attrgetter] = '.'

def op_symbol(op):
    return OP_SYMBOLS[op]


#
# The placeholder symbol
#
_ = placeholder(None, identity)
