"""Unified filesystem utilities for ChainedPy.

This service provides uniform fsspec-based file operations for both local and remote files,
ensuring consistent behavior across all filesystem operations in ChainedPy. It abstracts
away the complexity of different storage backends and provides a unified interface for
file operations regardless of whether files are local, on GitHub, GitLab, FTP, or other
supported filesystems.

The service handles authentication, credential management, and protocol-specific operations
transparently, allowing other parts of ChainedPy to work with files using simple, consistent
APIs. All file operations go through this service to maintain consistency and enable
easy testing and mocking.

Note:
    This is the ONLY module that should perform direct file I/O operations in ChainedPy.
    All other modules should use the functions provided here rather than accessing
    files directly through pathlib, open(), or other mechanisms.

Example:
    ```python
    from chainedpy.services import filesystem_service as fs
    from pathlib import Path

    # Local file operations
    content = fs.read_text(Path("config.yaml"))
    fs.write_text(Path("output.txt"), "Hello World")

    # Remote file operations (same API)
    remote_content = fs.read_text("https://github.com/user/repo/raw/main/config.yaml")

    # Directory operations
    if fs.exists(Path("my_directory")):
        files = fs.list_directory(Path("my_directory"))

    # YAML operations
    config = fs.read_yaml(Path("chainedpy.yaml"))
    fs.write_yaml(Path("output.yaml"), {"key": "value"})
    ```

See Also:
    - [read_text][chainedpy.services.filesystem_service.read_text]: Read text files
    - [write_text][chainedpy.services.filesystem_service.write_text]: Write text files
    - [read_yaml][chainedpy.services.filesystem_service.read_yaml]: Read YAML files
    - [chainedpy.services.credential_service][chainedpy.services.credential_service]: Credential management for remote access
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

# @@ STEP 2: Import third-party modules. @@
import yaml
import fsspec
from dotenv import load_dotenv

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    # URL patterns
    GITLAB_TOKEN_KEY, URL_SCHEME_HTTPS, URL_SCHEME_SEPARATOR, SUPPORTED_URL_SCHEMES,
    ENV_FILE_NAME, CREDENTIAL_KEYS, GITLAB_PRIVATE_TOKEN_KEY, PYTHON_EXTENSION,
    # Default values
    DEFAULT_BASE_PROJECT,
    # Credential keys
    GITHUB_TOKEN_KEY,
    FTP_USERNAME_KEY, FTP_PASSWORD_KEY, SFTP_USERNAME_KEY, SFTP_PASSWORD_KEY,
    # Configuration keys
    CONFIG_KEY_BASE_PROJECT, CONFIG_KEY_SUMMARY,
    # Filesystem types
    FS_TYPE_LOCAL, FS_TYPE_FILE, FS_TYPE_GITHUB, FS_TYPE_GITLAB, FS_TYPE_HTTP, FS_TYPE_HTTPS, FS_TYPE_FTP, FS_TYPE_SFTP,
    # Domain constants
    GITHUB_RAW_DOMAIN, GITHUB_DOMAIN, GITHUB_API_DOMAIN, GITLAB_DOMAIN, GITLAB_KEYWORD, GITLAB_PRIVATE_TOKEN_HEADER,
)

# @@ STEP 4: Import ChainedPy services. @@
from chainedpy.services.credential_service import load_repository_credentials

# @@ STEP 5: Import ChainedPy internal modules. @@
from chainedpy.exceptions import FilesystemServiceError

# @@ STEP 6: Import TYPE_CHECKING modules. @@
# (none)

from chainedpy.services.logging_service import get_logger


# @@ STEP 7: Define module-level variables. @@
_env_loaded = False

def _validate_url_scheme(url: str) -> None:
    """Validate URL scheme against supported schemes.

    Example:
        ```python
        from chainedpy.services.filesystem_service import _validate_url_scheme
        from chainedpy.exceptions import FilesystemServiceError

        # Valid schemes pass without error
        _validate_url_scheme("https://github.com/user/repo")
        _validate_url_scheme("file:///local/path")
        _validate_url_scheme("/local/path")  # Local paths are always valid

        # Invalid scheme raises error
        try:
            _validate_url_scheme("ftp://example.com/file")
        except FilesystemServiceError as e:
            print(f"Unsupported scheme: {e}")
            assert "ftp" in str(e)
            assert "Supported schemes" in str(e)

        # Custom protocol error
        try:
            _validate_url_scheme("custom://protocol/path")
        except FilesystemServiceError as e:
            print(f"Custom protocol not supported: {e}")
        ```

    :param url: URL to validate.
    :type url: [str][str]
    :raises FilesystemServiceError: If URL scheme is not supported.
    """
    if URL_SCHEME_SEPARATOR not in url:
        return  # Local path, no validation needed.

    parsed = urlparse(url)

    if parsed.scheme and parsed.scheme.lower() not in SUPPORTED_URL_SCHEMES:
        raise FilesystemServiceError(
            f"Unsupported URL scheme '{parsed.scheme}'. "
            f"Supported schemes: {', '.join(sorted(SUPPORTED_URL_SCHEMES))}"
        )

def load_env_credentials() -> Dict[str, str]:
    """Load credentials from .env file if available.

    Example:
        ```python
        from chainedpy.services.filesystem_service import load_env_credentials
        import os
        from pathlib import Path

        # Create a test .env file
        env_content = '''
        GITHUB_TOKEN=ghp_example_token
        GITLAB_PRIVATE_TOKEN=glpat_example_token
        CUSTOM_KEY=custom_value
        '''
        Path(".env").write_text(env_content)

        # Load credentials
        credentials = load_env_credentials()

        # Check loaded credentials
        assert "github_token" in credentials
        assert credentials["github_token"] == "ghp_example_token"
        assert "gitlab_private_token" in credentials

        # Credentials are lowercase keys
        print(f"GitHub token: {credentials.get('github_token')}")
        print(f"GitLab token: {credentials.get('gitlab_private_token')}")

        # Empty dict if no .env file
        Path(".env").unlink()  # Remove .env
        credentials = load_env_credentials()
        assert isinstance(credentials, dict)
        ```

    :return [Dict][dict][[str][str], [str][str]]: Dictionary of loaded credentials.
    """
    global _env_loaded

    # @@ STEP 1: Load environment file if not already loaded. @@
    if not _env_loaded:
        # Try to load from current directory .env file only.
        env_path = Path.cwd() / ENV_FILE_NAME
        if env_path.exists():
            load_dotenv(env_path)
            get_logger().debug(f"Loaded environment variables from {env_path}")
        _env_loaded = True

    # @@ STEP 2: Extract relevant credentials from environment. @@
    credentials = {}
    credential_keys = CREDENTIAL_KEYS + [GITLAB_PRIVATE_TOKEN_KEY]

    for key in credential_keys:
        value = os.environ.get(key)
        if value:
            credentials[key.lower()] = value

    return credentials


def get_filesystem(path_or_url: str, credentials: Optional[Dict[str, str]] = None) -> tuple[Any, str]:
    """Get appropriate fsspec filesystem for the given path or URL.

    :param path_or_url: Local path or remote URL.
    :type path_or_url: str
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: Optional[Dict[str, str]], optional
    :return tuple[Any, str]: Tuple of (filesystem instance, filesystem type).
    :raises FilesystemServiceError: If URL scheme is not supported.
    """
    _validate_url_scheme(path_or_url)

    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in path_or_url:
            credentials = load_repository_credentials(path_or_url)
        else:
            credentials = load_env_credentials()

    # @@ STEP 2: Parse the URL/path to determine filesystem type. @@
    if URL_SCHEME_SEPARATOR not in path_or_url:
        # Local path - always use fsspec file system for uniformity.
        return fsspec.filesystem(FS_TYPE_FILE), FS_TYPE_LOCAL

    parsed = urlparse(path_or_url)
    scheme = parsed.scheme.lower()

    fs_kwargs = {}
    
    # @@ STEP 3: Handle HTTP/HTTPS schemes. @@
    if scheme in (FS_TYPE_HTTP, FS_TYPE_HTTPS):
        # || S.S. 3.1: Determine if it's GitHub, GitLab, or generic HTTP. ||
        if GITHUB_RAW_DOMAIN in parsed.netloc:
            # GitHub raw URLs should use HTTP filesystem with authentication headers.
            http_kwargs = {}
            if credentials.get(GITHUB_TOKEN_KEY):
                token = credentials[GITHUB_TOKEN_KEY]
                http_kwargs["headers"] = {"Authorization": f"token {token}"}
            return fsspec.filesystem(FS_TYPE_HTTP, **http_kwargs), FS_TYPE_GITHUB
        elif GITHUB_DOMAIN in parsed.netloc:
            # Don't convert GitHub API URLs - they should use HTTP filesystem directly.
            if parsed.netloc == GITHUB_API_DOMAIN:
                # GitHub API URLs use HTTP filesystem with auth headers.
                http_kwargs = {}
                if credentials.get(GITHUB_TOKEN_KEY):
                    token = credentials[GITHUB_TOKEN_KEY]
                    http_kwargs["headers"] = {"Authorization": f"token {token}"}
                return fsspec.filesystem(FS_TYPE_HTTP, **http_kwargs), FS_TYPE_HTTP

            # Convert github.com URLs to raw.githubusercontent.com format for file access.
            if "/blob/" in path_or_url:
                # github.com/user/repo/blob/branch/path -> raw.githubusercontent.com/user/repo/branch/path.
                raw_url = path_or_url.replace(f"{URL_SCHEME_HTTPS}{GITHUB_DOMAIN}/", f"{URL_SCHEME_HTTPS}{GITHUB_RAW_DOMAIN}/")
                raw_url = raw_url.replace("/blob/", "/")
            elif "/tree/" in path_or_url:
                # github.com/user/repo/tree/branch/path -> raw.githubusercontent.com/user/repo/branch/path.
                raw_url = path_or_url.replace(f"{URL_SCHEME_HTTPS}{GITHUB_DOMAIN}/", f"{URL_SCHEME_HTTPS}{GITHUB_RAW_DOMAIN}/")
                raw_url = raw_url.replace("/tree/", "/")
            else:
                # github.com/user/repo -> raw.githubusercontent.com/user/repo/main/.
                raw_url = path_or_url.replace(f"{URL_SCHEME_HTTPS}{GITHUB_DOMAIN}/", f"{URL_SCHEME_HTTPS}{GITHUB_RAW_DOMAIN}/")
                if not raw_url.endswith("/"):
                    raw_url += "/main/"

            # Recursively call with the converted raw URL.
            return get_filesystem(raw_url, credentials)

        elif GITLAB_DOMAIN in parsed.netloc or GITLAB_KEYWORD in parsed.netloc:
            # GitLab - use HTTP with token if available.
            if credentials.get(GITLAB_TOKEN_KEY):
                fs_kwargs["headers"] = {GITLAB_PRIVATE_TOKEN_HEADER: credentials[GITLAB_TOKEN_KEY]}
            elif credentials.get(GITLAB_PRIVATE_TOKEN_KEY):
                fs_kwargs["headers"] = {GITLAB_PRIVATE_TOKEN_HEADER: credentials[GITLAB_PRIVATE_TOKEN_KEY]}
            return fsspec.filesystem(FS_TYPE_HTTP, **fs_kwargs), FS_TYPE_GITLAB

        else:
            # Generic HTTP.
            return fsspec.filesystem(FS_TYPE_HTTP), FS_TYPE_HTTP
    
    # @@ STEP 4: Handle FTP scheme. @@
    elif scheme == FS_TYPE_FTP:
        if credentials.get(FTP_USERNAME_KEY):
            fs_kwargs["username"] = credentials[FTP_USERNAME_KEY]
        if credentials.get(FTP_PASSWORD_KEY):
            fs_kwargs["password"] = credentials[FTP_PASSWORD_KEY]
        return fsspec.filesystem(FS_TYPE_FTP, **fs_kwargs), FS_TYPE_FTP

    # @@ STEP 5: Handle SFTP scheme. @@
    elif scheme == FS_TYPE_SFTP:
        if credentials.get(SFTP_USERNAME_KEY):
            fs_kwargs["username"] = credentials[SFTP_USERNAME_KEY]
        if credentials.get(SFTP_PASSWORD_KEY):
            fs_kwargs["password"] = credentials[SFTP_PASSWORD_KEY]
        return fsspec.filesystem(FS_TYPE_SFTP, **fs_kwargs), FS_TYPE_SFTP

    # @@ STEP 6: Handle unknown schemes. @@
    else:
        # Try to create filesystem for unknown schemes.
        try:
            return fsspec.filesystem(scheme, **fs_kwargs), scheme
        except Exception as e:
            raise ValueError(f"Unsupported filesystem scheme '{scheme}': {e}")


def read_text(path_or_url: str, encoding: str = 'utf-8', credentials: Optional[Dict[str, str]] = None) -> str:
    """Read text from a file using fsspec (uniform for local and remote).

    :param path_or_url: Local path or remote URL to read from.
    :type path_or_url: [str][str]
    :param encoding: Text encoding, defaults to 'utf-8'.
    :type encoding: [str][str], optional
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :return [str][str]: File content as string.
    :raises FilesystemServiceError: If reading fails.

    Example:
        ```python
        from chainedpy.services.filesystem_service import read_text
        from chainedpy.exceptions import FilesystemServiceError
        from pathlib import Path

        # Read local file
        Path("test.txt").write_text("Hello, World!")
        content = read_text("test.txt")
        assert content == "Hello, World!"

        # Read with specific encoding
        Path("utf8.txt").write_text("Héllo, Wörld!", encoding="utf-8")
        content = read_text("utf8.txt", encoding="utf-8")
        assert "Héllo" in content

        # Read remote file (GitHub)
        content = read_text(
            "https://raw.githubusercontent.com/user/repo/main/README.md",
            credentials={"github_token": "ghp_example"}
        )
        assert isinstance(content, str)

        # Error handling
        try:
            read_text("nonexistent.txt")
        except FilesystemServiceError as e:
            print(f"File not found: {e}")

        # Read with auto-detected credentials
        content = read_text("https://github.com/user/repo/raw/main/file.txt")
        ```
    """
    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in path_or_url:
            credentials = load_repository_credentials(path_or_url)
        else:
            credentials = load_env_credentials()

    # @@ STEP 2: Convert GitHub blob URLs to raw URLs if needed. @@
    if (GITHUB_DOMAIN in path_or_url and "/blob/" in path_or_url):
        path_or_url = path_or_url.replace(f"{URL_SCHEME_HTTPS}{GITHUB_DOMAIN}/", f"{URL_SCHEME_HTTPS}{GITHUB_RAW_DOMAIN}/")
        path_or_url = path_or_url.replace("/blob/", "/")
    elif (GITHUB_DOMAIN in path_or_url and "/tree/" in path_or_url):
        path_or_url = path_or_url.replace(f"{URL_SCHEME_HTTPS}{GITHUB_DOMAIN}/", f"{URL_SCHEME_HTTPS}{GITHUB_RAW_DOMAIN}/")
        path_or_url = path_or_url.replace("/tree/", "/")

    # @@ STEP 3: Get filesystem and read file. @@
    fs, fs_type = get_filesystem(path_or_url, credentials)

    try:
        if fs_type == FS_TYPE_LOCAL:
            # For local files, path_or_url is just a path.
            with fs.open(path_or_url, 'r', encoding=encoding) as f:
                return f.read()
        else:
            # For remote files, we may need to handle authentication.
            open_kwargs = {'encoding': encoding}
            if fs_type in (FS_TYPE_HTTP, FS_TYPE_GITLAB) and hasattr(fs, 'session') and fs.session:
                # HTTP-based filesystems may need headers passed through.
                pass  # Headers are already set in filesystem creation.

            with fs.open(path_or_url, 'r', **open_kwargs) as f:
                return f.read()
    except Exception as e:
        msg = f"Failed to read text from {path_or_url}: {e}"
        raise FilesystemServiceError(msg) from e


def write_text(path_or_url: str, content: str, encoding: str = 'utf-8',
               credentials: Optional[Dict[str, str]] = None) -> None:
    """Write text to a file using fsspec (uniform for local and remote).

    Example:
        ```python
        from chainedpy.services.filesystem_service import write_text, read_text
        from chainedpy.exceptions import FilesystemServiceError
        from pathlib import Path

        # Write local file
        write_text("output.txt", "Hello, World!")
        assert Path("output.txt").read_text() == "Hello, World!"

        # Write with specific encoding
        write_text("utf8.txt", "Héllo, Wörld!", encoding="utf-8")
        content = read_text("utf8.txt", encoding="utf-8")
        assert "Héllo" in content

        # Write to directory (creates parent dirs)
        write_text("subdir/nested.txt", "Nested content")
        assert Path("subdir/nested.txt").exists()

        # Error handling for protected paths
        try:
            write_text("/root/protected.txt", "content")
        except FilesystemServiceError as e:
            print(f"Permission denied: {e}")

        # Remote writing (if supported)
        try:
            write_text(
                "ftp://example.com/file.txt",
                "Remote content",
                credentials={"ftp_username": "user", "ftp_password": "pass"}
            )
        except NotImplementedError as e:
            print(f"Remote writing not supported: {e}")
        ```

    :param path_or_url: Local path or remote URL to write to.
    :type path_or_url: [str][str]
    :param content: Text content to write.
    :type content: [str][str]
    :param encoding: Text encoding, defaults to 'utf-8'.
    :type encoding: [str][str], optional
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :raises FilesystemServiceError: If writing fails.
    :raises NotImplementedError: If writing to remote filesystem is not supported.
    """
    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in path_or_url:
            credentials = load_repository_credentials(path_or_url)
        else:
            credentials = load_env_credentials()

    # @@ STEP 2: Get filesystem and write file. @@
    fs, fs_type = get_filesystem(path_or_url, credentials)

    try:
        if fs_type == FS_TYPE_LOCAL:
            # For local files, ensure parent directories exist.
            path_obj = Path(path_or_url)
            path_obj.parent.mkdir(parents=True, exist_ok=True)

            with fs.open(path_or_url, 'w', encoding=encoding) as f:
                f.write(content)
        else:
            # For remote files, writing may not be supported.
            raise NotImplementedError(f"Writing to {fs_type} filesystem is not supported")
    except Exception as e:
        msg = f"Failed to write text to {path_or_url}: {e}"
        raise FilesystemServiceError(msg) from e


def exists(path_or_url: str, credentials: Optional[Dict[str, str]] = None) -> bool:
    """Check if a file or directory exists using fsspec.

    Example:
        ```python
        from chainedpy.services.filesystem_service import exists, write_text
        from chainedpy.exceptions import FilesystemServiceError
        from pathlib import Path

        # Check local file existence
        write_text("test.txt", "content")
        assert exists("test.txt") == True
        assert exists("nonexistent.txt") == False

        # Check directory existence
        Path("testdir").mkdir(exist_ok=True)
        assert exists("testdir") == True
        assert exists("nonexistent_dir") == False

        # Check remote file existence
        remote_exists = exists(
            "https://raw.githubusercontent.com/user/repo/main/README.md",
            credentials={"github_token": "ghp_example"}
        )
        assert isinstance(remote_exists, bool)

        # Error handling for invalid URLs
        try:
            exists("invalid://protocol/path")
        except FilesystemServiceError as e:
            print(f"Invalid URL: {e}")

        # Auto-detect credentials
        exists("https://github.com/user/repo/raw/main/file.txt")
        ```

    :param path_or_url: Local path or remote URL to check.
    :type path_or_url: [str][str]
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :return [bool][bool]: True if path exists, False otherwise.
    :raises FilesystemServiceError: If check fails.
    """
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL
        if URL_SCHEME_SEPARATOR in path_or_url:
            credentials = load_repository_credentials(path_or_url)
        else:
            credentials = load_env_credentials()
    
    fs, fs_type = get_filesystem(path_or_url, credentials)
    
    try:
        return fs.exists(path_or_url)
    except Exception as e:
        get_logger().debug(f"Error checking existence of {path_or_url}: {e}")
        return False


def makedirs(path_or_url: str, exist_ok: bool = True, credentials: Optional[Dict[str, str]] = None) -> None:
    """Create directories using fsspec (only for local filesystem).
 
    Example:
        ```python
        from chainedpy.services.filesystem_service import makedirs, exists, write_text
        from chainedpy.exceptions import FilesystemServiceError
        from pathlib import Path
        import shutil

        # Create nested directories
        makedirs("deep/nested/path")
        assert exists("deep/nested/path") == True

        # Create with exist_ok=True (default)
        makedirs("existing/path")
        makedirs("existing/path")  # No error

        # Create with exist_ok=False
        makedirs("new/path", exist_ok=False)
        try:
            makedirs("new/path", exist_ok=False)  # Should raise error
        except FilesystemServiceError as e:
            print(f"Directory exists: {e}")

        # Use for file parent directories
        makedirs("parent/subdir")
        write_text("parent/subdir/file.txt", "content")
        assert exists("parent/subdir/file.txt") == True

        # Error for remote URLs
        try:
            makedirs("https://example.com/path")
        except NotImplementedError as e:
            print(f"Remote directories not supported: {e}")

        # Cleanup
        shutil.rmtree("deep", ignore_errors=True)
        shutil.rmtree("existing", ignore_errors=True)
        shutil.rmtree("new", ignore_errors=True)
        shutil.rmtree("parent", ignore_errors=True)
        ```

    :param path_or_url: Local path to create directories for.
    :type path_or_url: [str][str]
    :param exist_ok: If True, don't raise error if directory exists, defaults to True.
    :type exist_ok: [bool][bool], optional
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :raises NotImplementedError: If trying to create directories on remote filesystem.
    :raises FilesystemServiceError: If directory creation fails.
    """
    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in path_or_url:
            credentials = load_repository_credentials(path_or_url)
        else:
            credentials = load_env_credentials()

    # @@ STEP 2: Get filesystem and validate it's local. @@
    fs, fs_type = get_filesystem(path_or_url, credentials)

    if fs_type != FS_TYPE_LOCAL:
        raise NotImplementedError(f"Directory creation on {fs_type} filesystem is not supported")

    # @@ STEP 3: Create directories. @@
    try:
        # For local filesystem, use Path for directory creation.
        Path(path_or_url).mkdir(parents=True, exist_ok=exist_ok)
    except Exception as e:
        msg = f"Failed to create directories for {path_or_url}: {e}"
        raise FilesystemServiceError(msg) from e


def read_config(config_path: str, credentials: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Read project configuration from filesystem using fsspec.

    Example:
        ```python
        from chainedpy.services.filesystem_service import read_config, write_text
        from chainedpy.exceptions import FilesystemServiceError
        import yaml

        # Create test config file
        config_data = {
            "project": {
                "base_project": "chainedpy",
                "summary": "Test project description"
            }
        }
        config_content = yaml.dump(config_data)
        write_text("chainedpy.yaml", config_content)

        # Read configuration
        config = read_config("chainedpy.yaml")
        assert config["base_project"] == "chainedpy"
        assert config["summary"] == "Test project description"

        # Read remote configuration
        remote_config = read_config(
            "https://raw.githubusercontent.com/user/repo/main/chainedpy.yaml",
            credentials={"github_token": "ghp_example"}
        )
        assert isinstance(remote_config, dict)
        assert "base_project" in remote_config

        # Error handling for invalid config
        write_text("invalid.yaml", "invalid: yaml: content:")
        try:
            read_config("invalid.yaml")
        except FilesystemServiceError as e:
            print(f"Config parsing failed: {e}")

        # Error for missing file
        try:
            read_config("nonexistent.yaml")
        except FilesystemServiceError as e:
            print(f"Config not found: {e}")
        ```

    :param config_path: Path to configuration file.
    :type config_path: [str][str]
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :return [Dict][dict][[str][str], [str][str]]: Configuration dictionary with base_project and summary.
    :raises FilesystemServiceError: If reading or parsing config fails.
    """
    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in config_path:
            credentials = load_repository_credentials(config_path)
        else:
            credentials = load_env_credentials()

    try:
        # @@ STEP 2: Read and parse configuration file. @@
        content = read_text(config_path, credentials=credentials)

        # Parse the YAML configuration content.
        config_data = yaml.safe_load(content)

        # Extract project configuration.
        project_section = config_data["project"] # config_data.get('project', {})

        # @@ STEP 3: Return standardized configuration. @@
        return {
            CONFIG_KEY_BASE_PROJECT: str(project_section.get(CONFIG_KEY_BASE_PROJECT, DEFAULT_BASE_PROJECT)).strip(),
            CONFIG_KEY_SUMMARY: str(project_section[CONFIG_KEY_SUMMARY]).strip()
        }

    except Exception as e:
        msg = f"Failed to read config from {config_path}: {e}"
        raise FilesystemServiceError(msg) from e


