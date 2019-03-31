from collections.abc import MutableSequence

from ..core import extract_function

SIGNALS = {'pre-setitem', 'pre-delitem', 'pre-insert', 'post-setitem',
           'post-delitem', 'post-insert'}
ARGUMENTS = set(map(lambda x: x.replace('-', '_'), SIGNALS))


class ObservableSeq(MutableSequence):
    """
    A list that implements the "Observer" pattern. It executes callback
    functions before performing changes such as insertions, deletions and
    changing items. Callbacks functions can also prevent these modifications
    from happening.
    """

    def __init__(self, data, **kwargs):
        self.data = data
        self.pre_setitem = []
        self.post_setitem = []
        self.pre_delitem = []
        self.post_delitem = []
        self.pre_insert = []
        self.post_insert = []

        # Register callbacks
        for k, v in kwargs.items():
            if k in ARGUMENTS:
                callbacks = getattr(self, k)
                if callable(v):
                    callbacks.append(extract_function(v))
                else:
                    callbacks.extend(map(extract_function, v))
            else:
                raise TypeError(f'invalid parameter: {k}')

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, repr(self.data))

    def __delitem__(self, idx):
        value = self.data[idx]
        if self.trigger_pre_delitem(idx, value):
            del self.data[idx]
            self.trigger_post_delitem(idx, value)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return type(self)(self.data[idx], copy=False)
        return self.data[idx]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __setitem__(self, idx, value):
        if self.trigger_pre_setitem(idx, value):
            self.data[idx] = value
            self.trigger_post_setitem(idx, value)

    def __contains__(self, idx):
        return idx in self.data

    __eq__ = lambda x, y: x.data == y
    __lt__ = lambda x, y: x.data < y
    __gt__ = lambda x, y: x.data > y
    __le__ = lambda x, y: x.data <= y
    __ge__ = lambda x, y: x.data >= y

    def insert(self, idx, value):
        if self.trigger_pre_insert(idx, value):
            self.data.insert(idx, value)
            self.trigger_post_insert(idx, value)

    def append(self, value):
        idx = len(self)
        if self.trigger_pre_insert(idx, value):
            self.data.append(value)
            self.trigger_post_insert(idx, value)

    def _trigger_pre_event(self, callbacks, *args):
        result = True
        for func in callbacks:
            try:
                func(*args)
            except StopIteration:
                result = False
        return result

    def _trigger_post_event(self, callbacks, *args):
        for func in callbacks:
            func(*args)

    def trigger_pre_insert(self, idx, value):
        """
        Run all callbacks registered to 'pre-setitem' and return True if
        modification should be executed and False otherwise.
        """
        return self._trigger_pre_event(self.pre_insert, idx, value)

    def trigger_post_insert(self, idx, value):
        """
        Called just after insertions.
        """
        return self._trigger_post_event(self.post_insert, idx, value)

    def trigger_pre_setitem(self, idx, value):
        """
        Run all callbacks registered to 'pre-setitem' and return True if
        modification should be executed and False otherwise.
        """
        return self._trigger_pre_event(self.pre_setitem, idx, value)

    def trigger_post_setitem(self, idx, value):
        """
        Called just after an item is modified.
        """
        return self._trigger_post_event(self.post_setitem, idx, value)

    def trigger_pre_delitem(self, idx, value):
        """
        Run all callbacks registered to 'pre-delitem' and return True if
        deletion should be executed and False otherwise.
        """
        return self._trigger_pre_event(self.pre_delitem, idx, value)

    def trigger_post_delitem(self, idx, value):
        """
        Called just after an item is deleted.
        """
        return self._trigger_post_event(self.post_delitem, idx, value)

    def register(self, signal, callback, clear=False):
        """
        Register callback for executing at the given signal.

        Signal can be any of 'pre-setitem', 'pre-delitem', 'pre-insert',
        'post-setitem', 'post-delitem', 'post-insert'.
        """
        if isinstance(signal, (tuple, list)):
            for signal in signal:
                self.register(signal, callback, clear)
            return

        if signal not in SIGNALS:
            raise ValueError('signal not recognized: %r' % signal)

        callbacks = getattr(self, signal.replace('-', '_'))
        if clear:
            callbacks.clear()
        callbacks.append(callback)
