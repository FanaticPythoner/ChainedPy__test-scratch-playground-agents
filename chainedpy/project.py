"""ChainedPy Project Management Utilities.

This module provides utility functions that manipulate *projects* - stand-alone ChainedPy plugin
collections that live outside the core library. Projects enable users to create custom
chain implementations with their own methods and processors while maintaining compatibility
with the core ChainedPy ecosystem.

The module handles project creation, configuration management, activation/deactivation,
and integration with shell environments. All functions maintain immutability and avoid
global state mutations unless explicitly requested through [set_global_project][chainedpy.project.set_global_project].

Note:
    Nothing in this module mutates global state **unless** the caller explicitly invokes
    [set_global_project][chainedpy.project.set_global_project]. All other operations are pure functions
    that return new state without side effects.

Example:
    ```python
    from chainedpy.project import (
        create_project, activate_project, get_active_project
    )
    from pathlib import Path

    # Create a new project
    project_path = Path("./my_project")
    create_project(
        name="my_project",
        dest=project_path,
        base_project="chainedpy",
        summary="My custom chain project"
    )

    # Activate the project
    activate_project(project_path)

    # Check active project
    active = get_active_project()
    print(f"Active project: {active}")
    ```

See Also:
    - [set_global_project][chainedpy.project.set_global_project]: Function that modifies global state
    - [chainedpy.services.project_lifecycle][chainedpy.services.project_lifecycle]: Project lifecycle management
    - [chainedpy.services.shell_integration][chainedpy.services.shell_integration]: Shell integration utilities
"""
from __future__ import annotations

import importlib
import inspect
import os
import re
import sys
from pathlib import Path
from types import ModuleType

from chainedpy.services.logging_service import get_logger


# Import constants for centralized string management
from chainedpy.constants import (
    # Environment variables
    ENV_ACTIVE_PROJECT, ENV_PROJECT_NAME,
    # File names and extensions
    INIT_FILE_NAME, CONFIG_FILE_NAME, CHAIN_FILE_SUFFIX,
    # Directory structure
    PLUGINS_DIR, DEFAULT_BASE_PROJECT, DEFAULT_SUMMARY_FORMAT,
    # File paths
    ACTIVE_PROJECT_FILE,
    # URL patterns
    URL_SCHEME_SEPARATOR,
    # Import constants
    BASE_CHAIN_IMPORT, TEMPLATE_BASE_IMPORT_LOCAL, PYTHON_EXTENSION, CHAIN_CLASS_NAME,
    # Message templates
    MSG_ERROR_PREFIX, TEMPLATE_STALE_PROJECT_WARNING, TEMPLATE_STALE_PROJECT_CLEANUP_SUCCESS,
    # Configuration keys
    CONFIG_KEY_BASE_PROJECT, CONFIG_KEY_SUMMARY,
    # Logging messages
    LOG_CONFIG_UPDATED, LOG_FAILED_WRITE_ACTIVE_PROJECT, LOG_FAILED_READ_ACTIVE_PROJECT,
)

# Import filesystem utilities for uniform fsspec-based operations
from chainedpy.services import filesystem_service as fs_utils

# Import services for compartmentalized functionality
from chainedpy.services.shell_integration import (
    generate_activation_script,
    generate_deactivation_script,
    initialize_shell_integration
)
from chainedpy.services.stub_generation_service import (
    update_project_stub
)
from chainedpy.services.template_service import (
    create_plugin_file
)

import chainedpy.chain as _core_chain_mod
from chainedpy.models import ProjectConfig
import chainedpy
from chainedpy.services.template_service import render_template
from chainedpy.services.chain_traversal_service import traverse_project_chain, format_project_chain, ChainTraversalError
from chainedpy.services.project_lifecycle import create_project as lifecycle_create_project

__all__ = [
    "create_project",
    "set_global_project",
    "generate_activation_script",
    "generate_deactivation_script",
    "initialize_shell_integration",
    "activate_project",
    "deactivate_project",
    "list_projects",
    "get_active_project",
    "update_project_stub",
    "create_then_plugin",
    "create_as_plugin",
    "create_processor",
    "show_project_chain",
]

