import operator
from collections import namedtuple
from functools import singledispatch

from .._operators import OP_SYMBOLS, op_wrapper_class

flip = lambda f: lambda x, y: f(y, x)


class Placeholder:
    """
    Base class for placeholder objects.
    """


#
# Magic X and Y objects. Implementation of operator factories for (E)xpr nodes
# (X) and (Y) magics.
#
Eop = lambda op: lambda self, other: Expr(BinOp(op, self._ast, to_ast(other)))


# noinspection PyPep8Naming
def Xop(op):
    def func(_, other):
        if other is X:
            return lambda x: op(x, x)
        elif other is Y:
            return lambda x, y: op(x, y)
        else:
            return lambda x: op(x, other)

    return func


# noinspection PyPep8Naming
def Yop(op):
    def func(_, other):
        if other is X:
            return lambda x, y: op(y, x)
        elif other is Y:
            return lambda x, y: op(y, y)
        else:
            return lambda x, y: op(y, other)

    return func


Erop = lambda op: lambda self, value: Expr(BinOp(op, to_ast(value), self._ast))
Xrop = lambda op: lambda self, value: lambda x: op(value, x)
Yrop = lambda op: lambda self, value: lambda x, y: op(value, y)

Eunary = lambda op: lambda self: Expr(UnaryOp(op, self._ast))
Xunary = lambda op: lambda self: op
Yunary = lambda op: lambda self: lambda x, y: op(y)


class _X(op_wrapper_class(Xop, Xrop, Xunary), Placeholder):
    @property
    def __sk_callable__(self):
        return lambda x: x

    def __repr__(self):
        return "X"

    def __call__(self, x):
        return x

    def __getattr__(self, attr):
        return operator.attrgetter(attr)


class _Y(op_wrapper_class(Yop, Yrop, Yunary), Placeholder):
    @property
    def __sk_callable__(self):
        return lambda x, y: y

    def __repr__(self):
        return "Y"

    def __call__(self, x, y):
        return y

    def __getattr__(self, attr):
        return lambda x, y: getattr(y, attr)


class _M(Placeholder):
    def __repr__(self):
        return "M"

    def __call__(self, *args, **kwargs):
        return lambda fn: fn(*args, **kwargs)

    def __getattr__(self, attr):
        return lambda *args, **kwargs: operator.methodcaller(attr, *args, **kwargs)


class _F:
    def __getitem__(self, func):
        return lambda *args, **kwargs: self(func, *args, **kwargs)

    def __call__(self, func, /, *args, **kwargs):
        return Expr(call_node(func, *args, **kwargs))


class Expr(op_wrapper_class(Eop, Erop, Eunary), Placeholder):
    """
    Placeholder objects represents a variable or expression on quick lambda.
    """

    __slots__ = "_ast", "_callable"

    _name = property(lambda self: self.__repr__())

    @property
    def __sk_callable__(self):
        if self._callable is None:
            self._callable = compile_ast(simplify_ast(self._ast))
        return self._callable

    def __init__(self, ast):
        self._ast = ast
        self._callable = None

    def __repr__(self):
        return f"{type(self).__name__}({self})"

    def __str__(self):
        return source(self._ast)

    def __getattr__(self, attr):
        if attr == "__wrapped__":
            raise AttributeError
        return Expr(GetAttr(attr, self._ast))

    def __call__(self, *args, **kwargs):
        args = tuple(map(to_ast, args))
        kwargs = {k: to_ast(v) for k, v in kwargs.items()}
        return Expr(Call(self._ast, args, kwargs))


#
# AST node types and representation
#
BinOp = namedtuple("BinOp", ["op", "lhs", "rhs"])
Call = namedtuple("Call", ["caller", "arguments", "kwargs"])
Cte = namedtuple("Cte", ["value"])
GetAttr = namedtuple("GetAttr", ["attr", "value"])
UnaryOp = namedtuple("SingleOp", ["op", "value"])
Var = type("Var", (), {"__repr__": lambda x: "Var"})()


# noinspection PyProtectedMember
def to_ast(obj: Expr):
    """
    Convert object to AST node.
    """
    if isinstance(obj, Expr):
        return obj._ast
    elif obj is X:
        return Var
    elif obj is Y:
        msg = "placeholder expressions do not accept a second argument"
        raise NotImplementedError(msg)
    else:
        return Cte(obj)


def call_node(func, /, *args, **kwargs):
    """
    Create a call node for ast.
    """
    func = to_ast(func)
    args = tuple(map(to_ast, args))
    kwargs = {k: to_ast(v) for k, v in kwargs.items()}
    return Call(func, args, kwargs)


#
# Rendering ASTs
#
OP_SYMBOLS = dict(OP_SYMBOLS)
OP_SYMBOLS[operator.attrgetter] = "."


def op_symbol(op):
    return OP_SYMBOLS[op]


@singledispatch
def source(obj):
    if obj is Var:
        return "_"
    raise ValueError(obj)


# Make static analysis happy ;)
source.register = source.register


