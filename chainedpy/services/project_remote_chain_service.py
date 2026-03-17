"""Project Remote Chain Service.

This service handles downloading and managing remote chains within individual project
directories. It ensures that remote chains are properly downloaded, cached, and made
available for local imports and type checking within ChainedPy projects.

The service manages the complete lifecycle of remote chain dependencies including
initial download, update checking, version management, and cleanup. It coordinates
with the gitignore service to ensure downloaded chains are properly excluded from
version control while maintaining import compatibility.

Note:
    Remote chains are downloaded directly to the project root so that imports
    work naturally without complex path manipulation. The service handles
    dependency resolution and ensures all transitive dependencies are available.

Example:
    ```python
    from chainedpy.services.project_remote_chain_service import (
        update_project_chains, get_remote_chain_status, list_project_remote_chains
    )
    from pathlib import Path

    # Update all remote chains in a project
    project_path = Path("./my_project")
    updated_chains = update_project_chains(project_path, force=False)

    # Check status of remote chains
    status = get_remote_chain_status(project_path)
    for chain_name, info in status.items():
        print(f"{chain_name}: {info['status']}")

    # List all remote chains used by project
    chains = list_project_remote_chains(project_path)
    for chain in chains:
        print(f"Chain: {chain['name']}, URL: {chain['url']}")
    ```

See Also:
    - [update_project_chains][chainedpy.services.project_remote_chain_service.update_project_chains]: Update remote chain dependencies
    - [get_remote_chain_status][chainedpy.services.project_remote_chain_service.get_remote_chain_status]: Check chain status
    - [chainedpy.services.remote_chain_service][chainedpy.services.remote_chain_service]: Core remote chain operations
    - [chainedpy.services.gitignore_service][chainedpy.services.gitignore_service]: Gitignore management for downloaded chains
"""
from __future__ import annotations

# 1. Standard library imports
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 2. Third-party imports
# (none)

