import pytest

from sidekick import Record, Maybe, Nothing, Union, Case, maybe, Ok, Err, rcall
from sidekick.types.union import SingletonMeta, SingletonMixin

UnionMeta = type(Union)


class TestCreateUnionType:
    def test_case_constructor(self):
        assert issubclass(Case("foo"), Record)
        assert issubclass(Case(), SingletonMixin)
        assert not issubclass(Case(), Record)
        assert isinstance(Case(), SingletonMeta)
        assert Case() is Case()

    def test_union_type_hierarchy(self):
        class ADT(Union):
            Foo: Case()
            Bar: Case("value")

        assert ADT.__name__ == "ADT"

        # Non singleton
        assert issubclass(ADT.Bar, ADT)
        assert isinstance(ADT.Bar(42), ADT)
        assert isinstance(ADT.Bar(42), ADT.Bar)

        # Singleton
        assert not isinstance(ADT.Foo, type)
        assert isinstance(ADT.Foo, ADT), type(ADT.Foo).__mro__
        assert isinstance(ADT.Foo, ADT.Foo)
        assert issubclass(type(ADT.Foo), ADT)

    def test_construct_adt_with_more_than_two_states(self):
        class ADT(Union):
            Foo: Case()
            Bar: Case()
            Ham: Case()

        assert isinstance(ADT.Foo, ADT)
        assert isinstance(ADT.Bar, ADT)
        assert isinstance(ADT.Ham, ADT)

    def test_construct_composite_adt_with_more_than_two_states(self):
        class ADT(Union):
            Foo: Case("value")
            Bar: Case("value")
            Ham: Case("value")

        assert isinstance(ADT.Foo(1), ADT)
        assert isinstance(ADT.Bar(2), ADT)
        assert isinstance(ADT.Ham(3), ADT)

    def test_forbids_multiple_adt_inheritance(self):
        class FooBar(Union):
            Foo: Case()
            Bar: Case()

        class HamSpam(Union):
            Ham: Case()
            Spam: Case()

        with pytest.raises(TypeError):

            class ADT(FooBar, HamSpam):
                pass

                # def test_forbids_multiple_levels_of_inheritance(self):
                #     class ADT(Union):
                #         Foo: Case()
                #         Bar: Case()
                #
                #     ADT.__module__ = "not_the_same_module_as_child"
                #
                #     with pytest.raises(TypeError):
                #         class Child(ADT):
                ...

    def test_can_define_case_classes_outside_the_class_body(self):
        class ADT(Union):
            Foo: Case()
            Bar: Case()

        class Child(ADT):
            args: Case("value")

        assert ADT.Child is Child


