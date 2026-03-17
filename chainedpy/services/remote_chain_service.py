"""Remote Chain Download Service.

This service handles downloading and dependency resolution for remote ChainedPy projects
directly to project directories. It supports recursive dependency resolution with
per-repository credential management, caching, and update detection.

The service provides comprehensive functionality for working with remote ChainedPy
projects including download, caching, dependency resolution, update checking, and
metadata management. It handles authentication for private repositories and maintains
local caches to improve performance.

Note:
    Remote chains are downloaded directly to project directories to enable natural
    import statements. The service manages metadata, dependencies, and ensures
    proper cleanup and update mechanisms.

Example:
    ```python
    from chainedpy.services.remote_chain_service import (
        download_remote_chain, resolve_dependencies_recursively,
        check_for_updates, list_remote_chains_in_project
    )
    from pathlib import Path

    # Download a remote chain
    project_path = Path("./my_project")
    chain_info = download_remote_chain(
        "https://github.com/user/my-chain",
        project_path,
        github_token="ghp_example"
    )

    # Resolve all dependencies
    all_chains = resolve_dependencies_recursively(
        "https://github.com/user/my-chain",
        project_path,
        credentials={"github_token": "ghp_example"}
    )

    # Check for updates
    updates = check_for_updates(project_path)
    for chain_name, has_update in updates.items():
        if has_update:
            print(f"Update available for {chain_name}")
    ```

See Also:
    - [RemoteChainInfo][chainedpy.services.remote_chain_service.RemoteChainInfo]: Remote chain metadata class
    - [download_remote_chain][chainedpy.services.remote_chain_service.download_remote_chain]: Download remote chains
    - [resolve_dependencies_recursively][chainedpy.services.remote_chain_service.resolve_dependencies_recursively]: Resolve chain dependencies
    - [chainedpy.services.filesystem_service][chainedpy.services.filesystem_service]: Underlying filesystem operations
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from chainedpy.constants import (
    REMOTE_CHAIN_META_FILE_NAME, REMOTE_CHAIN_DEFAULT_TTL_HOURS,
    CONFIG_FILE_NAME, INIT_FILE_NAME, CHAIN_FILE_SUFFIX, PYI_FILE_SUFFIX, PYTHON_EXTENSION,
    PLUGINS_DIR, URL_SCHEME_HTTPS, URL_SCHEME_SEPARATOR, DEFAULT_BASE_PROJECT,
    CONFIG_KEY_BASE_PROJECT, GITHUB_RAW_DOMAIN,
    METADATA_KEY_URL, METADATA_KEY_DOWNLOADED_AT, METADATA_KEY_DEPENDENCIES,
    METADATA_KEY_FILES, METADATA_KEY_TTL_HOURS, METADATA_KEY_LOCAL_PATH, METADATA_KEY_SIZE_MB
)
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.filesystem_service import _validate_url_scheme, FilesystemServiceError


from chainedpy.services.logging_service import get_logger


from chainedpy.exceptions import RemoteChainServiceError


class RemoteChainInfo:
    """Information about a downloaded remote chain."""
    
    def __init__(self, url: str, local_path: Path, metadata: Dict):
        self.url = url
        self.local_path = local_path
        self.metadata = metadata
    
    @property
    def downloaded_at(self) -> datetime:
        """Get the download timestamp."""
        if METADATA_KEY_DOWNLOADED_AT not in self.metadata:
            raise RemoteChainServiceError(f"Invalid metadata: missing required key '{METADATA_KEY_DOWNLOADED_AT}'")
        return datetime.fromisoformat(self.metadata[METADATA_KEY_DOWNLOADED_AT])
    
    @property
    def size_mb(self) -> float:
        """Get the size in MB."""
        if METADATA_KEY_SIZE_MB not in self.metadata:
            raise RemoteChainServiceError(f"Invalid metadata: missing required key '{METADATA_KEY_SIZE_MB}'")
        return self.metadata[METADATA_KEY_SIZE_MB]
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        if METADATA_KEY_DEPENDENCIES not in self.metadata:
            raise RemoteChainServiceError(f"Invalid metadata: missing required key '{METADATA_KEY_DEPENDENCIES}'")
        return self.metadata[METADATA_KEY_DEPENDENCIES]
    
    @property
    def is_expired(self) -> bool:
        """Check if the remote chain has expired based on TTL."""
        if METADATA_KEY_TTL_HOURS not in self.metadata:
            raise RemoteChainServiceError(f"Invalid metadata: missing required key '{METADATA_KEY_TTL_HOURS}'")
        ttl_hours = self.metadata[METADATA_KEY_TTL_HOURS]
        expiry_time = self.downloaded_at + timedelta(hours=ttl_hours)
        return datetime.now() > expiry_time


def _get_project_name_from_url(repository_url: str) -> str:
    """Extract the project name from a repository URL.

    Example:
        ```python
        from chainedpy.services.remote_chain_service import _get_project_name_from_url

        # GitHub URL
        name = _get_project_name_from_url("https://github.com/user/my-project")
        assert name == "my-project"

        # GitLab URL
        name = _get_project_name_from_url("https://gitlab.com/user/awesome-chain")
        assert name == "awesome-chain"

        # URL with .git suffix
        name = _get_project_name_from_url("https://github.com/user/project.git")
        assert name == "project"

        # Complex path
        name = _get_project_name_from_url("https://github.com/org/subgroup/project-name")
        assert name == "project-name"

        # Simple case
        name = _get_project_name_from_url("https://example.com/repo")
        assert name == "repo"
        ```

    :param repository_url: Repository URL.
    :type repository_url: [str][str]
    :return [str][str]: Project name.
    """
    # Get the last part of the URL path as project name
    parsed = urlparse(repository_url)
    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
    
    if not path_parts:
        raise RemoteChainServiceError(f"Cannot determine project name from URL: {repository_url}")
    
    # For GitHub raw URLs, the project name is typically the last part
    if parsed.netloc == GITHUB_RAW_DOMAIN and len(path_parts) >= 4:
        return path_parts[-1]  # Last part of the path
    else:
        return path_parts[-1]  # Last part of the path


def _create_remote_metadata(repository_url: str, local_path: Path, 
                          dependencies: List[str], files: List[str]) -> Dict:
    """Create metadata for a downloaded remote chain.

    :param repository_url: Repository URL.
    :type repository_url: str
    :param local_path: Local path where chain was downloaded.
    :type local_path: Path
    :param dependencies: List of dependency URLs.
    :type dependencies: List[str]
    :param files: List of downloaded files.
    :type files: List[str]
    :return Dict: Metadata dictionary.
    """
    now = datetime.now().isoformat()
    
    # Calculate size
    try:
        total_size = 0
        for root in local_path.rglob('*'):
            if root.is_file():
                total_size += root.stat().st_size
        size_mb = total_size / (1024 * 1024)
    except Exception as e:
        error_msg = f"Failed to calculate size for remote chain metadata at {local_path}: {e}"
        raise RemoteChainServiceError(error_msg) from e

    return {
        METADATA_KEY_URL: repository_url,
        METADATA_KEY_DOWNLOADED_AT: now,
        METADATA_KEY_DEPENDENCIES: dependencies,
        METADATA_KEY_FILES: files,
        METADATA_KEY_TTL_HOURS: REMOTE_CHAIN_DEFAULT_TTL_HOURS,
        METADATA_KEY_LOCAL_PATH: str(local_path),
        METADATA_KEY_SIZE_MB: size_mb
    }


def _save_remote_metadata(local_path: Path, metadata: Dict) -> None:
    """Save remote chain metadata to the local directory.

    :param local_path: Local path where chain was downloaded.
    :type local_path: Path
    :param metadata: Metadata to save.
    :type metadata: Dict
    :raises RemoteChainServiceError: If metadata saving fails.
    """
    try:
        metadata_file = local_path / REMOTE_CHAIN_META_FILE_NAME
        fs_utils.write_text(str(metadata_file), json.dumps(metadata, indent=2))
        get_logger().debug(f"Saved remote chain metadata to {metadata_file}")
    except Exception as e:
        error_msg = f"Failed to save remote chain metadata to {local_path}: {e}"
        raise RemoteChainServiceError(error_msg) from e


def _load_remote_metadata(local_path: Path) -> Optional[Dict]:
    """Load remote chain metadata from the local directory.

    :param local_path: Local path where chain was downloaded.
    :type local_path: Path
    :return Optional[Dict]: Metadata dictionary or None if not found.
    :raises RemoteChainServiceError: If metadata loading fails.
    """
    try:
        metadata_file = local_path / REMOTE_CHAIN_META_FILE_NAME
        if fs_utils.exists(str(metadata_file)):
            content = fs_utils.read_text(str(metadata_file))
            return json.loads(content)
        return None
    except Exception as e:
        error_msg = f"Failed to load remote chain metadata from {local_path}: {e}"
        raise RemoteChainServiceError(error_msg) from e


def _download_remote_files(repository_url: str, local_path: Path) -> List[str]:
    """Download all required files for a remote chain project.

    :param repository_url: Repository URL to download from.
    :type repository_url: str
    :param local_path: Local path to download to.
    :type local_path: Path
    :return List[str]: List of downloaded file paths (relative to local_path).
    :raises RemoteChainServiceError: If download fails.
    """
    downloaded_files = []
    project_name = _get_project_name_from_url(repository_url)
    
    # List of required files for a ChainedPy project
    required_files = [
        INIT_FILE_NAME,  # __init__.py
        CONFIG_FILE_NAME,  # chainedpy.yaml
        f"{project_name}{CHAIN_FILE_SUFFIX}",  # {project}_chain.py
    ]
    
    # Optional files
    optional_files = [
        f"{project_name}{PYI_FILE_SUFFIX}",  # {project}_chain.pyi (stub file)
    ]
    
    try:
        # Ensure local directory exists
        fs_utils.makedirs(str(local_path), exist_ok=True)
        
        # Download required files
        for file_name in required_files:
            file_url = f"{repository_url.rstrip('/')}/{file_name}"
            local_file_path = local_path / file_name
            
            try:
                content = fs_utils.read_text(file_url)
                fs_utils.write_text(str(local_file_path), content)
                downloaded_files.append(file_name)
                get_logger().debug(f"Downloaded {file_name} from {file_url}")
            except Exception as e:
                raise RemoteChainServiceError(f"Failed to download required file {file_name}: {e}")

        # Download optional files (don't fail if they don't exist)
        for file_name in optional_files:
            file_url = f"{repository_url.rstrip('/')}/{file_name}"
            local_file_path = local_path / file_name

            if fs_utils.exists(file_url):
                content = fs_utils.read_text(file_url)
                fs_utils.write_text(str(local_file_path), content)
                downloaded_files.append(file_name)
                get_logger().debug(f"Downloaded optional file {file_name}")
            else:
                get_logger().debug(f"Optional file {file_name} not found, skipping")
        
        # Download plugins directory if it exists
        plugins_url = f"{repository_url.rstrip('/')}/{PLUGINS_DIR}"
        if _download_plugins_directory(plugins_url, local_path / PLUGINS_DIR):
            downloaded_files.append(PLUGINS_DIR)
        
        return downloaded_files
        
    except Exception as e:
        # Clean up on failure
        if local_path.exists():
            shutil.rmtree(local_path, ignore_errors=True)
        raise RemoteChainServiceError(f"Failed to download remote chain files: {e}")


def _download_plugins_directory(plugins_url: str, local_plugins_path: Path) -> bool:
    """Download the plugins directory structure.

    :param plugins_url: URL to the plugins directory.
    :type plugins_url: str
    :param local_plugins_path: Local path for plugins directory.
    :type local_plugins_path: Path
    :return bool: True if plugins were downloaded, False if not available.
    """
    try:
        # Check if plugins directory exists remotely
        plugins_init_url = f"{plugins_url}/{INIT_FILE_NAME}"
        if not fs_utils.exists(plugins_init_url):
            get_logger().debug(f"No plugins directory found at {plugins_url}")
            return False
        
        # Create local plugins directory
        fs_utils.makedirs(str(local_plugins_path), exist_ok=True)
        
        # Download plugins/__init__.py
        content = fs_utils.read_text(plugins_init_url)
        fs_utils.write_text(str(local_plugins_path / INIT_FILE_NAME), content)
        
        subdirs = ['then', 'as_', 'processors']
        for subdir in subdirs:
            subdir_url = f"{plugins_url}/{subdir}"
            local_subdir_path = local_plugins_path / subdir

            # Try to download subdir/__init__.py
            subdir_init_url = f"{subdir_url}/{INIT_FILE_NAME}"
            if fs_utils.exists(subdir_init_url):
                fs_utils.makedirs(str(local_subdir_path), exist_ok=True)
                content = fs_utils.read_text(subdir_init_url)
                fs_utils.write_text(str(local_subdir_path / INIT_FILE_NAME), content)

                # Download all plugin files in this subdirectory
                _download_plugin_files(subdir_url, local_subdir_path, subdir)
        
        get_logger().debug(f"Downloaded plugins directory structure")
        return True

    except Exception as e:
        get_logger().debug(f"Plugins directory not found or inaccessible: {plugins_url}: {e}")
        return False


def _download_github_plugin_files(subdir_url: str, subdir_type: str, local_subdir_path: Path) -> None:
    """Download plugin files from GitHub using the GitHub API for discovery.

    :param subdir_url: GitHub raw URL to the subdirectory.
    :type subdir_url: str
    :param subdir_type: Type of subdirectory ('then', 'as_', 'processors').
    :type subdir_type: str
    :param local_subdir_path: Local path for the subdirectory.
    :type local_subdir_path: Path
    """
    try:
        # Convert raw.githubusercontent.com URL to GitHub API URL
        # raw.githubusercontent.com/user/repo/branch/path -> api.github.com/repos/user/repo/contents/path?ref=branch
        parsed_url = urlparse(subdir_url)
        if parsed_url.netloc != GITHUB_RAW_DOMAIN:
            raise RemoteChainServiceError(f"Invalid GitHub raw URL format: {subdir_url}")

        # Parse the URL path: /user/repo/branch/path
        path_parts = [p for p in parsed_url.path.strip('/').split('/') if p]
        if len(path_parts) < 4:
            raise RemoteChainServiceError(f"Invalid GitHub raw URL structure: {subdir_url}")

        user = path_parts[0]
        repo = path_parts[1]
        if path_parts[2] == "refs" and len(path_parts) > 4 and path_parts[3] == "heads":
            branch = path_parts[4]
            path = "/".join(path_parts[5:])
        else:
            branch = path_parts[2]
            path = "/".join(path_parts[3:])

        # Construct GitHub API URL
        api_url = f"{URL_SCHEME_HTTPS}api.github.com/repos/{user}/{repo}/contents/{path}?ref={branch}"

        # Get directory contents from GitHub API
        api_response = fs_utils.read_text(api_url)
        files_data = json.loads(api_response)

        downloaded_count = 0
        for file_info in files_data:
            if file_info.get('type') == 'file':
                filename = file_info.get('name', '')
                if filename.startswith(f"{subdir_type}_") and filename.endswith(PYTHON_EXTENSION):
                    # Download the file using the raw download URL
                    download_url = file_info.get('download_url')
                    if download_url:
                        local_plugin_file = local_subdir_path / filename
                        content = fs_utils.read_text(download_url)
                        fs_utils.write_text(str(local_plugin_file), content)
                        downloaded_count += 1
                        get_logger().debug(f"Downloaded GitHub plugin file: {filename}")

        get_logger().debug(f"Downloaded {downloaded_count} plugin files from GitHub API: {subdir_url}")

    except Exception as e:
        # get_logger().warning(f"Failed to download plugin files via GitHub API from {subdir_url}: {e}")
        raise RemoteChainServiceError(f"Failed to download plugin files via GitHub API from {subdir_url}: {e}") from e


def _download_plugin_files(subdir_url: str, local_subdir_path: Path, subdir_type: str) -> None:
    """Download all plugin files from a remote subdirectory.

    :param subdir_url: URL to the remote subdirectory.
    :type subdir_url: str
    :param local_subdir_path: Local path for the subdirectory.
    :type local_subdir_path: Path
    :param subdir_type: Type of subdirectory ('then', 'as_', 'processors').
    :type subdir_type: str
    """
    try:
        # Discover and download plugin files using filesystem operations
        discovered_files = fs_utils.discover_plugin_files(subdir_url, subdir_type)
        downloaded_count = 0

        for file_info in discovered_files:
            plugin_name = file_info['name']
            plugin_file_url = file_info['url']
            local_plugin_file = local_subdir_path / plugin_name

            content = fs_utils.read_text(plugin_file_url)
            fs_utils.write_text(str(local_plugin_file), content)
            downloaded_count += 1
            get_logger().debug(f"Downloaded plugin file: {plugin_name}")

        if downloaded_count > 0:
            get_logger().info(f"Downloaded {downloaded_count} plugin files from {subdir_type} directory")
        else:
            get_logger().debug(f"No plugin files discovered in {subdir_type} directory")

    except Exception as e:
        # The real issue: GitHub's raw.githubusercontent.com doesn't support directory listing
        # which is required by discover_plugin_files(). For GitHub URLs, we should use the
        # GitHub API to discover files, then download them via raw URLs.
        if GITHUB_RAW_DOMAIN in subdir_url:
            get_logger().debug(f"Discovery failed for GitHub raw URL, trying GitHub API discovery: {subdir_url}")
            _download_github_plugin_files(subdir_url, subdir_type, local_subdir_path)
            return

        # For other filesystem errors, still raise the exception
        error_msg = f"Failed to download plugin files from {subdir_url}: {e}"
        raise RemoteChainServiceError(error_msg) from e


def download_remote_chain_to_project(repository_url: str, project_path: Path,
                                   force_refresh: bool = False) -> RemoteChainInfo:
    """Download a remote chain directly to a project directory.

    Example:
        ```python
        from chainedpy.services.remote_chain_service import download_remote_chain_to_project
        from chainedpy.services.project_lifecycle import create_project
        from pathlib import Path
        import shutil

        # Create a test project
        project_path = create_project(Path("test_project"), "test_project")

        # Download remote chain
        try:
            remote_info = download_remote_chain_to_project(
                "https://github.com/user/example-chain",
                project_path
            )

            print(f"Downloaded: {remote_info.url}")
            print(f"Size: {remote_info.size_mb:.2f} MB")
            print(f"Dependencies: {remote_info.dependencies}")

            # Verify download
            assert remote_info.local_path.exists()
            assert remote_info.size_mb > 0

        except Exception as e:
            print(f"Download failed: {e}")

        # Force re-download
        try:
            remote_info = download_remote_chain_to_project(
                "https://github.com/user/example-chain",
                project_path,
                force_refresh=True
            )
            print("Force re-download completed")

        except Exception as e:
            print(f"Force download failed: {e}")

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param repository_url: URL to the remote chain repository.
    :type repository_url: [str][str]
    :param project_path: Path to the project directory where chain should be downloaded.
    :type project_path: [Path][pathlib.Path]
    :param force_refresh: If True, re-download even if cached version exists, defaults to False.
    :type force_refresh: [bool][bool], optional
    :return [RemoteChainInfo][chainedpy.services.remote_chain_service.RemoteChainInfo]: RemoteChainInfo object with information about the downloaded chain.
    :raises RemoteChainServiceError: If download fails.
    """
    try:
        try:
            _validate_url_scheme(repository_url)
        except FilesystemServiceError as e:
            raise RemoteChainServiceError(str(e)) from e

        # Determine the local path for the remote chain
        project_name = _get_project_name_from_url(repository_url)
        local_path = project_path / project_name

        # Check if already downloaded and not expired
        if not force_refresh and local_path.exists():
            metadata = _load_remote_metadata(local_path)
            if metadata:
                chain_info = RemoteChainInfo(repository_url, local_path, metadata)
                if not chain_info.is_expired:
                    get_logger().debug(f"Using existing remote chain from {local_path}")
                    return chain_info

        # Download the chain
        get_logger().info(f"Downloading remote chain from {repository_url} to {local_path}")

        # Clean up existing download if it exists
        if local_path.exists():
            shutil.rmtree(local_path, ignore_errors=True)

        # Download all required files
        downloaded_files = _download_remote_files(repository_url, local_path)

        # Read dependencies from the downloaded config
        dependencies = _extract_dependencies(local_path)

        # Create and save metadata
        metadata = _create_remote_metadata(repository_url, local_path, dependencies, downloaded_files)
        _save_remote_metadata(local_path, metadata)

        get_logger().info(f"Successfully downloaded remote chain: {repository_url}")
        return RemoteChainInfo(repository_url, local_path, metadata)

    except RemoteChainServiceError:
        # Re-raise RemoteChainServiceError as-is
        raise
    except Exception as e:
        # Convert filesystem service errors and other exceptions to RemoteChainServiceError
        if isinstance(e, FilesystemServiceError):
            raise RemoteChainServiceError(str(e)) from e
        error_msg = f"Failed to download remote chain {repository_url}: {e}"
        raise RemoteChainServiceError(error_msg) from e


def _extract_dependencies(local_path: Path) -> List[str]:
    """Extract dependencies from a downloaded chain's configuration.

    :param local_path: Local path to the downloaded chain.
    :type local_path: Path
    :return List[str]: List of dependency URLs.
    """
    dependencies = []

    try:
        config_file = local_path / CONFIG_FILE_NAME
        if fs_utils.exists(str(config_file)):
            config_data = fs_utils.read_config(str(config_file))
            if CONFIG_KEY_BASE_PROJECT not in config_data:
                raise RemoteChainServiceError(f"Invalid config: missing required key '{CONFIG_KEY_BASE_PROJECT}'")
            base_project = config_data[CONFIG_KEY_BASE_PROJECT].strip()

            # If base_project is a URL, it's a dependency
            if base_project != DEFAULT_BASE_PROJECT and URL_SCHEME_SEPARATOR in base_project:
                dependencies.append(base_project)
                get_logger().debug(f"Found dependency: {base_project}")

    except Exception as e:
        # get_logger().warning(f"Failed to extract dependencies from {local_path}: {e}")
        raise RemoteChainServiceError(f"Failed to extract dependencies from {local_path}: {e}") from e

    return dependencies


def resolve_dependencies_recursively(repository_url: str, project_path: Path,
                                   visited: Optional[Set[str]] = None) -> List[RemoteChainInfo]:
    """Recursively resolve and download all dependencies for a remote chain to a project directory.

    :param repository_url: URL to the remote chain repository.
    :type repository_url: str
    :param project_path: Path to the project directory where chains should be downloaded.
    :type project_path: Path
    :param visited: Set of already visited URLs to prevent circular dependencies, defaults to None.
    :type visited: Optional[Set[str]], optional
    :return List[RemoteChainInfo]: List of RemoteChainInfo objects for all dependencies (including the root).
    :raises RemoteChainServiceError: If dependency resolution fails.
    """
    if visited is None:
        visited = set()

    # Check for circular dependencies
    if repository_url in visited:
        raise RemoteChainServiceError(f"Circular dependency detected: {repository_url}")

    visited.add(repository_url)
    resolved_chains = []

    try:
        # Download the current chain
        chain_info = download_remote_chain_to_project(repository_url, project_path)
        resolved_chains.append(chain_info)

        # Recursively resolve dependencies
        for dependency_url in chain_info.dependencies:
            if dependency_url != DEFAULT_BASE_PROJECT:
                dependency_chains = resolve_dependencies_recursively(dependency_url, project_path, visited.copy())
                resolved_chains.extend(dependency_chains)

        return resolved_chains

    except Exception as e:
        error_msg = f"Failed to resolve dependencies for {repository_url}: {e}"
        raise RemoteChainServiceError(error_msg) from e


def get_remote_chain_info(repository_url: str, project_path: Path) -> Optional[RemoteChainInfo]:
    """Get information about a downloaded remote chain if it exists in the project.

    :param repository_url: URL to the remote chain repository.
    :type repository_url: str
    :param project_path: Path to the project directory.
    :type project_path: Path
    :return Optional[RemoteChainInfo]: RemoteChainInfo object if downloaded, None otherwise.
    """
    try:
        project_name = _get_project_name_from_url(repository_url)
        local_path = project_path / project_name
        if local_path.exists():
            metadata = _load_remote_metadata(local_path)
            if metadata:
                return RemoteChainInfo(repository_url, local_path, metadata)
    except Exception as e:
        msg = f"Failed to get remote chain info for {repository_url}: {e}"
        raise RemoteChainServiceError(msg) from e

    return None


def list_remote_chains_in_project(project_path: Path) -> List[RemoteChainInfo]:
    """List all downloaded remote chains in a project directory.

    Example:
        ```python
        from chainedpy.services.remote_chain_service import (
            list_remote_chains_in_project,
            download_remote_chain_to_project
        )
        from chainedpy.services.project_lifecycle import create_project
        from pathlib import Path
        import shutil

        # Create a test project
        project_path = create_project(Path("test_project"), "test_project")

        # Initially no remote chains
        chains = list_remote_chains_in_project(project_path)
        assert len(chains) == 0

        # Download some remote chains
        try:
            download_remote_chain_to_project(
                "https://github.com/user/chain1",
                project_path
            )
            download_remote_chain_to_project(
                "https://github.com/user/chain2",
                project_path
            )

            # List remote chains
            chains = list_remote_chains_in_project(project_path)
            assert len(chains) == 2

            for chain in chains:
                print(f"Chain: {chain.url}")
                print(f"Size: {chain.size_mb:.2f} MB")
                print(f"Downloaded: {chain.downloaded_at}")
                assert chain.local_path.exists()

        except Exception as e:
            print(f"Download failed: {e}")

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project directory.
    :type project_path: [Path][pathlib.Path]
    :return [List][list][[RemoteChainInfo][chainedpy.services.remote_chain_service.RemoteChainInfo]]: List of RemoteChainInfo objects for all downloaded remote chains.
    """
    remote_chains = []

    try:
        if not project_path.exists():
            return remote_chains

        # Look for directories with remote chain metadata
        for item in project_path.iterdir():
            if item.is_dir():
                metadata_file = item / REMOTE_CHAIN_META_FILE_NAME
                if metadata_file.exists():
                    try:
                        metadata = _load_remote_metadata(item)
                        if metadata:
                            if METADATA_KEY_URL not in metadata:
                                raise RemoteChainServiceError(f"Invalid metadata: missing required key '{METADATA_KEY_URL}'")
                            url = metadata[METADATA_KEY_URL]
                            remote_chains.append(RemoteChainInfo(url, item, metadata))
                    except Exception as e:
                        msg = f"Failed to load metadata from {item}: {e}"
                        raise RemoteChainServiceError(msg) from e

    except Exception as e:
        msg = f"Failed to list remote chains in {project_path}: {e}"
        raise RemoteChainServiceError(msg) from e

    return remote_chains
