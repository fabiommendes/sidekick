from copy import copy

import pytest

from sidekick import Record, Namespace, record


# ==============================================================================
# RECORD AND NAMESPACES
# ==============================================================================


class TestMetaclass:
    def test_create_class_with_define(self):
        self._check(Record.define("Point", ["x", "y"]))
        self._check_mutable(Namespace.define("Point", ["x", "y"]))

    def test_create_class_with_class_notation(self):
        class Point(Record):
            x: object
            y: object

        self._check(Point)

        class Point(Namespace):
            x: object
            y: object

        self._check_mutable(Point)

    def _check(self, cls, is_mutable=False, base=Record):
        assert cls.__name__ == "Point"
        assert cls._meta.fields == ("x", "y")
        assert cls._meta.types == (object, object)
        assert not cls._meta.defaults
        assert cls._meta.is_mutable == is_mutable
        assert issubclass(cls, base)

    def _check_mutable(self, cls):
        self._check(cls, True, Namespace)


class TestRecord:
    @pytest.fixture(scope="class")
    def cls(self):
        class Point(Record):
            x: object
            y: object = 0

        return Point

    @pytest.fixture
    def pt(self, cls):
        return cls(1, 2)

    def test_meta_information(self, cls):
        meta = cls._meta
        assert not meta.is_mutable
        assert meta.types == (object, object)
        assert meta.fields == ("x", "y")

    def test_record_is_immutable(self, pt):
        assert hash(pt) != -1

        with pytest.raises(AttributeError):
            pt.x = 2

        with pytest.raises(AttributeError):
            pt.z = 3

    def test_record_base_methods(self, pt):
        name = type(pt).__name__
        assert repr(pt) == f"{name}(1, 2)"
        assert pt.x == 1
        assert pt.y == 2
        assert pt is not copy(pt)
        assert pt == copy(pt)
        assert hash(pt) != -1

    def test_record_constructors(self, pt, cls):
        assert pt == cls(1, 2)
        assert pt == cls(x=1, y=2)
        assert cls(1, 0) == cls(1)

    def test_record_to_dict(self, pt):
        assert dict(pt) == {"x": 1, "y": 2}

    def test_do_not_make_record_with_invalid_names(self):
        with pytest.raises(ValueError):
            Record.define("IfBlock", ["if", "else"])

    def test_make_record_with_invalid_names(self):
        Rec = Record.define("IfBlock", ["if", "else"], use_invalid=True)
        rec = Rec(1, 2)
        assert dict(rec) == {"if": 1, "else": 2}
        assert getattr(rec, "if") == 1


class TestNamespace(TestRecord):
    @pytest.fixture(scope="function")
    def cls(self):
        class MutablePoint(Namespace):
            x: object
            y: object = 0

        return MutablePoint

    test_record_is_immutable = None

    def test_meta_information(self, cls):
        meta = cls._meta
        assert meta.is_mutable
        assert meta.types == (object, object)
        assert meta.fields == ("x", "y")


class TestRecordView:
    cls = TestRecord.cls
    pt = TestRecord.pt

    def test_anonymous_recordM(self):
        assert set(record(x=1, y=2).M) == {"x", "y"}
        assert len(record(x=1, y=2).M) == 2
        assert record(x=1, y=2).M["x"] == 1

    def test_recordM_emit_key_error(self, pt):
        assert pt.M["x"] == 1

        with pytest.raises(KeyError):
            print(pt.M["foo"])

        with pytest.raises(KeyError):
            print(pt.M["_foo"])

        with pytest.raises(KeyError):
            print(pt.M[0])


# ==============================================================================
# ANONYMOUS STRUCTURES
# ==============================================================================


class TestAnonymousRecord:
    @pytest.fixture
    def pt(self):
        return record(x=1, y=2)

    test_record_is_immutable = TestRecord.test_record_is_immutable

    def test_record_base_funcs(self):
        r = record(x=1, y=2)
        assert r.x == 1
        assert r.y == 2
        assert repr(r) == "record(x=1, y=2)"

    def test_conversion(self, pt):
        assert dict(pt) == {"x": 1, "y": 2}
