from itertools import starmap
from operator import add, mul
from pickle import dumps, loads
from random import Random

from toolz.utils import raises

from sidekick import *
from sidekick import _

# is comparison will fail between this and no_default
no_default2 = loads(dumps('__no__default__'))


def identity(x):
    return x


def iseven(x):
    return x % 2 == 0


def isodd(x):
    return x % 2 == 1


def inc(x):
    return x + 1


def double(x):
    return 2 * x


class TestOwnedFunctions:
    def test_repeatedly(self):
        assert repeatedly(tuple, 2) | L == [(), ()]

    def test_butlast(self):
        assert butlast(range(5)) | L == [0, 1, 2, 3]
        assert butlast(range(0)) | L == []

    def test_consume(self):
        lst = []
        consume(lst.append(1) for _ in range(3))
        assert lst == [1, 1, 1]

    def test_has(self):
        assert has(_ == 2, range(5)) is True
        assert has(_ == 20, range(5)) is False

    def test_append(self):
        assert append(4, range(4)) | L == [0, 1, 2, 3, 4]

    def test_order_by(self):
        assert order_by(_ * _)([-4, -2, 1, 3]) == [1, -2, 3, -4]

    def test_distinct(self):
        assert distinct([1, 2, 1, 2, 3]) | L == [1, 2, 3]
        assert distinct([1, 2, 1, 2, 3], key=_ % 2) | L == [1, 2]

    def test_keep(self):
        assert keep([0, 1, 2]) | L == [1, 2]
        assert keep(_ - 1, [0, 1, 2]) | L == [-1, 1]
        assert keep(_ - 1, None)([0, 1, 2]) | L == [-1, 1]

    def test_without(self):
        assert without(range(4), 1, 2) | L == [0, 3]

    def test_split(self):
        a, b = split(_ < 2, range(5))
        assert a | L == [0, 1]
        assert b | L == [2, 3, 4]

    def test_split_at(self):
        a, b = split_at(2, range(1, 6))
        assert a | L == [1, 2]
        assert b | L == [3, 4, 5]

    def test_split_by(self):
        a, b = split_by(_ <= 3, range(1, 6))
        assert a | L == [1, 2, 3]
        assert b | L == [4, 5]

    def test_with_prev(self):
        assert with_prev(range(3)) | L == [(None, 0), (0, 1), (1, 2)]

    def test_with_next(self):
        assert with_next(range(3)) | L == [(0, 1), (1, 2), (2, None)]

    def test_pairwise(self):
        assert pairwise(range(3)) | L == [(0, 1), (1, 2)]

    def test_reductions_and_sums(self):
        assert reductions(op.add, range(4)) | L == [0, 1, 3, 6]
        assert reductions(op.add, range(0)) | L == []
        assert reductions(op.add, range(0), 1) | L == []
        assert reductions(op.add, range(2), acc=1) | L == [1, 2]
        assert sums(range(4)) | L == [0, 1, 3, 6]
        assert sums(range(4), 1) | L == [1, 2, 4, 7]

    def test_isequal(self):
        assert isequal(range(2), [0, 1]) is True
        assert isequal(range(2), [0, 1, 2]) is False
        assert isequal(range(4), [0, 1, 2]) is False

    def test_zipwith(self):
        f = zipwith(range(3), range(1, 4))
        assert f(repeat(0)) | L == [(0, 0, 1), (0, 1, 2), (0, 2, 3)]

        f = rzipwith(range(3), range(1, 4))
        assert f(repeat(0)) | L == [(0, 1, 0), (1, 2, 0), (2, 3, 0)]

    def test_flatten(self):
        lst = [1, 2, [3, 4, [5, 6]]]
        assert flatten(lst) | L == [1, 2, 3, 4, 5, 6]

    def test_tree_leaves(self):
        lst = [1, [2, [3]]]
        assert tree_leaves(lst) | L == [1, 2, 3]

    def test_tree_nodes(self):
        lst = [1, [2, [3]]]
        result = [[1, [2, [3]]], 1, [2, [3]], 2, [3], 3]
        assert tree_nodes(lst) | L == result


