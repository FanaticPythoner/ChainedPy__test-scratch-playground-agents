"""ChainedPy - A fluent, type-safe chaining library for Python.

This module provides the main public API for ChainedPy, including the core [Chain][chainedpy.chain.Chain] class,
decorators for method registration, processors, and exception handling. It serves as the
primary entry point for users of the ChainedPy library, automatically loading plugins
and exposing all necessary components for fluent method chaining.

The module automatically imports all plugin modules to ensure decorators are registered
and processors are available. It provides a clean, organized API surface that follows
the principle of least surprise for library users.

Note:
    This module automatically loads all plugins from the [chainedpy.plugins][chainedpy.plugins] package
    to ensure all decorators are properly registered at import time. This ensures that all
    chain methods and processors are available immediately upon importing ChainedPy.

Example:
    ```python
    from chainedpy import Chain

    # Basic chain usage
    result = await (
        Chain("hello world")
        .then_map(str.upper)
        .then_map(lambda s: s.replace(" ", "_"))
    )

    assert result == "HELLO_WORLD"
    ```

See Also:
    - [Chain][chainedpy.chain.Chain]: The core chaining class
    - [then][chainedpy.register.then]: Decorator for registering chain methods
    - [as_][chainedpy.register.as_]: Decorator for registering transformation methods
    - [processor][chainedpy.register.processor]: Decorator for registering processors
    - [Proc][chainedpy.plugins.processors.Proc]: Built-in processor collection
"""

# @@ STEP 1: Import standard library modules. @@
from importlib import import_module
import pathlib
import pkgutil

# @@ STEP 2: Import core components. @@
from .chain     import Chain
from .register  import then, as_, processor
from .link      import Processor   # For user import convenience.
from .exceptions import (
    ChainError, ValidationError, RetryExhausted, TimeoutExpired,
    ProcessorError, ConcurrencyError, CacheError, ExtensibilityError,
    FilesystemServiceError, ASTServiceError, ProjectValidationError,
    GitignoreServiceError, RemoteChainServiceError, StubGenerationError,
    ProjectRemoteChainServiceError, ProjectLifecycleError, ChainTraversalError,
    ProjectFileServiceError, CredentialServiceError, TemplateServiceError,
    ShellIntegrationError
)
from .project import set_global_project

# @@ STEP 3: Auto-import plugin modules. @@
# Auto-import every module in chainedpy.plugins to ensure decorators run.
_pkg_path = pathlib.Path(__file__).with_suffix('').parent / "plugins"
for mod in pkgutil.iter_modules([str(_pkg_path)]):
    # Import each plugin module to trigger decorator registration.
    import_module(f"chainedpy.plugins.{mod.name}")

# @@ STEP 4: Import processors after plugins are loaded. @@
# Import Proc after plugins are loaded to ensure all processors are available.
# This import must happen after the plugin auto-import loop above.
from .plugins.processors import Proc  # noqa: E402

# @@ STEP 5: Define public API exports. @@
__all__ = (
    "Chain", "then", "as_", "processor", "Processor", "Proc",
    "ChainError", "ValidationError", "RetryExhausted", "TimeoutExpired",
    "ProcessorError", "ConcurrencyError", "CacheError", "ExtensibilityError",
    "FilesystemServiceError", "ASTServiceError", "ProjectValidationError",
    "GitignoreServiceError", "RemoteChainServiceError", "StubGenerationError",
    "ProjectRemoteChainServiceError", "ProjectLifecycleError", "ChainTraversalError",
    "ProjectFileServiceError", "CredentialServiceError", "TemplateServiceError",
    "ShellIntegrationError", "set_global_project"
)
"""[tuple][tuple][[str][str], ...]: Public API exports for the ChainedPy library.

This tuple defines all the symbols that are exported when using `from chainedpy import *`.
It includes the core [Chain][chainedpy.chain.Chain] class, decorators for method registration,
processors, all exception classes, and utility functions. The exports are organized to provide
a clean, comprehensive API surface for library users.

:type: [tuple][tuple][[str][str], ...]
"""
