import time

SKIP = object()
NOT_GIVEN = object()
identity = lambda x: x


class Stream:
    def __init__(self, value=SKIP):
        self._targets = []
        self._value = value

    def __call__(self):
        value = self._value
        if value is SKIP:
            raise ValueError("stream was not initialized")
        return value

    def __iter__(self):
        return self

    def __next__(self):
        value = self._value
        if value is SKIP:
            raise StopIteration
        return value

    def with_default(self, default):
        return default if self._value is SKIP else self._value

    def send(self, value):
        if value is not SKIP:
            self._value = value
            for fn, s in self._targets:
                s.send(fn(value))

    def end(self):
        self._targets.clear()

    def map(self, func):
        start = SKIP if self._value is SKIP else func(self._value)
        return self.register(Stream(start), func)

    def register(self, child=None, func=identity):
        if child is None:
            child = Stream(self._value)
        self._targets.append((func, child))
        return child

    def register_coroutine(self, constructor, func=identity):
        stream = Stream(self._value)
        coro = constructor(stream)
        self.register(coro, func)
        return coro, stream


def combine(func, *streams, default=SKIP):
    args = []
    stream = Stream()
    for i, s in enumerate(streams):
        if isinstance(s, Stream):
            args.append(s.with_default(default))
            s.register(stream, _combiner(i, args, func))
        else:
            args.append(s)
    return stream


def _combiner(i, args, func):
    execute = all(x is not SKIP for x in args)

    def fn(x):
        nonlocal execute
        args[i] = x
        if execute:
            return func(*args)
        execute = all(x is not SKIP for x in args)
        return func(*args) if execute else SKIP

    return fn


def merge(*streams):
    value = SKIP
    stream = Stream()
    for s in streams:
        if value is not SKIP:
            value = s.with_default(SKIP)
        s.register(stream)
    stream.send(value)
    return stream


def reduce(op, stream, start=SKIP):
    def fn(value):
        try:
            x = acc()
        except ValueError:
            return value
        else:
            return op(x, value)

    acc = Stream(stream.with_default(start))
    return stream.register(acc, fn)


def throttle(dt, stream):
    def fn(value):
        nonlocal t
        if gettime() < t:
            return SKIP
        else:
            t = gettime() + dt
            return value

    t = 0
    gettime = time.time
    return stream.register(None, fn)


def filter(pred, stream):
    def fn(value):
        return value if pred(value) else SKIP

    return stream.register(None, fn)


def map(func, stream):
    return stream(map, func)


def ifte(cond, then, else_):
    res = Stream()


# y = fibonacci = Stream(1)
# x = delay(1, fibonacci)
# ratios = map((Y / X), x, y)
# fibonacci.send(1)
# fibonacci.send(x() + y())