#
# This test suite was taken from toolz (
# https://github.com/pytoolz/toolz/blob/master/toolz/tests/test_itertoolz.py)
# and adapted
#
class TestToolzSuite:
    def test_remove(self):
        r = remove(iseven, range(5))
        assert type(r) is not list
        assert list(r) == list(filter(isodd, range(5)))

    def test_groupby(self):
        assert groupby(iseven, [1, 2, 3, 4]) == {True: [2, 4], False: [1, 3]}

    def test_groupby_non_callable(self):
        assert groupby(0, [(1, 2), (1, 3), (2, 2), (2, 4)]) == \
               {
                   1: [(1, 2), (1, 3)],
                   2: [(2, 2), (2, 4)]
               }

        assert groupby([0], [(1, 2), (1, 3), (2, 2), (2, 4)]) == \
               {
                   (1,): [(1, 2), (1, 3)],
                   (2,): [(2, 2), (2, 4)]
               }

        assert groupby([0, 0], [(1, 2), (1, 3), (2, 2), (2, 4)]) == \
               {
                   (1, 1): [(1, 2), (1, 3)],
                   (2, 2): [(2, 2), (2, 4)]
               }

    def test_merge_sorted(self):
        assert list(merge_sorted([1, 2, 3], [1, 2, 3])) == [1, 1, 2, 2, 3, 3]
        assert list(merge_sorted([1, 3, 5], [2, 4, 6])) == [1, 2, 3, 4, 5, 6]
        assert list(merge_sorted([1], [2, 4], [3], [])) == [1, 2, 3, 4]
        assert list(merge_sorted([5, 3, 1], [6, 4, 3], [],
                                 key=lambda x: -x)) == [6, 5, 4, 3, 3, 1]
        assert list(merge_sorted([2, 1, 3], [1, 2, 3],
                                 key=lambda x: x // 3)) == [2, 1, 1, 2, 3, 3]
        assert list(merge_sorted([2, 3], [1, 3],
                                 key=lambda x: x // 3)) == [2, 1, 3, 3]
        assert ''.join(merge_sorted('abc', 'abc', 'abc')) == 'aaabbbccc'
        assert ''.join(
            merge_sorted('abc', 'abc', 'abc', key=ord)) == 'aaabbbccc'
        assert ''.join(merge_sorted('cba', 'cba', 'cba',
                                    key=lambda x: -ord(x))) == 'cccbbbaaa'
        assert list(merge_sorted([1], [2, 3, 4], key=identity)) == [1, 2, 3, 4]

        data = [[(1, 2), (0, 4), (3, 6)], [(5, 3), (6, 5), (8, 8)],
                [(9, 1), (9, 8), (9, 9)]]
        assert list(merge_sorted(*data, key=lambda x: x[1])) == \
               [(9, 1), (1, 2), (5, 3), (0, 4), (6, 5), (3, 6), (8, 8), (9, 8),
                (9, 9)]
        assert list(merge_sorted()) == []
        assert list(merge_sorted([1, 2, 3])) == [1, 2, 3]
        assert list(merge_sorted([1, 4, 5], [2, 3])) == [1, 2, 3, 4, 5]
        assert list(merge_sorted([1, 4, 5], [2, 3], key=identity)) == \
               [1, 2, 3, 4, 5]
        assert list(
            merge_sorted([1, 5], [2], [4, 7], [3, 6], key=identity)) == \
               [1, 2, 3, 4, 5, 6, 7]

    def test_interleave(self):
        assert ''.join(interleave(('ABC', '123'))) == 'A1B2C3'
        assert ''.join(interleave(('ABC', '1'))) == 'A1BC'

    def test_unique(self):
        assert tuple(unique((1, 2, 3))) == (1, 2, 3)
        assert tuple(unique((1, 2, 1, 3))) == (1, 2, 3)
        assert tuple(unique((1, 2, 3), key=iseven)) == (1, 2)

    def test_isiterable(self):
        assert isiterable([1, 2, 3]) is True
        assert isiterable('abc') is True
        assert isiterable(5) is False

    def test_isdistinct(self):
        assert isdistinct([1, 2, 3]) is True
        assert isdistinct([1, 2, 1]) is False

        assert isdistinct("Hello") is False
        assert isdistinct("World") is True

        assert isdistinct(iter([1, 2, 3])) is True
        assert isdistinct(iter([1, 2, 1])) is False

    def test_nth(self):
        assert nth(2, 'ABCDE') == 'C'
        assert nth(2, iter('ABCDE')) == 'C'
        assert nth(1, (3, 2, 1)) == 2
        assert nth(0, {'foo': 'bar'}) == 'foo'
        assert raises(StopIteration, lambda: nth(10, {10: 'foo'}))
        assert nth(-2, 'ABCDE') == 'D'
        assert raises(ValueError, lambda: nth(-2, iter('ABCDE')))

    def test_first(self):
        assert first('ABCDE') == 'A'
        assert first((3, 2, 1)) == 3
        assert isinstance(first({0: 'zero', 1: 'one'}), int)

    def test_second(self):
        assert second('ABCDE') == 'B'
        assert second((3, 2, 1)) == 2
        assert isinstance(second({0: 'zero', 1: 'one'}), int)

    def test_last(self):
        assert last('ABCDE') == 'E'
        assert last((3, 2, 1)) == 1
        assert isinstance(last({0: 'zero', 1: 'one'}), int)

    def test_rest(self):
        assert list(rest('ABCDE')) == list('BCDE')
        assert list(rest((3, 2, 1))) == list((2, 1))

    def test_take(self):
        assert list(take(3, 'ABCDE')) == list('ABC')
        assert list(take(2, (3, 2, 1))) == list((3, 2))

    def test_tail(self):
        assert list(tail(3, 'ABCDE')) == list('CDE')
        assert list(tail(3, iter('ABCDE'))) == list('CDE')
        assert list(tail(2, (3, 2, 1))) == list((2, 1))

    def test_drop(self):
        assert list(drop(3, 'ABCDE')) == list('DE')
        assert list(drop(1, (3, 2, 1))) == list((2, 1))

    def test_take_nth(self):
        assert list(take_nth(2, 'ABCDE')) == list('ACE')

    def test_get(self):
        assert get(1, 'ABCDE') == 'B'
        assert list(get([1, 3], 'ABCDE')) == list('BD')
        assert get('a', {'a': 1, 'b': 2, 'c': 3}) == 1
        assert get(['a', 'b'], {'a': 1, 'b': 2, 'c': 3}) == (1, 2)

        assert get('foo', {}, default='bar') == 'bar'
        assert get({}, [1, 2, 3], default='bar') == 'bar'
        assert get([0, 2], 'AB', 'C') == ('A', 'C')

        assert get([0], 'AB') == ('A',)
        assert get([], 'AB') == ()

        assert raises(IndexError, lambda: get(10, 'ABC'))
        assert raises(KeyError, lambda: get(10, {'a': 1}))
        assert raises(TypeError, lambda: get({}, [1, 2, 3]))
        assert raises(TypeError, lambda: get([1, 2, 3], 1, None))
        assert raises(KeyError, lambda: get('foo', {}, default=no_default2))

    def test_mapcat(self):
        assert (list(mapcat(identity, [[1, 2, 3], [4, 5, 6]])) ==
                [1, 2, 3, 4, 5, 6])

        assert (list(mapcat(reversed, [[3, 2, 1, 0], [6, 5, 4], [9, 8, 7]])) ==
                list(range(10)))

        inc = lambda i: i + 1
        assert ([4, 5, 6, 7, 8, 9] ==
                list(mapcat(partial(map, inc), [[3, 4, 5], [6, 7, 8]])))

    def test_cons(self):
        assert list(cons(1, [2, 3])) == [1, 2, 3]

    def test_concat(self):
        assert list(concat([[], [], []])) == []
        assert (list(take(5, concat([['a', 'b'], range(1000000000)]))) ==
                ['a', 'b', 0, 1, 2])

    def test_concatv(self):
        assert list(concat([], [], [])) == []
        assert (list(take(5, concat(['a', 'b'], range(1000000000)))) ==
                ['a', 'b', 0, 1, 2])

    def test_interpose(self):
        assert "a" == first(rest(interpose("a", range(1000000000))))
        assert "tXaXrXzXaXn" == "".join(interpose("X", "tarzan"))
        assert list(interpose(0, itertools.repeat(1, 4))) == [1, 0, 1, 0, 1, 0,
                                                              1]
        assert list(interpose('.', ['a', 'b', 'c'])) == ['a', '.', 'b', '.',
                                                         'c']

    def test_frequencies(self):
        assert (frequencies(["cat", "pig", "cat", "eel",
                             "pig", "dog", "dog", "dog"]) ==
                {"cat": 2, "eel": 1, "pig": 2, "dog": 3})
        assert frequencies([]) == {}
        assert frequencies("onomatopoeia") == {
            "a": 2, "e": 1, "i": 1, "m": 1,
            "o": 4, "n": 1, "p": 1, "t": 1
        }

    def test_reduceby(self):
        data = [1, 2, 3, 4, 5]
        iseven = lambda x: x % 2 == 0
        assert reduceby(iseven, add, data, 0) == {False: 9, True: 6}
        assert reduceby(iseven, mul, data, 1) == {False: 15, True: 8}

        projects = [{'name': 'build roads', 'state': 'CA', 'cost': 1000000},
                    {'name': 'fight crime', 'state': 'IL', 'cost': 100000},
                    {'name': 'help farmers', 'state': 'IL', 'cost': 2000000},
                    {'name': 'help farmers', 'state': 'CA', 'cost': 200000}]
        assert reduceby(lambda x: x['state'],
                        lambda acc, x: acc + x['cost'],
                        projects, 0) == {'CA': 1200000, 'IL': 2100000}

        assert reduceby('state',
                        lambda acc, x: acc + x['cost'],
                        projects, 0) == {'CA': 1200000, 'IL': 2100000}

    def test_reduce_by_init(self):
        assert reduceby(iseven, add, [1, 2, 3, 4]) == {
            True: 2 + 4, False: 1 + 3
        }
        assert reduceby(iseven, add, [1, 2, 3, 4], no_default2) == {
            True: 2 + 4,
            False: 1 + 3
        }

    def test_reduce_by_callable_default(self):
        def set_add(s, i):
            s.add(i)
            return s

        assert reduceby(iseven, set_add, [1, 2, 3, 4, 1, 2], set) == \
               {True: {2, 4}, False: {1, 3}}

    def test_iterate(self):
        assert list(itertools.islice(iterate(inc, 0), 0, 5)) == [0, 1, 2, 3, 4]
        assert list(take(4, iterate(double, 1))) == [1, 2, 4, 8]

    def test_accumulate(self):
        assert list(accumulate(add, [1, 2, 3, 4, 5])) == [1, 3, 6, 10, 15]
        assert list(accumulate(mul, [1, 2, 3, 4, 5])) == [1, 2, 6, 24, 120]
        assert list(accumulate(add, [1, 2, 3, 4, 5], -1)) == [-1, 0, 2, 5, 9,
                                                              14]

        def binop(a, b):
            raise AssertionError('binop should not be called')

        start = object()
        assert list(accumulate(binop, [], start)) == [start]
        assert list(accumulate(add, [1, 2, 3], no_default2)) == [1, 3, 6]

    def test_accumulate_works_on_consumable_iterables(self):
        assert list(accumulate(add, iter((1, 2, 3)))) == [1, 3, 6]

    def test_sliding_window(self):
        assert list(sliding_window(2, [1, 2, 3, 4])) == [(1, 2), (2, 3), (3, 4)]
        assert list(sliding_window(3, [1, 2, 3, 4])) == [(1, 2, 3), (2, 3, 4)]

    def test_sliding_window_of_short_iterator(self):
        assert list(sliding_window(3, [1, 2])) == []

    def test_partition(self):
        assert list(partition(2, [1, 2, 3, 4])) == [(1, 2), (3, 4)]
        assert list(partition(3, range(7))) == [(0, 1, 2), (3, 4, 5)]
        assert list(partition(3, range(4), pad=-1)) == [(0, 1, 2),
                                                        (3, -1, -1)]
        assert list(partition(2, [])) == []

    def test_partition_all(self):
        assert list(partition_all(2, [1, 2, 3, 4])) == [(1, 2), (3, 4)]
        assert list(partition_all(3, range(5))) == [(0, 1, 2), (3, 4)]
        assert list(partition_all(2, [])) == []

    def test_count(self):
        assert count((1, 2, 3)) == 3
        assert count([]) == 0
        assert count(iter((1, 2, 3, 4))) == 4

        assert count('hello') == 5
        assert count(iter('hello')) == 5

    def test_pluck(self):
        assert list(pluck(0, [[0, 1], [2, 3], [4, 5]])) == [0, 2, 4]
        assert list(pluck([0, 1], [[0, 1, 2], [3, 4, 5]])) == [(0, 1), (3, 4)]
        assert list(pluck(1, [[0], [0, 1]], None)) == [None, 1]

        data = [{'id': 1, 'name': 'cheese'},
                {'id': 2, 'name': 'pies', 'price': 1}]
        assert list(pluck('id', data)) == [1, 2]
        assert list(pluck('price', data, 0)) == [0, 1]
        assert list(pluck(['id', 'name'], data)) == [(1, 'cheese'), (2, 'pies')]
        assert list(pluck(['name'], data)) == [('cheese',), ('pies',)]
        assert list(pluck(['price', 'other'], data, 0)) == [(0, 0), (1, 0)]

        assert raises(IndexError, lambda: list(pluck(1, [[0]])))
        assert raises(KeyError, lambda: list(pluck('name', [{'id': 1}])))

        assert list(pluck(0, [[0, 1], [2, 3], [4, 5]], no_default2)) == [0, 2,
                                                                         4]
        assert raises(IndexError, lambda: list(pluck(1, [[0]], no_default2)))

    def test_join(self):
        names = [(1, 'one'), (2, 'two'), (3, 'three')]
        fruit = [('apple', 1), ('orange', 1), ('banana', 2), ('coconut', 2)]

        def addpair(pair):
            return pair[0] + pair[1]

        result = set(starmap(add, join(first, names, second, fruit)))

        expected = {((1, 'one', 'apple', 1)), ((1, 'one', 'orange', 1)),
                    ((2, 'two', 'banana', 2)), ((2, 'two', 'coconut', 2))}

        assert result == expected

        result = set(starmap(add, join(first, names, second, fruit,
                                       left_default=no_default2,
                                       right_default=no_default2)))
        assert result == expected

    def test_key_as_getter(self):
        squares = [(i, i ** 2) for i in range(5)]
        pows = [(i, i ** 2, i ** 3) for i in range(5)]

        assert set(join(0, squares, 0, pows)) == set(
            join(lambda x: x[0], squares,
                 lambda x: x[0], pows))

        get = lambda x: (x[0], x[1])
        assert set(join([0, 1], squares, [0, 1], pows)) == set(
            join(get, squares,
                 get, pows))

        get = lambda x: (x[0],)
        assert set(join([0], squares, [0], pows)) == set(join(get, squares,
                                                              get, pows))

    def test_join_double_repeats(self):
        names = [(1, 'one'), (2, 'two'), (3, 'three'), (1, 'uno'), (2, 'dos')]
        fruit = [('apple', 1), ('orange', 1), ('banana', 2), ('coconut', 2)]

        result = set(starmap(add, join(first, names, second, fruit)))

        expected = {((1, 'one', 'apple', 1)), ((1, 'one', 'orange', 1)),
                    ((2, 'two', 'banana', 2)), ((2, 'two', 'coconut', 2)),
                    ((1, 'uno', 'apple', 1)), ((1, 'uno', 'orange', 1)),
                    ((2, 'dos', 'banana', 2)), ((2, 'dos', 'coconut', 2))}

        assert result == expected

    def test_join_missing_element(self):
        names = [(1, 'one'), (2, 'two'), (3, 'three')]
        fruit = [('apple', 5), ('orange', 1)]

        result = set(starmap(add, join(first, names, second, fruit)))

        expected = {((1, 'one', 'orange', 1))}

        assert result == expected

    def test_left_outer_join(self):
        result = set(
            join(identity, [1, 2], identity, [2, 3], left_default=None))
        expected = {(2, 2), (None, 3)}

        assert result == expected

    def test_right_outer_join(self):
        result = set(
            join(identity, [1, 2], identity, [2, 3], right_default=None))
        expected = {(2, 2), (1, None)}

        assert result == expected

    def test_outer_join(self):
        result = set(join(identity, [1, 2], identity, [2, 3],
                          left_default=None, right_default=None))
        expected = {(2, 2), (1, None), (None, 3)}

        assert result == expected

    def test_diff(self):
        assert raises(TypeError, lambda: list(diff()))
        assert raises(TypeError, lambda: list(diff([1, 2])))
        assert raises(TypeError, lambda: list(diff([1, 2], 3)))
        assert list(diff([1, 2], (1, 2), iter([1, 2]))) == []
        assert list(diff([1, 2, 3], (1, 10, 3), iter([1, 2, 10]))) == [
            (2, 10, 2), (3, 3, 10)]
        assert list(diff([1, 2], [10])) == [(1, 10)]
        assert list(diff([1, 2], [10], default=None)) == [(1, 10), (2, None)]
        # non-variadic usage
        assert raises(TypeError, lambda: list(diff([])))
        assert raises(TypeError, lambda: list(diff([[]])))
        assert raises(TypeError, lambda: list(diff([[1, 2]])))
        assert raises(TypeError, lambda: list(diff([[1, 2], 3])))
        assert list(diff([(1, 2), (1, 3)])) == [(2, 3)]

        data1 = [{'cost': 1, 'currency': 'dollar'},
                 {'cost': 2, 'currency': 'dollar'}]

        data2 = [{'cost': 100, 'currency': 'yen'},
                 {'cost': 300, 'currency': 'yen'}]

        conversions = {'dollar': 1, 'yen': 0.01}

        def indollars(item):
            return conversions[item['currency']] * item['cost']

        list(diff(data1, data2, key=indollars)) == [
            ({'cost': 2, 'currency': 'dollar'},
             {'cost': 300, 'currency': 'yen'})]

    def test_topk(self):
        assert topk(2, [4, 1, 5, 2]) == (5, 4)
        assert topk(2, [4, 1, 5, 2], key=lambda x: -x) == (1, 2)
        assert topk(2, iter([5, 1, 4, 2]), key=lambda x: -x) == (1, 2)

        assert topk(2, [{'a': 1, 'b': 10}, {'a': 2, 'b': 9},
                        {'a': 10, 'b': 1}, {'a': 9, 'b': 2}], key='a') == \
               ({'a': 10, 'b': 1}, {'a': 9, 'b': 2})

        assert topk(2, [{'a': 1, 'b': 10}, {'a': 2, 'b': 9},
                        {'a': 10, 'b': 1}, {'a': 9, 'b': 2}], key='b') == \
               ({'a': 1, 'b': 10}, {'a': 2, 'b': 9})
        assert topk(2, [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)], 0) == \
               ((4, 0), (3, 1))

    def test_topk_is_stable(self):
        assert topk(4, [5, 9, 2, 1, 5, 3], key=lambda x: 1) == (5, 9, 2, 1)

    def test_peek(self):
        alist = ["Alice", "Bob", "Carol"]
        element, blist = peek(alist)
        assert element == alist[0]
        assert list(blist) == alist
        assert raises(StopIteration, lambda: peek([]))

    def test_random_sample(self):
        alist = list(range(100))

        assert list(
            random_sample(1, alist, random_state=2016)) == alist

        mk_rsample = lambda rs=1: \
            list(random_sample(0.1, alist, random_state=rs))
        rsample1 = mk_rsample()
        assert rsample1 == mk_rsample()

        rsample2 = mk_rsample(1984)
        randobj = Random(1984)
        assert rsample2 == mk_rsample(randobj)

        assert rsample1 != rsample2

        assert mk_rsample(object) == mk_rsample(object)
        assert mk_rsample(object) != mk_rsample(object())
        assert mk_rsample(b"a") == mk_rsample(u"a")

        assert raises(TypeError, lambda: mk_rsample([]))