@source.register(BinOp)
def _(node):
    op, lhs, rhs = node
    lhs_src = source(lhs)
    rhs_src = source(rhs)
    if isinstance(lhs, BinOp):
        lhs_src = f"({lhs_src})"
    if isinstance(rhs, BinOp):
        rhs_src = f"({rhs_src})"
    return "%s %s %s" % (lhs_src, op_symbol(op), rhs_src)


@source.register(UnaryOp)
def _(node):
    op, value = node
    return "(%s%s)" % (op_symbol(op), source(value))


@source.register(Call)
def _(node):
    obj, args, kwargs = node
    args = list(map(source, args))
    args.extend(f"{k}=source(v)" for k, v in kwargs.items())
    args = ", ".join(args)
    return "%s(%s)" % (source(obj), args)


@source.register(GetAttr)
def _(node):
    attr, obj = node
    return "%s.%s" % (source(obj), attr)


@source.register(Cte)
def _(node):
    return repr(node.value)


#
# Compiling AST nodes
#
SIMPLE_TYPES = (int, float, complex, str, bytes, bool, type(None))


@singledispatch
def compile_ast(ast):
    """
    Compile a placeholder expression and return the corresponding anonymous
    function.
    """
    if ast is Var:
        return lambda x: x
    else:
        raise TypeError(f"invalid AST type: {type(ast).__name__}")


# noinspection PyUnresolvedReferences
compiler = compile_ast.register


@compiler(Cte)
def _(ast):
    obj = ast.value
    return lambda x: obj


@compiler(BinOp)
def _(ast):
    op, lhs, rhs = ast
    simple_lhs = simple_rhs = False

    lhs = compile_ast(lhs)
    rhs = compile_ast(rhs)

    if simple_lhs:
        return lambda x: op(lhs, rhs(x))
    elif simple_rhs:
        return lambda x: op(lhs(x), rhs)

    return lambda x: op(lhs(x), rhs(x))


@compiler(Call)
def _(ast):
    caller, args, kwargs = ast
    caller = compile_ast(caller)
    args = tuple(map(compile_ast, args))
    kwargs = {k: compile_ast(v) for k, v in kwargs.items()}
    return lambda x: caller(x)(
        *(f(x) for f in args), **{k: v(x) for k, v in kwargs.items()}
    )


@compiler(GetAttr)
def _(ast):
    # Optimizations:
    #   * Var nodes are handled more efficiently with operator.attrgetter
    #   * Call nodes are handled with operator.methodcaller, when possible
    #   * Chained getattrs are also handled with operator.attrgetter
    #   * Constant propagation for safe objects
    from operator import attrgetter

    attr, value = ast
    getter = attrgetter(attr)

    # After simplification, attr can be given in the dot notation
    assert not isinstance(value, GetAttr), "Should have gone after simplification"

    if value is Var:
        return getter

    elif isinstance(value, Cte):
        arg = value.value
        if isinstance(arg, SIMPLE_TYPES):
            arg = getter(arg)
            return lambda x: arg
        else:
            return lambda x: getter(arg)

    else:
        inner = compile_ast(value)
        return lambda x: getter(inner(x))


@compiler(UnaryOp)
def _(ast):
    # Optimizations:
    #   * Var nodes are eliminated
    #   * Cte nodes are extracted from node. Performs rudimentary constant
    #     propagation in safe types.
    op, value = ast
    value = to_ast(value)

    if value is Var:
        return op

    elif isinstance(value, Cte):
        arg = value.value
        if isinstance(arg, SIMPLE_TYPES):
            arg = op(arg)
            return lambda x: arg
        arg = compile_ast(arg)
        return lambda x: op(arg(x))

    else:
        expr = compile_ast(value)
        return lambda x: expr(x)


#
# Simplifying AST nodes
#
def simplify_ast(ast):
    """Deep AST simplification"""

    if isinstance(ast, GetAttr):
        attr, value = ast
        value = simplify_ast(value)

        if isinstance(value, Cte):
            obj = value.value
            if isinstance(obj, SIMPLE_TYPES):
                return Cte(getattr(obj, attr))

        elif isinstance(value, GetAttr):
            return GetAttr(f"{value.attr}.{attr}", value.value)

        elif value is not ast.value:
            return GetAttr(attr, value)

    elif isinstance(ast, BinOp):
        op, lhs, rhs = ast
        lhs = simplify_ast(lhs)
        rhs = simplify_ast(rhs)
        if lhs is not ast.lhs or rhs is not ast.rhs:
            return BinOp(op, lhs, rhs)

    elif isinstance(ast, Call):
        caller, args, kwargs = ast
        caller = simplify_ast(caller)
        args = tuple(map(simplify_ast, args))
        kwargs = {k: simplify_ast(v) for k, v in kwargs.items()}
        return Call(caller, args, kwargs)

    return ast


#
# The placeholder singletons
#
placeholder = _ = Expr(Var)
X = _X()
Y = _Y()
M = _M()
F = _F()
