"""Project Validation Service.

This service handles validation of ChainedPy projects, both local and remote.
It provides comprehensive validation functionality to ensure projects meet
ChainedPy requirements and are properly structured for use as base projects
or dependencies.

The service validates project structure, configuration files, required files,
and remote accessibility. It supports validation of both local filesystem
projects and remote projects accessible via URLs (GitHub, GitLab, etc.).

Note:
    This service was extracted from cli.py to eliminate code duplication and
    centralize validation logic. It provides reusable validation functions
    that can be used across different parts of the ChainedPy system.

Example:
    ```python
    from chainedpy.services.project_validation import (
        validate_local_project, validate_remote_project, validate_project_structure
    )
    from pathlib import Path

    # Validate local project
    try:
        project_path = validate_local_project("./my_project")
        print(f"Valid local project: {project_path}")
    except ProjectValidationError as e:
        print(f"Validation failed: {e}")

    # Validate remote project
    try:
        config = validate_remote_project(
            "https://github.com/user/chainedpy-project",
            github_token="ghp_example"
        )
        print(f"Valid remote project: {config}")
    except ProjectValidationError as e:
        print(f"Remote validation failed: {e}")

    # Validate project structure
    is_valid = validate_project_structure(Path("./my_project"))
    ```

See Also:
    - [validate_local_project][chainedpy.services.project_validation.validate_local_project]: Validate local project structure
    - [validate_remote_project][chainedpy.services.project_validation.validate_remote_project]: Validate remote project accessibility
    - [chainedpy.exceptions.ProjectValidationError][chainedpy.exceptions.ProjectValidationError]: Validation-specific exceptions
"""
from __future__ import annotations

# 1. Standard library imports
from pathlib import Path
from typing import Dict, Any, Tuple

# 2. Third-party imports
# (none)

# 3. Internal constants
from chainedpy.constants import (
    GITHUB_TOKEN_KEY, GITLAB_TOKEN_KEY, CONFIG_FILE_NAME, INIT_FILE_NAME,
    CHAIN_FILE_SUFFIX, DEFAULT_BASE_PROJECT, URL_SCHEME_SEPARATOR
)

# 4. ChainedPy services
from chainedpy.services.chain_traversal_service import (
    _get_filesystem, _read_remote_config, _load_env_credentials
)
from chainedpy.services.logging_service import get_logger

# 5. ChainedPy internal modules
from chainedpy.exceptions import ProjectValidationError

# 6. TYPE_CHECKING imports (none)


def validate_local_project(project_path: str | Path) -> Path:
    """Validate that a local path is a valid ChainedPy project.

    Example:
        ```python
        from chainedpy.services.project_validation import validate_local_project
        from chainedpy.services.project_lifecycle import create_project
        from chainedpy.exceptions import ProjectValidationError
        from pathlib import Path
        import shutil

        # Create valid project
        project_path = create_project(Path("valid_project"), "valid_project")

        # Validate with Path object
        validated_path = validate_local_project(project_path)
        assert validated_path == project_path.resolve()
        assert validated_path.is_absolute()

        # Validate with string path
        validated_str = validate_local_project(str(project_path))
        assert validated_str == project_path.resolve()

        # Validate with relative path
        relative_path = Path("valid_project")
        validated_rel = validate_local_project(relative_path)
        assert validated_rel.is_absolute()

        # Invalid project (missing config file)
        invalid_project = Path("invalid_project")
        invalid_project.mkdir(exist_ok=True)
        (invalid_project / "__init__.py").touch()

        try:
            validate_local_project(invalid_project)
            assert False, "Should have raised ProjectValidationError"
        except ProjectValidationError as e:
            assert "chainedpy.yaml" in str(e)

        # Non-existent project
        try:
            validate_local_project("nonexistent_project")
            assert False, "Should have raised ProjectValidationError"
        except ProjectValidationError as e:
            assert "does not exist" in str(e)

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        shutil.rmtree(invalid_project, ignore_errors=True)
        ```

    :param project_path: Path to the project directory.
    :type project_path: [str][str] | [Path][pathlib.Path]
    :return [Path][pathlib.Path]: Resolved Path object.
    :raises ProjectValidationError: If validation fails.
    """
    base_path = Path(project_path).expanduser().resolve()
    
    if not base_path.exists():
        raise ProjectValidationError(f"Project path does not exist: {base_path}")
    
    if not (base_path / INIT_FILE_NAME).exists():
        raise ProjectValidationError(f"Project is not a Python package: {base_path}")
    
    chain_file = base_path / f"{base_path.name}{CHAIN_FILE_SUFFIX}"
    if not chain_file.exists():
        raise ProjectValidationError(
            f"Project is not a ChainedPy project (missing {chain_file})"
        )
    
    return base_path


