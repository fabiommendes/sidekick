from .deferred import *
from .lazy import *
from .zombie import zombie, ZombieTypes as _ZombieTypes


def touch(obj):
    """
    Return a non-proxy, non-zombie version of object. Regular objects are
    returned as-is.
    """
    if isinstance(obj, _ZombieTypes):
        obj._Zombie__awake()
        return obj
    elif isinstance(obj, Proxy):
        return obj._proxy_obj_
    return obj