# ─── SESSION-BASED PROJECT MANAGEMENT ──────────────────────────────────────
# Use constants directly instead of redundant variables

def activate_project(project_path: Path | str) -> None:
    """Activate a project for the current session (like conda activate).

    Example:
        ```python
        from chainedpy.project import activate_project, get_active_project, create_project
        from pathlib import Path
        import shutil

        # Create a test project
        project_path = create_project(
            Path("test_project"),
            "test_project",
            summary="Test project for activation"
        )

        # Activate the project
        activate_project(project_path)

        # Verify activation
        active = get_active_project()
        assert active == project_path.resolve()

        # Activate with string path
        activate_project(str(project_path))
        active = get_active_project()
        assert active == project_path.resolve()

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project to activate.
    :type project_path: [Path][pathlib.Path] | [str][str]
    :raises FileNotFoundError: If project path is invalid or not a ChainedPy project.
    """
    # @@ STEP 1: Normalize and validate project path. @@
    project_path = Path(project_path).expanduser().resolve()
    if project_path.is_file():
        project_path = project_path.parent
    if not (project_path / "__init__.py").exists():
        raise FileNotFoundError(f"{project_path} is not a Python package")

    # @@ STEP 2: Set environment variables for current session. @@
    os.environ[ENV_ACTIVE_PROJECT] = str(project_path)
    os.environ[ENV_PROJECT_NAME] = project_path.name

    # @@ STEP 3: Store active project in persistent file for subprocess access. @@
    try:
        fs_utils.write_text(str(ACTIVE_PROJECT_FILE), str(project_path))
    except (OSError, PermissionError):
        get_logger().warning(LOG_FAILED_WRITE_ACTIVE_PROJECT.format(ACTIVE_PROJECT_FILE))
        # If we can't write the file, continue anyway (environment variable still works for shell).
        pass

    # @@ STEP 4: Also set global project for immediate use. @@
    set_global_project(project_path)

def deactivate_project() -> None:
    """Deactivate the current project session.

    Example:
        ```python
        from chainedpy.project import activate_project, deactivate_project, get_active_project, create_project
        from pathlib import Path
        import shutil

        # Create and activate a project
        project_path = create_project(
            Path("test_project"),
            "test_project",
            summary="Test project for deactivation"
        )
        activate_project(project_path)

        # Verify project is active
        active = get_active_project()
        assert active is not None

        # Deactivate the project
        deactivate_project()

        # Verify no project is active
        active = get_active_project()
        assert active is None

        # Deactivating when no project is active should not error
        deactivate_project()

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :raises OSError: If removing persistent file fails.
    :raises PermissionError: If removing persistent file fails.
    """
    # @@ STEP 1: Remove environment variables. @@
    if ENV_ACTIVE_PROJECT in os.environ:
        del os.environ[ENV_ACTIVE_PROJECT]
    if ENV_PROJECT_NAME in os.environ:
        del os.environ[ENV_PROJECT_NAME]

    # @@ STEP 2: Remove persistent file. @@
    try:
        if ACTIVE_PROJECT_FILE.exists():
            ACTIVE_PROJECT_FILE.unlink()
    except (OSError, PermissionError):
        # If we can't remove the file, continue anyway.
        pass

