The Babylonian method
=====================

Many algorithms can be formulated as a sequence of approximations by some
transformation function. We will illustrate with a simple example of computing
square roots, but the general idea can be expanded to many other domains.

Let us recall the Babylon method to compute square roots. Consider R to be the
square root of x. We will approximate R by a sequence of r0, r1, r2, ... etc that
starts with some guess and converges gradually to the correct value using the
formula

    r' = 0.5 * (r + x / r)

This formula was allegedly used by Babylonian mathematicians thousands of years
ago, and can be derived with modern mathematics as an instance of Newton's
method for finding roots.

Let us define:

>>> x = 2
>>> f = lambda r: 0.5 * (r + x / r)

By iterating f, we obtain progressively better approximations of square root
of x.

>>> sk.iterate(f, x)
sk.iter([2.0, 1.5, ...])

When should we stop? There are several workable criteria and we can play around a little
bit. We may fix the number of iterations...

>>> n_iter = 5
>>> sk.iterate(f, x)[:n_iter].last()
?

... or define a tolerance...

>>> tol = 1e-6
>>> stop = lambda r: abs(r * r - x) / x < tol
>>> sk.iterate(f, x).take(stop).last()
?

We can even mix the results by selecting a minimum and maximum number of 
iterations, different convergence criteria, and more. Those are the building 
can be used to create a function with a custom implementation of square 
roots and are very easy to move around and experiment with.

>>> def sqrt(x):
...     max_iter = 20
...     min_iter = 5
...     f = lambda r: 0.5 * (r + x / r)
...     return sk.iterate(f, x)[min_iter:max_iter].last()

Very nice, but this pattern can be generalized further to any function that
can be handled by Newton's method.

>>> @sk.curry(2)
... def newton(update, x, min_iter=5, max_iter=10):
...     f = sk.partial(update, x)
...     return sk.iterate(f, x)[min_iter:max_iter].last()

From this, we easily create a collection of functions, reusing bits and pieces

>>> sqrt = newton(lambda x, r: 0.5 * (r + x / r))
>>> acos = newton(lambda x, r: 0.5 * (r + x / r))
>>> atan = newton(lambda x, r: 0.5 * (r + x / r))

This illustrates good features of functional code: we bundle together small
functions and compose them using very simple interfaces. Passing functions to
functions achieve a high degree of flexibility and code reuse without involving
ad hoc abstractions.