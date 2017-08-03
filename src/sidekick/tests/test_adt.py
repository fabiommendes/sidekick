from sidekick import Maybe, Just, Nothing, Union, opt, maybe, Ok, Err, Result
from sidekick.adt import UnionMeta
import pytest


class TestADTMeta:
    def test_adt_name(self):
        class ADT(opt.Foo | opt.Bar):
            pass

        assert (opt.Foo | opt.Bar).__name__ == 'Union(Foo|Bar)'
        assert ADT.__name__ == 'ADT'

    def test_forbid_multiple_levels_of_inheritance(self):
        ADT = opt.Foo | opt.Bar
        
        class ADT2(ADT):
            pass

        assert isinstance(ADT.Foo, ADT)
        assert isinstance(ADT2.Foo, ADT2)
        assert not isinstance(ADT2.Foo, ADT)
        assert not isinstance(ADT.Foo, ADT2)
        assert not issubclass(ADT2, ADT)

    def test_construct_adt_with_more_than_two_states(self):
        ADT = opt.Foo | opt.Bar | opt.Ham
        
        assert issubclass(ADT, Union)
        assert isinstance(ADT.Foo, ADT)
        assert isinstance(ADT.Bar, ADT)
        assert isinstance(ADT.Ham, ADT)
        
    def test_construct_composite_adt_with_more_than_two_states(self):
        ADT = opt.Foo(object) | opt.Bar(object) | opt.Ham(object)
        assert issubclass(ADT, Union)
        assert isinstance(ADT.Foo(1), ADT)
        assert isinstance(ADT.Bar(2), ADT)
        assert isinstance(ADT.Ham(3), ADT)

    def test_state_numeric_initializer(self):
        assert opt.State(2) == opt.State(object, object)
        
    def test_none_forces_creation_of_union_type(self):
        adt = opt.Foo | None
        assert isinstance(adt, UnionMeta)
        assert (
            (opt.Foo | opt.Bar)._states == (opt.Foo | opt.Bar | None)._states
        )

    def test_forbids_multiple_adt_inheritance(self):
        with pytest.raises(TypeError):
            class ADT(opt.Foo | opt.Bar, opt.Ham | opt.Spam):
                pass

    def test_forbids_multiple_levels_of_inheritance(self):
        class ADT(opt.Foo | opt.Bar):
                pass

        with pytest.raises(TypeError):
            class ADTChild(ADT):
                pass

    def test_forbids_lowercase_state_names(self):
        with pytest.raises(TypeError):
            opt.foo


