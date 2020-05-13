import operator as op

from .node_classes import Leaf
from .node_sexpr import SExpr


class Transform:
    """
    Transformer class for tree nodes.

    Args:
        node_class (default=SExpr):
            Class or callable used to construct nodes. Function is called with
            node_class(tag, children, **attrs).
        leaf_class (default=Leaf):
            Class for nodes that are considered to be leaves.
        methods:
            Optional mapping of tag names to transformer methods. Usually this
            dictionary is filled.
        default:
            Default method used to transform nodes not declared as methods or
            entries in the methods dictionary.
        tag:
            A method that receives a node and return the corresponding tag. The
            default implementation assumes SExpr nodes and just return the
            .tag attribute.
    """

    def __init__(self, **kwargs):
        methods = {k: getattr(self, k) for k in dir(self) if not k.startswith("_")}
        if "methods" in kwargs:
            methods = {**kwargs.pop("methods", {}), **methods}
        self._methods = methods
        self._leaf_class = kwargs.pop("leaf_class", getattr(self, "leaf_class", Leaf))
        self._node_class = kwargs.pop("node_class", getattr(self, "node_class", SExpr))
        self._default = kwargs.pop("default", lambda x: x.copy())
        self._tag = kwargs.pop("tag", op.attrgetter("tag"))
        if kwargs:
            raise TypeError(f"invalid argument: {next(iter(kwargs))}")

    def __call__(self, tree):
        methods = self._methods
        dispatch = methods.__getitem__
        leaf = self._leaf_class
        node = self._node_class
        default = self._default
        get_tag = self._tag

        def transform(x):
            if isinstance(x, leaf):
                return x.copy()
            tag = get_tag(x)
            children = list(map(transform, x.children))
            new_x = node(tag, children, **x.attrs)
            try:
                fn = dispatch(tag)
            except KeyError:
                fn = methods[tag] = default
            return fn(new_x)

        return transform(tree)

    def transform(self, tree):
        """
        Call transformer. This method exists for compatibility with Lark
        transformers. The idiomatic way to use a transformer is to call it
        as a function.
        """
        return self(tree)


class TransformArgs(Transform):
    """
    Like Transform, but the transform methods receive children as positional
    arguments and attributes as keyword arguments.
    """

    def __init__(self, **kwargs):
        node = kwargs.get("node_class", SExpr)
        kwargs.setdefault("default", lambda tag, *xs, **kws: node(tag, xs, **kws))
        super().__init__(**kwargs)

    def __call__(self, tree):
        dispatch = self._methods.__getitem__
        leaf = self._leaf_class
        default = self._default

        def transform(x):
            if isinstance(x, leaf):
                return x.value
            tag = x.tag
            args = map(transform, x.children)
            try:
                fn = dispatch(tag)
            except KeyError:
                return default(tag, *args, **x.attrs)
            else:
                return fn(*args, **x.attrs)

        return transform(tree)
