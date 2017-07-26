import operator as op


class predicate:
    """
    A predicate function.
    """

    __slots__ = ('fn',)
    __name__ = property(lambda x: x.fn.__name__)

    def __init__(self, function):
        self.fn = function

    def __call__(self, x):
        return self.fn(x)

    def __or__(self, other):
        other = self._other_fn
        return predicate(lambda x: self.fn(x) or other(x))

    def __ror__(self, other):
        other = self._other_fn
        return predicate(lambda x: other(x) or self.fn(x))

    def __and__(self, other):
        other = self._other_fn
        return predicate(lambda x: self.fn(x) and other(x))

    def __rand__(self, other):
        other = self._other_fn
        return predicate(lambda x: other(x) and self.fn(x))

    def __not__(self):
        other = self._other_fn
        return predicate(op.not_(self.fn))

    @staticmethod
    def _other_fn(other):
        return other.fn if isinstance(other, predicate) else other


def typeof(cls):
    """
    Return a predicate function that checks if argument is an instance of a class.
    """
    return predicate(lambda x: isinstance(x, cls))


def valueof(value):
    """
    Return a predicate function that checks if the argument is the given value. 
    """
    return predicate(lambda x: x is value)


def anyof(*predicates):
    """
    Return a new predicate that performs an logic AND to all predicate 
    functions.
    """
    return predicate(lambda x: any(f(x) for f in predicates))


def allof(*predicates):
    """
    Return a new predicate that performs an logic ALL to all predicate 
    functions.
    """
    return predicate(lambda x: all(f(x) for f in predicates))

isnone = valueof(None)
istrue = valueof(True)
isfalse = valueof(False)


#
# Numeric
#
isodd = lambda x: x % 2 == 1
iseven = lambda x: x % 2 == 0
ispositive = lambda x: x >= 0
isnegative = lambda x: x <= 0
isnonzero = lambda x: x != 0
iszero = lambda x: x == 0


class cond:
    """
    Conditional pipeline.

    It creates a function that takes a predicate and a true and false
    branches. The resulting function executes either branch depending on the
    value of the predicate.
    """

    def __init__(self, predicate, true=lambda: None, false=lambda: None):
        self.predicate = predicate
        self._true = true
        self._false = false

    def __call__(self, x):
        if self.predicate(x):
            return self.true(x)
        else:
            return self.false(x)

    def __rshift__(self, other):
        true, false = self._true, self._false
        return cond(
            self.predicate, 
            lambda x: other(true(x)), 
            lambda x: other(false(x)),
        )
        
    def __rrshift__(self, other):
        true, false = self._true, self._false
        return cond(
            self.predicate, 
            lambda x: true(other(x)), 
            lambda x: false(other(x)),
        )

    def true(self, true):
        """
        Sets the function for the True branch of the pipeline.
        """
        return cond(self.predicate, true, self.false)
    
    def false(self, false):
        """
        Sets the function for the False branch of the pipeline.
        """
        return cond(self.predicate, self.true, false)


if __name__ == __main__:
    f = (
        cond(isnone | isfalse)
            .true(
                foo >> bar >> baz
            )
            .false(
                const(None)
            )
    )

    (
        cond(cond)
            .true(x)
            .false(y)
    )

    cond(cond, true=x, false=y)

