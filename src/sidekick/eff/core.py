import inspect
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from functools import lru_cache

INTENT_CACHE = {}
NoneType = type(None)


#
# Basic effect classes
#
class Effect:
    """
    Base class for all effects.
    """

    def _get_intents(self):
        typ = type(self)
        try:
            return INTENT_CACHE[typ]
        except KeyError:
            intents = [k for k in dir(self) if not k.startswith("_")]
            INTENT_CACHE[typ] = intents
            return intents


class OverrideEffect(Effect):
    """
    Implements overridable results from another effect class.
    """

    def __init__(self, effect, overrides, fallback=False):
        self._effect = effect
        self._overrides = {k: iter(v).__next__ for k, v in overrides.items()}
        self._fallback = fallback

    def __getattr__(self, attr):
        if attr in self._overrides:

            def intent(*args):
                try:
                    values = self._overrides[attr]
                    return values()
                except (KeyError, StopIteration):
                    if self._fallback:
                        return getattr(self._effect, attr)(*args)
                    else:
                        raise InsufficientDataError()

            return intent
        else:
            return getattr(self._effect, attr)


class CheckedEffect(Effect):
    def __init__(self, cls, context):
        self._class = cls
        self._context = context

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError(attr)

        def intent(*args):
            intent, data = self._context.consume_intent()
            method, *expected_args = data
            if intent.restype is NoneType:
                output = None
            else:
                *expected_args, output = expected_args

            # Check arguments
            expected_args = tuple(expected_args)
            if args != expected_args or attr != intent.name:
                clsname = self._class.__name__
                expected_args = ", ".join(map(repr, expected_args))
                args = ", ".join(map(repr, args))
                msg = "\n".join(
                    [
                        f"Invalid intent execution",
                        f"  - expect: {clsname}.{intent.name}({expected_args})",
                        f"  - got:    {clsname}.{attr}({args})",
                    ]
                )
                raise self._context.error(msg)

            # Check return type
            if not isinstance(output, intent.restype):
                expect = self.restype.__name__
                got = type(output).__name__
                msg = f"Invalid result type: expect {expect}, got {got}"
                raise self._context.error(msg)
            return output

        setattr(self, attr, intent)
        return intent


class Invalid(Effect):
    """
    Represents an invalid effect.

    Raise an error when any intent is called.
    """

    def __init__(self, exception=None):
        self._exception = exception or UnhandledEffect()

    def __getattr__(self, attr):
        raise self._exception


class LogEffect(Effect):
    """
    Log all intents requested from the given effect.

    Log is appended in some list or object with an append function.
    """

    def __init__(self, effect, collector):
        self._effect = effect
        self._log = collector.append

    def __getattr__(self, attr):
        def intent(*args):
            result = getattr(self._effect, attr)(*args)
            self._log(LogEntry(self._effect, attr, args, result))
            return result

        return intent


class LogEntry:
    """
    A entry in the log of intents.
    """

    def __init__(self, effect, intent, args, result):
        self.effect = effect
        self.intent = intent
        self.args = args
        self.result = result

    def __repr__(self):
        return f"LogEntry({self.effect!r}, {self.intent!r}, {self.args!r}, {self.result!r})"


class Intent:
    """
    Represents the signature of an intent.
    """

    def __init__(self, name, argtypes, restype):
        self.name = name
        self.argtypes = tuple(argtypes)
        self.restype = restype
        self.num_args = len(argtypes)

    def __repr__(self):
        types = ", ".join(tt.__name__ for tt in self.argtypes)
        restype = "None" if self.restype is None else self.restype.__name__
        return f"Intent({self.name!r}, [{types}], {restype})"


@lru_cache(maxsize=256)
def get_intent(func):
    sig = inspect.Signature.from_callable(func)
    name = func.__name__
    _, *argtypes = (
        annotated_type(param.annotation) for param in sig.parameters.values()
    )
    restype = annotated_type(sig.return_annotation)
    return Intent(name, argtypes, restype)


def annotated_type(x):
    if x is None:
        return NoneType
    elif x is inspect._empty:
        return object
    elif isinstance(x, type):
        return x
    else:
        raise TypeError(f"invalid annotation: {x!r}")


def override(effect, *, _fallback=False, **kwargs):
    """
    Overrides the return values of all given intents of the effect..

    Usage:
        >>> eff = override(eff_, readline=['foo', 'bar'])
        >>> eff.readline()
        'foo'
        >>> eff.readline()
        'bar'

    Returns:
        A new effect.
    """
    return OverrideEffect(effect, kwargs, fallback=_fallback)


