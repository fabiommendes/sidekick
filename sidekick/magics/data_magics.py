from .base_magics import DataMagic, pure, impure


class S(DataMagic, type=set):
    """
    Magic object for set operations.
    """
    _meta = {
        'methods': [
            *map(pure(arity=1), ['copy']),
            *map(pure(arity=2), ['intersection', 'symmetric_difference', 'union']),
            *map(pure(flip=True), ['isdisjoint', 'issubset', 'issuperset', 'difference']),
            *map(impure(flip=True), [
                'add', 'difference_update', 'discard', 'intersection_update',
                'remove', 'pop', 'symmetric_difference_update', 'update']),
            *map(impure(arity=1), ['clear']),
        ],
    }


class D(DataMagic, type=dict):
    """
    Magic object for dict operations.
    """
    _meta = {
        'methods': [
            *map(pure(flip=True), ['get']),
        ]
    }


class T(DataMagic, type=str):
    """
    Magic object for text operations.
    """

    _meta = {
        'methods': [
            *map(pure(flip=True), ['split'])
        ],
    }


class B(DataMagic, type=bytes):
    """
    Magic object for bytestring operations
    """

    _meta = {
        'methods': T._meta['methods'],
    }

    def convert(self, obj):
        try:
            return bytes(obj)
        except TypeError:
            return str(obj).encode('utf8')
