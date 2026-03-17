"""Credential Service.

This service handles .env file creation and credential management for ChainedPy projects.
It provides functionality for creating environment files with appropriate credential
placeholders, loading credentials from various sources, and managing authentication
for remote repositories and services.

The service supports multiple credential types including GitHub tokens, GitLab tokens,
FTP/SFTP credentials, and custom environment variables. It automatically detects
repository types and includes only relevant credential placeholders.

Note:
    All credential operations maintain security best practices by using placeholders
    in template files and loading actual values from environment variables or
    secure credential stores.

Example:
    ```python
    from chainedpy.services.credential_service import (
        create_env_file, load_credentials_for_url
    )
    from pathlib import Path

    # Create .env file for a project
    project_dir = Path("./my_project")
    success = create_env_file(
        project_dir,
        github_token="ghp_example_token",
        repository_url="https://github.com/user/repo"
    )

    # Load credentials for a specific URL
    credentials = load_credentials_for_url(
        "https://github.com/private/repo",
        project_dir
    )

    # Check if credentials are available
    if credentials.get("github_token"):
        print("GitHub authentication available")
    ```

See Also:
    - [create_env_file][chainedpy.services.credential_service.create_env_file]: Create environment files
    - [load_credentials_for_url][chainedpy.services.credential_service.load_credentials_for_url]: Load URL-specific credentials
    - [chainedpy.exceptions.CredentialServiceError][chainedpy.exceptions.CredentialServiceError]: Credential-specific exceptions
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
import glob
import os
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

# @@ STEP 2: Import third-party modules. @@
from dotenv import load_dotenv

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    CREDENTIAL_KEYS, CREDENTIAL_VALIDATION_ERROR_MSG,
    ENV_FILE_NAME, CHAINEDPY_DIR, CREDENTIALS_DIR, DEFAULT_ENV_FILE_NAME,
    ENV_FILE_EXTENSION, REPO_TYPE_GITHUB, REPO_TYPE_GITLAB, REPO_TYPE_FTP,
    REPO_TYPE_SFTP, REPO_TYPE_UNKNOWN, URL_SCHEME_FTP, URL_SCHEME_SFTP,
    URL_SCHEME_SSH, GITHUB_RAW_DOMAIN, GITHUB_DOMAIN, GITLAB_DOMAIN,
    GITLAB_KEYWORD, TEMPLATE_REPOSITORY_ENV, GITHUB_TOKEN_KEY,
    GITLAB_TOKEN_KEY, GITLAB_PRIVATE_TOKEN_KEY, FTP_USERNAME_KEY, FTP_PASSWORD_KEY,
    SFTP_USERNAME_KEY, SFTP_PASSWORD_KEY
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.chain_traversal_service import _load_env_credentials
from chainedpy.services.logging_service import get_logger
from chainedpy.services.template_service import render_template

# 5. ChainedPy internal modules
from chainedpy.exceptions import CredentialServiceError

# 6. TYPE_CHECKING imports (none)


def create_env_file(project_dir: Path, github_token: str = None, gitlab_token: str = None,
                   repository_url: str = None) -> bool:
    """Create .env file with credential placeholders or provided values.

    Only includes credentials relevant to the repository URL.

    Example:
        ```python
        from chainedpy.services.credential_service import create_env_file
        from pathlib import Path
        import shutil

        # Create test project directory
        project_dir = Path("test_project")
        project_dir.mkdir(exist_ok=True)

        # Create .env file with GitHub token
        success = create_env_file(
            project_dir,
            github_token="ghp_example_token_123",
            repository_url="https://github.com/user/repo"
        )
        assert success == True

        # Verify .env file was created
        env_file = project_dir / ".env"
        assert env_file.exists()

        content = env_file.read_text()
        assert "GITHUB_TOKEN=ghp_example_token_123" in content

        # Try to create again (should return False)
        success = create_env_file(
            project_dir,
            github_token="ghp_new_token"
        )
        assert success == False  # File already exists

        # Create with GitLab token
        project_dir2 = Path("test_project2")
        project_dir2.mkdir(exist_ok=True)

        success = create_env_file(
            project_dir2,
            gitlab_token="glpat_example_token",
            repository_url="https://gitlab.com/user/repo"
        )
        assert success == True

        env_content = (project_dir2 / ".env").read_text()
        assert "GITLAB_PRIVATE_TOKEN=glpat_example_token" in env_content

        # Cleanup
        shutil.rmtree(project_dir, ignore_errors=True)
        shutil.rmtree(project_dir2, ignore_errors=True)
        ```

    :param project_dir: Project directory where .env file should be created.
    :type project_dir: [Path][pathlib.Path]
    :param github_token: Optional GitHub token to include, defaults to None.
    :type github_token: [str][str], optional
    :param gitlab_token: Optional GitLab token to include, defaults to None.
    :type gitlab_token: [str][str], optional
    :param repository_url: Optional repository URL to determine which credentials to include, defaults to None.
    :type repository_url: [str][str], optional
    :return [bool][bool]: True if file was created, False if it already existed.
    :raises CredentialServiceError: If file creation fails.
    """
    env_file = project_dir / ENV_FILE_NAME
    env_file_str = str(env_file)

    # @@ STEP 1: Check if .env file already exists. @@
    # Don't overwrite existing .env file.
    if fs_utils.exists(env_file_str):
        get_logger().info(f"{ENV_FILE_NAME} file already exists at {env_file}")
        return False

    # @@ STEP 2: Generate .env file content. @@
    env_content = _generate_env_template(github_token, gitlab_token, repository_url)

    # @@ STEP 3: Write .env file. @@
    try:
        fs_utils.write_text(env_file_str, env_content)
        get_logger().info(f"Created {ENV_FILE_NAME} file at {env_file}")

        if not github_token and not gitlab_token:
            get_logger().info(f"Edit the {ENV_FILE_NAME} file to add your credentials for private repository access")

        return True

    except Exception as e:
        error_msg = f"Failed to create {ENV_FILE_NAME} file: {e}"
        raise CredentialServiceError(error_msg) from e


def _detect_repository_type(repository_url: str) -> str:
    """Detect the type of repository from URL.

    Example:
        ```python
        from chainedpy.services.credential_service import _detect_repository_type

        # GitHub URLs
        assert _detect_repository_type("https://github.com/user/repo") == "github"
        assert _detect_repository_type("https://raw.githubusercontent.com/user/repo/main/file.py") == "github"

        # GitLab URLs
        assert _detect_repository_type("https://gitlab.com/user/repo") == "gitlab"

        # FTP URLs
        assert _detect_repository_type("ftp://example.com/path") == "ftp"

        # SFTP URLs
        assert _detect_repository_type("sftp://example.com/path") == "sftp"

        # Unknown URLs
        assert _detect_repository_type("https://example.com/repo") == "unknown"
        assert _detect_repository_type("") == "unknown"
        assert _detect_repository_type("invalid-url") == "unknown"
        ```

    :param repository_url: Repository URL to analyze.
    :type repository_url: [str][str]
    :return [str][str]: Repository type: 'github', 'gitlab', 'ftp', 'sftp', or 'unknown'.
    """
    # @@ STEP 1: Handle empty URL. @@
    if not repository_url:
        return REPO_TYPE_UNKNOWN

    # @@ STEP 2: Analyze URL to determine repository type. @@
    url_lower = repository_url.lower()

    if GITHUB_DOMAIN in url_lower or GITHUB_RAW_DOMAIN in url_lower:
        return REPO_TYPE_GITHUB
    elif GITLAB_DOMAIN in url_lower or GITLAB_KEYWORD in url_lower:
        return REPO_TYPE_GITLAB
    elif url_lower.startswith(URL_SCHEME_FTP):
        return REPO_TYPE_FTP
    elif url_lower.startswith(URL_SCHEME_SFTP) or url_lower.startswith(URL_SCHEME_SSH):
        return REPO_TYPE_SFTP
    else:
        return REPO_TYPE_UNKNOWN


def _generate_env_template(github_token: str = None, gitlab_token: str = None,
                          repository_url: str = None) -> str:
    """Generate .env file template content based on repository type.

    Only includes credentials relevant to the repository URL.

    :param github_token: Optional GitHub token to include, defaults to None.

    Example:
        ```python
        from chainedpy.services.credential_service import _generate_env_template

        # GitHub template with token
        template = _generate_env_template(
            github_token="ghp_example_token",
            repository_url="https://github.com/user/repo"
        )
        assert "GITHUB_TOKEN=ghp_example_token" in template
        assert "GITLAB_PRIVATE_TOKEN" not in template

        # GitLab template with token
        template = _generate_env_template(
            gitlab_token="glpat_example_token",
            repository_url="https://gitlab.com/user/repo"
        )
        assert "GITLAB_PRIVATE_TOKEN=glpat_example_token" in template
        assert "GITHUB_TOKEN" not in template

        # Template with placeholders
        template = _generate_env_template(
            repository_url="https://github.com/user/repo"
        )
        assert "GITHUB_TOKEN=" in template
        assert "your_github_token_here" in template

        # Unknown repository type
        template = _generate_env_template(
            repository_url="https://example.com/repo"
        )
        # Should include both GitHub and GitLab placeholders
        assert "GITHUB_TOKEN=" in template
        assert "GITLAB_PRIVATE_TOKEN=" in template
        ```
    
    :type github_token: [str][str], optional
    :param gitlab_token: Optional GitLab token to include, defaults to None.
    :type gitlab_token: [str][str], optional
    :param repository_url: Optional repository URL to determine which credentials to include, defaults to None.
    :type repository_url: [str][str], optional
    :return [str][str]: .env file content as string.
    """
    # @@ STEP 1: Detect repository type. @@
    repo_type = _detect_repository_type(repository_url)

    get_logger().debug(f"Generating {ENV_FILE_NAME} template: repository_url={repository_url}, repo_type={repo_type}, {REPO_TYPE_GITHUB}_token={github_token}, {REPO_TYPE_GITLAB}_token={gitlab_token}")

    # @@ STEP 2: Render template with context. @@
    return render_template(
        'credentials/env_template.j2',
        repository_url=repository_url,
        repo_type=repo_type,
        github_token=github_token,
        gitlab_token=gitlab_token
    )


def _validate_single_credential(value: str, credential_type: str) -> str:
    """Validate a single credential value.

    Example:
        ```python
        from chainedpy.services.credential_service import _validate_single_credential
        from chainedpy.exceptions import CredentialServiceError

        # Valid credential
        result = _validate_single_credential("  ghp_valid_token  ", "GitHub token")
        assert result == "ghp_valid_token"

        # Valid credential with no whitespace
        result = _validate_single_credential("glpat_valid_token", "GitLab token")
        assert result == "glpat_valid_token"

        # Invalid empty credential
        try:
            _validate_single_credential("", "GitHub token")
        except CredentialServiceError as e:
            assert "GitHub token" in str(e)

        # Invalid whitespace-only credential
        try:
            _validate_single_credential("   ", "GitLab token")
        except CredentialServiceError as e:
            assert "GitLab token" in str(e)

        # Invalid non-string credential
        try:
            _validate_single_credential(None, "API token")
        except CredentialServiceError as e:
            assert "API token" in str(e)
        ```

    :param value: Credential value to validate.
    :type value: [str][str]
    :param credential_type: Type of credential for error messages.
    :type credential_type: [str][str]
    :return [str][str]: Stripped credential value.
    :raises CredentialServiceError: If validation fails.
    """
    if not isinstance(value, str) or len(value.strip()) == 0:
        error_msg = CREDENTIAL_VALIDATION_ERROR_MSG.format(credential_type=credential_type)
        raise CredentialServiceError(error_msg)
    return value.strip()


def validate_credentials(github_token: str = None, gitlab_token: str = None,
                       ftp_username: str = None, ftp_password: str = None,
                       sftp_username: str = None, sftp_password: str = None) -> Dict[str, str]:
    """Validate and normalize credential inputs.

    Example:
        ```python
        from chainedpy.services.credential_service import validate_credentials
        from chainedpy.exceptions import CredentialServiceError

        # Validate GitHub token
        creds = validate_credentials(github_token="  ghp_example_token  ")
        assert creds["github_token"] == "ghp_example_token"

        # Validate multiple credentials
        creds = validate_credentials(
            github_token="ghp_token",
            gitlab_token="glpat_token",
            ftp_username="ftpuser",
            ftp_password="ftppass"
        )
        assert creds["github_token"] == "ghp_token"
        assert creds["gitlab_private_token"] == "glpat_token"
        assert creds["ftp_username"] == "ftpuser"
        assert creds["ftp_password"] == "ftppass"

        # Empty credentials return empty dict
        creds = validate_credentials()
        assert creds == {}

        # Invalid credential raises error
        try:
            validate_credentials(github_token="")
        except CredentialServiceError as e:
            assert "GitHub token" in str(e)
        ```

    :param github_token: Optional GitHub token, defaults to None.
    :type github_token: [str][str], optional
    :param gitlab_token: Optional GitLab token, defaults to None.
    :type gitlab_token: [str][str], optional
    :param ftp_username: Optional FTP username, defaults to None.
    :type ftp_username: [str][str], optional
    :param ftp_password: Optional FTP password, defaults to None.
    :type ftp_password: [str][str], optional
    :param sftp_username: Optional SFTP username, defaults to None.
    :type sftp_username: [str][str], optional
    :param sftp_password: Optional SFTP password, defaults to None.
    :type sftp_password: [str][str], optional
    :return [Dict][dict][[str][str], [str][str]]: Dictionary of validated credentials.
    """
    # @@ STEP 1: Initialize credentials dictionary. @@
    credentials = {}

    # @@ STEP 2: Use reusable validation function for all credential types. @@
    credential_mappings = [
        (github_token, GITHUB_TOKEN_KEY, 'GitHub token'),
        (gitlab_token, GITLAB_TOKEN_KEY, 'GitLab token'),
        (ftp_username, FTP_USERNAME_KEY, 'FTP username'),
        (ftp_password, FTP_PASSWORD_KEY, 'FTP password'),
        (sftp_username, SFTP_USERNAME_KEY, 'SFTP username'),
        (sftp_password, SFTP_PASSWORD_KEY, 'SFTP password'),
    ]

    # @@ STEP 3: Validate and store each credential. @@
    for value, key, credential_type in credential_mappings:
        if value:
            credentials[key] = _validate_single_credential(value, credential_type)

    return credentials


def load_project_credentials(project_dir: Path = None) -> Dict[str, str]:
    """Load credentials from project .env file and environment.

    Example:
        ```python
        from chainedpy.services.credential_service import load_project_credentials, create_env_file
        from pathlib import Path
        import os
        import shutil

        # Set environment variable
        os.environ["GITHUB_TOKEN"] = "env_github_token"

        # Load from environment only
        creds = load_project_credentials()
        assert creds.get("github_token") == "env_github_token"

        # Create project with .env file
        project_dir = Path("test_project")
        project_dir.mkdir(exist_ok=True)
        create_env_file(project_dir, github_token="project_github_token")

        # Load from project (should override environment)
        creds = load_project_credentials(project_dir)
        assert creds.get("github_token") == "project_github_token"

        # Load from non-existent project
        creds = load_project_credentials(Path("nonexistent"))
        assert creds.get("github_token") == "env_github_token"

        # Cleanup
        shutil.rmtree(project_dir, ignore_errors=True)
        del os.environ["GITHUB_TOKEN"]
        ```

    :param project_dir: Optional project directory to look for .env file, defaults to None.
    :type project_dir: [Path][pathlib.Path], optional
    :return [Dict][dict][[str][str], [str][str]]: Dictionary of loaded credentials.
    :raises CredentialServiceError: If loading project .env file fails.
    """
    # @@ STEP 1: Load from environment and standard locations. @@
    credentials = _load_env_credentials()

    # @@ STEP 2: Also try to load from project-specific .env file. @@
    if project_dir:
        project_env = project_dir / ENV_FILE_NAME
        if fs_utils.exists(str(project_env)):
            try:
                load_dotenv(project_env)
                get_logger().debug(f"Loaded project credentials from {project_env}")
            except Exception as e:
                raise CredentialServiceError(
                    f"Failed to load project {ENV_FILE_NAME} from {project_env}: {e}"
                ) from e

    return credentials


def _get_repository_key(repository_url: str) -> str:
    """Generate a unique key for a repository URL for credential storage.

    Example:
        ```python
        from chainedpy.services.credential_service import _get_repository_key

        # GitHub repository
        key = _get_repository_key("https://github.com/user/repo")
        assert "github.com" in key
        assert "user_repo" in key

        # GitLab repository
        key = _get_repository_key("https://gitlab.com/group/project")
        assert "gitlab.com" in key
        assert "group_project" in key

        # GitHub raw URL
        key = _get_repository_key("https://raw.githubusercontent.com/user/repo/main/file.py")
        assert "github.com" in key
        assert "user_repo" in key

        # Complex path
        key = _get_repository_key("https://github.com/org/sub-project")
        assert "github.com" in key
        assert "org_sub-project" in key
        ```

    :param repository_url: Repository URL (e.g., https://github.com/user/repo).
    :type repository_url: [str][str]
    :return [str][str]: Unique key for the repository.
    """
    # @@ STEP 1: Parse URL and extract components. @@
    parsed = urlparse(repository_url)
    # Create key from hostname and path, removing common prefixes.
    hostname = parsed.netloc.lower()
    path = parsed.path.strip('/').lower()

    # @@ STEP 2: Remove common path prefixes for raw URLs. @@
    if hostname == GITHUB_RAW_DOMAIN:
        hostname = GITHUB_DOMAIN
        # Extract user/repo from raw URL path like /user/repo/branch/...
        path_parts = path.split('/')
        if len(path_parts) >= 2:
            path = f"{path_parts[0]}/{path_parts[1]}"

    # @@ STEP 3: Generate unique key. @@
    # Create a safe filename from hostname and path
    key = f"{hostname}_{path}".replace('/', '_').replace('.', '_')
    return key


def _get_credential_file_path(repository_url: str, project_dir: Path = None) -> Path:
    """Get the path to the credential file for a specific repository within a project.

    :param repository_url: Repository URL.
    :type repository_url: str
    :param project_dir: Project directory (uses current directory if not provided), defaults to None.
    :type project_dir: Path, optional
    :return Path: Path to the credential file.
    """
    # @@ STEP 1: Set default project directory if not provided. @@
    if project_dir is None:
        project_dir = Path.cwd()

    # @@ STEP 2: Generate credential file path. @@
    key = _get_repository_key(repository_url)
    credentials_dir = project_dir / CHAINEDPY_DIR / CREDENTIALS_DIR
    return credentials_dir / f"{key}{ENV_FILE_EXTENSION}"


def load_repository_credentials(repository_url: str, project_dir: Path = None) -> Dict[str, str]:
    """Load credentials for a specific repository, falling back to global credentials.

    :param repository_url: Repository URL to load credentials for.
    :type repository_url: [str][str]
    :param project_dir: Project directory (uses current directory if not provided), defaults to None.
    :type project_dir: [Path][pathlib.Path], optional
    :return [Dict][dict][[str][str], [str][str]]: Dictionary of credentials for the repository.
    :raises CredentialServiceError: If loading repository credentials fails.

    Example:
        ```python
        from chainedpy.services.credential_service import load_repository_credentials
        from pathlib import Path
        import os

        # Set up test environment
        os.environ["GITHUB_TOKEN"] = "ghp_global_token"

        # Load credentials for GitHub repository
        creds = load_repository_credentials("https://github.com/user/repo")
        assert "github_token" in creds
        assert creds["github_token"] == "ghp_global_token"

        # Load with specific project directory
        project_dir = Path("test_project")
        creds = load_repository_credentials(
            "https://github.com/user/repo",
            project_dir=project_dir
        )
        assert isinstance(creds, dict)

        # GitLab repository
        os.environ["GITLAB_PRIVATE_TOKEN"] = "glpat_global_token"
        creds = load_repository_credentials("https://gitlab.com/user/repo")
        assert "gitlab_private_token" in creds
        assert creds["gitlab_private_token"] == "glpat_global_token"

        # Cleanup
        del os.environ["GITHUB_TOKEN"]
        del os.environ["GITLAB_PRIVATE_TOKEN"]
        ```
    """
    # @@ STEP 1: Initialize credentials dictionary. @@
    credentials = {}

    # @@ STEP 2: First load global credentials as fallback (only if no repo-specific exist). @@
    repo_cred_file = _get_credential_file_path(repository_url, project_dir)
    if not fs_utils.exists(str(repo_cred_file)):
        credentials.update(_load_env_credentials())

    # @@ STEP 3: Try to load repository-specific credentials. @@
    repo_cred_file = _get_credential_file_path(repository_url, project_dir)
    if fs_utils.exists(str(repo_cred_file)):
        try:
            # Read the credential file directly and parse it manually to avoid file locking issues.
            content = fs_utils.read_text(str(repo_cred_file))

            # || S.S. 3.1: Parse the .env file manually. ||
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present.
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Only store credential keys we care about.
                    if key in CREDENTIAL_KEYS + [GITLAB_PRIVATE_TOKEN_KEY]:
                        credentials[key.lower()] = value

            get_logger().debug(f"Loaded repository-specific credentials from {repo_cred_file}")

        except Exception as e:
            raise CredentialServiceError(
                f"Failed to load repository credentials from {repo_cred_file}: {e}"
            ) from e

    return credentials


def save_repository_credentials(repository_url: str, project_dir: Path = None,
                              github_token: str = None, gitlab_token: str = None,
                              ftp_username: str = None, ftp_password: str = None,
                              sftp_username: str = None, sftp_password: str = None) -> bool:
    """Save credentials for a specific repository within a project.

    :param repository_url: Repository URL to save credentials for.
    :type repository_url: str
    :param project_dir: Project directory (uses current directory if not provided), defaults to None.
    :type project_dir: Path, optional
    :param github_token: Optional GitHub token, defaults to None.
    :type github_token: str, optional
    :param gitlab_token: Optional GitLab token, defaults to None.
    :type gitlab_token: str, optional
    :param ftp_username: Optional FTP username, defaults to None.
    :type ftp_username: str, optional
    :param ftp_password: Optional FTP password, defaults to None.
    :type ftp_password: str, optional
    :param sftp_username: Optional SFTP username, defaults to None.
    :type sftp_username: str, optional
    :param sftp_password: Optional SFTP password, defaults to None.
    :type sftp_password: str, optional
    :return bool: True if credentials were saved successfully.
    :raises CredentialServiceError: If saving fails.
    """
    try:
        # @@ STEP 1: Set default project directory if not provided. @@
        if project_dir is None:
            project_dir = Path.cwd()

        # @@ STEP 2: Ensure credentials directory exists. @@
        credentials_dir = project_dir / CHAINEDPY_DIR / CREDENTIALS_DIR
        fs_utils.makedirs(str(credentials_dir), exist_ok=True)

        # @@ STEP 3: Generate credential file content with all credential types. @@
        env_content = _generate_repository_env_template(
            repository_url, github_token, gitlab_token,
            ftp_username, ftp_password, sftp_username, sftp_password
        )

        # @@ STEP 4: Save to repository-specific file. @@
        repo_cred_file = _get_credential_file_path(repository_url, project_dir)
        fs_utils.write_text(str(repo_cred_file), env_content)

        get_logger().info(f"Saved repository credentials to {repo_cred_file}")
        return True

    except Exception as e:
        error_msg = f"Failed to save repository credentials: {e}"
        raise CredentialServiceError(error_msg) from e


def _generate_repository_env_template(repository_url: str, github_token: str = None,
                                    gitlab_token: str = None, ftp_username: str = None,
                                    ftp_password: str = None, sftp_username: str = None,
                                    sftp_password: str = None) -> str:
    """Generate repository-specific .env file template content.

    :param repository_url: Repository URL.
    :type repository_url: str
    :param github_token: Optional GitHub token, defaults to None.
    :type github_token: str, optional
    :param gitlab_token: Optional GitLab token, defaults to None.
    :type gitlab_token: str, optional
    :param ftp_username: Optional FTP username, defaults to None.
    :type ftp_username: str, optional
    :param ftp_password: Optional FTP password, defaults to None.
    :type ftp_password: str, optional
    :param sftp_username: Optional SFTP username, defaults to None.
    :type sftp_username: str, optional
    :param sftp_password: Optional SFTP password, defaults to None.
    :type sftp_password: str, optional
    :return str: .env file content as string.
    """
    return render_template(
        TEMPLATE_REPOSITORY_ENV,
        repository_url=repository_url,
        github_token=github_token,
        gitlab_token=gitlab_token,
        ftp_username=ftp_username,
        ftp_password=ftp_password,
        sftp_username=sftp_username,
        sftp_password=sftp_password
    )


def list_repository_credentials(project_dir: Path = None) -> Dict[str, Path]:
    """List all repository-specific credential files within a project.

    :param project_dir: Project directory (uses current directory if not provided), defaults to None.
    :type project_dir: Path, optional
    :return Dict[str, Path]: Dictionary mapping repository keys to credential file paths.
    """
    credentials_map = {}

    # @@ STEP 1: Set default project directory if not provided. @@
    if project_dir is None:
        project_dir = Path.cwd()

    # @@ STEP 2: Initialize credentials directory and result dictionary. @@
    credentials_dir = project_dir / CHAINEDPY_DIR / CREDENTIALS_DIR

    if not fs_utils.exists(str(credentials_dir)):
        return credentials_map

    # @@ STEP 3: List all .env files in credentials directory. @@
    pattern = str(credentials_dir / f"*{ENV_FILE_EXTENSION}")
    try:
        for file_path in glob.glob(pattern): # TODO: USE FSSPEC SERVICE. NO GLOB.
            file_path_obj = Path(file_path)
            if file_path_obj.name != DEFAULT_ENV_FILE_NAME:  # Skip default file.
                key = file_path_obj.stem  # Remove .env extension.
                credentials_map[key] = file_path_obj
    except Exception as e:
        raise CredentialServiceError(
            f"Failed to list repository credentials: {e}"
        ) from e

    return credentials_map


def remove_repository_credentials(repository_url: str, project_dir: Path = None) -> bool:
    """Remove credentials for a specific repository within a project.

    :param repository_url: Repository URL to remove credentials for.
    :type repository_url: str
    :param project_dir: Project directory (uses current directory if not provided), defaults to None.
    :type project_dir: Path, optional
    :return bool: True if credentials were removed successfully.
    :raises CredentialServiceError: If removal fails.
    """
    # @@ STEP 1: Get credential file path. @@
    repo_cred_file = _get_credential_file_path(repository_url, project_dir)

    # @@ STEP 2: Remove credentials file if it exists. @@
    if fs_utils.exists(str(repo_cred_file)):
        try:
            os.unlink(repo_cred_file)
            get_logger().info(f"Removed repository credentials: {repo_cred_file}")
            return True
        except Exception as e:
            raise CredentialServiceError(
                f"Failed to remove repository credentials: {e}"
            ) from e
    else:
        get_logger().debug(f"No credentials found for repository: {repository_url}")
        return False