def write_config(config_path: str, base_project: str, summary: str,
                 credentials: Optional[Dict[str, str]] = None) -> None:
    """Write project configuration to filesystem using fsspec.

    Example:
        ```python
        from chainedpy.services.filesystem_service import write_config, read_config, read_text
        from chainedpy.exceptions import FilesystemServiceError
        from pathlib import Path

        # Write configuration file
        write_config(
            "chainedpy.yaml",
            base_project="chainedpy",
            summary="My custom ChainedPy project"
        )

        # Verify written config
        config = read_config("chainedpy.yaml")
        assert config["base_project"] == "chainedpy"
        assert config["summary"] == "My custom ChainedPy project"

        # Check YAML format
        content = read_text("chainedpy.yaml")
        assert "project:" in content
        assert "base_project: chainedpy" in content
        assert "summary: My custom ChainedPy project" in content

        # Write to subdirectory
        write_config(
            "subproject/chainedpy.yaml",
            base_project="advanced_chain",
            summary="Advanced project configuration"
        )
        assert Path("subproject/chainedpy.yaml").exists()

        # Error handling for protected paths
        try:
            write_config("/root/protected.yaml", "base", "summary")
        except FilesystemServiceError as e:
            print(f"Permission denied: {e}")

        # Cleanup
        Path("chainedpy.yaml").unlink(missing_ok=True)
        Path("subproject/chainedpy.yaml").unlink(missing_ok=True)
        Path("subproject").rmdir()
        ```

    :param config_path: Path to write configuration file to.
    :type config_path: [str][str]
    :param base_project: Base project name.
    :type base_project: [str][str]
    :param summary: Project summary.
    :type summary: [str][str]
    :param credentials: Optional credentials dictionary, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :raises FilesystemServiceError: If writing config fails.
    """
    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in config_path:
            credentials = load_repository_credentials(config_path)
        else:
            credentials = load_env_credentials()

    # @@ STEP 2: Create YAML configuration structure. @@
    config_data = {
        'project': {
            CONFIG_KEY_BASE_PROJECT: base_project,
            CONFIG_KEY_SUMMARY: summary
        }
    }

    # @@ STEP 3: Convert config to YAML and write. @@
    content = yaml.dump(config_data, default_flow_style=False, sort_keys=False)

    write_text(config_path, content, credentials=credentials)


