"""Chain traversal functionality for ChainedPy projects.

This service provides functionality to traverse and display the inheritance chain
of ChainedPy projects, supporting both local and remote filesystems through fsspec.
It enables users to understand the project hierarchy and inheritance relationships
in their ChainedPy project ecosystem.

The service can traverse complex inheritance chains, resolve remote dependencies,
and generate comprehensive reports showing the complete project lineage. It handles
both local file paths and remote URLs (GitHub, GitLab, etc.) seamlessly.

Note:
    All filesystem operations use fsspec for consistent handling of both local
    and remote filesystems. The service maintains compatibility with various
    storage backends and authentication mechanisms.

Example:
    ```python
    from chainedpy.services import chain_traversal_service
    from pathlib import Path

    # Get project chain information
    chain_info = chain_traversal_service.get_project_chain(
        Path("./my_project")
    )

    # Display the inheritance chain
    for project in chain_info:
        print(f"{project.name} -> {project.base_project}")
        print(f"  Path: {project.path}")
        print(f"  Summary: {project.summary}")
        print(f"  Remote: {project.is_remote}")

    # Generate formatted chain display
    display = chain_traversal_service.format_project_chain(chain_info)
    print(display)
    ```

See Also:
    - [ProjectInfo][chainedpy.services.chain_traversal_service.ProjectInfo]: Project information data structure
    - [get_project_chain][chainedpy.services.chain_traversal_service.get_project_chain]: Main traversal function
    - [chainedpy.services.filesystem_service][chainedpy.services.filesystem_service]: Underlying filesystem operations
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
from pathlib import Path
from typing import NamedTuple, List, Dict, Any

# @@ STEP 2: Import third-party modules. @@
# (none)

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    DEFAULT_BASE_PROJECT, CONFIG_FILE_NAME, FS_TYPE_LOCAL,
    URL_SCHEME_SEPARATOR, INIT_FILE_NAME,
    CONFIG_KEY_BASE_PROJECT, CONFIG_KEY_SUMMARY, DEFAULT_SUMMARY_TEMPLATE,
    TEMPLATE_PROJECT_CHAIN
)

# @@ STEP 4: Import ChainedPy services. @@
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.template_service import render_template

# @@ STEP 5: Import ChainedPy internal modules. @@
from chainedpy.exceptions import ChainTraversalError

# @@ STEP 6: Import TYPE_CHECKING modules. @@
# (none)


class ProjectInfo(NamedTuple):
    """Information about a project in the chain.

    :param name: Project name.
    :type name: str
    :param path: Project path or URL.
    :type path: str
    :param base_project: Base project this inherits from.
    :type base_project: str
    :param summary: Project summary description.
    :type summary: str
    :param is_remote: Whether project is remote.
    :type is_remote: bool
    :param filesystem_type: Type of filesystem.
    :type filesystem_type: str
    """
    name: str
    path: str
    base_project: str
    summary: str
    is_remote: bool
    filesystem_type: str


def _load_env_credentials() -> Dict[str, str]:
    """Load credentials from .env file if available - delegate to filesystem service.

    Example:
        ```python
        from chainedpy.services.chain_traversal_service import _load_env_credentials
        import os

        # Set test environment variables
        os.environ["GITHUB_TOKEN"] = "ghp_test_token"
        os.environ["GITLAB_PRIVATE_TOKEN"] = "glpat_test_token"

        # Load credentials
        credentials = _load_env_credentials()

        # Check loaded credentials
        assert "github_token" in credentials
        assert credentials["github_token"] == "ghp_test_token"
        assert "gitlab_private_token" in credentials
        assert credentials["gitlab_private_token"] == "glpat_test_token"

        # Cleanup
        del os.environ["GITHUB_TOKEN"]
        del os.environ["GITLAB_PRIVATE_TOKEN"]

        # Empty credentials when no env vars
        empty_creds = _load_env_credentials()
        assert isinstance(empty_creds, dict)
        ```

    :return [Dict][dict][[str][str], [str][str]]: Dictionary of loaded credentials.
    """
    return fs_utils.load_env_credentials()


def _get_filesystem(path_or_url: str, credentials: Dict[str, str]) -> tuple[Any, str]:
    """Get appropriate fsspec filesystem for the given path or URL - delegate to filesystem service.

    Example:
        ```python
        from chainedpy.services.chain_traversal_service import _get_filesystem

        # Get filesystem for local path
        fs, fs_type = _get_filesystem("/local/path", {})
        assert fs_type == "local"
        assert fs is not None

        # Get filesystem for GitHub URL
        fs, fs_type = _get_filesystem(
            "https://github.com/user/repo",
            {"github_token": "ghp_example"}
        )
        assert fs_type == "github"
        assert fs is not None

        # Get filesystem for GitLab URL
        fs, fs_type = _get_filesystem(
            "https://gitlab.com/user/repo",
            {"gitlab_private_token": "glpat_example"}
        )
        assert fs_type == "gitlab"
        assert fs is not None

        # Get filesystem without credentials
        fs, fs_type = _get_filesystem("https://github.com/user/repo", {})
        assert fs is not None
        ```

    :param path_or_url: Path or URL to get filesystem for.
    :type path_or_url: [str][str]
    :param credentials: Credentials dictionary.
    :type credentials: [Dict][dict][[str][str], [str][str]]
    :return [tuple][tuple][[Any][typing.Any], [str][str]]: Tuple of filesystem and filesystem type.
    :raises ChainTraversalError: If filesystem creation fails.
    """
    try:
        return fs_utils.get_filesystem(path_or_url, credentials)
    except ValueError as e:
        # Convert ValueError to ChainTraversalError for consistency
        raise ChainTraversalError(str(e)) from e


def _read_remote_config(fs: Any, config_path: str, credentials: Dict[str, str] = None) -> Dict[str, str]:
    """Read project configuration from remote filesystem - delegate to filesystem service.

    Example:
        ```python
        from chainedpy.services.chain_traversal_service import _read_remote_config, _get_filesystem
        from chainedpy.exceptions import ChainTraversalError

        # Get filesystem for remote URL
        fs, _ = _get_filesystem("https://github.com/user/repo", {})

        # Read remote config
        try:
            config = _read_remote_config(
                fs,
                "https://raw.githubusercontent.com/user/repo/main/chainedpy.yaml"
            )

            assert isinstance(config, dict)
            assert "base_project" in config
            assert "summary" in config

        except Exception as e:
            print(f"Config read failed: {e}")

        # Read with credentials
        try:
            config = _read_remote_config(
                fs,
                "https://raw.githubusercontent.com/user/repo/main/chainedpy.yaml",
                {"github_token": "ghp_example"}
            )

            assert isinstance(config, dict)

        except Exception as e:
            print(f"Config read with credentials failed: {e}")
        ```

    :param fs: Filesystem instance (unused, kept for compatibility).
    :type fs: [Any][typing.Any]
    :param config_path: Path to configuration file.
    :type config_path: [str][str]
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Dict][dict][[str][str], [str][str]], optional
    :return [Dict][dict][[str][str], [str][str]]: Configuration dictionary.
    """
    return fs_utils.read_config(config_path, credentials)


def _normalize_project_path(base_path: str, current_project_path: str) -> str:
    """Normalize project path relative to workspace or as absolute.

    Example:
        ```python
        from chainedpy.services.chain_traversal_service import _normalize_project_path
        from chainedpy.constants import DEFAULT_BASE_PROJECT

        # Default base project
        normalized = _normalize_project_path(DEFAULT_BASE_PROJECT, "/current/project")
        assert normalized == DEFAULT_BASE_PROJECT

        # Relative path
        normalized = _normalize_project_path("../other-project", "/current/project")
        assert "/other-project" in normalized

        # Absolute path
        normalized = _normalize_project_path("/absolute/path", "/current/project")
        assert normalized == "/absolute/path"

        # URL path
        normalized = _normalize_project_path(
            "https://github.com/user/repo",
            "/current/project"
        )
        assert normalized == "https://github.com/user/repo"

        # Current directory reference
        normalized = _normalize_project_path(".", "/current/project")
        assert "/current/project" in normalized
        ```

    :param base_path: Base project path to normalize.
    :type base_path: [str][str]
    :param current_project_path: Current project path for context.
    :type current_project_path: [str][str]
    :return [str][str]: Normalized project path.
    """
    # @@ STEP 1: Handle default base project. @@
    if base_path == DEFAULT_BASE_PROJECT:
        return DEFAULT_BASE_PROJECT

    # @@ STEP 2: Handle URLs. @@
    if URL_SCHEME_SEPARATOR in base_path:
        return base_path

    # @@ STEP 3: Handle local paths. @@
    base_path_obj = Path(base_path)
    if base_path_obj.is_absolute():
        return str(base_path_obj)

    # @@ STEP 4: Resolve relative paths. @@
    if "://" in current_project_path:
        # For remote projects, we can't easily resolve relative paths.
        # Return as-is and let the caller handle it.
        return base_path
    else:
        # Local project - resolve relative to workspace root.
        current_path_obj = Path(current_project_path)
        workspace_root = current_path_obj.parent
        resolved = workspace_root / base_path_obj
        return str(resolved.resolve())


def traverse_project_chain(project_path: str) -> List[ProjectInfo]:
    """Traverse the project inheritance chain starting from the given project.

    Example:
        ```python
        from chainedpy.services.chain_traversal_service import traverse_project_chain
        from chainedpy.services.project_lifecycle import create_project
        from chainedpy.exceptions import ChainTraversalError
        from pathlib import Path
        import shutil

        # Create test project
        project_path = create_project(Path("test_project"), "test_project")

        # Traverse project chain
        try:
            project_chain = traverse_project_chain(str(project_path))

            assert isinstance(project_chain, list)
            assert len(project_chain) > 0

            # Check first project info (the project itself)
            first_project = project_chain[0]
            assert first_project.path == str(project_path)
            assert first_project.base_project is not None
            assert first_project.summary is not None

            print(f"Found {len(project_chain)} projects in chain")
            for i, project in enumerate(project_chain):
                print(f"  {i}: {project.path} -> {project.base_project}")

        except ChainTraversalError as e:
            print(f"Traversal failed: {e}")

        # Test with remote URL
        try:
            remote_chain = traverse_project_chain("https://github.com/user/chainedpy-project")
            assert isinstance(remote_chain, list)

        except ChainTraversalError as e:
            print(f"Remote traversal failed: {e}")

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path or URL to the starting project.
    :type project_path: [str][str]
    :return [List][list][[ProjectInfo][chainedpy.services.chain_traversal_service.ProjectInfo]]: List of ProjectInfo objects representing the chain from current to root.
    :raises ChainTraversalError: If traversal fails or circular dependency detected.
    """
    credentials = _load_env_credentials()
    chain = []
    visited = set()
    current_path = project_path

    while current_path and current_path != DEFAULT_BASE_PROJECT:
        # Check for circular dependencies
        if current_path in visited:
            raise ChainTraversalError(f"Circular dependency detected at: {current_path}")
        
        visited.add(current_path)
        
        try:
            # Get filesystem for current path
            fs, fs_type = _get_filesystem(current_path, credentials)
            is_remote = fs_type != FS_TYPE_LOCAL

            # Validate that the project exists and is a valid ChainedPy project
            if not is_remote:
                # Local path validation
                project_path_obj = Path(current_path)
                if not project_path_obj.exists():
                    raise ChainTraversalError(f"Project path does not exist: {current_path}")
                if not project_path_obj.is_dir():
                    raise ChainTraversalError(f"Project path is not a directory: {current_path}")
                if not (project_path_obj / INIT_FILE_NAME).exists():
                    raise ChainTraversalError(
                        f"Project is not a Python package (missing {INIT_FILE_NAME}): {current_path}"
                    )

                project_name = project_path_obj.name
                config_path = str(project_path_obj / CONFIG_FILE_NAME)
            else:
                # Remote path - extract project name from URL
                project_name = Path(current_path).name
                config_file_suffix = f"/{CONFIG_FILE_NAME}"
                if (current_path.endswith(config_file_suffix) or
                    current_path.endswith(CONFIG_FILE_NAME)):
                    config_path = current_path
                else:
                    config_path = f"{current_path.rstrip('/')}/{CONFIG_FILE_NAME}"

                # For remote paths, we'll validate existence when we try to read the config
            
            # Read project configuration
            config_data = _read_remote_config(fs, config_path, credentials)
            base_project_raw = config_data.get(CONFIG_KEY_BASE_PROJECT, DEFAULT_BASE_PROJECT).strip()
            summary = config_data.get(CONFIG_KEY_SUMMARY, DEFAULT_SUMMARY_TEMPLATE.format(project_name=project_name)).strip()

            # Resolve the base project path for display and next iteration
            if base_project_raw == DEFAULT_BASE_PROJECT:
                base_project_display = DEFAULT_BASE_PROJECT
                next_path = None
            else:
                next_path = _normalize_project_path(base_project_raw, current_path)
                base_project_display = next_path

            # Add to chain
            chain.append(ProjectInfo(
                name=project_name,
                path=current_path,
                base_project=base_project_display,
                summary=summary,
                is_remote=is_remote,
                filesystem_type=fs_type
            ))

            # Move to next project in chain
            if base_project_raw == DEFAULT_BASE_PROJECT:
                break

            current_path = next_path
            
        except Exception as e:
            raise ChainTraversalError(f"Chain traversal failed at {current_path}: {e}") from e
    
    return chain


def format_project_chain(chain: List[ProjectInfo]) -> str:
    """Format the project chain for display using Jinja2 template."""
    return render_template(TEMPLATE_PROJECT_CHAIN, chain=chain, default_base_project=DEFAULT_BASE_PROJECT).strip()
