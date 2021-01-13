from ..functions import fn


# ------------------------------------------------------------------------------
# DATA MAGICS
# ------------------------------------------------------------------------------


class DataMagicMeta(type):
    def __new__(mcs, name, bases, ns, *, type=None):
        if type is not None:
            ns = dict(default_namespace(type), **ns)
            meta = ns.get("_meta", {})
            for method in meta.get("methods", ()):
                ns.update(method(type, ns))

        return super().__new__(mcs, name, bases, ns)

    __init__ = lambda *args, **kwargs: None


#
# Factory functions
#
def default_namespace(tt):
    def pipe(self, obj):
        try:
            return tt(obj)
        except TypeError:
            return self.coerce(obj)

    ns = {"type": tt, "__ror__": pipe, "__lt__": pipe}
    return ns


@fn.curry(3)
def pure(name, type, ns, *, arity=None, flip=False):
    base = impure(name, type, ns, arity=arity, flip=flip)
    return base


@fn.curry(3)
def impure(name, tt, ns, *, arity=None, flip=False):
    method = getattr(tt, name)
    if name in ns:
        raise TypeError(f"function already registered: {name}")

    if flip and arity is None:
        arity = 2

    # Simple methods. Just call the inner function
    if arity == 1:
        func = fn.wraps(method, method)

    # Implement methods of arbitrary arity
    elif arity is not None:

        @staticmethod
        @fn.wraps(method)
        @fn.curry(arity)
        def func(*args, **kwargs):
            if len(args) != arity:
                raise TypeError
            args = args[::-1] if flip else args
            obj = args[0]
            if isinstance(obj, type):
                return method(*args, **kwargs)
            else:
                action = getattr(obj, name)
                return action(*args[1:], **kwargs)

    else:
        raise ValueError(name)

    return {name: func}


#
# Base class
#
class DataMagic(metaclass=DataMagicMeta, type=None):
    def coerce(self, obj):
        """Coerce argument to the magic object expected type."""
        if isinstance(obj, self.type):
            return obj
        else:
            return self.convert(obj)

    def convert(self, obj):
        return self.type(obj)
