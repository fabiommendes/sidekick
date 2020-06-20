import os
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Type


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
