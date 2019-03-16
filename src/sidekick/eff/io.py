import builtins
from collections import deque

from .core import Effect, get_effect, handle, InsufficientDataError


#
# Effect classes
#
class TermIO(Effect):
    """
    Codifies basic terminal IO operations.

    This effect have two intents: readline() -> str and write(str) -> None.
    """

    def readline(self) -> str:
        return builtins.input()

    def write(self, data: str) -> None:
        builtins.print(data, end="")


class InputTermIO:
    """
    A TermIO effect that pre-defines a list of inputs.
    """

    def __init__(self, inputs, fallback=False, echo=False, effect=None):
        self._inputs = deque(inputs)
        self._fallback = fallback
        self._echo = echo
        self._effect = get_effect(TermIO, effect)

    def readline(self) -> str:
        try:
            result = self._inputs.popleft()
            if self._echo:
                self._effect.write(result + "\n")
            return result
        except IndexError:
            if self._fallback:
                return self._effect.readline()
            else:
                raise InsufficientDataError()

    def write(self, data: str):
        self._effect.write(data)


#
# Effectful replacements for Python builtins
#
def input(msg=None, term_io=None):
    """
    Drop in replacement for Python's input function.
    """

    term_io = get_effect(TermIO, term_io)
    if msg:
        print(msg, end="")
    return term_io.readline()


def print(*args, sep=" ", end="\n", file=None, term_io=None):
    """
    Drop in replacement for Python's print function.
    """

    data = sep.join(map(str, args)) + end
    if file is None:
        term_io = get_effect(TermIO, term_io)
        return term_io.write(data)
    else:
        file.write(data)
        return term_io.empty


#
# Context managers
#
def with_inputs(inputs, echo=False, fallback=False, handlers=None):
    """
    Context manager that defines a list of inputs returned from the readline()
    intent.
    """
    handlers = handlers or {}
    term_io = handlers.pop(TermIO, None)
    term_io = InputTermIO(inputs, fallback=fallback, echo=echo, effect=term_io)
    return handle({TermIO: term_io, **handlers})
