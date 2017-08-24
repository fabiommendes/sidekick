class LMeta(type):
    """
    Class for the L magic object.
    """

    def __ror__(cls, other):  # noqa: N805
        return list(other)


class L(metaclass=LMeta):
    """
    A wrapper for list-related functions.
    """