class _TestADT:
    @pytest.fixture
    def Maybe(self):
        class Maybe(Union):
            Nothing: Case()
            Just: Case(1)

        return Maybe

    @pytest.fixture
    def just(self, Maybe):
        return Maybe.Just(42)

    @pytest.fixture
    def nothing(self, Maybe):
        return Maybe.Nothing

    def test_adt_has_correct_type(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert isinstance(x, Maybe.Just)
        assert isinstance(y, Maybe.Nothing)
        assert isinstance(x, Maybe)
        assert isinstance(y, Maybe)
        assert isinstance(x, Union)
        assert isinstance(y, Union)
        assert issubclass(Maybe, Union)

    def test_adt_repr(self, Maybe):
        assert repr(Maybe.Just(42)) == "Just(42)"
        assert repr(Maybe.Nothing) == "Nothing"

    def test_adt_requires_correct_number_of_arguments(self, Maybe):
        with pytest.raises(TypeError):
            Maybe.Just(1, 2)

        with pytest.raises(TypeError):
            Maybe.Just()

    def test_conditionals(self, Maybe):
        x = Maybe.Just(42)
        assert x.is_just
        assert not x.is_nothing

        y = Maybe.Nothing
        assert y.is_nothing
        assert not y.is_just

    def test_match_function(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing

        res = case[x](Just=lambda x: x * 2, Nothing=lambda: 0)
        assert res == 84

        res = case[y](Just=lambda x: x * 2, Nothing=lambda: 0)
        assert res == 0

    def test_match_function_constructor(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing

        func = case_fn[Maybe](Just=lambda x: x * 2, Nothing=lambda: 0)
        assert func(x) == 84
        assert func(y) == 0

    def test_equality(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert y == Maybe.Nothing
        assert x == Maybe.Just(42)
        assert x != y

    def test_can_access_state_args_attribute(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert x.args == (42,)
        assert y.args == ()

    def test_match_fn_raises_error_on_non_exaustive_options(self, Maybe):
        err = TypeError

        with pytest.raises(err):
            case_fn[Maybe](just=lambda x: x)

        with pytest.raises(err):
            case_fn[Maybe](just=lambda x: x, nothing=lambda: 0, other=lambda: 0)

        with pytest.raises(err):
            case_fn[Maybe](ok=lambda x: x, err=lambda: 0)

    def test_adt_matches_instance(self, Maybe):
        a = Maybe.Just(42)
        b = Maybe.Nothing

        assert case[a](Just=lambda x: x, Nothing=lambda: 0) == 42
        assert case[b](Just=lambda x: x, Nothing=lambda: 0) == 0

    def test_adt_matches_are_exaustive(self, Maybe):
        err = TypeError

        def f1(x):
            return x

        def f2(x):
            return None

        with pytest.raises(err):
            case[Maybe.Nothing](just=f1)

        with pytest.raises(err):
            case[Maybe.Nothing](nothing=f1)

        with pytest.raises(err):
            case[Maybe.Nothing](just=f1, nothing=f2, other=f2)

    def test_adt_has_hash(self, Maybe):
        assert hash(Maybe.Nothing) != hash(Maybe.Just(1))


class _TestADTWithExternalDefinition(_TestADT):
    @pytest.fixture
    def Maybe(self):
        class Maybe(Union):
            pass

        class Just(Maybe):
            args: Case(object)

        class Nothing(Maybe):
            pass

        return Maybe


class _TestMaybe(_TestADT):
    @pytest.fixture
    def Maybe(self):
        return Maybe

    def test_maybe_class_structure(self, Maybe):
        assert issubclass(Maybe.Just, Maybe)
        assert issubclass(type(Maybe.Nothing), Maybe)

    def test_maybe_type(self, Maybe):
        assert Maybe.__name__ == "Maybe"

    def test_then_method(self):
        x = Maybe.Just(1)
        y = x.map(lambda x: x + 1).map(lambda x: x + 1)

        assert y.is_just
        assert y.value == 3

    def test_then_method_nothing(self):
        x = Maybe.Nothing
        y = x.map(lambda x: x + 1).map(lambda x: x + 1)
        assert y.is_nothing

    def test_maybe_chaining(self):
        x = (Maybe.Just(42) >> (lambda x: 2 * x)).get_value()
        y = (Maybe.Nothing >> (lambda x: 2 * x)).get_value()
        assert x == 84
        assert y is None

    def test_call(self):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert mcall(lambda x, y: x + y, x, x) == Maybe.Just(84)
        assert mcall(lambda x, y: x + y, x, y) == Maybe.Nothing

    def test_bitwise(self):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert x & y == y
        assert x | y == x

    def test_ok_alias_just(self, just, nothing):
        assert just.is_ok is just.is_just
        assert nothing.is_ok is nothing.is_just

    def test_convertion_to_result(self, just, nothing):
        assert just.to_result().is_ok
        assert nothing.to_result().is_err

    def test_thruthness(self, just, nothing):
        assert just
        assert not nothing

    def test_maybe_function_conversions(self, Maybe):
        assert maybe(42) == Maybe.Just(42)
        assert maybe(None) == Maybe.Nothing

    def test_logical_operations(self, just, nothing):
        assert just | nothing == nothing | just == just
        assert just & nothing == nothing & just == nothing
        assert just | None == None | just == just
        assert just & None == None & just == nothing

    def test_maybe_binops(self, just, nothing):
        assert (just + just).is_just
        assert just + nothing == nothing

    def test_maybe_function(self, just, nothing):
        assert maybe(42) == just
        assert maybe(None) == nothing


class _TestResult:
    @pytest.fixture
    def ok(self):
        return Ok(42)

    @pytest.fixture
    def err(self):
        return Err("err")

    def test_result_get_value(self, ok, err):
        assert ok.value == 42
        assert getattr(err, "value", None) is None

    def test_result_get_error(self, ok, err):
        assert ok.error is None
        assert err.error == "err"

    def test_result_apply_method(self, ok, err):
        assert rcall(str, ok) == Ok("42")
        assert rcall(str, err) == Err("err")

    def test_result_then_chaining(self, ok, err):
        assert ok.map(str) == Ok("42")
        assert err.map(str) == Err("err")

    def test_result_map_error_chaining(self, ok, err):
        assert ok.map_error(str.upper) == Ok(42)
        assert err.map_error(str.upper) == Err("ERR")

    def test_test_get_value_from_result(self, ok, err):
        assert ok.get_value() == 42
        assert err.get_value() is None

    def test_to_maybe(self, ok, err):
        assert ok.to_maybe() == Maybe.Just(42)
        assert err.to_maybe() == Maybe.Nothing

    def test_logical_operations(self, ok, err):
        assert ok | err == err | ok == ok
        assert ok | Nothing == ok
        assert ok & err == err & ok == err
        assert ok & Nothing == Nothing.to_result()

    def test_result_operators(self, ok, err):
        assert ok + ok == Ok(84)
        assert ok + err == err
