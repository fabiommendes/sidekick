import ctypes
import sys
import types
import warnings

from ._modules import GetAttrModule, set_module_class

sys = sys
types = types
warnings = warnings
set_module_class(__name__, GetAttrModule)
cpython = ctypes.pythonapi
NOT_GIVEN = object()
DUNDER_GROUPS = {"number_methods": ["rshift", "lshift", "ror"]}
DUNDER_CATEGORIES = {
    meth: cat for cat, methods in DUNDER_GROUPS.items() for meth in methods
}
SPELL_1 = (
    'df_obde_oes*kag)\n  "\n  pl l oes\n  "\n  i y.lg.neatv rhstrss p1) #rnigfo '
    'l\n    rn(NwrglrPto ucin cetsdkc prtr n ehd.)  ei wrs! "pl" Inwsmo h ra oeso '
    ""
    'aba":    pit\n      D o s hsfnto npouto oe fyural elyn\n      wn t ov  '
    "uze\\\\'    )    rieRniero(yuivkdtewogsel)  es:    wrig.an\"ontueti "
    'ouefrntigsros"\n  @e_udrtpsFntoTp)  df_rhf_(ef te)\n    eunlmd ag,'
    "*kag:ohrsl(ag,*kag)\n  @e_udrtpsFntoTp)  df_lhf_(ef te)\n    eunlmd ag,"
    "*kag:sl(te(ag,*kag)\n  @e_udrtpsFntoTp)  df_rr_sl,ohr:    rtr efohr\n  "
    "@oc_eat(ye.ucinye pril)  dfprilsl,*rs *wrs:    rtr aba*o,*k:sl(ag,*o,*kag,*k)"
)
SPELL_2 = (
    'e fridnpwr(*wrs:  ""  Apyalpwr.  ""\n  fssfasitrcieo aat(y,\'s\':  unn rmci  '
    ""
    "  pit'o eua yhnfntosacp ieikoeaosadmtos'\n  lfkag ={sel:\" o umntegetpwr "
    "flmd!}\n    rn(      'ontueti ucini rdcincd.I o elyral\\'      'ati,"
    'sleapzl.nn\n    \n    as utmErr"o noe h rn pl"\n  le\n    annswr(D o s hsmdl '
    ""
    "o ohn eiu!)\n  stdne(ye.ucinye\n  e _sit_sl,ohr:    rtr aba*rs *wrs te(ef*rs "
    ""
    "*wrs)\n  stdne(ye.ucinye\n  e _sit_sl,ohr:    rtr aba*rs *wrs efohr*rs "
    "*wrs)\n  stdne(ye.ucinye\n  e _o_(ef te)\n    eunsl(te)\n  fresttrtpsFntoTp,"
    '"ata"\n  e ata(ef ag,*kag)\n    eunlmd ps *w ef*rs ps *wrs *w\n'
)


def no_evil():
    """
    Remove overloading arithmetic operators from fn-functions.
    """
    raise NotImplementedError


def force_setattr(obj, attr, value=NOT_GIVEN):
    """
    Adds a new attribute to builtin object cls.

    Tries setting attribute using Python, but falls back to C-level manipulation
    if not allowed.
    """
    if value is NOT_GIVEN:
        return lambda value: force_setattr(obj, attr, value) or value

    try:
        return setattr(obj, attr, value)
    except (AttributeError, TypeError):
        pass

    target = obj.__dict__
    proxy_dict = SlotsProxy.from_address(id(target))
    proxy_dict.dict[attr] = value


def capture_dunder(cls, magic):
    """
    Makes dunder method of builtin type available to be defined by a Python
    function.
    """
    name = DUNDER_CATEGORIES.get(magic, magic)
    offset = dunder_offsets[name]
    ref_from_address = ctypes.c_ssize_t.from_address
    tp_func_ref = ref_from_address(id(Object) + offset)
    tp_func_new = ref_from_address(id(cls) + offset)
    tp_func_new.value = tp_func_ref.value


def set_dunder(cls, method=None, name=None):
    """
    Saves a dunder method in class, enabling its usage.
    """
    if method is None:
        return lambda method: set_dunder(cls, method, name) or method
    name = name or method.__name__
    capture_dunder(cls, name.strip("_"))
    force_setattr(cls, name, method)