def get_active_project() -> Path | None:
    """Get the currently active project path.

    Example:
        ```python
        from chainedpy.project import activate_project, get_active_project, deactivate_project, create_project
        from pathlib import Path
        import shutil

        # Initially no project is active
        active = get_active_project()
        assert active is None

        # Create and activate a project
        project_path = create_project(
            Path("test_project"),
            "test_project",
            summary="Test project for getting active"
        )
        activate_project(project_path)

        # Get active project
        active = get_active_project()
        assert active == project_path.resolve()
        assert isinstance(active, Path)

        # Deactivate and check again
        deactivate_project()
        active = get_active_project()
        assert active is None

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :return [Path][pathlib.Path] | [None][None]: Path to active project or None if no project is active.
    """
    # @@ STEP 1: First try environment variable (for shell-based activation). @@
    active_path = os.environ.get(ENV_ACTIVE_PROJECT)
    if active_path:
        project_path = Path(active_path)
        if project_path.exists() and (project_path / INIT_FILE_NAME).exists():
            return project_path
        else:
            # Project no longer exists, clean up stale state.
            _cleanup_stale_project(active_path, "environment variable")
            return None

    # @@ STEP 2: Fall back to persistent file (for subprocess activation). @@
    try:
        active_project_file_str = str(ACTIVE_PROJECT_FILE)
        if fs_utils.exists(active_project_file_str):
            active_path = fs_utils.read_text(active_project_file_str).strip()
            if active_path:
                project_path = Path(active_path)
                if project_path.exists() and (project_path / INIT_FILE_NAME).exists():
                    return project_path
                else:
                    # Project no longer exists, clean up stale state.
                    _cleanup_stale_project(active_path, "persistent file")
                    return None
    except (OSError, PermissionError, UnicodeDecodeError):
        # If we can't read the file, continue anyway.
        get_logger().warning(LOG_FAILED_READ_ACTIVE_PROJECT.format(ACTIVE_PROJECT_FILE))
        pass

    return None

def _cleanup_stale_project(project_path: str, source: str) -> None:
    """Clean up stale project state and show warning.

    :param project_path: Path to the stale project.
    :type project_path: str
    :param source: Source of the stale project reference.
    :type source: str
    """
    # @@ STEP 1: Show warning message. @@
    warning_message = render_template(TEMPLATE_STALE_PROJECT_WARNING,
                                    project_path=project_path, source=source)
    get_logger().warning(warning_message)

    # @@ STEP 2: Clean up environment variables. @@
    if ENV_ACTIVE_PROJECT in os.environ:
        del os.environ[ENV_ACTIVE_PROJECT]
    if ENV_PROJECT_NAME in os.environ:
        del os.environ[ENV_PROJECT_NAME]

    # @@ STEP 3: Clean up persistent file. @@
    try:
        if ACTIVE_PROJECT_FILE.exists():
            ACTIVE_PROJECT_FILE.unlink()
    except (OSError, PermissionError) as e:
        get_logger().warning(f"Failed to remove active project file: {e}")
        # Don't re-raise as this is cleanup - log the error but continue.

    success_message = render_template(TEMPLATE_STALE_PROJECT_CLEANUP_SUCCESS)
    get_logger().info(success_message)

def list_projects(search_paths: list[Path] | None = [Path.cwd()]) -> list[Path]:
    """List available ChainedPy projects.

    :param search_paths: Specific paths to search for projects, defaults to [Path.cwd()].
    :type search_paths: list[Path] | None, optional
    :return list[Path]: List of paths to ChainedPy projects found.
    """
    # @@ STEP 1: Initialize projects list. @@
    projects = []

    # @@ STEP 2: Search each provided path. @@
    for search_path in search_paths:
        if not search_path.exists():
            continue

        # @@ STEP 3: Look for directories with chainedpy project structure. @@
        # Search both direct children and one level deeper.
        search_dirs = [search_path]
        # Add subdirectories for deeper search.
        for item in search_path.iterdir():
            if item.is_dir():
                search_dirs.append(item)

        for search_dir in search_dirs:
            for item in search_dir.iterdir():
                if not item.is_dir():
                    continue

                # Check if it's a ChainedPy project
                if (item / INIT_FILE_NAME).exists() and (item / PLUGINS_DIR).exists():
                    chain_file = item / f"{item.name}{CHAIN_FILE_SUFFIX}"
                    if chain_file.exists():
                        projects.append(item)

    return sorted(set(projects))

