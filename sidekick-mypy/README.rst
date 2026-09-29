=================
``sidekick.mypy``
=================

This module defines some MyPy plugins to support Sidekick's functional idioms. 
This separate module does not need to be installed in production, but helps MyPy
make better type inference with some Sidekick functions and types.

:: 
    # In setup.cfg or mypy.ini:
    [mypy]
    plugins =
        sidekick.mypy.plugin