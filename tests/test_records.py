from copy import copy

import pytest

from sidekick import Record, record


class TestAnonymousRecord:
    @pytest.fixture
    def pt(self):
        return record(x=1, y=2)

    def test_record_base_funcs(self):
        r = record(x=1, y=2)
        assert r.x == 1
        assert r.y == 2
        assert repr(r) == "record(x=1, y=2)"

    def test_record_is_immutable(self, pt):
        assert hash(pt) != -1

        with pytest.raises(AttributeError):
            pt.x = 2

        with pytest.raises(AttributeError):
            pt.z = 3

    def test_conversion(self, pt):
        assert dict(pt) == {"x": 1, "y": 2}


class TestRecord:
    @pytest.fixture(scope="class")
    def Point(self):
        class Point(Record):
            x: object
            y: object = 0

        return Point

    @pytest.fixture
    def pt(self, Point):
        return Point(1, 2)

    test_record_is_immutable = TestAnonymousRecord.test_record_is_immutable

    def test_record_base_methods(self, pt):
        assert repr(pt) == "Point(1, 2)"
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
        assert dict(pt) == {"x": 1, "y": 2}


class TestRecordView:
    Point = TestRecord.Point
    pt = TestRecord.pt

    def test_anonymous_recordM(self):
        assert set(record(x=1, y=2).M) == {"x", "y"}
        assert len(record(x=1, y=2).M) == 2
        assert record(x=1, y=2).M["x"] == 1

    def test_recordM_emit_key_error(self, pt):
        assert pt.M["x"] == 1

        with pytest.raises(KeyError):
            res = pt.M["foo"]

        with pytest.raises(KeyError):
            res = pt.M["_foo"]

        with pytest.raises(KeyError):
            res = pt.M[0]


class TestRecordWithInvalidNames:
    def test_do_not_make_record_with_invalid_names(self):
        with pytest.raises(ValueError):
            Record.define("IfBlock", ["if", "else"])

    def test_make_record_with_invalid_names(self):
        Rec = Record.define("IfBlock", ["if", "else"], use_invalid=True)
        rec = Rec(1, 2)
        assert dict(rec) == {"if": 1, "else": 2}
        assert getattr(rec, "if") == 1