def show_project_chain(project_path: Path | str | None = None) -> str:
    """Show the inheritance chain for a project."""
    
    # Determine which project to analyze
    if project_path is None:
        # Use active project
        active_project = get_active_project()
        if active_project is None:
            return "No active project found. Please activate a project or specify --project-path."
        project_path = active_project
    else:
        # Convert to Path and resolve
        project_path = Path(project_path).expanduser().resolve()
        if project_path.is_file():
            project_path = project_path.parent
        if not (project_path / INIT_FILE_NAME).exists():
            return f"{MSG_ERROR_PREFIX} {project_path} is not a Python package"

    try:
        # Traverse the project chain
        chain = traverse_project_chain(str(project_path))
        return format_project_chain(chain)

    except ChainTraversalError as e:
        return f"{MSG_ERROR_PREFIX} {e}"
    except Exception as e:
        get_logger().error(f"Unexpected error during chain traversal: {e}")
        return f"{MSG_ERROR_PREFIX} Unexpected error during chain traversal: {e}"


# ─── INTERNAL HELPERS ──────────────────────────────────────────────────────
# Configuration file handling

def _read_project_config(project_path: Path) -> ProjectConfig:
    """Read project configuration from chainedpy.yaml file using fsspec."""
    config_file = project_path / CONFIG_FILE_NAME
    config_file_str = str(config_file)
    project_name = project_path.name

    # Default values
    default_base_project = DEFAULT_BASE_PROJECT
    default_summary = DEFAULT_SUMMARY_FORMAT.format(project_name)

    if not fs_utils.exists(config_file_str):
        return ProjectConfig(base_project=default_base_project, summary=default_summary)

    try:
        # Read config using fsspec
        config_data = fs_utils.read_config(config_file_str)

        if not config_data:
            return ProjectConfig(base_project=default_base_project, summary=default_summary)

        base_project = config_data.get(CONFIG_KEY_BASE_PROJECT, default_base_project).strip()
        summary = config_data.get(CONFIG_KEY_SUMMARY, default_summary).strip()

        # Validate values
        if not base_project:
            base_project = default_base_project
        if not summary:
            summary = default_summary

        return ProjectConfig(base_project=base_project, summary=summary)

    except Exception as e:
        get_logger().error(f"Failed to read project config from {config_file}: {e}")
        get_logger().error(f"Using default configuration: base_project={default_base_project}, summary={default_summary}")
        return ProjectConfig(base_project=default_base_project, summary=default_summary)

def _validate_base_project(base_project: str, current_project_path: Path) -> None:
    """Validate that base_project is valid and doesn't create circular dependencies."""
    if base_project == DEFAULT_BASE_PROJECT:
        return  # Base ChainedPy is always valid

    # Handle remote URLs - skip local validation for remote projects
    if URL_SCHEME_SEPARATOR in base_project:
        # Remote URL - validation should be done by CLI before calling this function
        # This function only handles local path validation and circular dependency detection
        get_logger().debug(f"Skipping local validation for remote base project: {base_project}")
        return

    # Resolve base project path relative to workspace root for relative paths
    base_project_path = Path(base_project).expanduser()
    if not base_project_path.is_absolute():
        # Resolve relative paths relative to the workspace root (parent of current project)
        workspace_root = current_project_path.parent
        base_project_path = workspace_root / base_project_path
    base_project_path = base_project_path.resolve()

    # Check if base project exists and is valid
    if not base_project_path.exists():
        raise ValueError(f"Base project path does not exist: {base_project_path}")
    if not (base_project_path / INIT_FILE_NAME).exists():
        raise ValueError(f"Base project is not a Python package: {base_project_path}")

    chain_file = base_project_path / f"{base_project_path.name}{CHAIN_FILE_SUFFIX}"
    if not chain_file.exists():
        raise ValueError(f"Base project is not a ChainedPy project (missing {chain_file})")

    # Check for circular dependencies
    visited = set()
    current = base_project_path

    # Add the current project to visited set to detect if we circle back to it
    visited.add(current_project_path)

    while current:
        # Check if we've encountered this project before (circular dependency)
        if current in visited:
            if current == current_project_path:
                raise ValueError(f"Circular dependency: project {current_project_path.name} cannot extend itself directly or indirectly")
            else:
                raise ValueError(f"Circular dependency detected in project extension chain at {current}")

        visited.add(current)

        # Read the base project's config to check its base_project
        try:
            config = _read_project_config(current)
            if config.base_project == DEFAULT_BASE_PROJECT:
                break  # Reached the root - this is valid

            next_base = Path(config.base_project)
            if not next_base.is_absolute():
                # Resolve relative paths relative to the workspace root (parent of current project)
                # All projects should be siblings in the same workspace
                workspace_root = current_project_path.parent
                next_base = workspace_root / next_base
                next_base = next_base.resolve()
            current = next_base

        except Exception as e:
            get_logger().error(f"Failed to read config for base project {current}: {e}")
            get_logger().warning(f"Cannot validate circular dependencies for {current}, assuming valid")
            break

