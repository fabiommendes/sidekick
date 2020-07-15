from .monoid import monoid


class group(monoid):
    def inv(self, x):
        return self._inv(x)


def dual(group):
    """
    Dual of a group or monoid or semigroup is the algebraic structure defined
    by flipping the binary operation.

    Commutative operations are self-dual, i.e., the dual is equal to the group
    itself.
    """
    raise NotImplementedError
