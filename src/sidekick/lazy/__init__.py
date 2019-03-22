from .deferred import *
from .lazy import *
from .zombie import *


# noinspection PyProtectedMember
def touch(obj):
    """
    Return a non-proxy, non-zombie version of object. Regular objects are
    returned as-is.
    """
    if isinstance(obj, ZombieTypes):
        obj._Zombie__awake()
        return obj
    elif isinstance(obj, Proxy):
        return obj._proxy_obj_
    return obj