# 3. Internal constants
from chainedpy.constants import (
    TEMPLATE_BASE_IMPORT_LOCAL,
    PLUGINS_DIR, CHAIN_FILE_SUFFIX, URL_SCHEME_SEPARATOR
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.gitignore_service import add_chain_to_gitignore
from chainedpy.services.logging_service import get_logger
from chainedpy.services.remote_chain_service import (
    resolve_dependencies_recursively,
    list_remote_chains_in_project
)
from chainedpy.services.template_service import render_template

# 5. ChainedPy internal modules
from chainedpy.exceptions import ProjectRemoteChainServiceError

# 6. TYPE_CHECKING imports (none)


def _get_project_chains_dir(project_path: Path) -> Path:
    """Get the directory where remote chains are stored within a project.

    Remote chains are downloaded directly to the project root so imports work naturally.

    Example:
        ```python
        from chainedpy.services.project_remote_chain_service import _get_project_chains_dir
        from pathlib import Path

        # Get chains directory for a project
        project_path = Path("my_project")
        chains_dir = _get_project_chains_dir(project_path)

        # Remote chains are stored directly in project root
        assert chains_dir == project_path

        # Works with absolute paths
        abs_project = Path("/absolute/path/to/project")
        abs_chains_dir = _get_project_chains_dir(abs_project)
        assert abs_chains_dir == abs_project

        # Works with relative paths
        rel_project = Path("./relative/project")
        rel_chains_dir = _get_project_chains_dir(rel_project)
        assert rel_chains_dir == rel_project

        # This allows natural imports like:
        # from my_project.remote_chain_name.remote_chain_name_chain import Chain
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :return [Path][pathlib.Path]: Path to the project root (where remote chains are downloaded).
    """
    return project_path




def download_remote_chains_to_project(base_project_url: str, project_path: Path) -> List[Path]:
    """Download remote chains and all their dependencies directly to the project directory.

    Example:
        ```python
        from chainedpy.services.project_remote_chain_service import download_remote_chains_to_project
        from chainedpy.services.project_lifecycle import create_project
        from chainedpy.exceptions import ProjectRemoteChainServiceError
        from pathlib import Path
        import shutil

        # Create test project
        project_path = create_project(Path("test_project"), "test_project")

        # Download remote chains
        try:
            downloaded_paths = download_remote_chains_to_project(
                "https://github.com/user/base-project",
                project_path
            )

            # Verify downloads
            assert isinstance(downloaded_paths, list)
            for chain_path in downloaded_paths:
                assert chain_path.exists()
                assert chain_path.is_dir()
                assert chain_path.parent == project_path

                # Should contain chain files
                chain_files = list(chain_path.glob("*_chain.py"))
                assert len(chain_files) > 0

            print(f"Downloaded {len(downloaded_paths)} remote chains")

        except ProjectRemoteChainServiceError as e:
            print(f"Download failed: {e}")

        # Download with credentials
        try:
            # This would use credentials from environment or .env files
            downloaded_paths = download_remote_chains_to_project(
                "https://github.com/user/private-base",
                project_path
            )
            print(f"Downloaded {len(downloaded_paths)} private chains")

        except ProjectRemoteChainServiceError as e:
            print(f"Private download failed: {e}")

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param base_project_url: URL to the remote base project.
    :type base_project_url: [str][str]
    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :return [List][list][[Path][pathlib.Path]]: List of paths to downloaded chains in the project directory.
    :raises ProjectRemoteChainServiceError: If download fails.
    """
    try:
        get_logger().info(f"Downloading remote chains to project: {base_project_url}")

        # Download directly to project directory (no global cache)
        resolved_chains = resolve_dependencies_recursively(base_project_url, project_path)

        if not resolved_chains:
            raise ProjectRemoteChainServiceError(f"Failed to resolve remote chains: {base_project_url}")

        # Extract paths from RemoteChainInfo objects
        project_chain_paths = [chain_info.local_path for chain_info in resolved_chains]

        # Add chains to gitignore to exclude from version control
        for chain_path in project_chain_paths:
            try:
                add_chain_to_gitignore(project_path, chain_path.name)
            except Exception as e:
                get_logger().warning(f"Failed to add {chain_path.name} to gitignore: {e}")

        get_logger().info(f"Successfully downloaded {len(project_chain_paths)} remote chains to project")
        return project_chain_paths

    except Exception as e:
        error_msg = f"Failed to download remote chains to project: {e}"
        raise ProjectRemoteChainServiceError(error_msg) from e


def get_project_chain_import(base_project_url: str, project_path: Path) -> str:
    """Generate the import statement for a remote chain in the project directory.

    :param base_project_url: URL to the remote base project.
    :type base_project_url: str
    :param project_path: Path to the project root.
    :type project_path: Path
    :return str: Import statement for the remote chain.
    :raises ProjectRemoteChainServiceError: If import generation fails.
    """
    try:
        # Download chains to project if not already present
        project_chain_paths = download_remote_chains_to_project(base_project_url, project_path)

        if not project_chain_paths:
            msg = f"No chains downloaded for: {base_project_url}"
            raise ProjectRemoteChainServiceError(msg)

        # The first chain is the direct base project
        base_chain_path = project_chain_paths[0]
        chain_name = base_chain_path.name

        import_statement = render_template(TEMPLATE_BASE_IMPORT_LOCAL, base_project_name=chain_name).strip()

        get_logger().info(f"Generated import statement: {import_statement}")
        return import_statement

    except Exception as e:
        error_msg = f"Failed to generate project chain import: {e}"
        raise ProjectRemoteChainServiceError(error_msg) from e


def list_project_chains(project_path: Path) -> List[Path]:
    """List all remote chains in the project directory.

    :param project_path: Path to the project root.
    :type project_path: Path
    :return List[Path]: List of paths to remote chains in the project.
    """
    # Use the new service function
    remote_chains = list_remote_chains_in_project(project_path)
    return [chain_info.local_path for chain_info in remote_chains]


def remove_project_chains(project_path: Path) -> bool:
    """Remove all remote chains from the project directory.

    :param project_path: Path to the project root.
    :type project_path: Path
    :return bool: True if chains were removed successfully.
    """
    chains_dir = _get_project_chains_dir(project_path)
    if chains_dir.exists():
        def remove_readonly(func, path, _):
            """Clear the readonly bit and reattempt the removal"""
            os.chmod(path, 0o777)
            func(path)
        # Try multiple times with different approaches for Windows compatibility
        for attempt in range(3):
            try:
                if chains_dir.exists():
                    shutil.rmtree(chains_dir, onerror=remove_readonly)
                break
            except (OSError, PermissionError) as e:
                if attempt < 2:
                    time.sleep(0.1)  # Brief pause before retry
                    continue
                else:
                    raise e
        get_logger().info(f"Removed project chains directory: {chains_dir}")
        return True
    else:
        get_logger().debug(f"No project chains directory found: {chains_dir}")
        return False


def update_project_chains(base_project_url: str, project_path: Path) -> List[Path]:
    """Update remote chains in the project directory by re-downloading them.

    :param base_project_url: URL to the remote base project.
    :type base_project_url: str
    :param project_path: Path to the project root.
    :type project_path: Path
    :return List[Path]: List of paths to updated chains in the project directory.
    :raises ProjectRemoteChainServiceError: If update fails.
    """
    try:
        get_logger().info(f"Updating project chains: {base_project_url}")

        # Remove existing chains
        remove_project_chains(project_path)

        # Download fresh copies
        return download_remote_chains_to_project(base_project_url, project_path)

    except Exception as e:
        error_msg = f"Failed to update project chains: {e}"
        raise ProjectRemoteChainServiceError(error_msg) from e


def detect_chain_changes(project_path: Path, base_project_url: str) -> bool:
    """Detect if remote chains have changes without downloading them.

    :param project_path: Path to the project root.
    :type project_path: Path
    :param base_project_url: URL of the base project to check.
    :type base_project_url: str
    :return bool: True if changes are detected, False otherwise.
    :raises ProjectRemoteChainServiceError: If detection fails.
    """
    try:
        if "://" not in base_project_url:
            return False

        get_logger().debug(f"Detecting changes for: {base_project_url}")

        # For now, use a simple approach: check if local chains exist
        # In a more sophisticated implementation, we could compare timestamps or checksums
        local_chains = list_project_remote_chains(project_path, base_project_url)

        if not local_chains:
            return True  # No local chains but remote exists = changes

        # For now, always return False (no changes) unless forced
        # This is a placeholder - real implementation would check remote timestamps
        return False

    except Exception as e:
        error_msg = f"Failed to detect chain changes: {e}"
        raise ProjectRemoteChainServiceError(error_msg) from e


def list_project_remote_chains(project_path: Path, base_project_url: str) -> List[Dict[str, Any]]:
    """List all remote chains in a project.

    :param project_path: Path to the project root.
    :type project_path: Path
    :param base_project_url: URL of the base project.
    :type base_project_url: str
    :return List[Dict[str, Any]]: List of dictionaries with chain information.
    :raises ProjectRemoteChainServiceError: If listing fails.
    """
    try:
        if "://" not in base_project_url:
            return []

        chains = []

        # Find all remote chain directories in project
        for item in project_path.iterdir():
            if item.is_dir() and item.name not in [PLUGINS_DIR, '__pycache__']:
                chain_file = item / f"{item.name}{CHAIN_FILE_SUFFIX}"
                if chain_file.exists():
                    # This looks like a remote chain
                    try:
                        stat = item.stat()
                        total_size = 0
                        pattern = str(item / "**" / "*")
                        matching_files = fs_utils.glob(pattern)
                        for file_path_str in matching_files:
                            file_path = Path(file_path_str)
                            if file_path.is_file():
                                total_size += file_path.stat().st_size

                        size_mb = total_size / (1024 * 1024)

                        chains.append({
                            'name': item.name,
                            'url': base_project_url,  # Use provided base project URL
                            'local_path': str(item),
                            'last_updated': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                            'size_mb': size_mb
                        })
                    except Exception as e:
                        # get_logger().warning(f"Failed to get info for chain {item.name}: {e}")
                        raise ProjectRemoteChainServiceError(f"Failed to get info for chain {item.name}: {e}") from e

        return chains

    except Exception as e:
        error_msg = f"Failed to list project remote chains: {e}"
        raise ProjectRemoteChainServiceError(error_msg) from e


def get_remote_chain_status(project_path: Path, base_project_url: str) -> Dict[str, Any]:
    """Get detailed status of remote chains in a project.

    :param project_path: Path to the project root.
    :type project_path: Path
    :param base_project_url: URL of the base project.
    :type base_project_url: str
    :return Dict[str, Any]: Dictionary with detailed status information.
    :raises ProjectRemoteChainServiceError: If status retrieval fails.
    """
    try:
        status = {
            'project_name': project_path.name,
            'project_path': str(project_path),
            'base_url': base_project_url,
            'remote_chains': []
        }

        if URL_SCHEME_SEPARATOR not in base_project_url:
            return status

        # Get list of remote chains
        chains = list_project_remote_chains(project_path, base_project_url)

        for chain in chains:
            # Check if chain has updates
            has_updates = detect_chain_changes(project_path, base_project_url)

            chain_status = {
                **chain,
                'status': 'downloaded',
                'has_updates': has_updates
            }

            status['remote_chains'].append(chain_status)

        return status

    except Exception as e:
        error_msg = f"Failed to get remote chain status: {e}"
        raise ProjectRemoteChainServiceError(error_msg) from e
