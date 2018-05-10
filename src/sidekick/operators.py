import operator as op


def identity(x):
    "A function that returns its single argument."
    return x


UNARY = [
    op.abs, op.invert, op.neg, op.pos, op.index,
]

METHODS = [
    op.attrgetter, op.contains, op.delitem, op.getitem, op.itemgetter,
]

BINARY = [
    op.add, op.and_, op.floordiv, op.lshift, op.mod, op.mul,
    op.pow, op.rshift, op.sub, op.truediv, op.xor,
]

COMPARISON = [
    op.eq, op.ge, op.gt, op.le, op.lt, op.ne,
]

KEYWORDS = [
    op.is_, op.is_not, op.or_, op.not_,
]

SYMBOLS = {
    op.invert: '~',
    op.neg: '-',
    op.pos: '+',
    op.add: '+',
    op.and_: '&',
    op.floordiv: '//',
    op.lshift: '<<',
    op.mod: '%',
    op.mul: '*',
    op.pow: '**',
    op.rshift: '>>',
    op.sub: '-',
    op.truediv: '/',
    op.xor: '^ ',
    op.eq: '==',
    op.ge: '>=',
    op.gt: '>',
    op.le: '<=',
    op.lt: '<',
    op.ne: '!=',
}

if hasattr(op, 'matmul'):  # only on Python 3.5+
    BINARY.append(op.matmul)
    SYMBOLS[op.matmul] = '@'
