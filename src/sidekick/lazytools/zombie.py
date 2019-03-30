from types import MemberDescriptorType

from ..core.operators import NAMES, UNARY, BINARY, COMPARISON
from ..functools import call

ZOMBIE_CLASSES = {}
UNARY_METHODS = [NAMES[op] for op in UNARY]
BINARY_METHODS = [NAMES[op] for op in COMPARISON + BINARY]
RBINARY_METHODS = ["__r" + NAMES[op][2:] for op in BINARY]
__all__ = ["ZombieTypes", "zombie", "UNARY_METHODS", "BINARY_METHODS", "RBINARY_METHODS"]


class Zombie:
    """
    A magic zombie object.

    It creates a proxy that is converted to the desired object on almost any
    interaction. This only works with pure Python objects with no slots since
    the Delayed object must have the same C level interface as the real object.

    For a safer version of :class:`sidekick.Delayed`, try the
    :class:`sidekick.Proxy` class. One advantage of deferred objects is that,
    when alive, they transform to objects of the correct class.

    Args:
        func (callable):
            Any callable used to create the final object.
        *args, **kwargs:
            Optional positional and keyword arguments used to call the first
            argument.

    Examples:
        Imagine we have some arbitrary Python class

        >>> class SomeClass:
        ...     def method(self):
        ...         return 42

        Now create a delayed object
        >>> x = zombie(SomeClass)
        >>> type(x)                                         # doctest: +ELLIPSIS
        <class '...Zombie'>

        If we touch any method (even magic methods triggered by operators),
        the zombie awakens and is converted to the result produced by the
        factory function:
        >>> x.method()
        42
        >>> type(x)                                         # doctest: +ELLIPSIS
        <class '...SomeClass'>
    """

    def __init__(self, func, *args, **kwargs):
        object.__setattr__(self, "_Zombie__constructor", lambda: func(*args, **kwargs))

    def __getattr__(self, attr):
        self.__awake()
        return getattr(self, attr)

    def __del__(self):
        del self.__constructor

    def __call__(self, *args, **kwargs):
        self.__awake()
        return self(*args, **kwargs)

    def __setitem__(self, k, v):
        self.__awake()
        self[k] = v

    def __awake(self):
        result = self.__constructor()
        del self.__constructor
        if hasattr(result, "__dict__"):
            object.__getattribute__(self, "__dict__").update(result.__dict__)

        # Safer than obj.__class__ = type(result) since avoids custom __setattr__
        object.__setattr__(self, "__class__", type(result))
        return self


class ZombieFactory:
    """
    Base class that implements the zombie[class] syntax.
    """

    def __call__(self, func, *args, **kwargs):
        return Zombie(func, *args, **kwargs)

    def __getitem__(self, cls):
        try:
            return ZOMBIE_CLASSES[cls]
        except KeyError:
            pass

        slots = get_class_slots(cls)
        base = Zombie if slots is None else SlottedZombie
        constructor_cache = {}

        # noinspection PyPep8Naming
        class SpecializedZombie(base, cls):
            """
            Specialized zombie class that creates objects some specific class.
            """

            # Classes with slots need special treatment since both the zombie
            # and the awaken instances must have the same slots layout. This
            # means that the constructor cannot be saved as a class attribute
            # and rather must be stored in a separate cache.
            if slots is not None:
                __slots__ = ()

                def __init__(self, func, *args, **kwargs):
                    constructor = lambda: func(*args, **kwargs)
                    constructor_cache[id(self)] = constructor

                def __del__(self):
                    constructor_cache.pop(id(self), None)

                # noinspection PyCallByClass
                def _Zombie__awake(self):
                    constructor = constructor_cache.pop(id(self))
                    result = constructor()

                    if not isinstance(result, cls):
                        res_class = type(result).__name__
                        msg = f"expect {cls.__name__}, got {res_class}"
                        raise TypeError(msg)

                    # Safer than obj.__class__ = type(result) since avoids
                    # custom __setattr__
                    object.__setattr__(self, "__class__", type(result))

                    update_slot_attributes(self, result, slots)
                    if "__dict__" in slots:
                        update_dict_attributes(self, result)

                    return self

        for attr in dir(cls):
            if not hasattr(base, attr) and attr not in SpecializedZombie.__dict__:
                setattr(SpecializedZombie, attr, zombie_attribute(attr))

        SpecializedZombie.__name__ = f"Zombie[{cls.__name__}]"
        ZOMBIE_CLASSES[cls] = SpecializedZombie
        return SpecializedZombie


#
# Auxiliary functions
#
def zombie_attribute(attr):
    """
    Return an attribute that awakes zombie object before access.
    """

    def attribute(self):
        self._Zombie__awake()
        return getattr(self, attr)

    return property(attribute)


def get_class_slots(cls):
    """
    Return a list of all slots registered in class and parent classes.
    """
    slots = set()
    for sub in cls.mro():
        if sub is object:
            continue

        # Get slots from slots attribute
        cls_slots = sub.__dict__.get("__slots__")
        if isinstance(cls_slots, str):
            slots.add(cls_slots)
            continue
        elif isinstance(cls_slots, (tuple, list)):
            slots.update(slots)
            continue

        # Explicitly search for slot member objects
        else:
            members = []
            for k, v in sub.__dict__.items():
                if isinstance(v, MemberDescriptorType):
                    members.append(k)
            if members:
                slots.update(members)
            else:
                return None

    return tuple(slots)


def update_slot_attributes(obj, source, slots):
    """
    Save attributes from source that are stored in slots.
    """
    for field in slots:
        if field == "__dict__":
            continue
        try:
            value = getattr(source, field)
        except AttributeError:
            pass
        else:
            object.__setattr__(obj, field, value)


def update_dict_attributes(obj, source):
    """
    Save attributes from source that are stored in __dict__.
    """
    for k, v in source.__dict__.items():
        object.__setattr__(obj, k, v)


#
# Zombie types
#
SlottedZombie = type("SlottedZombie", (), {"__slots__": ()})
ZombieTypes = (Zombie, SlottedZombie)
zombie = ZombieFactory()


#
# Add magical methods to ZombieTypes
#
@call()
def _patch_zombie_class():
    definitions = []
    zombie_ns = dict(Zombie.__dict__)
    del zombie_ns["__doc__"]
    del zombie_ns["__dict__"]
    del zombie_ns["__weakref__"]
    template = (
        "def __{name}__(self{sep}{args}):\n"
        "   self._Zombie__awake()\n"
        "   return self.__{name}__({args})"
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
    zombie_ns.update(ns)

    for k, v in ns.items():
        setattr(Zombie, k, v)

    for k, v in zombie_ns.items():
        setattr(SlottedZombie, k, v)
