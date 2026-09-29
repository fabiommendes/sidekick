from typing import Callable as Fn, TypeVar


a = TypeVar("a")
b = TypeVar("b")
BinOp = Fn[[a, a], a]
