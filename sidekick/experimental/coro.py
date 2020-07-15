# """
# Experimental module: COROUTINES
#
# source = range(100)
# coro = records(target=print,
#                count=count(),
#                mean=mean(),
#                std=std(),
#                sum=reduce((X + Y), 0))
#
# >>> coro.send(10)
# record(count=1, mean=10, std=0, sum=10)
#
# >>> coro.send(2)
# record(count=2, mean=6, std=4.0, sum=12)
#
# >>> coro.send(3)
# record(count=3, mean=5, std=3.559026084010437, sum=15)
#
# >>> coro.send(5)
# record(count=4, mean=5, std=3.082207001484488, sum=20)
# """
from collections import deque
from math import sqrt
from threading import Thread
from time import sleep

from ..functions import to_callable
from ..types import record


def feed(coro, seq):
    for x in seq:
        coro.send(x)


def dispatch(*args):
    while True:
        x = yield
        for coro in args:
            coro.send(x)


def sync(n, target):
    def make_sync_coro(i, qs):
        def coro():
            while True:
                x = yield
                qs[i].append(x)
                if all(queues):
                    target.send(tuple(q.popleft() for q in qs))

        return coro

    queues = [deque() for _ in range(n)]
    return [make_sync_coro(i, queues) for i in range(n)]


def sync_named(names, target):
    mk_record = lambda values: record(**dict(zip(names, values)))
    return sync(len(names), map(mk_record, target))


def map_record(mapping, target):
    mapping = dict(mapping)
    coros = sync_named()


def count(target, start=0):
    send = target.send
    while True:
        _ = yield
        start += 1
        send(start)


def mean(target):
    acc = 0
    size = 0
    send = target.send
    while True:
        acc += yield
        size += 1
        send(acc / size)


def moment(n, target, central=False):
    acc = 0
    size = 0
    send = target.send
    if central:
        mean_acc = 0
        while True:
            x = yield
            size += 1
            mean_acc += x
            acc += (x - mean_acc / size) ** n
            send(acc / size)
    else:
        while True:
            x = yield
            size += 1
            acc += x ** n
            send(acc / size)


def std(target, central=False):
    return map(sqrt, moment(2, target, central=central))


def map(func, target, *extra):
    func = to_callable(func)
    send = target.send
    if extra:
        for args in zip(*extra):
            x = yield
            send(func(x, *args))


def filter(pred, target):
    pred = to_callable(pred)
    send = target.send
    while True:
        x = yield
        if pred(x):
            send(x)


def reduce(func, start, target):
    func = to_callable(func)
    send = target.send
    send(start)
    while True:
        x = yield
        start = func(start, x)
        send(start)


def chunk(n, target):
    send = target.send
    while True:
        chunk = []
        for _ in range(n):
            x = yield
            chunk.append(x)
        send(chunk)


def choice(pred, ok, bad):
    while True:
        value = yield
        if pred(value):
            ok.send(value)
        else:
            bad.send(value)


def loop(func):
    def routine():
        while True:
            x = yield
            target.send(func(x))

    target = routine()
    return target


class Iter:
    def __init__(self, iterator):
        self.iter = iter(iterator)
        self.alive = True

    def pop(self):
        return next(self.iter)

    def push(self, x):
        self.iter.send(x)


class Buffer:
    def __init__(self):
        self.buffer = []
        self.alive = True

    def pop(self):
        while not self.buffer and self.alive:
            sleep(1e-6)
        if not self.alive:
            raise StopIteration
        return self.buffer.pop(0)

    def push(self, x):
        return self.buffer.append(x)


class Wrapper:
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
        self.stopped = False

    def start(self, func, args):
        self.thread = Thread(target=func, args=(*args, self))
        self.thread.start()

    def get(self):
        return self.src.pop()

    def pop(self):
        return self.dest.pop()

    def send(self, x):
        self.dest.push(x)

    def push(self, x):
        self.src.push(x)

    def stop(self):
        self.src.alive = False
        self.dest.alive = False


def start_wrapper(func, args, order=1):
    *args, obj = args
    wrapper_args = [Iter(args), Buffer()]
    wrapper = Wrapper(*wrapper_args[::order])
    wrapper.start(func, args)
    return wrapper


def iterator_transform(func):
    def wrapped(*args):
        wrapper = start_wrapper(func, args)
        while True:
            yield wrapper.pop()

    return wrapped


def coroutine_transform(func):
    def wrapped(*args):
        wrapper = start_wrapper(func, args)
        while True:
            wrapper.push((yield))

    return wrapped


def reduce_acc(func, x, obj):
    obj.send(x)
    while True:
        x = func(x, obj.recv())
        yield obj.send(x)


def drop(n, obj):
    for _ in range(n):
        obj.get()
    while True:
        obj.send(obj.recv())


def take(n, obj):
    for _ in range(n):
        obj.send(obj.recv())


def map(func, obj):
    while True:
        obj.send(func(obj.recv()))


def map(func, obj):
    while True:
        yield obj.send(func((yield obj.recv())))


async def map(func, obj):
    while True:
        await obj.send(func(await obj.recv()))


from collections import namedtuple

out = namedtuple("out", ["value"])


async def cmap(func, send, recv):
    while True:
        await send(func(await recv()))


async def cfilter(pred, send, recv):
    while True:
        x = await recv()
        if pred(x):
            await send(x)


async def cdrop(n, send, recv):
    for _ in range(n):
        await recv()
    while True:
        await send(await recv())


def iterator(func, *args):
    *args, it = args

    async def send(x):
        return out(x)

    async def recv():
        return next(it)

    coro = func(*args, send, recv)
    while True:
        try:
            obj = coro.send(None)
            if isinstance(obj, out):
                yield out.value

        except StopIteration:
            break