def _write_project_config(project_path: Path, base_project: str, summary: str) -> None:
    """Write project configuration to chainedpy.yaml file using fsspec."""
    config_file = project_path / CONFIG_FILE_NAME
    config_file_str = str(config_file)

    # Normalize the base_project path to be relative to the workspace root
    if base_project != DEFAULT_BASE_PROJECT:
        base_project_path = Path(base_project).expanduser()

        # Only normalize if it's an absolute path; preserve relative paths as-is
        if base_project_path.is_absolute():
            base_project_path = base_project_path.resolve()
            workspace_root = project_path.parent
            try:
                # Convert to relative path from workspace root
                relative_path = base_project_path.relative_to(workspace_root)
                base_project = f"./{relative_path}"
            except ValueError:
                # If paths are not relative (different drives/roots), keep absolute path
                base_project = str(base_project_path)
        # If already relative, keep as-is

    # Write config using fsspec
    fs_utils.write_config(config_file_str, base_project, summary)


# ─── PUBLIC API: create new project scaffold ────────────────────────────────
def create_project(dest: Path, name: str, *, base_project: str = DEFAULT_BASE_PROJECT, summary: str | None = None) -> Path:
    """Create a new ChainedPy project using the project lifecycle service.

    :param dest: Destination directory for the project.
    :type dest: Path
    :param name: Name of the project.
    :type name: str
    :param base_project: Base project to inherit from, defaults to DEFAULT_BASE_PROJECT.
    :type base_project: str, optional
    :param summary: Project summary, defaults to None.
    :type summary: str | None, optional
    :return Path: Path to the created project.
    """
    # @@ STEP 1: Create project using lifecycle service. @@
    project_path = lifecycle_create_project(dest, name, base_project, summary)

    # @@ STEP 2: Generate stub file after project creation. @@
    update_project_stub(project_path, silent=True)

    # @@ STEP 3: Set global project for immediate use. @@
    set_global_project(project_path)

    return project_path

# ─── PUBLIC API: patch global Chain import ─────────────────────────────────
def set_global_project(project_path: Path | str) -> None:
    """Set a project as the global Chain import (monkey-patch).

    :param project_path: Path to the project to set as global.
    :type project_path: Path | str
    :raises FileNotFoundError: If project path is invalid or not a Python package.
    :raises TypeError: If Chain class is not found or invalid.
    """
    # @@ STEP 1: Normalize and validate project path. @@
    project_path = Path(project_path).expanduser().resolve()
    if project_path.is_file():
        project_path = project_path.parent
    if not (project_path / INIT_FILE_NAME).exists():
        raise FileNotFoundError(f"{project_path} is not a Python package")

    # @@ STEP 2: Import project package and chain module. @@
    package_name = project_path.name
    if str(project_path.parent) not in sys.path:
        sys.path.insert(0, str(project_path.parent))

    importlib.import_module(package_name)
    chain_module_suffix = CHAIN_FILE_SUFFIX.replace(PYTHON_EXTENSION, '')
    chain_mod: ModuleType = importlib.import_module(f"{package_name}.{package_name}{chain_module_suffix}")

    # Project plugins are auto-imported by the chain module, no need to call init_plugins.
    # init_plugins is for core library plugins, not project plugins.

    # @@ STEP 3: Get project Chain class and validate. @@
    project_chain_cls = getattr(chain_mod, CHAIN_CLASS_NAME)
    if not inspect.isclass(project_chain_cls):
        raise TypeError(f"{package_name}_chain.Chain is not a class")

    # @@ STEP 4: Monkey-patch the global Chain import. @@
    chainedpy.Chain = project_chain_cls  # type: ignore[attr-defined]
    _core_chain_mod.Chain = project_chain_cls  # type: ignore[attr-defined]
    sys.modules["chainedpy.chain"].Chain = project_chain_cls  # type: ignore[attr-defined]

