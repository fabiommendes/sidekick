from .zombie import UNARY_METHODS, BINARY_METHODS, RBINARY_METHODS
from ..functools import call

__all__ = ["Deferred", "Proxy", "deferred"]


class Proxy:
    """
    Base class for proxy types.
    """

    __slots__ = ("_proxy_obj_",)

    def __init__(self, obj):
        self._proxy_obj_ = obj

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._get_object())})"

    def __get_object(self):
        return self._proxy_obj_

    def __call__(self, *args, **kwargs):
        return self._proxy_obj_(*args, **kwargs)

    def __getattr__(self, attr):
        obj = self._proxy_obj_
        return getattr(obj, attr)


# noinspection PyMissingConstructor
class Deferred(Proxy):
    """
    Like Delayed, but wraps object into a proxy shell.
    """

    __slots__ = ("_deferred_constructor_",)

    def __init__(self, func, *args, **kwargs):
        init = lambda: func(*args, **kwargs)
        self._deferred_constructor_ = init

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._Proxy__get_object())})"

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


def deferred(func, *args, **kwargs):
    """
    Similar to delayed, but safer since it creates a Deferred object.

    The proxy delegates all methods to the lazy object. It can break a few
    interfaces since it is never converted to the same value as the proxied
    element.

    Usage:

        >>> from operator import add
        >>> x = Deferred(add, 40, 2)  # add function not called yet
        >>> print(x)                  # trigger object construction!
        42
    """
    return Deferred(func, *args, **kwargs)


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

    ns = {}
    code = "\n".join(definitions)
    exec(code, {}, ns)
    for k, v in ns.items():
        setattr(Proxy, k, v)
