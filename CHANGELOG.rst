-------
Roadmap
-------

Sidekick is still a Beta-quality library in the sense that the API isn't stable and there
are a few bugs lurking (but then, as with all code). Some parts of the library are stable
and are very unlikely to change. If you plan to use Sidekick, please contact the authors,
inform about your usage and contribute to this roadmap.

1.0.0
=====

* Stabilize API
* Create module ``sidekick.collections``
* Move functions from ``sidekick.itertools`` to ``sidekick.iterators``
* Override module types to allow lazy imports

---------
Changelog
---------


0.8.0
=====

This is a major refactor preparing to 1.0.0

* Documentation now uses sphinx.ext.doctest instead of manuel and passes all tests.
* Moved fn and most of functools to sidekick.functions.
* Created sk.iter().
* Start changelog and roadmap.
* Refactor documentation
* Create the ``import sidekick.api as sk`` idiom.
* Move functions from ``sidekick.functools`` to ``sidekick.functions``
* Move functions from ``sidekick.itertools`` to ``sidekick.seq``
