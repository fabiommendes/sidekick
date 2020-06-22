from sidekick import fn, Seq, Func


@fn.curry(2)
def top_k(k: int, seq: Seq, *, key: Func = None) -> tuple:
    """
    Find the k largest elements of a sequence.

    Examples:
        >>> top_k(3, "hello world") | L
        ['w', 'r', 'o']
    """
    return toolz.topk(k, seq, key)
