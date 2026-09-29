from copy import copy
import re
import os
import sys
from functools import cached_property, wraps
from types import ModuleType
from typing import Any, List, Tuple, Type, Union
from pathlib import Path
from importlib import import_module

from .types import Raisable, Catchable

SPACES = re.compile(r"\s+")
BUILDING_DOCS = False


# =============================================================================
# String and documentation utilities
# =============================================================================
class lazy_string(cached_property):
    """
    A lazy string property
    """

    __slots__ = "string"

    def __init__(self, func, string):
        super().__init__(func)
        self.string = string

    def __get__(self, instance, cls=None):
        if instance is None:
            return self.string
        return self.func(instance)


def dash_case(name: str) -> str:
    """
    Convert a camel case string to dash case.

    Example:
        >>> dash_case('SomeName')
        'some-name'
    """
    return _dash_case(name, "-")


def snake_case(name: str) -> str:
    """
    Convert camel case to snake case.
    """
    return _dash_case(name, "_")


def _dash_case(name: str, sep: str) -> str:
    letters: List[str] = []
    for c in name:
        if c.isupper() and letters and letters[-1] != sep:
            letters.append(sep + c.lower())
        else:
            letters.append(c.lower())
    return "".join(letters)


def indent(ind: Union[int, str], st: str) -> str:
    """
    Indent string.
    """

    if isinstance(ind, int):
        ind = " " * ind
    return ind.join(st.splitlines(True))


def dedent(st: str) -> str:
    """
    Dedent string.
    """
    st = st.strip()
    lines = [ln.strip() for ln in st.splitlines()]
    matches = filter(
        None, (SPACES.match(ln) for ln in lines if not SPACES.fullmatch(ln))
    )
    indent = max([0, *map(lambda m: m.span()[1], matches)])
    if not indent:
        return st

    out = []
    for ln in lines:
        if SPACES.fullmatch(ln):
            out.append("")
        else:
            out.append(ln[indent:])
    return "\n".join(out)


def function_in_docs(fn):
    """
    Convert function-like objects to functions to make sphinx understand
    them correctly.
    """
    if BUILDING_DOCS:

        @wraps(fn)
        def function(*args, **kwargs):
            return fn(*args, **kwargs)

        return function
    return fn


def building_docs():
    """
    Activated when building documentation.
    """
    global BUILDING_DOCS
    BUILDING_DOCS = True


def coalesce(*args) -> Any:
    """
    Return the first non-null argument.
    """
    for arg in args:
        if arg is not None:
            return arg


def safe_repr(x: Any) -> str:
    """
    A repr() that never fails, even if object has some bad implementation.
    """
    try:
        return repr(x)
    except:
        name = getattr(type(x), "__name__", "object")
        return f"<{name} instance>"


# =============================================================================
# Raising and catching errors utilities
# =============================================================================
def is_raisable(obj) -> bool:
    """
    Test if object is valid in a "raise obj" statement.
    """

    return isinstance(obj, Exception) or (
        isinstance(obj, type) and issubclass(obj, Exception)
    )


def is_catchable(obj) -> bool:
    """
    Check if object is valid in a "except obj" statement.
    """

    if isinstance(obj, tuple):
        return all(isinstance(x, type) and issubclass(x, Exception) for x in obj)
    return isinstance(obj, type) and issubclass(obj, Exception)


def to_raisable(obj: Any, exception=ValueError) -> Raisable:
    """
    Wrap object in exception if object is not valid in a "raise obj" statement.
    """

    if not is_raisable(obj):
        return exception(obj)
    return obj


def catches(raisable: Raisable, catchable: Catchable):
    """
    Tests if raisable value would be catchable by catchable value.
    """
    if isinstance(catchable, type):
        catchables: Tuple[Type[Exception], ...] = (catchable,)
    else:
        catchables = catchable

    if isinstance(raisable, type):
        return any(issubclass(raisable, exc) for exc in catchables)
    else:
        return any(isinstance(raisable, exc) for exc in catchables)


# =============================================================================
# Special modules
# =============================================================================
class GetAttrModule(ModuleType):
    """
    A module type that implements the __getattr__ behavior from Python 3.7+
    """

    def __getattr__(self, item):
        try:
            method = self.__dict__["__getattr__"]
        except KeyError:
            raise AttributeError(item)
        else:
            value = method(item)
            setattr(self, item, value)
            return value


class LazyPackage(GetAttrModule):
    """
    A suitable module type for __init__.py files. It automatically loads
    names in __all__ from lazily loaded sub-packages.
    """

    def __getattr__(self, item):
        if item in self.__all__:
            for package in get_subpackages(self):
                try:
                    value = get_item(package, item)
                except AttributeError:
                    continue
                else:
                    setattr(self, item, value)
                    return value

        return super().__getattr__(item)


def get_subpackages(mod):
    try:
        return mod.__sk_subpackages__
    except AttributeError:
        ...
    prefix = mod.__name__ + "."
    path: Path = Path(mod.__file__).parent
    mod.__sk_subpackages__ = subpackages = [
        prefix + x[:-3]
        for x in os.listdir(path)
        if x.endswith(".py") and x != "__init__.py"
    ]

    return subpackages


def get_item(module, item):
    try:
        mod = sys.modules[module]
    except KeyError:
        mod = import_module(module)
    return getattr(mod, item)


def set_module_class(name: str, kind: Type[ModuleType]):
    """
    Register model class to given module.
    """
    mod = sys.modules[name]
    mod.__class__ = kind

    try:
        if mod.set_module_class == set_module_class:
            del mod.set_module_class
    except AttributeError:
        pass

    try:
        cls_name = kind.__name__
        if getattr(mod, cls_name) == kind:
            delattr(mod, cls_name)
    except AttributeError:
        pass


# =============================================================================
# Misc. classes
# =============================================================================
class mixed_accessor:
    """
    Descriptor with different class and an instance implementations.
    """

    __slots__ = ("_cls", "_instance")

    def __init__(self, instance=None, cls=None):
        self._cls = cls
        self._instance = instance
        if cls:
            self._cls = classmethod(cls).__get__
        if instance:
            self._instance = instance.__get__

    def classmethod(self, func):
        new = copy(self)
        new._cls = classmethod(func).__get__
        return new

    def instancemethod(self, func):
        new = copy(self)
        new._instance = func.__get__
        return new

    def __get__(self, instance, cls=None):
        if instance is None:
            return self._cls(cls)
        else:
            return self._instance(instance)

    def __set__(self, _instance, _value):
        raise TypeError
