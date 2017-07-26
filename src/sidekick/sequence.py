class LMeta(type):
    """
    Metaclass for the L type.
    """

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return L(*item)
        return L([item])

    def map(self, func, *iterables, **kwargs):
        """
        Map function over a list of iterables.
        """
        return L(func(*args, **kwargs) for args in zip(*iterables))


class L(list, metaclass=LMeta):
    """
    A list with extended methods.
    """

    def foreach(self, func, *args, **kwargs):
        """
        Apply function on list.
        """
        return L(func(x, *args, **kwargs) for x in self)


print(L[1, 2 ,3].foreach(lambda x, y: x + y, 1))

