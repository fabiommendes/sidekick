from time import sleep

import pytest

from sidekick.beta.cache import ttl_cache


class TestCaches:
    @pytest.mark.slow
    def test_tle_cache_works(self):
        lst = []

        @ttl_cache("testing", timeout=0.01)
        def cache_function_with_side_effects(n):
            print(f"Calling with argument {n}")
            lst.append(n)
            return n

        fn = cache_function_with_side_effects
        fn.clear()

        # Execute w/ side effect
        assert fn(1) == 1
        assert lst == [1]

        # Again...
        assert fn(2) == 2
        assert lst == [1, 2]

        # Now it gets from cache and there is no side-effect
        assert fn(1) == 1
        assert lst == [1, 2]

        # We sleep to invalidate timeout and it should recompute again
        sleep(0.02)
        assert fn(1) == 1
        assert lst == [1, 2, 1]
