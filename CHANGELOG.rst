-------
Roadmap
-------

Sidekick is still a Beta-quality library in the sense that the API isn't stable and there
are a few bugs lurking (but then, as with all code). Some parts of the library are stable
and are very unlikely to change or to contain bugs. If you plan to use Sidekick, please
contact the authors, inform about your intended usage and contribute to this roadmap.

1.0.x
=====

* Stabilize API


0.9.x
=====

* Small changes with deprecation warnings, when possible.
* Define a deprecation path and implement deprecation helpers.
* `import sidekick` will not be an alias to `import sidekick.api` anymore.
* Remove all undocumented features from main codebase (sidekick.experimental is for that).
* Support for the (now) experimental `sidekick.interfaces` module and `sk.apply` function.

0.8.x
=====

* Complete documentation with proper introduction to concepts and functional
  programming.
* Better integration of maybe and result types.
* Remove cruft and clean the experimental package.
* Remove all flake8 errors.
* Continuous integration with strict tests.
* Build documentation cleanly and add it to the CI.
* Create and document sidekick.collections.
* Move Union/Record to sidekick.types with other classical functional types and document it.
* Move collection types to sidekick.collections and document.
* Create sidekick.types with algebraic data types.


---------
Changelog
---------

0.8.2
=====

* Remove the legacy ``sidekick.functools`` module.
* Expose/document ``sidekick.evil``.
* Expose `sidekick.op` with minimal documentation.
* Expose and document ``sidekick.pred``.


0.8.1
=====

* Split ``sidekick.lazytools`` into ``proxy`` and ``properties`` submodules.
* Rename properties parameters to be more consistent.
* Rework zombie[cls] factory to allow instance checks.

0.8.0
=====

This is a major refactor preparing to 1.0.0

* Documentation now uses sphinx.ext.doctest instead of manuel and passes all tests.
* Moved fn and most of functools to sidekick.functions.
* Created sk.iter().
* Start changelog and roadmap.
* Refactor documentation
* Create the ``import sidekick.api as sk`` idiom.
* Move functions from ``sidekick.functools`` to ``sidekick.functions``.
* Move functions from ``sidekick.itertools`` to ``sidekick.seq``.
