import pytest

from sidekick import Maybe, Just, Nothing, case, case_fn, casedispatch


def fargs(*args):
    return args


@pytest.fixture
def just():
    return Just(42)


@pytest.fixture
def nothing():
    return Nothing


class TestCaseSyntax:
    def test_case_syntax_works_in_well_formed_cases(self, just, nothing):
        assert case[just](Just=fargs, Nothing=fargs) == (42,)
        assert case[nothing](Just=fargs, Nothing=fargs) == ()

        assert case[just](Just=fargs, else_=fargs) == (42,)
        assert case[nothing](Just=fargs, else_=fargs) == (nothing,)

    def test_case_syntax_works_in_incomplete_cases(self, just, nothing):
        assert case[just](Just=fargs) == (42,)
        assert case[nothing](Nothing=fargs) == ()

        assert case[just](else_=fargs) == (just,)
        assert case[nothing](else_=fargs) == (nothing,)

    def test_case_syntax_works_with_overspecified_cases(self, just, nothing):
        assert case[just](Just=fargs, Nothing=fargs, Other=fargs) == (42,)
        assert case[nothing](Just=fargs, Nothing=fargs, Other=fargs) == ()

    def test_case_syntax_bad_cases(self, just, nothing):
        with pytest.raises(TypeError):
            case[just](Nothing=fargs)

        with pytest.raises(TypeError):
            case[nothing](Just=fargs)


class TestCaseFnSyntax:
    def test_case_fn_exaustive(self, just, nothing):
        func = case_fn[Maybe](Just=lambda x: x, Nothing=lambda: 0)
        assert func(just) == 42
        assert func(nothing) == 0

    def test_case_with_else_case(self, just, nothing):
        func = case_fn[Maybe](Just=lambda x: x, else_=lambda x: 0)
        assert func(just) == 42
        assert func(nothing) == 0

    def test_case_class_syntax(self, just, nothing):
        @casedispatch.from_namespace(Maybe)
        class func:
            def Just(x):
                return x

            def Nothing():
                return 0

        assert func(just) == 42
        assert func(nothing) == 0

    def test_case_fn_checks_for_bad_defs(self):
        err = TypeError

        with pytest.raises(err):
            case_fn[Maybe](Just=lambda x: x)

        with pytest.raises(err):
            case_fn[Maybe](Just=lambda x: x, Other=lambda: 0)

        with pytest.raises(err):
            case_fn[Maybe](Just=lambda x: x, Nothing=lambda: 0, Other=lambda: 0)


class TestCaseDispatchDecorator:
    def test_case_dispatch_full(self, just, nothing):
        @casedispatch(Maybe.Just)
        def add(x, y):
            return x + y

        @add.register(Maybe.Nothing)
        def _(y):
            return y

        assert add(just, 2) == 44
        assert add(nothing, 2) == 2

    def test_case_dispatch_with_default(self, just, nothing):
        @casedispatch(Maybe)
        def add(x, y):
            return y

        @add.register(Maybe.Just)
        def _(x, y):
            return x + y

        assert add(just, 2) == 44
        assert add(nothing, 2) == 2

    def test_case_dispatch_incomplete(self, just):
        @casedispatch(Maybe.Just)
        def add(x, y):
            return x + y

        with pytest.raises(TypeError):
            add(just, 2)
