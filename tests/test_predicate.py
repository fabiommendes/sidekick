from sidekick import predicate, cond, is_odd, placeholder


class TestPredicate:
    def test_predicate_object_is_callable(self):
        p = predicate(lambda x: x == 2)
        assert p(2) is True
        assert p(1) is False

    def test_predicate_accepts_extended_function_semantics(self):
        assert predicate(placeholder == 2)(2) is True
        assert predicate(placeholder == 2)(3) is False

    def test_predicate_composes_on_logical_operations(self):
        p1 = predicate(placeholder > 0)
        p2 = predicate(placeholder < 10)
        p3 = p1 & p2
        assert p3(5) is True
        assert p3(11) is False
        assert (p1 | p2)(0) is True
        assert (~p1)(1) is False

    def test_cond(self):
        f = cond(is_odd).true((placeholder - 1) // 2).false(placeholder // 2)

        assert f(3) == 1
        assert f(4) == 2
