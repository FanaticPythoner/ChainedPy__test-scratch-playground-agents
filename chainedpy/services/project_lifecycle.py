"""Project Lifecycle Service.

This service handles project creation, updates, and management operations for ChainedPy
projects. It provides comprehensive functionality for managing the entire lifecycle
of ChainedPy projects from initial creation through updates, activation, and maintenance.

The service coordinates between multiple other services to provide high-level project
operations including creation, configuration management, plugin generation, and
project activation/deactivation. It serves as the orchestration layer for complex
project operations that involve multiple subsystems.

Note:
    This service was extracted from project.py to centralize project lifecycle
    functionality and maintain clean separation between file operations and
    lifecycle management. It focuses on orchestrating project operations
    rather than low-level file manipulation.

Example:
    ```python
    from chainedpy.services.project_lifecycle import (
        create_project, update_project_base, get_active_project
    )
    from pathlib import Path

    # Create a new project
    project_path = create_project(
        name="my_project",
        dest=Path("./projects"),
        base_project="chainedpy",
        summary="My custom chain project",
        github_token="ghp_example",
        create_env=True
    )

    # Update project base
    update_project_base(
        project_path,
        new_base_project="advanced_chain",
        summary="Updated project with advanced features"
    )

    # Check active project
    active = get_active_project()
    if active:
        print(f"Active project: {active}")
    ```

See Also:
    - [create_project][chainedpy.services.project_lifecycle.create_project]: Create new ChainedPy projects
    - [update_project_base][chainedpy.services.project_lifecycle.update_project_base]: Update project inheritance
    - [get_active_project][chainedpy.services.project_lifecycle.get_active_project]: Get currently active project
    - [chainedpy.services.project_file_service][chainedpy.services.project_file_service]: Low-level file operations
"""
from __future__ import annotations

# 1. Standard library imports
import os
from pathlib import Path
from typing import Sequence

# 2. Third-party imports
# (none)

