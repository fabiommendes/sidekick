from copy import copy

import pytest

from sidekick import Record, field, record, record_to_dict


class TestAnonymousRecord:
    @pytest.fixture
    def pt(self):
        return record(x=1, y=2)

    def test_record_base_funcs(self):
        r = record(x=1, y=2)
        assert r.x == 1
        assert r.y == 2
        assert repr(r) == 'record(x=1, y=2)'

    def test_record_is_immutable(self, pt):
        assert hash(pt) != -1

        with pytest.raises(AttributeError):
            pt.x = 2

        with pytest.raises(AttributeError):
            pt.z = 3


class TestRecord:
    @pytest.fixture(scope='class')
    def Point(self):
        class Point(Record):
            x = field()
            y = field(default=0)

        return Point

    @pytest.fixture
    def pt(self, Point):
        return Point(1, 2)

    test_record_is_immutable = TestAnonymousRecord.test_record_is_immutable

    def test_record_base_methods(self, pt):
        assert repr(pt) == 'Point(1, 2)'
        assert pt.x == 1
        assert pt.y == 2
        assert pt is not copy(pt)
        assert pt == copy(pt)
        assert hash(pt) != -1

    def test_record_constructors(self, pt, Point):
        assert pt == Point(1, 2)
        assert pt == Point(x=1, y=2)
        assert Point(1, 0) == Point(1)

    def test_record_to_dict(self, pt):
        assert record_to_dict(pt) == {'x': 1, 'y': 2}
