import operator
from collections import namedtuple
from functools import singledispatch

from .operators import UNARY, BINARY, COMPARISON, METHODS, SYMBOLS, NAMES

flip = lambda f: lambda x, y: f(y, x)
named = lambda name, obj: setattr(obj, "__name__", name) or obj
__all__ = ["placeholder", "Placeholder", "F"]


#
# Operator factories and registration
#
def register_operators(rfunc, operators):
    """
    Register a list of operators.
    """

    def decorator(cls):
        registered = set(cls.__dict__)
        registered.update(("__index__",))

        for op in operators:
            op = rfunc(op, cls)
            if op.__name__ not in registered:
                setattr(cls, op.__name__, op)
        return cls

    return decorator


def unary(op, cls):
    name = NAMES[op]
    return named("__%s__" % name, lambda self: cls(UnaryOp(op, self._ast)))


def binary(op, cls):
    name = NAMES[op]
    return named(
        "__%s__" % name, lambda self, other: cls(BinOp(op, self._ast, to_ast(other)))
    )


def rbinary(op, cls):
    name = NAMES[op]
    return named(
        "__r%s__" % name, lambda self, other: cls(BinOp(op, to_ast(other), self._ast))
    )


@register_operators(unary, UNARY)
@register_operators(binary, BINARY + COMPARISON + METHODS)
@register_operators(rbinary, BINARY)
class Placeholder:
    """
    Placeholder objects represents a variable or expression on quick lambda.
    """

    __slots__ = "_ast", "_cache"

    _name = property(lambda self: self.__repr__())

    @property
    def __wrapped__(self):
        raise AttributeError('__wrapped__')

    @property
    def __inner_function__(self):
        if self._cache is None:
            self._cache = compile_ast(simplify_ast(self._ast))
        return self._cache

    def __init__(self, ast, cache=None):
        self._ast = ast
        self._cache = cache

    def __repr__(self):
        return f"{type(self).__name__}({self})"

    def __str__(self):
        if self._ast is None:
            return "_"
        return source(self._ast)

    def __getattr__(self, attr):
        return Placeholder(GetAttr(attr, self._ast))

    def __call__(self, *args, **kwargs):
        args = tuple(map(to_ast, args))
        kwargs = {k: to_ast(v) for k, v in kwargs.items()}
        return Placeholder(Call(self._ast, args, kwargs))


# noinspection PyPep8Naming
def F(func, *args, **kwargs):  # noqa: N802
    """
    A helper object that can be used to define function calls on a placeholder
    object.
    """

    args = tuple(to_ast(x) for x in args)
    kwargs = {k: to_ast(x) for k, x in kwargs.items()}
    return Placeholder(Call(Cte(func), args, kwargs))


# ------------------------------------------------------------------------------
# AST node types and representation
# ------------------------------------------------------------------------------

VarType = type("Var", (), {"__repr__": lambda x: "Var"})
BinOp = namedtuple("BinOp", ["op", "lhs", "rhs"])
Call = namedtuple("Call", ["caller", "arguments", "kwargs"])
Cte = namedtuple("Cte", ["value"])
GetAttr = namedtuple("GetAttr", ["attr", "value"])
UnaryOp = namedtuple("SingleOp", ["op", "value"])
Var = VarType()


def to_ast(obj):
    """
    Convert object to AST node.
    """
    if isinstance(obj, Placeholder):
        # noinspection PyProtectedMember
        return obj._ast
    else:
        return Cte(obj)


def call_node(func, *args, **kwargs):
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
OP_SYMBOLS = {k: " %s " % v for k, v in SYMBOLS.items()}
OP_SYMBOLS[operator.attrgetter] = "."


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
    return "(%s %s %s)" % (source(lhs), op_symbol(op), source(rhs))


@source.register(UnaryOp)
def _(node):
    op, value = node
    return "(%s %s)" % (op_symbol(op), source(value))


@source.register(Call)
def _(node):
    obj, args, kwargs = node
    return "%s(*%s, **%s)" % (obj, args, kwargs)


@source.register(GetAttr)
def _(node):
    attr, obj = node
    return "%s.%s" % (obj, attr)


@source.register(Cte)
def _(node):
    return repr(node.value)


def op_symbol(op):
    return OP_SYMBOLS[op]


# ------------------------------------------------------------------------------
# Compiling AST nodes
# ------------------------------------------------------------------------------
SIMPLE_TYPES = (int, float, complex, str, bytes, bool, type(None))


@singledispatch
def compile_ast(ast):
    """
    Compile a placeholder expression and return the corresponding anonymous
    function.
    """
    if ast is Var:
        return var_identity
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
    return lambda x: caller(x)(*(f(x) for f in args), **{k: v(x) for k, v in kwargs})


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


var_identity = lambda x: x


# ------------------------------------------------------------------------------
# Simplifying AST nodes
# ------------------------------------------------------------------------------


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
# The placeholder symbol
#
placeholder = _placeholder = Placeholder(Var, var_identity)
