from importlib import import_module

from .deferred import deferred


def import_later(path, package=None):
    """
    Lazily import module or object.

    Lazy imports can dramatically decrease the initialization time of your python
    modules, specially when heavy weights such as numpy, and pandas are used.
    Beware that import errors that normally are triggered during import time
    now can be triggered at first use, which may introduce confusing and hard
    to spot bugs.

    Args:
        path:
            Python path to module or object. Modules are specified by their
            Python names (e.g., 'os.path') and objects are identified by their
            module path + ":" + object name (e.g., "os.path.splitext").
        package:
            Package name if path is a relative module path.

    Examples:
        >>> np = sk.import_later('numpy')  # Numpy is not yet imported
        >>> np.array([1, 2, 3])  # It imports as soon as required
        array([1, 2, 3])

        It also accepts relative imports if the package keyword is given. This
        is great to break circular imports.

        >>> mod = sk.import_later('.sub_module', package=__package__)
    """
    if ":" in path:
        path, _, obj = path.partition(":")
        return _DeferredImport(path, obj, package=package)
    else:
        return _LazyModule(path, package=package)


class _LazyModule(deferred):
    """
    A module that has not been imported yet.
    """

    def __init__(self, path, package=None):
        super().__init__(import_module, path, package=package)

    def __getattr__(self, attr):
        value = super().__getattr__(attr)
        setattr(self, attr, value)
        return value


class _DeferredImport(deferred):
    """
    An object of a module that has not been imported yet.
    """

    def __init__(self, path, attr, package=None):
        mod = _LazyModule(path, package)
        super().__init__(lambda: getattr(mod, attr))
