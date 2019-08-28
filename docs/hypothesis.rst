==================
Hypothesis testing
==================

Sidekick uses and integrates with the excellent Hypothesis_ library for property-based
testing. Hypothesis lets you parametrize tests using strategies that often uncover
bugs in the dark corner cases of your code. The basic idea is that you create recipes
(or strategies, in Hypothesis nomenclature) to create random inputs to your functions
and check if some invariants hold for a variety of inputs. This is often makes writing
tests easier and more effective at finding subtle bugs.

.. _Hypothesis: https://hypothesis.works

Sidekick uses Hypothesis internally and also exposes and documents its own strategies.
This document showcases the implemented strategies and their options.


Generic strategies
==================

Strategies in this category are not bound to any Sidekick type, but are used internally
to compose with other strategies. You can use them

.. automodule:: hypothesis.base
    :members: