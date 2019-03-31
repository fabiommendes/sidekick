===================
Miscellaneous types
===================

Sidekick also implement a few straightforward types.

FrozenDict
==========

:cls:`FrozenDict` implements a straightforward immutable dictionary variant.
It differs from ``mappingproxy`` types since it owns its data, instead of
proxying it to another mapping. More importantly, FrozenDict are hashable and
thus can be used as elements in sets and keys in other mappings.

:cls:`FrozenKeyDict` is intermediate type in which keys are fixed, but values
can be mutated.
