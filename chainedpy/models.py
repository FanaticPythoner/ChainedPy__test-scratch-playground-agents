"""ChainedPy data models and types.

This module contains data classes and type definitions used across the ChainedPy codebase.
It is designed to avoid circular imports by providing shared types that can be imported
by multiple modules without creating dependency cycles.

The models defined here represent core data structures used throughout ChainedPy,
including project configuration, chain metadata, and other shared data types.
All models are designed to be immutable and type-safe.

Note:
    This module intentionally has minimal dependencies to avoid circular imports.
    It should only import from the standard library and typing modules.

Example:
    ```python
    from chainedpy.models import ProjectConfig

    # Create project configuration
    config = ProjectConfig(
        base_project="chainedpy",
        summary="My custom ChainedPy project"
    )

    print(f"Base: {config.base_project}")
    print(f"Summary: {config.summary}")
    ```

See Also:
    - [ProjectConfig][chainedpy.models.ProjectConfig]: Project configuration model
    - [chainedpy.project][chainedpy.project]: Project management functionality
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
from typing import NamedTuple

# @@ STEP 2: Import third-party modules. @@
# (none)

# @@ STEP 3: Import internal constants. @@
# (none)

# @@ STEP 4: Import ChainedPy services. @@
# (none)

# @@ STEP 5: Import ChainedPy internal modules. @@
# (none)

# @@ STEP 6: Import TYPE_CHECKING modules. @@
# (none)


class ProjectConfig(NamedTuple):
    """Configuration for a ChainedPy project.

    This immutable data structure holds the essential configuration
    information for a ChainedPy project, including inheritance and
    descriptive metadata.

    :param base_project: Name of the base project to inherit from.
    :type base_project: [str][str]
    :param summary: Project summary description.
    :type summary: [str][str]

    Example:
        ```python
        from chainedpy.models import ProjectConfig

        # Create configuration for a new project
        config = ProjectConfig(
            base_project="chainedpy",
            summary="Email processing chain project"
        )

        # Access configuration values
        print(f"Inherits from: {config.base_project}")
        print(f"Description: {config.summary}")

        # Configurations are immutable
        # config.base_project = "other"  # This would raise an error
        ```

    See Also:
        - [chainedpy.project][chainedpy.project]: Project management using this configuration
        - [chainedpy.services.project_file_service][chainedpy.services.project_file_service]: Service for reading/writing project configs
    """
    base_project: str
    summary: str
