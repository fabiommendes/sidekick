from functools import wraps as _wraps

import builtins as _builtins

from sidekick import fn, Pred, Seq, extract_function, Func

_execute_with = lambda *args, **kwargs: lambda f: f(*args, **kwargs) or f
_flipped = lambda f: _wraps(f)(lambda x, y: f(y, x))
_filter = filter
_map = map


# Arity-1 functions
# abs, all, any, ascii, bin, bool, callable, chr, classmethod, dict, dir, float
# frozenset, hash, help, hex, id, input, int, iter, len, list, memoryview
# next, oct, ord, repr, reversed, round, set, sorted, staticmethod, str, sum
# tuple, type, vars


@fn.annotate(2)
def filter(pred: Pred, seq: Seq):
    """
    Return an iterator yielding those items of iterable for which function(item)
    is true.

    filter(pred, seq) ==> seq[a], seq[b], seq[c], ...

    in which a, b, c, ... are the indexes in which pred(seq[i]) == True.
    """
    return _filter(extract_function(pred), seq)


@fn.annotate(2)
def map(func: Func, *seqs: Seq) -> Seq:
    """
    Make an iterator that computes the function using arguments from
    each of the iterables.  Stops when the shortest iterable is exhausted.

        map(func, *seqs) ==> f(X[0], Y[0], ...), f(X[1], Y[1], ...), ...

    in which X, Y, Z, ... are the sequences in seqs.
    """
    return _map(func, *seqs)


@fn.annotate(2)
def int_base(base, x):
    """
    Convert string x representing a number in some base to integer.
    """
    return _builtins.int(x, base)


@fn.annotate(3)
def getattr_or(default, attr, obj):
    """
    Return given attribute of object or the default argument if attr is not
    given.
    """
    return _builtins.getattr(obj, attr, default)


@fn.annotate(2)
@_wraps(setattr)
def setattr(value, attr, obj):
    """
    Like setattr, but with the arguments flipped.
    """
    return _builtins.setattr(obj, attr, value)


max = fn(max)
min = fn(min)


# What should we do with those functions?
def _raise(*args, **kwargs):
    raise NotImplementedError('use the builtin function for now!')


bytearray = bytes = compile = eval = exec = pow = open = print = property = \
    range = slice = super = zip = _raise


#
# Patch module to include other functions
#
@_execute_with(
    _builtins, globals(),
    arities={
        'complex': 2, 'divmod': 2, 'globals': 0, 'locals': 0, 'object': 0
    },
    flipped={
        'delattr', 'enumerate', 'format', 'getattr', 'hasattr', 'isinstance',
        'issubclass',
    },
    blacklist={
        'breakpoint', 'copyright', 'credits', 'display', 'get_ipython',
        'license',
    })
def _create_fn_functions(mod, variables, arities=None, flipped=(), blacklist=()):
    arities = arities or {}
    for k, v in vars(mod).items():
        if k.startswith('_') or k in variables or k in blacklist:
            continue

        if callable(v):
            if k in flipped:
                v = fn.annotate(2)(_flipped(v))
            else:
                v = fn.annotate(arities.get(k, 1))(v)
        variables[k] = v
