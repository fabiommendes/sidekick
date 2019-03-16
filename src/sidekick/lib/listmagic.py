from itertools import islice, chain

from .sequences import filter, nth


class SType:
    """
    Class for the L magic object.
    """

    def __ror__(self, other):  # noqa: N805
        return iter(other)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return lambda seq: islice(seq, *item)
        else:
            return lambda seq: nth(item, seq)

    def append(self, x):
        return lambda seq: chain(seq, [x])

    def clear(self):
        raise TypeError("clear() function is not implemented in list magic types")

    def copy(self):
        raise TypeError("copy() function is not implemented in list magic types")

    def count(self, value):
        def count(seq):
            n = 0
            for x in seq:
                if x == value:
                    n += 1
            return n

        return count

    def extend(self, other):
        return lambda seq: chain(seq, other)

    def index(self, obj, start=None, end=None):
        def index(seq):
            seq = islice(seq, start, end)
            for i, x in enumerate(seq):
                if x == obj:
                    return i
            else:
                raise ValueError

        return index

    def insert(self, index, obj):
        if index == 0:
            return lambda seq: chain([obj], seq)
        else:
            return lambda seq: chain(islice(seq, 0, index), [obj], islice(seq, index))

    def pop(self, index=None):
        raise TypeError("pop() function is not implemented in list magic types")

    def remove(self, value):
        def removing(seq):
            for x in seq:
                if x != value:
                    yield
                else:
                    break
            else:
                raise ValueError("item not found in sequence")
            yield from seq

        return removing

    def discard(self, value):
        def discarding(seq):
            for x in seq:
                if x != value:
                    yield
                else:
                    break
            yield from seq

        return discarding

    def discard_all(self, value):
        return filter(lambda x: x != value)

    def reverse(self):
        return lambda seq: iter(reversed(seq))


class LType(SType):
    """
    Class for the L magic object.
    """

    def __ror__(self, other):  # noqa: N805
        return list(other)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return lambda seq: list(islice(seq, *item))
        else:
            return lambda seq: seq[item]

    def append(self, x):
        return lambda seq: [*seq, x]

    def extend(self, other):
        return lambda seq: [*seq, *other]

    def insert(self, index, obj):
        if index == 0:
            return lambda seq: [obj, *seq]
        else:
            return lambda seq: [*islice(seq, 0, index), obj, *islice(seq, index)]

    def remove(self, value):
        def removing(seq):
            res = list(seq)
            res.remove(value)
            return res

        return removing

    def discard(self, value):
        def removing(seq):
            res = list(seq)
            try:
                res.remove(value)
            except ValueError:
                pass
            return res

        return removing

    def discard_all(self, value):
        return lambda seq: [x for x in seq if x != value]

    def reverse(self):
        return lambda seq: reversed(seq)


L = LType()
S = SType()