def glob(pattern: str, credentials: Optional[Dict[str, str]] = None) -> List[str]:
    """Find files matching a glob pattern using fsspec.

    Example:
        ```python
        from chainedpy.services.filesystem_service import glob, write_text, makedirs
        from chainedpy.exceptions import FilesystemServiceError
        from pathlib import Path
        import shutil

        # Create test files
        makedirs("testdir/subdir")
        write_text("test1.py", "# Python file 1")
        write_text("test2.py", "# Python file 2")
        write_text("testdir/test3.py", "# Python file 3")
        write_text("testdir/subdir/test4.py", "# Python file 4")
        write_text("readme.txt", "Text file")

        # Find Python files in current directory
        py_files = glob("*.py")
        assert "test1.py" in py_files
        assert "test2.py" in py_files
        assert len([f for f in py_files if f.endswith(".py")]) >= 2

        # Find all Python files recursively
        all_py_files = glob("**/*.py")
        assert "test1.py" in all_py_files
        assert "testdir/test3.py" in all_py_files
        assert "testdir/subdir/test4.py" in all_py_files

        # Find text files
        txt_files = glob("*.txt")
        assert "readme.txt" in txt_files

        # No matches
        no_matches = glob("*.nonexistent")
        assert no_matches == []

        # Error handling for invalid patterns
        try:
            glob("invalid://pattern")
        except FilesystemServiceError as e:
            print(f"Invalid pattern: {e}")

        # Cleanup
        Path("test1.py").unlink(missing_ok=True)
        Path("test2.py").unlink(missing_ok=True)
        Path("readme.txt").unlink(missing_ok=True)
        shutil.rmtree("testdir", ignore_errors=True)
        ```

    :param pattern: Glob pattern to match (e.g., "*.py", "**/*.txt").
    :type pattern: [str][str]
    :param credentials: Optional credentials for remote filesystems, defaults to None.
    :type credentials: [Optional][typing.Optional][[Dict][dict][[str][str], [str][str]]], optional
    :return [List][list][[str][str]]: List of file paths matching the pattern.
    :raises FilesystemServiceError: If glob operation fails.
    """
    # @@ STEP 1: Load credentials if not provided. @@
    if credentials is None:
        # Use repository-specific credentials if it's a remote URL.
        if URL_SCHEME_SEPARATOR in pattern:
            credentials = load_repository_credentials(pattern)
        else:
            credentials = load_env_credentials()

    # @@ STEP 2: Get filesystem and perform glob operation. @@
    try:
        fs, fs_type = get_filesystem(pattern, credentials)
        return fs.glob(pattern)
    except Exception as e:
        msg = f"Failed to glob pattern {pattern}: {e}"
        raise FilesystemServiceError(msg) from e


