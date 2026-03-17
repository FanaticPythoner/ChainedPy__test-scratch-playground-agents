"""Execute ``python -m chainedpy …`` exactly like the ``chainedpy`` console command.

This module allows ChainedPy to be executed as a module using ``python -m chainedpy``,
providing the same functionality as the ``chainedpy`` console command installed by
the package's entry-points. It serves as a simple wrapper that delegates to the main
CLI function, ensuring consistent behavior regardless of how the tool is invoked.

This pattern follows Python's standard practice for making packages executable as
modules, providing users with multiple ways to invoke the same functionality.

Note:
    This module is automatically executed when running ``python -m chainedpy``
    and provides identical functionality to the ``chainedpy`` console command.
    The module simply imports and calls the main CLI function without any
    additional processing or argument modification.

Example:
    ```bash
    # These commands are equivalent:
    chainedpy create my-project
    python -m chainedpy create my-project

    # Both will create a new ChainedPy project
    chainedpy --help
    python -m chainedpy --help
    ```

See Also:
    - [main][chainedpy.cli.main]: The main CLI entry point function
    - [chainedpy.cli][chainedpy.cli]: Complete CLI module documentation
"""
from __future__ import annotations
from chainedpy.cli import main

# @@ STEP 1: Execute main CLI function when run as module. @@
if __name__ == "__main__":             # pragma: no cover
    # Execute the main CLI function.
    main()
