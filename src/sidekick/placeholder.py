import operator as op
from functools import partial

from .adt import opt
from .operators import (
    UNARY, BINARY, COMPARISON, METHODS, KEYWORDS, SYMBOLS
)

flip = lambda f: (lambda x, y: f(y, x))


#
# AST node types
#
class Ast( opt.BinOp(callable, object, object) 
         | opt.SingleOp(callable, object) 
         | opt.Call(object, tuple, dict) 
         | opt.GetAttr(object, str)
         | opt.Placeholder(int)
         | opt.Cte(object) ):
    """
    AST node for a placeholder expression.
    """

    def source(self):
        return ast_source(self)

    def __repr__(self):
        return self.source()


ast_source = Ast.match_fn(
    placeholder=lambda n:
        '_' * n,

    binop=lambda op, lhs, rhs:
        '%s %s %s' % (lhs.source(), op_symbol(op), rhs.source()),

    singleop=lambda op, obj:
        '%s %s' % (op_symbol(op), obj.source()),

    call=lambda obj, args, kwargs:
        '%s(*%s, **%s)' % (obj, args, kwargs),

    getattr=lambda attr, obj:
        '%s.%s' % (obj, attr),

    cte=lambda x:
        repr(x),
)

BinOp = Ast.BinOp
SingleOp = Ast.SingleOp
Call = Ast.Call
GetAttr = Ast.GetAttr
Placeholder = Ast.Placeholder
Cte = Ast.Cte

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
        ast = SingleOp(op, self)
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
                g = self._acc
                f = other._acc
                acc = lambda x: op(g(x), f(x))
            ast = BinOp(op, self._ast, other._ast)
        
        else:
            if self is _:
                acc = lambda x: op(x, other)
            else:
                f = self._acc
                acc = lambda x: op(f(x), other)
            ast = BinOp(op, self._ast, Cte(other))
        
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
        ast = BinOp(op, Cte(other), self._ast)
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
        if self._ast is None:
            return '_'
        return self._ast.source()

    def __getattr__(self, attr):
        ast = self._ast
        if ast.getattr:
            parent_attr, ast = ast.getattr_args
            attr = '%s.%s' % (parent_attr, attr)
        ast = GetAttr(attr, ast)
        acc = op.attrgetter(attr)
        return placeholder(ast, acc)

    def __call__(self, *args, **kwargs):
        ast = Call(self._ast, args, kwargs)
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
    ast = Call(func, args, kwargs)
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
_ = placeholder(Ast.Placeholder(1), lambda x: x)
