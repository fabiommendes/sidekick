from sidekick import Maybe, Just, Nothing, Union, opt
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
