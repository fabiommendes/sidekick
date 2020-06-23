from .zombie import UNARY_METHODS, BINARY_METHODS, RBINARY_METHODS, ARBITRARY_METHODS
from ..functions import call


class Proxy:
    """
    Base class for proxy types.
    """

    __slots__ = ("_proxy_obj_",)

    def __init__(self, obj):
        self._proxy_obj_ = obj

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.__get_object())})"

    def __get_object(self):
        return self._proxy_obj_

    def __call__(self, *args, **kwargs):
        return self._proxy_obj_(*args, **kwargs)

    def __getattr__(self, attr):
        obj = self._proxy_obj_
        return getattr(obj, attr)


# noinspection PyMissingConstructor
class deferred(Proxy):
    """
    Wraps uninitialized object into a proxy shell.

    Object is declared as a thunk and is initialized the first time some
    attribute or method is requested.

    The proxy delegates all methods to the lazy object. Proxies work nicely with
    duck typing, but are a poor fit to code that relies in explicit instance
    checks since the deferred object is a :class:`Proxy` instance.

    Usage:
        >>> from operator import add
        >>> x = sk.deferred(add, 40, 2)  # add function not called yet
        >>> print(x)                     # any interaction triggers object construction!
        42

    """

    __slots__ = ("_deferred_constructor_",)

    def __init__(self, func, *args, **kwargs):
        init = lambda: func(*args, **kwargs)
        self._deferred_constructor_ = init

    def __repr__(self):
        # return f"{type(self).__name__}({repr(self._Proxy__get_object())})"
        return f"Proxy({repr(self._Proxy__get_object())})"

    # noinspection PyPep8Naming
    def _Proxy__get_object(self):
        try:
            return self._proxy_obj_
        except AttributeError:
            self._proxy_obj_ = obj = self._deferred_constructor_()
            return obj

    def __getattr__(self, attr):
        if attr == "_proxy_obj_":
            self._proxy_obj_ = obj = self._deferred_constructor_()
            del self._deferred_constructor_
            return obj
        try:
            obj = self._proxy_obj_
        except KeyError:
            obj = self._Proxy__get_object()
        return getattr(obj, attr)


@call()
def _patch_proxy():
    definitions = []
    template = (
        "def __{name}__(self{sep}{args}):\n"
        "   return self._proxy_obj_.__{name}__({args})"
    )

    for name in UNARY_METHODS:
        code = template.format(name=name, sep="", args="")
        definitions.append(code)

    for name in BINARY_METHODS + RBINARY_METHODS:
        code = template.format(name=name, sep=", ", args="other")
        definitions.append(code)

    for name in ARBITRARY_METHODS:
        code = template.format(name=name, sep=", ", args="*args, **kwargs")
        definitions.append(code)

    ns = {}
    code = "\n".join(definitions)
    exec(code, {}, ns)
    for k, v in ns.items():
        setattr(Proxy, k, v)
