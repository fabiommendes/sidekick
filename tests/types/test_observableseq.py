from sidekick import misc


class TestObservableSeq:
    dic_type = misc.ObservableSeq

    def test_observable_seq_observers(self):
        pre_events = []
        post_events = []
        clear = lambda: pre_events.clear() or post_events.clear()

        seq = misc.ObservableSeq([1, 2, 3])

        # Register events
        seq.register(
            ["pre-setitem", "pre-delitem", "pre-insert"],
            lambda i, x: pre_events.append((i, x)),
        )
        seq.register(
            ["post-setitem", "post-delitem", "post-insert"],
            lambda i, x: post_events.append((i, x)),
        )

        # Interact and check
        clear()
        seq.append(4)
        assert pre_events == post_events == [(3, 4)]

        clear()
        del seq[0]
        assert pre_events == post_events == [(0, 1)]

        clear()
        seq.insert(0, 1)
        assert pre_events == post_events == [(0, 1)]

        clear()
        seq[3] = 5
        assert pre_events == post_events == [(3, 5)]

        assert seq == [1, 2, 3, 5]
