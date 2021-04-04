from .. import api as sk


class EqList(list):
    """
    A list that tests for equality with iterator.
    """

    def __eq__(self, other):
        if self and self[-1] == ...:
            other = sk.take(len(self) - 1, other)
            self = self[:-1]
        other = list(other)
        assert list.__eq__(self, other), f"Different outputs: {other} != {self}"
        return True


LL = lambda *args: EqList(args)
VALUE = type("VALUE", (), {"__repr__": lambda self: "VALUE"})()
