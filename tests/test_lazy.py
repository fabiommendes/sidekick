import pytest

import sidekick as sk
from sidekick import _


#
# Lazy attribute
#
class TestLazyDecorator:
    @pytest.fixture
    def decorator(selfs):
        return sk.lazy

    @pytest.fixture
    def C(self, decorator):
        class C(object):
            @decorator
            def c(self):
                return self.a + self.b

            def __init__(self, a, b):
                self.a = a
                self.b = b

        return C

    def test_lazy_attribute_is_cached(self, C):
        a = C("foo", "bar")
        assert a.c == "foobar"
        assert a.c is a.c
        assert a.c is not "foobar"

    def test_lazy_attribute_is_writable(self, C):
        a = C(1, 2)
        a.c = 0
        assert a.c == 0

    def test_lazy_works_with_fns(self, C):
        class B(C):
            d = sk.lazy(_.a + _.b + _.c)

        x = B(1, 2)
        assert x.d == 6


class TestLazyShared:
    @pytest.fixture
    def decorator(self):
        return sk.lazy_shared

    @pytest.fixture
    def C(self, decorator):
        class C(object):
            a = 1.0
            b = 2.0

            @decorator
            def c(self):
                return self.a + self.b

        return C

    def test_shared_lazy_accessor(self, C):
        a = C()
        b = C()
        assert a.c is b.c
        assert a.c is C.c
        assert C.__dict__['c'] is a.c

#
# #
# # Delegate to
# #
# @pytest.fixture
# def B():
#     class B(object):
#         x = delegate_to('data')
#         y = delegate_to('data', readonly=True)
#         z = delegate_ro('data')
#
#         def __init__(self, data):
#             self.data = data
#
#     return B
#
#
# @pytest.fixture
# def data_cls():
#     class Data:
#         def __init__(self, x, y, z):
#             self.x = x
#             self.y = y
#             self.z = z
#
#     return Data
#
#
# def test_delegate_to_reads_data(B, data_cls):
#     data = data_cls(1, 2, 3)
#     b = B(data)
#     assert b.x == 1
#     assert b.y == 2
#
#
# def test_delegate_ro_reads_data(B, data_cls):
#     data = data_cls(1, 2, 3)
#     b = B(data)
#     assert b.z == 3
#
#
# def test_delegate_to_can_write(B, data_cls):
#     data = data_cls(1, 2, 3)
#     b = B(data)
#     b.x = 42
#     assert b.x == 42
#
#
# def test_delegate_ro_cannot_write(B, data_cls):
#     data = data_cls(1, 2, 3)
#     b = B(data)
#
#     with pytest.raises(AttributeError):
#         b.y = 42
#
#     with pytest.raises(AttributeError):
#         b.z = 42
#
#     assert b.y == 2
#     assert b.z == 3
#
#
# #
# # Aliases
# #
# @pytest.fixture
# def C():
#     class C(object):
#         x = 1
#         y = alias('x')
#         z = readonly('y')
#
#     return C
#
#
# def test_alias_read(C):
#     obj = C()
#     assert obj.x == obj.y
#     assert obj.y == obj.z
#
#
# def test_alias_write(C):
#     obj = C()
#     obj.y = 42
#     assert obj.x == obj.y
#     assert obj.x == 42
#     assert obj.y == 42
#
#
# def test_readonly_cannot_write(C):
#     obj = C()
#     with pytest.raises(AttributeError):
#         obj.z = 42
#
#     assert obj.z == obj.x
