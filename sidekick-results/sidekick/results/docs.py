import copy
import io
from collections import deque
from textwrap import dedent, indent
from types import FunctionType

from .util import Fn

SECTION_ORDER = [
    "summary",
    "signature",
    "signatures",
    "args",
    "return",
    "returns",
    "exceptions",
    "example",
    "examples",
    "see also",
]


def with_docs(**kwargs: str) -> Fn[[type], type]:
    """
    Supplement method documentation with the given docstrings.

    Example:

    >>> @with_docs(
    ...     bar="New documentation for `bar`",
    ... )
    ... class Foo:
    ...     def bar(self):
    ...         ...
    """

    def decorator(cls):
        _with_docs(cls, kwargs)
        return cls

    return decorator


def with_examples(src: str) -> Fn[[type], type]:
    '''
    Supplement method documentation examples extracted from the
    given docstring.

    Example:

    >>> @with_examples("""
    ...     answer:
    ...         >>> Foo().answer()
    ...         42
    ... """)
    ... class Foo:
    ...     def answer(self):
    ...         return 42
    '''

    data = parse_docstring(src)
    data.pop("summary")
    kwargs = {k: "{doc}\n\nExamples:\n" + indent(v, "    ") for k, v in data.items()}
    return with_docs(**kwargs)


def _with_docs(cls, docs: dict[str, str]) -> None:
    for name, doc in docs.items():
        try:
            obj = getattr(cls, name)
        except AttributeError:
            raise ValueError(f"No method named {name} was found")

        inplace = name in cls.__dict__
        factory = document_inplace if inplace else document_copy
        new = factory(obj, name, doc)
        setattr(cls, name, new)


def document_inplace(obj, name: str, doc: str):
    if isinstance(obj, FunctionType):
        obj.__doc__ = doc.format(doc=obj.__doc__ or "")
    else:
        raise TypeError(f"not supported: {type(obj).__name__}")


def document_copy(obj, name: str, doc: str):
    new = copy.copy(obj)
    return document_inplace(new, name, doc)


def parse_docstring(doc: str) -> dict[str, str]:
    '''
    Parse docstring as a mapping from sections to paragraphs.

    Examples:
        >>> def func(x, y):
        ...     """Some docstring
        ...
        ...     A long summary of what the function does.
        ...
        ...     Args:
        ...         x: first argument
        ...         y: second argument
        ...     """
        >>> sections = parse_docstring(func.__doc__)

        Now we have a dictionary with docstring sections and the corresponding
        contents. The first section is named "summary", while the remaining ones
        are explicitly named using Google's docstring convention.

        >>> print(sections["summary"])
        Some docstring
        <BLANKLINE>
        A long summary of what the function does.

        We can extract "Args" or any other arbitrary section we want. Indentation is
        explicitly removed.

        >>> print(sections["Args"])
        x: first argument
        y: second argument
    '''
    first_line, sep, rest = doc.partition("\n")
    if not sep:
        return {"summary": doc}
    doc = first_line + "\n" + dedent(rest)

    lines = deque(doc.splitlines())
    lines.append("__flush__")  # forces flushing last section

    parsed = {}
    section = "summary"
    paragraph = []

    while lines:
        line = lines.popleft()

        if not line or line[0].isspace():
            paragraph.append(line)
        elif section == "summary" and not line.endswith(":"):
            paragraph.append(line)
        else:
            parsed[section] = dedent("\n".join(paragraph).rstrip())
            paragraph.clear()
            section = line.removesuffix(":")

    return parsed


def render_docstring(parsed: dict[str, str], order: list[str] = SECTION_ORDER) -> str:
    """
    Renders docstring from a parsing dictionary.
    """

    def key(x: tuple[str, str], order_set=set(order)):
        key = x[0].lower()
        return n if key not in order_set else order.index(key)

    n = len(order)
    pairs = list(parsed.items())
    pairs.sort(key=key)
    data = io.StringIO()

    for title, paragraph in pairs:
        if title == "summary":
            data.write(paragraph)
        else:
            data.write(title + ":\n")
            data.write(indent(paragraph, "    "))
            data.write("\n\n")

    return data.getvalue()
