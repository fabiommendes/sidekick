import operator as op
from functools import partial

from .operators import (
    UNARY, BINARY, COMPARISON, METHODS, SYMBOLS
)
from .union import Union, opt, case_fn

this = None
Callable = object


def flip(f):
    return lambda x, y: f(y, x)


def make_instance(cls):
    instance = getattr(cls, '_placeholder_instance', None)
    if type(instance) is not cls:
        instance = cls(Ast.Placeholder(1), lambda x: x)
        cls._placeholder_instance = instance
    return instance


#
# AST node types
#
class Ast(Union):
    """
    AST node for a placeholder expression.
    """

    BinOp = opt([('op', Callable), ('lhs', object), ('rhs', object)])
    SingleOp = opt([('op', Callable), ('value', object)])
    Call = opt([('caller', this), ('arguments', tuple), ('kwargs', dict)])
    GetAttr = opt([('attr', str), ('value', this)])
    Placeholder = opt(index=int)
    Cte = opt(value=object)

    def source(self):
        return ast_source(self)


ast_source = case_fn[Ast](
    Placeholder=lambda n:
    '_' * n,

    BinOp=lambda op, lhs, rhs:
    '%s %s %s' % (lhs.source(), op_symbol(op), rhs.source()),

    SingleOp=lambda op, obj:
    '%s %s' % (op_symbol(op), obj.source()),

    Call=lambda obj, args, kwargs:
    '%s(*%s, **%s)' % (obj, args, kwargs),

    GetAttr=lambda attr, obj:
    '%s.%s' % (obj, attr),

    Cte=lambda x:
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
def register_operators(rfunc, operators):
    """
    Register a list of operators.
    """

    def decorator(cls):
        for op in operators:
            op = rfunc(op, cls)
            setattr(cls, op.__name__, op)
        return cls

    return decorator


def unary(op, cls):
    name = '__%s__' % op.__name__.rstrip('_')
    placeholder = make_instance(cls)

    def method(self):
        if self is placeholder:
            acc = op
        else:
            f = self._acc
            acc = lambda x: op(f(x))

        ast = SingleOp(op, self)
        return Placeholder(ast, acc)

    method.__name__ = name
    return method


def binary(op, cls):
    name = '__%s__' % op.__name__.rstrip('_')
    placeholder = make_instance(cls)

    def method(self, other):
        if isinstance(other, cls):
            if self is placeholder and other is placeholder:
                acc = lambda x: op(x, x)
            elif self is placeholder:
                f = other._acc
                acc = lambda x: op(x, f(x))
            else:
                g = self._acc
                f = other._acc
                acc = lambda x: op(g(x), f(x))

            ast = BinOp(op, self._ast, other._ast)

        else:
            if self is placeholder:
                acc = lambda x: op(x, other)
            else:
                f = self._acc
                acc = lambda x: op(f(x), other)

            ast = BinOp(op, self._ast, Cte(other))

        return cls(ast, acc)

    method.__name__ = name
    return method


def rbinary(op, cls):
    name = '__r%s__' % op.__name__.rstrip('_')
    placeholder = make_instance(cls)

    def method(self, other):
        if self is placeholder:
            acc = partial(op, other)
        else:
            f = self._acc
            acc = lambda x: op(other, f(x))

        ast = BinOp(op, Cte(other), self._ast)
        return Placeholder(ast, acc)

    method.__name__ = name
    return method


@register_operators(unary, UNARY)
@register_operators(binary, BINARY + COMPARISON + METHODS)
@register_operators(rbinary, BINARY)
class Placeholder:
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
        if attr == '__wrapped__':
            raise AttributeError('__wrapped__')
        ast = self._ast
        if ast.is_getattr:
            parent_attr, ast = ast.args
            attr = '%s.%s' % (parent_attr, attr)
        ast = GetAttr(attr, ast)
        acc = op.attrgetter(attr)
        return Placeholder(ast, acc)

    def __call__(self, *args, **kwargs):
        ast = Call(self._ast, args, kwargs)
        func = self._acc
        acc = lambda x: \
            func(x)(
                *((e._acc(x) if isinstance(e, Placeholder) else e)
                  for e in args),
                **{k: (e._acc(x) if isinstance(e, Placeholder) else e)
                   for k, e in kwargs.items()}
            )
        return Placeholder(ast, acc)


def F(func, *args, **kwargs):  # noqa: N802
    """
    A helper object that can be used to define function calls on a placeholder
    object.
    """

    def to_ast(x):
        return x._ast if isinstance(x, Placeholder) else Cte(x)

    fargs = tuple(to_ast(x) for x in args)
    fkwargs = {k: to_ast(x) for k, x in kwargs.items()}
    ast = Call(Cte(func), fargs, fkwargs)

    acc = lambda x: \
        func(
            *((e._acc(x) if isinstance(e, Placeholder) else e)
              for e in args),
            **{k: (e._acc(x) if isinstance(e, Placeholder) else e)
               for k, e in kwargs.items()}
        )
    return Placeholder(ast, acc)


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
placeholder = _placeholder = Placeholder(Ast.Placeholder(1), lambda x: x)
