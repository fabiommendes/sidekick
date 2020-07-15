#
# TODO: highly experimental
#
import itertools

from ..functions import once


def sequence_zip_functor(seq, func, *args):
    args = map(iter_or_always, args)
    return seq(map(func, *args))


def sequence_prod_functor(seq, func, *args):
    args = map(iter_or_singleton, args)
    return seq(map(lambda x: func(*x), itertools.product(args)))


def iter_or_singleton(x):
    try:
        x = iter(x)
    except TypeError:
        yield x
    else:
        yield from x


def iter_or_always(x):
    try:
        return iter(x)
    except TypeError:
        return itertools.repeat(x)


class Thunk:
    __slots__ = "_thunk"

    @classmethod
    def from_value(cls, x):
        return cls(lambda: x)

    @classmethod
    def from_action(*args, **kwargs):
        cls, func, *args = args
        return cls(once(lambda: func(*args, **kwargs)))

    @classmethod
    def apply(*args, **kwargs):
        cls, func, *args = args
        args = (x if not isinstance(x, Thunk) else x._thunk() for x in args)
        return Thunk(once(lambda: func(*args, **kwargs)))

    @classmethod
    def apply_flat(*args, **kwargs):
        cls, func, *args = args
        args = (x if not isinstance(x, Thunk) else x._thunk() for x in args)
        return Thunk(once(lambda: func(*args, **kwargs).run()))

    def __init__(self, thunk):
        self._thunk = thunk

    def map(self, func):
        return Thunk(once(lambda: func(self._thunk())))

    def run(self):
        return self._thunk()


class IO(Thunk):
    __slots__ = "_effects"

    def print(self, *args, **kwargs):
        return self.map(lambda x: print(*args, **kwargs) or x)

    def printf(self, fmt, **kwargs):
        return self.map(lambda x: print(fmt.format(x), **kwargs) or x)

    def input(self, msg="-> ", type=lambda x: x):
        return self.map(lambda _: type(input(msg)))

    def read_file(self, path):
        ...

    def read_lines(self, path):
        ...

    def open(self, *args, **kwargs):
        def read_file(_):
            with open(*args, **kwargs) as fd:
                return fd

        return self.map(read_file)

    def redirect_stdout(self, stdout):
        ...

    def fix_inputs(self, lst):
        ...

    def fix_files(self):
        ...


# (IO()
#  .input('What is your name? ')
#  .printf('My name is {}.')
#  .printf('{} is a pretty good name!')
#  .map(str.upper)
#  .printf('{}!!!')
#  )
#
#
# (IO()
#  .input('What is your age? ', to='name', type=int)
#  .printf('My name is {name}.')
#  .printf('{name} is a pretty good name!')
#  .map(name=str.upper)
#  .printf('{name}!!!')
#  )
#
# @IO().do
# def reader(io):
#     name = yield io.input('What is your name? ')
#     age = yield io.input('What is your age? ', int)
#     return io.print('Congratulations {}, for your {} years old!'.format(name, age))
#
# io()
# io(inputs=['John', '42'], stdout=None)
# 'dsfsdf'
