from importlib import import_module

from .deferred import Deferred


def import_later(path, package=None):
    """
    Lazily import module or object inside a module. Can refer to a module or
    a symbol exported by that module.

    Args:
        path:
            Python path to module or object. Specific objects inside a module
            are refered as "<module path>:<object name>".
        package:
            Package name if path is a relative module path.

    Usage:
        import_later('numpy.random'):
            Proxy to the numpy.random module.
        import_later('numpy.random:uniform'):
            Proxy to the "uniform" object of the numpy module.
        import_later('.models', package=__package__):
            Relative import
    """
    if ":" in path:
        path, _, obj = path.partition(":")
        return _DeferredImport(path, obj, package=package)
    else:
        return _LazyModule(path, package=package)


class _LazyModule(Deferred):
    """
    A module that has not been imported yet.
    """

    def __init__(self, path, package=None):
        super().__init__(import_module, path, package=package)

    def __getattr__(self, attr):
        value = super().__getattr__(attr)
        setattr(self, attr, value)
        return value


class _DeferredImport(Deferred):
    """
    An object of a module that has not been imported yet.
    """

    def __init__(self, path, attr, package=None):
        mod = _LazyModule(path, package)
        super().__init__(lambda: getattr(mod, attr))
