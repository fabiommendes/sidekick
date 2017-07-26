class Node:
    pass

class Var:
    pass

class Expr:
    pass


def compile(ast):
    """
    Compiles ast to a Python callable object.
    """

    pass


def compile_python(ast):
    """
    Compiles ast to a Python source code.
    """

    pass


def compile_js(ast):
    """
    Compiles an ast to a Javascript source code.
    """


def compile_elm(ast):
    """
    Compiles an ast to an Elm source code.
    """



_ = Var(0)
__ = Var(1)
___ = Var(2)


print(_.attr)
print(_.method(42))
print(_ + 42)
print(F(abs, _))


print(compile(_.imag)(42))
print(compile(_.conjugate())(42))
print(compile(_ + 40)(2))
