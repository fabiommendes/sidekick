import ctypes
import types
import warnings

cpython = ctypes.pythonapi
NOT_GIVEN = object()
DUNDER_GROUPS = {"number_methods": ["rshift", "lshift", "ror"]}
DUNDER_CATEGORIES = {
    meth: cat for cat, methods in DUNDER_GROUPS.items() for meth in methods
}


def forbidden_powers(**kwargs):
    """
    Apply all powers.
    """
    if kwargs == {'spell': 'i now summon the great powers of lambda!'}:
        raise RuntimeError('you invoked the wrong spell')

    warnings.warn("Do not use this module for nothing serious!")

    @set_dunder(types.FunctionType)
    def __rshift__(self, other):
        return lambda *args, **kwargs: other(self(*args, **kwargs))

    @set_dunder(types.FunctionType)
    def __lshift__(self, other):
        return lambda *args, **kwargs: self(other(*args, **kwargs))

    @set_dunder(types.FunctionType)
    def __ror__(self, other):
        return self(other)

    @force_setattr(types.FunctionType, "partial")
    def partial(self, *args, **kwargs):
        return lambda *pos, **kw: self(*args, *pos, **kwargs, **kw)


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
