import sys
from io import StringIO
from pprint import PrettyPrinter as BasePrinter
from types import MappingProxyType
from typing import Any, IO, NamedTuple, Mapping


class PrintContext(NamedTuple):
    """
    Store context for pretty printing operation.
    """

    printer: BasePrinter
    stream: IO = sys.stdout
    indent: int = 0
    allowance: int = 80
    context: Mapping = MappingProxyType({})
    level: int = 0

    def change_indent(self, delta):
        """
        Return a copy of context changing indentation by the given ammount.
        """
        return self.change(indent=max(0, self.indent + delta))

    def change_level(self, delta):
        """
        Return a copy of context changing level by the given ammount.
        """
        return self.change(indent=max(0, self.level + delta))

    def change_allowance(self, delta):
        """
        Return a copy of context changing allowance by the given ammount.
        """
        return self.change(indent=max(0, self.allowance + delta))

    def with_attr(self, **kwargs):
        """
        Return a copy of context setting the given attributes.
        """
        printer = kwargs.pop("printer", self.printer)
        stream = kwargs.pop("stream", self.stream)
        indent = kwargs.pop("indent", self.indent)
        allowance = kwargs.pop("allowance", self.allowance)
        context = kwargs.pop("context", self.context)
        level = kwargs.pop("level", self.level)
        return PrintContext(printer, stream, indent, allowance, context, level)

    def change(self, indent=0, level=0, allowance=0, **kwargs):
        """
        Like with_attr(), but increment/decrement integer values indent, level,
        and allowance.
        """
        kwargs["indent"] = max(0, self.indent + indent)
        kwargs["level"] = max(0, self.level + level)
        kwargs["allowance"] = max(0, self.allowance + allowance)
        return self.with_attr(**kwargs)

    def format(self, obj: Any, **kwargs) -> str:
        """
        Format object within the given context.
        """
        ctx = self.with_attr(**kwargs) if kwargs else self
        fd = StringIO()
        # noinspection PyProtectedMember
        self.printer._format(obj, fd, ctx.indent, ctx.allowance, ctx.context, ctx.level)
        return fd.getvalue()


class PrettyPrinter(BasePrinter):
    """
    Sidekick-enabled pretty printer.
    """

    _dispatch = BasePrinter._dispatch

    def __init__(self, *args, options=None, **kwargs):
        self.options = options or {}
        super().__init__(*args, **kwargs)

    @classmethod
    def register(cls, kind, func):
        def wrapped_func(printer, obj, stream, indent, allowance, context, level):
            ctx = PrintContext(printer, stream, indent, allowance, context, level)
            write = stream.write
            for part in func(obj, ctx, **printer.options):
                write(part)

        cls._dispatch[kind.__repr__] = wrapped_func
        return func


def pprint(
    obj, stream=None, indent=1, width=80, depth=None, *, compact=False, **options
):
    """Pretty-print a Python object to a stream [default is sys.stdout]."""
    kwargs = locals()
    obj = kwargs.pop("obj")
    printer = PrettyPrinter(**kwargs)
    printer.pprint(obj)


def pformat(obj, indent=1, width=80, depth=None, *, compact=False, **options) -> str:
    """Format a Python object into a pretty-printed representation."""
    kwargs = locals()
    obj = kwargs.pop("obj")
    printer = PrettyPrinter(**kwargs)
    return printer.pformat(obj)


def pregister(cls, func=None):
    """
    Decorator that register a pretty-print function for the given class.

    The decorated function must return a generator that yields the string bits
    necessary to assemble the final representation.
    """
    if func is None:

        def decorator(fn):
            f"""Register pretty-formatter function for{cls.__name__}"""
            return pregister(cls, fn)

        return decorator
    PrettyPrinter.register(cls, func)
    return func
