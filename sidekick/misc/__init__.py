from ..lazytools import import_later as _import_later

frozendict = _import_later('.frozendict', package=__package__)
idmap = _import_later('.idmap', package=__package__)
invmap = _import_later('.invmap', package=__package__)
lazylist = _import_later('.lazylist', package=__package__)
observableseq = _import_later('.observableseq', package=__package__)
tagseq = _import_later('.tagseq', package=__package__)


class _Misc:
    _locations = {
        'FrozenKeyDict': frozendict,
        'FrozenDict': frozendict,
        'IdMap': idmap,
        'InvMap': invmap,
        'LazyList': lazylist,
        'ObservableSeq': observableseq,
        'TagSeq': tagseq,
    }
    _names = {}

    def __getattr__(self, attr):
        if attr.startswith('_'):
            raise AttributeError(attr)
        try:
            loc = self._locations[attr]
        except KeyError:
            raise AttributeError(attr)
        value = getattr(loc, attr)
        setattr(self, attr, value)
        return value


misc = _Misc()