# Set offsets of python structures (from PyTypeObject)
offset = lambda x: (x + 4) * ctypes.sizeof(ctypes.c_ssize_t)
dunder_offsets = {
    # PyObject_VAR_HEAD
    "name": offset(0),  # const char *tp_name
    "itemsize": offset(1),  # Py_ssize_t tp_basicsize, tp_itemsize
    "dealloc": offset(2),  # destructor tp_dealloc
    "print": offset(3),  # printfunc tp_print
    "getattr": offset(4),  # getattrfunc tp_getattr
    "setattr": offset(5),  # setattrfunc tp_setattr
    "async_methods": offset(6),  # PyAsyncMethods *tp_as_async
    "repr": offset(7),  # reprfunc tp_repr
    "number_methods": offset(8),  # PyNumberMethods *tp_as_number
    "sequence_methods": offset(9),  # PySequenceMethods *tp_as_sequence
    "mapping_methods": offset(10),  # PyMappingMethods *tp_as_mapping
    "hash": offset(11),  # hashfunc tp_hash
    "call": offset(12),  # TernaryFunc tp_call
    "str": offset(13),  # reprfunc tp_str
    "getattro": offset(14),  # getattrofunc tp_getattro
    "setattro": offset(15),  # setattrofunc tp_setattro
    "buffer_methods": offset(16),  # PyBufferProcs *tp_as_buffer
    "flags": offset(17),  # unsigned long tp_flags
    "doc": offset(18),  # const char *tp_doc
    "traverse": offset(19),  # traverseproc tp_traverse
    "clear": offset(20),  # inquiry tp_clear
    "richcompare": offset(21),  # richcmpfunc tp_richcompare
    "weaklistoffset": offset(22),  # Py_ssize_t tp_weaklistoffset
    "iter": offset(23),  # getiterfunc tp_iter
    "iternext": offset(24),  # iternextfunc tp_iternext
    "methods": offset(25),  # struct PyMethodDef *tp_methods
    "members": offset(26),  # struct PyMemberDef *tp_members
    "getset": offset(27),  # struct PyGetSetDef *tp_getset
    "base": offset(28),  # struct _typeobject *tp_base
    "dict": offset(29),  # PyObject *tp_dict
    "get": offset(30),  # descrgetfunc tp_descr_get
    "set": offset(31),  # descrsetfunc tp_descr_set
    "dictoffset": offset(32),  # Py_ssize_t tp_dictoffset
    "init": offset(33),  # initproc tp_init
    "alloc": offset(34),  # allocfunc tp_alloc
    "new": offset(35),  # newfunc tp_new
    "free": offset(36),  # freefunc tp_free
    "is_gc": offset(37),  # inquiry tp_is_gc
    "bases": offset(38),  # PyObject *tp_bases
    "mro": offset(39),  # PyObject *tp_mro
    "cache": offset(40),  # PyObject *tp_cache
    "subclasses": offset(41),  # PyObject *tp_subclasses
    "weaklist": offset(42),  # PyObject *tp_weaklist
    "del": offset(43),  # destructor tp_del
    "version_tag": offset(44),  # unsigned int tp_version_tag
    "finalize": offset(45),  # destructor tp_finalize
}

py_object = ctypes.py_object
UnaryFunc = ctypes.CFUNCTYPE(py_object, py_object)
BinaryFunc = ctypes.CFUNCTYPE(py_object, py_object, py_object)
TernaryFunc = ctypes.CFUNCTYPE(py_object, py_object, py_object, py_object)
Inquiry = ctypes.CFUNCTYPE(ctypes.c_int, py_object)


class SlotsProxy(ctypes.Structure):
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", py_object),
        ("dict", py_object),
    ]


class NumberMethods(ctypes.Structure):
    _fields_ = [
        ("nb_add", BinaryFunc),
        ("nb_subtract", BinaryFunc),
        ("nb_multiply", BinaryFunc),
        ("nb_remainder", BinaryFunc),
        ("nb_divmod", BinaryFunc),
        ("nb_power", TernaryFunc),
        ("nb_negative", UnaryFunc),
        ("nb_positive", UnaryFunc),
        ("nb_absolute", UnaryFunc),
        ("nb_bool", Inquiry),
        ("nb_invert", UnaryFunc),
        ("nb_lshift", BinaryFunc),
        ("nb_rshift", BinaryFunc),
        ("nb_and", BinaryFunc),
        ("nb_xor", BinaryFunc),
        ("nb_or", BinaryFunc),
        ("nb_int", UnaryFunc),
        ("nb_reserved", ctypes.c_void_p),
        ("nb_float", UnaryFunc),
        ("nb_inplace_add", BinaryFunc),
        ("nb_inplace_subtract", BinaryFunc),
        ("nb_inplace_multiply", BinaryFunc),
        ("nb_inplace_remainder", BinaryFunc),
        ("nb_inplace_power", TernaryFunc),
        ("nb_inplace_lshift", BinaryFunc),
        ("nb_inplace_rshift", BinaryFunc),
        ("nb_inplace_and", BinaryFunc),
        ("nb_inplace_xor", BinaryFunc),
        ("nb_inplace_or", BinaryFunc),
        ("nb_floor_divide", BinaryFunc),
        ("nb_true_divide", BinaryFunc),
        ("nb_inplace_floor_divide", BinaryFunc),
        ("nb_inplace_true_divide", BinaryFunc),
        ("nb_index", UnaryFunc),
        ("nb_matrix_multiply", BinaryFunc),
        ("nb_inplace_matrix_multiply", BinaryFunc),
    ]


class Object:
    """
    Generic type we use to inspect the location of the generic C-level
    dunder functions.

    All methods supported must provide a placeholder implementation here.
    """

    def not_implemented(self):
        raise NotImplementedError

    __repr__ = __str__ = __rshift__ = __lshift__ = __ror__ = not_implemented


def __getattr__(name):
    # Highly obsfuscated code. This is the puzzle. If you solve it you can use
    # forbidden powers in production code. You can. but you shouldn't. Really,
    # don't do it!
    import toolz
    import inspect
    import os

    if name != "forbidden_powers":
        raise AttributeError(name)

    evil = os.environ.get("EVIL", "").lower() == "true"

    try:
        fn = globals()["_forbidden_powers"]
    except KeyError:
        pass
    else:
        if evil:
            data = inspect.getsource(fn)
            print("Forbidden power spells")
            print(f"SPELL_1 = {data[::2]!r}")
            print(f"SPELL_2 = {data[1::2]!r}")
            print("\n\n")
        return fn

    code = "".join(toolz.interleave([SPELL_1, SPELL_2]))
    if evil:
        print("Forbidden_powers code\n\n")
        print(code)
    exec(code, globals())
    return globals()["_forbidden_powers"]