def validate_remote_project(project_url: str, credentials: Dict[str, str] = None) -> Tuple[Any, str]:
    """Validate that a remote URL is a valid ChainedPy project.

    Example:
        ```python
        from chainedpy.services.project_validation import validate_remote_project
        from chainedpy.exceptions import ProjectValidationError

        # Validate GitHub project (public)
        try:
            fs, config_url = validate_remote_project("https://github.com/user/chainedpy-project")
            assert fs is not None
            assert "chainedpy.yaml" in config_url
            print(f"Valid remote project, config at: {config_url}")
        except ProjectValidationError as e:
            print(f"Invalid remote project: {e}")

        # Validate with credentials
        credentials = {"github_token": "ghp_example_token"}
        try:
            fs, config_url = validate_remote_project(
                "https://github.com/user/private-project",
                credentials=credentials
            )
            assert fs is not None
            assert "chainedpy.yaml" in config_url
        except ProjectValidationError as e:
            print(f"Private project validation failed: {e}")

        # Invalid URL
        try:
            validate_remote_project("https://github.com/user/nonexistent")
            assert False, "Should have raised ProjectValidationError"
        except ProjectValidationError as e:
            assert "not a valid ChainedPy project" in str(e)

        # Invalid URL format
        try:
            validate_remote_project("invalid-url")
            assert False, "Should have raised ProjectValidationError"
        except ProjectValidationError as e:
            assert "Invalid URL" in str(e) or "Failed to access" in str(e)
        ```

    :param project_url: Remote URL to validate.
    :type project_url: [str][str]
    :param credentials: Optional credentials for private repositories, defaults to None.
    :type credentials: [Dict][dict][[str][str], [str][str]], optional
    :return [Tuple][tuple][[Any][typing.Any], [str][str]]: Tuple of (filesystem, filesystem_type).
    :raises ProjectValidationError: If validation fails.
    """
    try:
        
        # Load credentials if not provided
        if credentials is None:
            credentials = _load_env_credentials()
        
        # Get filesystem for the URL
        fs, fs_type = _get_filesystem(project_url, credentials)
        
        # Try to read config to validate it's a ChainedPy project
        config_file_suffix = f"/{CONFIG_FILE_NAME}"
        if (project_url.endswith(config_file_suffix) or
            project_url.endswith(CONFIG_FILE_NAME)):
            config_path = project_url
        else:
            config_path = f"{project_url.rstrip('/')}/{CONFIG_FILE_NAME}"
        config_data = _read_remote_config(fs, config_path, credentials)

        if not config_data:
            msg = f"Remote project is not a valid ChainedPy project (missing {CONFIG_FILE_NAME}): {project_url}"
            raise ProjectValidationError(msg)

        get_logger().info(f"✅ Validated remote project: {project_url} ({fs_type})")
        return fs, fs_type
        
    except Exception as e:
        if isinstance(e, ProjectValidationError):
            raise
        raise ProjectValidationError(f"Failed to validate remote project {project_url}: {e}") from e


