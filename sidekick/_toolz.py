try:
    from cytoolz import *
    import cytoolz.curried as curried
except ImportError:
    try:
        from toolz import *
        import toolz.curried as curried
    except ImportError:
        import sys as _sys

        def __getattr__(attr: str) -> callable:
            def fn(*args, **kwargs):
                raise RuntimeError("you must install toolz or cytoolz.")

            fn.__name__ = fn.__qualname__ = attr
            globals()[attr] = fn
            return fn

        class _Lazy:
            def __getattr__(self, attr: str) -> callable:
                fn = __getattr__("curried." + attr)
                setattr(self, attr, fn)
                return fn

        curried = _Lazy()
        if _sys.version_info < (3, 7):
            _mod = _Lazy()
            _mod.curried = curried
            _sys.modules["sidekick._toolz"] = _mod