# 3. Internal constants
from chainedpy.constants import (
    # Environment variables
    ENV_ACTIVE_PROJECT, ENV_PROJECT_NAME, GITHUB_TOKEN_KEY, GITLAB_TOKEN_KEY,
    # File names and extensions
    INIT_FILE_NAME, CONFIG_FILE_NAME, CHAIN_FILE_SUFFIX,
    # Directory structure
    PLUGINS_THEN_PATH, PLUGINS_AS_PATH, PLUGINS_PROCESSORS_PATH,
    # Default values
    DEFAULT_BASE_PROJECT, DEFAULT_SUMMARY_FORMAT,
    # File paths
    ACTIVE_PROJECT_FILE,
    # URL patterns
    URL_SCHEME_SEPARATOR,
    # Domain and placeholder constants
    GITHUB_DOMAIN, GITHUB_RAW_DOMAIN, GITLAB_DOMAIN,
    GITHUB_TOKEN_PLACEHOLDER, GITLAB_TOKEN_PLACEHOLDER, GITLAB_PRIVATE_TOKEN_KEY,
    TEMPLATE_STALE_PROJECT_WARNING, CONFIG_KEY_BASE_PROJECT, CONFIG_KEY_SUMMARY,
    MSG_STUB_READ_CONFIG_DEFAULT,
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.chain_traversal_service import _load_env_credentials
from chainedpy.services.credential_service import create_env_file
from chainedpy.services.gitignore_service import create_project_gitignore
from chainedpy.services.project_file_service import create_project_files as pfs_create_project_files
from chainedpy.services.project_remote_chain_service import get_project_chain_import
from chainedpy.services.template_service import create_plugin_file, render_template

# 5. ChainedPy internal modules

# 6. TYPE_CHECKING imports (none)


from chainedpy.services.logging_service import get_logger


from chainedpy.exceptions import ProjectLifecycleError
from chainedpy.models import ProjectConfig


def _update_chain_file_with_import(project_path: Path, project_name: str, base_import: str) -> None:
    """Update the chain file with a custom import statement.

    :param project_path: Path to the project root.
    :type project_path: Path
    :param project_name: Name of the project.
    :type project_name: str
    :param base_import: Import statement to use.
    :type base_import: str
    """
    try:
        # Generate chain.py file using template with custom import
        chain_py = project_path / f"{project_name}{CHAIN_FILE_SUFFIX}"
        chain_content = render_template('project/chain_py.j2', base_import=base_import)

        fs_utils.write_text(str(chain_py), chain_content)
        get_logger().info(f"Updated chain file with custom import: {chain_py}")

    except Exception as e:
        error_msg = f"Failed to update chain file with import: {e}"
        raise ProjectLifecycleError(error_msg) from e


def _create_project_gitignore(project_path: Path) -> None:
    """Create gitignore file for the project.

    :param project_path: Path to the project root.
    :type project_path: Path
    """
    try:
        create_project_gitignore(project_path, include_env=True)
        get_logger().info(f"Created gitignore for project: {project_path}")

    except Exception as e:
        error_msg = f"Failed to create project gitignore: {e}"
        raise ProjectLifecycleError(error_msg) from e


def _create_env_file_for_remote_project(base_project_url: str, project_path: Path) -> None:
    """Automatically create .env file for remote base projects with appropriate credentials uncommented.

    Uses actual credentials from repository-level .env if available.

    :param base_project_url: URL to the remote base project.
    :type base_project_url: str
    :param project_path: Path to the project directory.
    :type project_path: Path
    """
    try:
        # Load credentials from environment and .env files
        loaded_credentials = _load_env_credentials()

        # Detect repository type from URL
        repository_url = None
        github_token = None
        gitlab_token = None

        if (GITHUB_DOMAIN in base_project_url.lower() or
            GITHUB_RAW_DOMAIN in base_project_url.lower()):
            repository_url = base_project_url
            # Use actual GitHub token if available, otherwise use placeholder
            github_token = loaded_credentials.get(GITHUB_TOKEN_KEY, GITHUB_TOKEN_PLACEHOLDER)
        elif GITLAB_DOMAIN in base_project_url.lower():
            repository_url = base_project_url
            # Use actual GitLab token if available, otherwise use placeholder
            gitlab_token = (loaded_credentials.get(GITLAB_TOKEN_KEY) or
                          loaded_credentials.get(GITLAB_PRIVATE_TOKEN_KEY, GITLAB_TOKEN_PLACEHOLDER))

        # Create .env file with appropriate credentials
        create_env_file(
            project_path,
            github_token=github_token,
            gitlab_token=gitlab_token,
            repository_url=repository_url
        )

        get_logger().info(f"Created .env file for remote project: {project_path}")

    except Exception as e:
        msg = f"Failed to create .env file for remote project: {e}"
        raise ProjectLifecycleError(msg) from e


def _handle_remote_base_project(base_project_url: str, project_path: Path) -> str:
    """Handle remote base project by downloading to project directory and generating import statement.

    :param base_project_url: URL to the remote base project.
    :type base_project_url: str
    :param project_path: Path to the project directory.
    :type project_path: Path
    :return str: Import statement for the remote base project.
    :raises ProjectLifecycleError: If remote dependency resolution fails.
    """
    try:
        get_logger().info(f"Handling remote base project: {base_project_url}")

        # Use the new project remote chain service to download chains to project directory
        base_import = get_project_chain_import(base_project_url, project_path)

        get_logger().info(f"Generated import for remote base project: {base_import}")
        return base_import

    except Exception as e:
        error_msg = f"Failed to handle remote base project {base_project_url}: {e}"
        raise ProjectLifecycleError(error_msg) from e


# Remove redundant variables - use constants directly




def create_project(dest: Path, name: str, base_project: str = DEFAULT_BASE_PROJECT, summary: str = None) -> Path:
    """Create a new ChainedPy project.

    Example:
        ```python
        from chainedpy.services.project_lifecycle import create_project
        from pathlib import Path
        import shutil

        # Create basic project
        project_path = create_project(
            Path("my_project"),
            "my_project",
            summary="My test project"
        )

        # Verify project structure
        assert project_path.exists()
        assert (project_path / "chainedpy.yaml").exists()
        assert (project_path / "my_project_chain.py").exists()
        assert (project_path / "plugins").exists()

        # Create with custom base project
        custom_project = create_project(
            Path("custom_project"),
            "custom_project",
            base_project="https://github.com/user/base-chain",
            summary="Project with custom base"
        )

        # Verify custom project
        assert custom_project.exists()

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        shutil.rmtree(custom_project, ignore_errors=True)
        ```

    :param dest: Destination directory.
    :type dest: [Path][pathlib.Path]
    :param name: Project name.
    :type name: [str][str]
    :param base_project: Base project to extend, defaults to DEFAULT_BASE_PROJECT.
    :type base_project: [str][str], optional
    :param summary: Project summary, defaults to None.
    :type summary: [str][str], optional
    :return [Path][pathlib.Path]: Path to the created project.
    :raises ProjectLifecycleError: If project creation fails.
    """
    try:
        project_dir = Path(dest) / name

        # Set default summary if not provided
        if summary is None:
            summary = DEFAULT_SUMMARY_FORMAT.format(name)

        # Create project structure using fsspec
        fs_utils.makedirs(str(project_dir / PLUGINS_THEN_PATH), exist_ok=True)
        fs_utils.makedirs(str(project_dir / PLUGINS_AS_PATH), exist_ok=True)
        fs_utils.makedirs(str(project_dir / PLUGINS_PROCESSORS_PATH), exist_ok=True)

        # Create project files first (with default base project)
        pfs_create_project_files(project_dir, name, base_project, summary)

        # Handle remote base project after project structure is created
        if base_project != DEFAULT_BASE_PROJECT and URL_SCHEME_SEPARATOR in base_project:
            # Create .env file with appropriate credentials uncommented based on repository type
            _create_env_file_for_remote_project(base_project, project_dir)

            # Remote base project - download dependencies and update chain file
            base_import = _handle_remote_base_project(base_project, project_dir)

            # Update the chain file with the correct import
            _update_chain_file_with_import(project_dir, name, base_import)

            # Create gitignore to exclude downloaded chains
            _create_project_gitignore(project_dir)

        # Create configuration file
        write_project_config(project_dir, base_project, summary)

        get_logger().info(f"Project created successfully: {project_dir}")
        return project_dir

    except Exception as e:
        error_msg = f"Failed to create project {name}: {e}"
        raise ProjectLifecycleError(error_msg) from e


def read_project_config(project_path: Path) -> ProjectConfig:
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
        get_logger().error(MSG_STUB_READ_CONFIG_DEFAULT.format(default_base_project, default_summary))
        return ProjectConfig(base_project=default_base_project, summary=default_summary)


def write_project_config(project_path: Path, base_project: str, summary: str) -> None:
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


def activate_project(project_path: Path | str) -> None:
    """Activate a project for the current session (like conda activate).

    Example:
        ```python
        from chainedpy.services.project_lifecycle import activate_project, get_active_project, create_project
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
    :raises ProjectLifecycleError: If activation fails.
    """
    project_path = Path(project_path).expanduser().resolve()
    if project_path.is_file():
        project_path = project_path.parent
    if not (project_path / INIT_FILE_NAME).exists():
        raise ProjectLifecycleError(f"{project_path} is not a Python package")

    # Set environment variable for current session
    os.environ[ENV_ACTIVE_PROJECT] = str(project_path)
    os.environ[ENV_PROJECT_NAME] = project_path.name

    # Store active project in persistent file for subprocess access
    try:
        fs_utils.write_text(str(ACTIVE_PROJECT_FILE), str(project_path))
    except (OSError, PermissionError):
        # If we can't write the file, continue anyway (environment variable still works for shell)
        pass

    # Global project setting will be handled by the caller in project.py


def deactivate_project() -> None:
    """Deactivate the current project session."""
    if ENV_ACTIVE_PROJECT in os.environ:
        del os.environ[ENV_ACTIVE_PROJECT]
    if ENV_PROJECT_NAME in os.environ:
        del os.environ[ENV_PROJECT_NAME]

    # Remove persistent file
    try:
        if ACTIVE_PROJECT_FILE.exists():
            ACTIVE_PROJECT_FILE.unlink()
    except (OSError, PermissionError):
        # If we can't remove the file, continue anyway
        pass


def get_active_project() -> Path | None:
    """Get the currently active project path."""
    # First try environment variable (for shell-based activation)
    active_path = os.environ.get(ENV_ACTIVE_PROJECT)
    if active_path:
        project_path = Path(active_path)
        if project_path.exists() and (project_path / INIT_FILE_NAME).exists():
            return project_path
        else:
            # Project no longer exists, clean up stale state
            _cleanup_stale_project(active_path, "environment variable")
            return None

    # Fall back to persistent file (for subprocess activation)
    try:
        active_project_file_str = str(ACTIVE_PROJECT_FILE)
        if fs_utils.exists(active_project_file_str):
            active_path = fs_utils.read_text(active_project_file_str).strip()
            if active_path:
                project_path = Path(active_path)
                if project_path.exists() and (project_path / INIT_FILE_NAME).exists():
                    return project_path
                else:
                    # Project no longer exists, clean up stale state
                    _cleanup_stale_project(active_path, "persistent file")
                    return None
    except (OSError, PermissionError, UnicodeDecodeError):
        # If we can't read the file, continue anyway
        pass

    return None


def _cleanup_stale_project(project_path: str, source: str) -> None:
    """Clean up stale project state and show warning."""
    warning_message = render_template(TEMPLATE_STALE_PROJECT_WARNING,
                                    project_path=project_path, source=source)
    get_logger().warning(warning_message)

    # Clean up environment variables
    if ENV_ACTIVE_PROJECT in os.environ:
        del os.environ[ENV_ACTIVE_PROJECT]
    if ENV_PROJECT_NAME in os.environ:
        del os.environ[ENV_PROJECT_NAME]

    # Clean up persistent file
    try:
        if ACTIVE_PROJECT_FILE.exists():
            ACTIVE_PROJECT_FILE.unlink()
    except (OSError, PermissionError):
        pass

    get_logger().info(f"✅ Stale project state cleaned up. No project is currently active.")


def list_projects(search_paths: Sequence[Path] = [Path.cwd()]) -> list[Path]:
    """List available ChainedPy projects.

    Example:
        ```python
        from chainedpy.services.project_lifecycle import list_projects, create_project
        from pathlib import Path
        import shutil

        # Create test projects
        project1 = create_project(Path("project1"), "project1", summary="Test 1")
        project2 = create_project(Path("project2"), "project2", summary="Test 2")

        # List projects in current directory
        projects = list_projects()
        project_names = [p.name for p in projects]
        assert "project1" in project_names
        assert "project2" in project_names

        # List projects in specific paths
        projects = list_projects([Path(".")])
        assert len(projects) >= 2

        # List projects in multiple paths
        projects = list_projects([Path("."), Path("../other_dir")])
        assert isinstance(projects, list)

        # Cleanup
        shutil.rmtree(project1, ignore_errors=True)
        shutil.rmtree(project2, ignore_errors=True)
        ```

    :param search_paths: Paths to search for projects (required), defaults to [Path.cwd()].
    :type search_paths: [Sequence][typing.Sequence][[Path][pathlib.Path]], optional
    :return [list][list][[Path][pathlib.Path]]: List of project paths.
    :raises ValueError: If no search paths provided.
    """
    if not search_paths:
        raise ValueError("Search paths must be provided - no default search paths allowed")

    projects = []

    for search_path in search_paths:
        if not search_path.exists():
            raise FileNotFoundError(f"Search path does not exist: {search_path}")

        for item in search_path.iterdir():
            if item.is_dir() and _is_chainedpy_project(item):
                projects.append(item)
    
    # Remove duplicates and sort
    unique_projects = list(set(projects))
    unique_projects.sort()
    
    return unique_projects


def _is_chainedpy_project(path: Path) -> bool:
    """Check if a directory is a ChainedPy project."""
    if not (path / INIT_FILE_NAME).exists():
        return False

    chain_file = path / f"{path.name}{CHAIN_FILE_SUFFIX}"
    return chain_file.exists()


def create_then_plugin(project_path: Path, name_after_prefix: str) -> Path:
    """Create a then_* plugin."""
    try:
        return create_plugin_file("then", project_path, name_after_prefix)
    except Exception as e:
        raise ProjectLifecycleError(f"Failed to create then plugin: {e}") from e


def create_as_plugin(project_path: Path, name_after_prefix: str) -> Path:
    """Create an as_* plugin."""
    try:
        return create_plugin_file("as", project_path, name_after_prefix)
    except Exception as e:
        raise ProjectLifecycleError(f"Failed to create as plugin: {e}") from e


def create_processor(project_path: Path, name: str) -> Path:
    """Create a processor plugin."""
    try:
        return create_plugin_file("processor", project_path, name)
    except Exception as e:
        raise ProjectLifecycleError(f"Failed to create processor: {e}") from e