def validate_base_project(base_project: str, credentials: Dict[str, str] = None) -> Tuple[Any, str] | Path:
    """Validate a base project, handling both local and remote projects.

    Example:
        ```python
        from chainedpy.services.project_validation import validate_base_project
        from chainedpy.services.project_lifecycle import create_project
        from chainedpy.exceptions import ProjectValidationError
        from pathlib import Path
        import shutil

        # Validate default base project
        result = validate_base_project("chainedpy")
        assert result is None  # Default project returns None

        # Create and validate local project
        local_project = create_project(Path("local_base"), "local_base")
        result = validate_base_project(str(local_project))
        assert isinstance(result, Path)
        assert result == local_project.resolve()

        # Validate relative local project
        result = validate_base_project("./local_base")
        assert isinstance(result, Path)

        # Validate remote project
        try:
            result = validate_base_project("https://github.com/user/chainedpy-base")
            if isinstance(result, tuple):
                fs, fs_type = result
                assert fs is not None
                assert fs_type in ["github", "gitlab", "http"]
            print("Remote base project validated")
        except ProjectValidationError as e:
            print(f"Remote validation failed: {e}")

        # Invalid base project
        try:
            validate_base_project("nonexistent_project")
            assert False, "Should have raised ProjectValidationError"
        except ProjectValidationError as e:
            assert "does not exist" in str(e) or "not a valid" in str(e)

        # Cleanup
        shutil.rmtree(local_project, ignore_errors=True)
        ```

    :param base_project: Base project identifier (local path, remote URL, or 'chainedpy').
    :type base_project: [str][str]
    :param credentials: Optional credentials for private repositories, defaults to None.
    :type credentials: [Dict][dict][[str][str], [str][str]], optional
    :return [Tuple][tuple][[Any][typing.Any], [str][str]] | [Path][pathlib.Path]: For remote projects: Tuple of (filesystem, filesystem_type). For local projects: Path object. For 'chainedpy': None.
    :raises ProjectValidationError: If validation fails.
    """
    if base_project == DEFAULT_BASE_PROJECT:
        return None
    
    if URL_SCHEME_SEPARATOR in base_project:
        # Remote URL
        return validate_remote_project(base_project, credentials)
    else:
        # Local path
        return validate_local_project(base_project)


def merge_credentials(cli_github_token: str = None, cli_gitlab_token: str = None) -> Dict[str, str]:
    """Merge CLI-provided credentials with environment credentials.

    Example:
        ```python
        from chainedpy.services.project_validation import merge_credentials
        import os

        # Set environment variables
        os.environ["GITHUB_TOKEN"] = "ghp_env_token"
        os.environ["GITLAB_PRIVATE_TOKEN"] = "glpat_env_token"

        # Merge with no CLI tokens (uses environment)
        creds = merge_credentials()
        assert creds["github_token"] == "ghp_env_token"
        assert creds["gitlab_private_token"] == "glpat_env_token"

        # CLI tokens override environment
        creds = merge_credentials(
            cli_github_token="ghp_cli_token",
            cli_gitlab_token="glpat_cli_token"
        )
        assert creds["github_token"] == "ghp_cli_token"
        assert creds["gitlab_private_token"] == "glpat_cli_token"

        # Partial override
        creds = merge_credentials(cli_github_token="ghp_cli_override")
        assert creds["github_token"] == "ghp_cli_override"
        assert creds["gitlab_private_token"] == "glpat_env_token"

        # No environment or CLI tokens
        del os.environ["GITHUB_TOKEN"]
        del os.environ["GITLAB_PRIVATE_TOKEN"]
        creds = merge_credentials()
        assert isinstance(creds, dict)
        # Should still return a dict, possibly empty or with other credentials
        ```

    :param cli_github_token: GitHub token from CLI, defaults to None.
    :type cli_github_token: [str][str], optional
    :param cli_gitlab_token: GitLab token from CLI, defaults to None.
    :type cli_gitlab_token: [str][str], optional
    :return [Dict][dict][[str][str], [str][str]]: Merged credentials dictionary.
    """
    credentials = _load_env_credentials()
    
    # CLI tokens override environment tokens
    if cli_github_token:
        credentials[GITHUB_TOKEN_KEY] = cli_github_token
    if cli_gitlab_token:
        credentials[GITLAB_TOKEN_KEY] = cli_gitlab_token
    
    return credentials