# ─── PUBLIC API: update project base ───────────────────────────────────────
def update_project_base(project_path: Path | str, new_base_project: str, new_summary: str | None = None) -> None:
    """Update the base project that this project extends.

    :param project_path: Path to the project to update.
    :type project_path: Path | str
    :param new_base_project: New base project to extend.
    :type new_base_project: str
    :param new_summary: New project summary, defaults to None.
    :type new_summary: str | None, optional
    :raises ValueError: If base project is invalid or creates circular dependencies.
    """
    # @@ STEP 1: Normalize project path and get package name. @@
    project_path = Path(project_path).expanduser().resolve()
    package_name = project_path.name

    # @@ STEP 2: Read current config. @@
    current_config = _read_project_config(project_path)

    # @@ STEP 3: Use current summary if new one not provided. @@
    if new_summary is None:
        new_summary = current_config.summary

    # @@ STEP 4: Validate the new base project (this will check for circular dependencies). @@
    # Only validate if it's not chainedpy and if it's a path.
    if new_base_project != DEFAULT_BASE_PROJECT:
        try:
            _validate_base_project(new_base_project, project_path)
        except Exception as e:
            raise ValueError(f"Invalid base project: {e}") from e

    # @@ STEP 5: Update configuration file. @@
    try:
        _write_project_config(project_path, new_base_project, new_summary)
        get_logger().info(LOG_CONFIG_UPDATED.format(project_path / CONFIG_FILE_NAME))

        # || S.S. 5.1: Verify the config was actually written. ||
        written_config = _read_project_config(project_path)

        # || S.S. 5.2: Normalize the expected base_project for comparison using same logic as _write_project_config. ||
        expected_base_project = new_base_project
        if new_base_project != DEFAULT_BASE_PROJECT:
            base_project_path = Path(new_base_project).expanduser()

            # Only normalize if it's an absolute path; preserve relative paths as-is.
            if base_project_path.is_absolute():
                base_project_path = base_project_path.resolve()
                workspace_root = project_path.parent
                try:
                    relative_path = base_project_path.relative_to(workspace_root)
                    expected_base_project = f"./{relative_path}"
                except ValueError:
                    expected_base_project = str(base_project_path)
            # If already relative, keep as-is.

        if written_config.base_project != expected_base_project or written_config.summary != new_summary:
            raise RuntimeError(f"Config verification failed: expected base_project={expected_base_project}, summary={new_summary}, got {written_config}")

    except Exception as e:
        get_logger().error(f"Failed to update configuration file: {e}")
        raise RuntimeError(f"Failed to update configuration file: {e}") from e

    # @@ STEP 6: Regenerate chain.py file with new base import. @@
    chain_py = project_path / f"{package_name}{CHAIN_FILE_SUFFIX}"

    # || S.S. 6.1: Determine base import based on new base project. ||
    if new_base_project == DEFAULT_BASE_PROJECT:
        base_import = BASE_CHAIN_IMPORT
    else:
        # Custom project - import from its chain module.
        base_project_path = Path(new_base_project)
        if not base_project_path.is_absolute():
            base_project_path = project_path.parent / base_project_path
            base_project_path = base_project_path.resolve()
        base_project_name = base_project_path.name
        base_import = render_template(TEMPLATE_BASE_IMPORT_LOCAL, base_project_name=base_project_name).strip()

    # || S.S. 6.2: Generate chain content using template. ||
    chain_content = render_template("project/chain_py.j2", base_import=base_import)

    try:
        chain_py_str = str(chain_py)
        fs_utils.write_text(chain_py_str, chain_content)

        # Verify the chain.py file was written correctly
        written_chain_content = fs_utils.read_text(chain_py_str)
        if written_chain_content != chain_content:
            raise RuntimeError(f"Chain.py file content verification failed")

        get_logger().info(f"Chain.py file successfully updated: {chain_py}")

    except Exception as e:
        get_logger().error(f"Failed to update chain.py file {chain_py}: {e}")
        raise RuntimeError(f"Failed to update chain.py file {chain_py}: {e}")

    # Regenerate stub file
    try:
        update_project_stub(project_path, silent=True)
        get_logger().info(f"Stub file regenerated successfully")
    except Exception as e:
        get_logger().error(f"Failed to regenerate stub file: {e}")
        raise RuntimeError(f"Failed to regenerate stub file: {e}")

