from itertools import count


class SeqType:
    """
    Magic factory of numeric ranges
    """

    def __iter__(self):
        return count()

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if item[-1] is ...:
                *args, _ = item
                n_args = len(args)
                if n_args == 1:
                    yield from count(args[0])
                else:
                    *start, a, b = args
                    yield from start
                    yield from count(a, b - a)

        raise TypeError


seq = SeqType()