def discover_plugin_files(base_url: str, plugin_type: str) -> List[Dict[str, str]]:
    """Discover plugin files in a remote directory using filesystem operations.

    Example:
        ```python
        from chainedpy.services.filesystem_service import discover_plugin_files
        from chainedpy.exceptions import FilesystemServiceError

        # Discover 'then' plugins in a remote repository
        try:
            then_plugins = discover_plugin_files(
                "https://raw.githubusercontent.com/user/chainedpy-plugins/main/plugins",
                "then"
            )

            for plugin in then_plugins:
                print(f"Plugin: {plugin['name']}")
                print(f"URL: {plugin['url']}")
                assert plugin['name'].startswith("then_")
                assert plugin['name'].endswith(".py")
                assert plugin['url'].startswith("https://")

        except FilesystemServiceError as e:
            print(f"Plugin discovery failed: {e}")

        # Discover 'as_' plugins
        try:
            as_plugins = discover_plugin_files(
                "https://raw.githubusercontent.com/user/chainedpy-plugins/main/plugins",
                "as_"
            )

            for plugin in as_plugins:
                assert plugin['name'].startswith("as_")
                assert 'name' in plugin
                assert 'url' in plugin

        except FilesystemServiceError as e:
            print(f"As plugins discovery failed: {e}")

        # Error handling for invalid URLs
        try:
            discover_plugin_files("invalid://url", "then")
        except FilesystemServiceError as e:
            print(f"Invalid URL: {e}")
        ```

    :param base_url: Base URL of the plugin directory.
    :type base_url: [str][str]
    :param plugin_type: Type of plugin (then, as_, processors).
    :type plugin_type: [str][str]
    :return [List][list][[Dict][dict][[str][str], [str][str]]]: List of dictionaries with 'name' and 'url' keys for each discovered plugin file.
    :raises FilesystemServiceError: If discovery fails.
    """
    try:
        # @@ STEP 1: Initialize discovery. @@
        discovered_files = []

        # @@ STEP 2: Use filesystem operations to list directory contents. @@
        fs, fs_type = get_filesystem(base_url)

        # @@ STEP 3: Try to list files in the directory. @@
        files = fs.ls(base_url, detail=False)
        for file_path in files:
            filename = file_path.split('/')[-1] if '/' in file_path else file_path
            # Check if it's a Python plugin file for this plugin type.
            if filename.startswith(f"{plugin_type}_") and filename.endswith(PYTHON_EXTENSION):
                discovered_files.append({
                    'name': filename,
                    'url': f"{base_url}/{filename}"
                })

        return discovered_files

    except Exception as e:
        msg = f"Failed to discover plugin files in {base_url}: {e}"
        raise FilesystemServiceError(msg) from e


def normalize_filesystem_probe_target(path_or_url: str) -> str:
    """Normalize a filesystem probe target into a stable lookup string.

    :param path_or_url: Local path or remote URL.
    :type path_or_url: str
    :return str: Normalized probe target.
    """
    if URL_SCHEME_SEPARATOR in path_or_url:
        return path_or_url.rstrip("/")
    return str(Path(path_or_url).expanduser())