#
# Context
#
class Context(Mapping):
    """
    Represents a context dictionary
    """

    __slots__ = ("_data", "_raises", "_parent")

    def __init__(self, mapping=None, raises=False, parent=None):
        self._data = {} if mapping is None else mapping
        self._raises = raises
        self._parent = parent

    def __getitem__(self, item):
        try:
            return self._data[item]
        except KeyError:
            if self._parent is not None:
                self._data[item] = value = self._parent[item]
                return value
            elif self._raises:
                raise UnhandledEffect()
            else:
                raise

    def __setitem__(self, key, value):
        self._data[key] = value
        if self._parent is not None and key not in self._parent:
            self._parent[key] = value

    def __iter__(self):
        yield from self._data

        visited = set(self._data)
        if self._parent:
            for key in self._parent:
                if key not in visited:
                    yield key

    def __len__(self):
        return sum(1 for _ in self)

    def setdefault(self, cls, value):
        try:
            return self[cls]
        except KeyError:
            self[cls] = value
            return value

    def update(self, map):
        return Context(map, raises=self._raises, parent=self)

    def parents(self):
        parent = self._parent
        if parent is not None:
            yield parent
            yield from parent.parents()

    def get_from_parent(self, cls):
        current = self._data[cls]

        for parent in self.parents():
            eff = parent.get(cls, current)
            if eff is not current:
                return eff
        else:
            return cls()


class CheckedContext(Context):
    """
    A checked context.
    """

    __slots__ = ("_intents", "_idx")

    def __init__(self, intents, *args, **kwargs):
        self._intents = list(intents)
        self._idx = 0
        super().__init__(*args, **kwargs)

    def __getitem__(self, item):
        try:
            return self._data[item]
        except KeyError:
            return CheckedEffect(item, self)

    def update(self, map):
        raises = getattr(self._parent, "_raises", False)
        return Context(map, raises=raises, parent=self)

    def consume_intent(self):
        try:
            data = self._intents[self._idx]
        except IndexError:
            raise UnhandledEffect()
        else:
            intent = get_intent(data[0])
            self._idx += 1
            return intent, data

    def error(self, msg):
        lines = ["Unexpected effect:\n", "    intents = ["]
        current = max(self._idx - 1, 0)
        for idx, line in enumerate(self._intents):
            method, *rest = line
            line = ", ".join([method.__qualname__, *map(repr, rest)])
            line = f"        [{line}],"
            if idx == current:
                line = f"\n        ### invalid test case ###\n{line}\n"
            lines.append(line)

        lines.extend(["    ]\n\n", msg])
        return AssertionError("\n".join(lines))


def get_effect(cls, eff=None):
    """
    Return the effect manager for the given class. If an instance is passed
    the second argument, it is returned instead.

    Args:
        cls:
            Effect class.
        eff:
            If given, must be an Effect instance or None.

    Returns:
        The Effect manager.
    """
    if eff is None:
        ctx = get_context()
        try:
            return ctx[cls]
        except KeyError:
            return ctx.setdefault(cls, cls())
    else:
        return eff


def get_super(cls):
    ctx = get_context()
    ctx._parent[cls] = value = ctx.get_from_parent(cls)
    return value


def get_context():
    """
    Gets the global context for the current thread.
    """
    try:
        return LOCAL_STORE.context
    except AttributeError:
        LOCAL_STORE.context = MAIN_CONTEXT
        return MAIN_CONTEXT


def set_context(ctx):
    """
    Sets the global context for the current thread.
    """
    global MAIN_CONTEXT
    if threading.current_thread() == threading.main_thread():
        MAIN_CONTEXT = ctx
    LOCAL_STORE.context = ctx


# Thread local storage
MAIN_CONTEXT = Context()
LOCAL_STORE = threading.local()
LOCAL_STORE.context = MAIN_CONTEXT


#
# Context managers
#


def change_context(func):
    ctx_old = get_context()
    ctx = func(ctx_old)
    try:
        set_context(ctx)
        yield ctx
    finally:
        set_context(ctx_old)


@contextmanager
def handle(map):
    """
    Context manager that can define overrides to effects.

    Usage:
        >>> with handle({TermIO: Invalid(ValueError)}):
        ...     io.print('This will raise an error.')
    """

    def new_context(ctx):
        return ctx.update(map)

    yield from change_context(new_context)


@contextmanager
def assert_intents(intents, handlers=None):
    def new_context(ctx):
        return CheckedContext(intents, handlers, parent=ctx)

    handlers = handlers or {}
    yield from change_context(new_context)


#
# Errors
#
class InsufficientDataError(Exception):
    """
    Raised when override does not have data to continue.
    """


class UnhandledEffect(Exception):
    """
    Raised for non-handled effects.
    """