class TestADT:
    @pytest.fixture
    def Maybe(self):
        return opt.Just(object) | opt.Nothing

    @pytest.fixture
    def just(self, Maybe):
        return Maybe.Just(42)

    @pytest.fixture
    def nothing(self, Maybe):
        return Maybe.Nothing

    def test_adt_has_correct_type(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert type(x) is Maybe
        assert type(y) is Maybe
        assert isinstance(x, Union)
        assert isinstance(y, Union)
        assert issubclass(Maybe, Union)

    def test_adt_repr(self, Maybe):
        assert repr(Maybe.Just(42)) == 'Just(42)'
        assert repr(Maybe.Nothing) == 'Nothing'

    def test_adt_requires_correct_number_of_arguments(self, Maybe):
        with pytest.raises(TypeError):
            Maybe.Just(1, 2)

        with pytest.raises(TypeError):
            Maybe.Just()

    def test_conditionals(self, Maybe):
        x = Maybe.Just(42)
        assert x.just
        assert not x.nothing

        y = Maybe.Nothing
        assert y.nothing
        assert not y.just 

    def test_match_function(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        
        res = x.match(
            just=lambda x: x * 2,
            nothing=lambda: 0,
        )
        assert res == 84

        res = y.match(
            just=lambda x: x * 2,
            nothing=lambda: 0,
        )
        assert res == 0
        
    def test_match_function_constructor(self, Maybe):
        x = Maybe.Just(42)
        y = Maybe.Nothing

        func = Maybe.match_fn(
            just=lambda x: x * 2,
            nothing=lambda: 0,
        )
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
        assert x.just_args == (42,)
        assert y.nothing_args == ()
        
        with pytest.raises(AttributeError):
            assert x.nothing_args
        
        with pytest.raises(AttributeError):
            assert y.just_args

    def test_match_fn_raises_error_on_non_exaustive_options(self, Maybe):
        with pytest.raises(ValueError):
            Maybe.match_fn(
                just=lambda x: x,
            )
        
        with pytest.raises(ValueError):
            Maybe.match_fn(
                just=lambda x: x,
                nothing=lambda: 0,
                other=lambda: 0,
            )
        
        with pytest.raises(ValueError):
            Maybe.match_fn(
                ok=lambda x: x,
                err=lambda: 0,
            )

    def test_adt_matches_instance(self, Maybe):
        a = Maybe.Just(42)
        b = Maybe.Nothing

        assert a.match(just=lambda x: x, nothing=lambda: 0) == 42
        assert b.match(just=lambda x: x, nothing=lambda: 0) == 0

    def test_adt_matches_are_exaustive(self, Maybe):
        err = ValueError
        f1 = lambda x: x
        f2 = lambda x: None

        with pytest.raises(err):
            Maybe.Nothing.match(just=f1)

        with pytest.raises(err):
            Maybe.Nothing.match(nothing=f1)

        with pytest.raises(err):
            Maybe.Nothing.match(just=f1, nothing=f2, other=f2)

    def test_adt_has_hash(self, Maybe):
        assert hash(Maybe.Nothing) != hash(Maybe.Just(1))


class TestMaybe(TestADT):
    @pytest.fixture
    def Maybe(self):
        return Maybe

    def test_maybe_type(self, Maybe):
        assert Maybe.__name__ == 'Maybe'
        assert hasattr(Maybe, 'value')

    def test_then_method(self):
        x = Maybe.Just(1)
        y = x.then(lambda x: x + 1).then(lambda x: x + 1)
        
        assert y.just
        assert y.value == 3
    
    def test_then_method_nothing(self):
        x = Maybe.Nothing
        y = x.then(lambda x: x + 1).then(lambda x: x + 1)
        assert y.nothing

    def test_maybe_chaining(self):
        x = (Maybe.Just(42) >> (lambda x: 2 * x)).get()
        y = (Maybe.Nothing >> (lambda x: 2 * x)).get()
        assert x == 84
        assert y == None

    def test_call(self):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert Maybe.call(lambda x, y: x + y, x, x) == Maybe.Just(84)
        assert Maybe.call(lambda x, y: x + y, x, y) == Maybe.Nothing

    def test_bitwise(self):
        x = Maybe.Just(42)
        y = Maybe.Nothing
        assert x & y == y
        assert x | y == x

    def test_ok_alias_just(self, just, nothing):
        assert just.ok is just.just
        assert nothing.ok is nothing.just

    def test_convertion_to_result(self, just, nothing):
        assert just.to_result().ok
        assert nothing.to_result().err

    def test_thruthness(self, just, nothing):
        assert just
        assert not nothing

    def test_maybe_function_conversions(self, Maybe):
        assert maybe(42) == Maybe.Just(42)
        assert maybe(None) == Maybe.Nothing

    def test_logical_operations(self, just, nothing):
        assert just | nothing == nothing | just == just
        assert just & nothing == nothing & just == nothing


class TestResult:
    @pytest.fixture
    def ok(self):
        return Ok(42)

    @pytest.fixture
    def err(self):
        return Err('err')

    def test_result_get_value(self, ok, err):
        assert ok.value == 42
        assert getattr(err, 'value', None) is None

    def test_result_get_error(self, ok, err):
        assert ok.error is None
        assert err.error == 'err'

    def test_result_apply_method(self, ok, err):
        assert Result.apply(str, ok) == Ok('42')
        assert Result.apply(str, err) == Err('err')

    def test_result_then_chaining(self, ok, err):
        assert ok.then(str) == Ok('42')
        assert err.then(str) == Err('err')

    def test_result_map_error_chaining(self, ok, err):
        assert ok.map_error(str.upper) == Ok(42)
        assert err.map_error(str.upper) == Err('ERR')

    def test_test_get_value_from_result(self, ok, err):
        assert ok.get() == 42
        assert err.get() == None

    def test_to_maybe(self, ok, err):
        assert ok.to_maybe() == Maybe.Just(42)
        assert err.to_maybe() == Maybe.Nothing

    def test_logical_operations(self, ok, err):
        assert ok | err == err | ok == ok
        assert ok & err == err & ok == err