# ─── PUBLIC API: create plugin templates ───────────────────────────────────
def _normalise_project_path(path: Path | str) -> Path:
    """Normalize project path to directory.

    :param path: Path to normalize.
    :type path: Path | str
    :return Path: Normalized directory path.
    """
    # @@ STEP 1: Expand and resolve path, return parent if file. @@
    p = Path(path).expanduser().resolve()
    return p.parent if p.is_file() else p

def create_then_plugin(project_path: Path | str, short_name: str) -> Path:
    """Create a then_ plugin using the template service.

    :param project_path: Path to the project.
    :type project_path: Path | str
    :param short_name: Short name for the plugin.
    :type short_name: str
    :return Path: Path to the created plugin file.
    :raises ValueError: If plugin name is invalid.
    """
    # @@ STEP 1: Validate plugin name. @@
    if not re.fullmatch(r"[a-z][a-z0-9_]*", short_name):
        raise ValueError("Plugin name must be snake_case starting with a letter")

    # @@ STEP 2: Normalize project path. @@
    project_path = _normalise_project_path(project_path)

    # @@ STEP 3: Create plugin file and update stub. @@
    file_path = create_plugin_file("then", project_path, short_name)
    update_project_stub(project_path, silent=True)
    return file_path

def create_as_plugin(project_path: Path | str, short_name: str) -> Path:
    """Create an as_ plugin using the template service.

    :param project_path: Path to the project.
    :type project_path: Path | str
    :param short_name: Short name for the plugin.
    :type short_name: str
    :return Path: Path to the created plugin file.
    :raises ValueError: If plugin name is invalid.
    """
    # @@ STEP 1: Validate plugin name. @@
    if not re.fullmatch(r"[a-z][a-z0-9_]*", short_name):
        raise ValueError("Plugin name must be snake_case starting with a letter")

    # @@ STEP 2: Normalize project path. @@
    project_path = _normalise_project_path(project_path)

    # @@ STEP 3: Create plugin file and update stub. @@
    file_path = create_plugin_file("as", project_path, short_name)
    update_project_stub(project_path, silent=True)
    return file_path

def create_processor(project_path: Path | str, snake_name: str) -> Path:
    """Create a processor plugin using the template service.

    :param project_path: Path to the project.
    :type project_path: Path | str
    :param snake_name: Snake case name for the processor.
    :type snake_name: str
    :return Path: Path to the created processor file.
    :raises ValueError: If processor name is invalid.
    """
    # @@ STEP 1: Validate processor name. @@
    if not re.fullmatch(r"[a-z][a-z0-9_]*", snake_name):
        raise ValueError("Processor name must be snake_case starting with a letter")

    # @@ STEP 2: Normalize project path. @@
    project_path = _normalise_project_path(project_path)

    # @@ STEP 3: Create processor file and update stub. @@
    file_path = create_plugin_file("processor", project_path, snake_name)
    update_project_stub(project_path, silent=True)
    return file_path
