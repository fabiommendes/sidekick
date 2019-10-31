import io

import sidekick as sk

Point = sk.Record.define("Point", ["x", "y"])
MPoint = sk.Namespace.define("MPoint", ["x", "y"])


class TestJson:
    def test_serializes_from_record_types(self):
        record = sk.record(x=1, y=2)

        assert sk.json.dumps(record) == '{"x": 1, "y": 2}'
        assert sk.json.dumps(sk.namespace(x=1, y=2)) == '{"x": 1, "y": 2}'

        assert sk.json.dumps(Point(x=1, y=2)) == '{"x": 1, "y": 2}'
        assert sk.json.dumps(MPoint(x=1, y=2)) == '{"x": 1, "y": 2}'

        file = io.StringIO()
        sk.json.dump(record, file)
        assert file.getvalue() == '{"x": 1, "y": 2}'

    def test_load_as_record_type(self):
        assert sk.record(x=1, y=2) == sk.json.loads('{"x": 1, "y": 2}')

        file = io.StringIO('{"x": 1, "y": 2}')
        assert sk.record(x=1, y=2) == sk.json.load(file)
