try:
    import hypothesis

    del hypothesis
except ImportError as exc:
    msg = "You must install hypothesis (pip install hypothesis) to use this module."
    raise RuntimeError(msg) from exc

from .tree import leaves, trees, shallow_trees
from .base import atoms, identifiers, kwargs, fcall, AtomT
