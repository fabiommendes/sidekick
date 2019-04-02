from itertools import count
from numbers import Real

from sidekick import fn, Seq


class N:
    """
    Magic factory of numeric ranges
    """

    def __iter__(self):
        return count()

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return self._count_interval(item)

        if isinstance(item, slice):
            return self._count_slice(item)
        raise TypeError

    def _count_slice(self, s):
        start = s.start or 0
        stop = s.stop
        step = s.step or 1
        if stop is None:
            return count(start, step)
        else:
            return self.range_step(start, stop, step)

    def _count_interval(self, args):
        if args[-1] is ...:
            *args, _ = args
            n_args = len(args)
            if n_args == 1:
                yield from count(args[0])
            else:
                *start, a, b = args
                yield from start
                yield from count(a, b - a)

        elif args[-2] is ...:
            *args, _, stop = args
            n_args = len(args)
            if n_args == 1:
                yield from self.range(args[0], stop + 0.5)
            else:
                *start, first, second = args
                delta = second - first
                yield from start
                yield from self.range_step(first, stop + delta / 2, delta)

        else:
            raise TypeError

    def count_from(self, n: Real) -> Seq:
        """
        Counts from n at steps of 1 (N[n, ...]).

        N.count_from(start) ==> start, start + 1, ...

        See Also:
            N.range - controls stop
            N.range_step - controls end value and step
        """
        return count(n)

    @fn.curry(2)
    def range(self, start: Real, stop: Real) -> Seq:
        """
        Counts in steps of 1 within range (N[start, ..., stop]).

        N.range(start, stop) ==> start, start + 1, ... (until stop)

        See Also:
            N.count_from - omit stop
            N.range_step - controls end value and step

        """
        return self.range_step(start, stop, 1)

    @fn.curry(3)
    def range_step(self, start: Real, stop: Real, step: Real) -> Seq:
        """
        Count from start to stop by given steps (N[start, start + step, ..., stop]).

        N.range_step(start, stop, delta) ==> start, start + delta, ... (until stop)

        See Also:
            N.count_from - omit step and stop
            N.range - omit step
        """
        x = start
        while x < stop:
            yield x
            x += step

    @fn.curry(3)
    def evenly_spaced(self, a: Real, b: Real, n: int) -> Seq:
        """
        Return a sequence of n evenly spaced numbers from a to b.
        """
        a = float(a)
        delta = b - a
        dt = delta / (n - 1)
        for _ in range(n):
            yield a
            a += dt
