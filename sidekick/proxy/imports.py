import re
from functools import lru_cache
from importlib import import_module

from .deferred import deferred

GIT_PATH = re.compile(r"(?:git\+)?\w+://(?:[\w.]+)/(?P<repo>[^/]+/[^/]+).git")
LOCAL_PATH = re.compile(r"(\w+(?:\.\w+)*)(:\w+)?")
END_PATH = re.compile(r".+?:\w+")
PYPI_ERROR = """The package {module!r} was not found in your system. 

Please install the necessary dependencies using `pip install {pipname}`.
"""


def import_later(path, package=None, error=None, pypi=None):
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
        error:
            An string or exception instance that is used to create an error if
            it is not possible to import the given module. This is useful to
            display messages to the user redirecting them to install an optional
            dependency.
        pypi:
            PyPI name of the desired package. If given, it is used to construct
            a string with a suitable (albeit generic) error message.


    Examples:
        >>> np = sk.import_later('numpy')  # Numpy is not yet imported
        >>> np.array([1, 2, 3])  # It imports as soon as required
        array([1, 2, 3])

        It also accepts relative imports if the package keyword is given. This
        is great to break circular imports.

        >>> mod = sk.import_later('.sub_module', package=__package__)
    """
    if END_PATH.fullmatch(path):
        path, _, obj = path.rpartition(":")
        error = _get_error_message(error, pypi, path)
        return _DeferredImport(path, obj, package=package, error=error)
    else:
        error = _get_error_message(error, pypi, path)
        return _LazyModule(path, package=package, error=error)


class _LazyModule(deferred):
    """
    A module that has not been imported yet.
    """

    def __init__(self, path, package=None, error=None):
        opts = {"package": package, "error": error}
        if LOCAL_PATH.fullmatch(path):
            super().__init__(_check_import, import_module, path, **opts)
        else:
            super().__init__(_check_import, _import_from_github, path, **opts)

    def __getattr__(self, attr):
        value = super().__getattr__(attr)
        setattr(self, attr, value)
        return value


class _DeferredImport(deferred):
    """
    An object of a module that has not been imported yet.
    """

    def __init__(self, path, attr, package=None, error=None):
        mod = _LazyModule(path, package, error=error)
        super().__init__(lambda: getattr(mod, attr))


def _check_import(*args, error=None, **kwargs):
    fn, *args = args
    try:
        return fn(*args, **kwargs)
    except ImportError:
        if isinstance(error, str):
            raise RuntimeError(error)
        elif error is None:
            raise
        raise error


def _get_error_message(error, pip_name, path):
    if error:
        return error
    elif pip_name:
        return PYPI_ERROR.format(pipname=pip_name, module=path)
    else:
        return None


@lru_cache(1024)
def _import_from_github(path: str, package: str = None):
    """
    Easter egg/hack that allows importing packages from git. It pip installs the
    package before loading it.
    """
    import pip

    url, _, mod = path.rpartition("@")
    if not url:
        url = mod
        if path.endswith(".git"):
            path = path[:-4]
        mod = path.rpartition("/")[-1]
    pip.main(["install", url])
    return import_module(mod)
