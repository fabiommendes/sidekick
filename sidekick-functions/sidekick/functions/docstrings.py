import re
from dataclasses import dataclass, field
from typing import NamedTuple, Optional, Dict, List


@dataclass
class Arg:
    name: str
    type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Docstring:
    description: Optional[str] = None
    args: Dict[str, Arg] = field(default_factory=dict)
    restype: Optional[Arg] = None


class LineTk(NamedTuple):
    indent: int
    data: List[str]


def parse_google_docstring(
    doc: str,
    _args_re=re.compile(r"[Aa]rgs:"),
    _return_re=re.compile(r"[Rr]eturns?:"),
) -> Docstring:
    """
    Parse a docstring in google format.
    """

    data = _parse_lines(map(str.rstrip, doc.splitlines()))
    return _clean_sexpr([x for _, x in _to_sexpr(data)])


# =============================================================================
# Auxiliary functions
# =============================================================================
def _parse_lines(lines: List[str], _space_re=re.compile(r"( *)(.*)")) -> List[LineTk]:
    """
    Transform a list of strings in a list of pairs (indentation, [content]),
    in which the indentation is stripped from the rhs.

    Lines that keep the same indentation are grouped in the output.
    """
    data: List[LineTk] = []

    k = -1
    for ln in lines:
        if not ln:
            continue

        m = _space_re.match(ln)
        n = len(m.group(1))
        ln = m.group(2)
        if n == k:
            data[-1][1].append(ln)
        else:
            data.append(LineTk(n, [ln]))
        k = n
    return data


def _clean_sexpr(sexpr):
    if not isinstance(sexpr, list):
        return sexpr
    elif len(sexpr) == 1:
        return _clean_sexpr(sexpr[0])
    else:
        return list(map(_clean_sexpr, sexpr))


def _to_sexpr(seq):
    m, y = seq.pop()
    try:
        n, x = seq[-1]
    except IndexError:
        yield (m, y)
    else:
        if n == m:
            x.extend(y)
            yield from _to_sexpr(seq)
        elif m > n:
            x.append([x.pop(), *y])
            yield from _to_sexpr(seq)
        elif m < n:
            rest = []
            while seq:
                n, _ = item = seq.pop()
                rest.append(item)
                if n <= m:
                    break
            rest.reverse()

            yield from _to_sexpr([*seq, *_to_sexpr(rest), (m, y)])


def _walk_sexpr(seq, kind=list):
    if type(seq) == kind:
        for elem in seq:
            yield from _walk_sexpr(elem, kind)
    else:
        yield seq
