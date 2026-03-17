"""Built-in plugins for ChainedPy.

This package contains core transformation operations, wrapper behaviors, and processors
that are automatically registered when ChainedPy is imported. These plugins provide
the standard chain methods like [then_map][chainedpy.plugins.core.then_map], [as_retry][chainedpy.plugins.wrappers.as_retry], and built-in processors
that form the foundation of the ChainedPy ecosystem.

The plugins are organized into logical modules: [core][chainedpy.plugins.core] for basic transformations,
[wrappers][chainedpy.plugins.wrappers] for decorating behaviors, and [processors][chainedpy.plugins.processors] for stateless operations.
All plugins are auto-discovered and registered through decorators when their modules
are imported.

Note:
    Plugins are automatically loaded by the main ChainedPy [__init__.py][chainedpy.__init__] module.
    User projects can extend functionality by adding plugins to their own plugins/
    directory following the same decorator patterns.

Example:
    ```python
    from chainedpy import Chain

    # Built-in plugins are automatically available
    result = await (
        Chain("hello")
        .then_map(str.upper)      # from core plugins
        .as_retry(max_attempts=3) # from wrapper plugins
        .then_process("format", param="Greeting: {}")  # from processors
    )
    ```

See Also:
    - [core][chainedpy.plugins.core]: Core transformation methods
    - [wrappers][chainedpy.plugins.wrappers]: Wrapper and decorator methods
    - [processors][chainedpy.plugins.processors]: Built-in processor collection
    - [chainedpy.register][chainedpy.register]: Registration system used by plugins
"""