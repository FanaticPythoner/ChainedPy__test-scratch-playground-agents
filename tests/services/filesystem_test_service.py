"""
Filesystem test service for ChainedPy tests.

Provides centralized filesystem operations, temporary workspace management,
and file system utilities for testing, following ChainedPy's service patterns.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

from chainedpy.constants import CONFIG_FILE_NAME


class FilesystemTestServiceError(Exception):
    """Exception raised when filesystem test operations fail."""
    pass


@contextmanager
def create_temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for testing.

    :yields: Temporary workspace directory that will be cleaned up automatically.
    :ytype: Path
    :return Generator[Path, None, None]: Generator yielding temporary workspace path.
    """
    # @@ STEP 1: Create temporary directory and yield workspace path. @@
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        yield workspace


def create_config_file(project_dir: Path, base_project: str = "chainedpy",
                      summary: str = "") -> Path:
    """Create a chainedpy.yaml config file in the specified directory.

    :param project_dir: Directory to create config file in.
    :type project_dir: Path
    :param base_project: Base project value for config, defaults to "chainedpy".
    :type base_project: str, optional
    :param summary: Summary value for config, defaults to "".
    :type summary: str, optional
    :return Path: Path to created config file.
    :raises FilesystemTestServiceError: If config file creation fails
    """
    try:
        config_file = project_dir / CONFIG_FILE_NAME
        
        if not summary:
            summary = f"ChainedPy project: {project_dir.name}"
            
        config_content = f"""project:
  base_project: {base_project}
  summary: {summary}
"""
        config_file.write_text(config_content)
        return config_file
        
    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to create config file: {e}") from e


def create_corrupted_config_file(project_dir: Path) -> Path:
    """Create a corrupted chainedpy.yaml config file for error testing.

    :param project_dir: Directory to create corrupted config file in.
    :type project_dir: Path
    :return Path: Path to created corrupted config file.
    :raises FilesystemTestServiceError: If corrupted config file creation fails.
    """
    try:
        # @@ STEP 1: Create corrupted config file with invalid YAML. @@
        config_file = project_dir / CONFIG_FILE_NAME
        config_file.write_text("key: value\n  invalid: indentation")
        return config_file

    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to create corrupted config file: {e}") from e


def make_file_readonly(file_path: Path) -> None:
    """Make a file read-only for permission error testing.

    :param file_path: Path to file to make read-only.
    :type file_path: Path
    :raises FilesystemTestServiceError: If permission change fails.
    :return None: None
    """
    try:
        # @@ STEP 1: Change file permissions to read-only. @@
        file_path.chmod(0o444)
    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to make file read-only: {e}") from e


def restore_file_permissions(file_path: Path) -> None:
    """Restore normal file permissions.

    :param file_path: Path to file to restore permissions for.
    :type file_path: Path
    :raises FilesystemTestServiceError: If permission restoration fails.
    :return None: None
    """
    try:
        # @@ STEP 1: Restore normal file permissions. @@
        file_path.chmod(0o644)
    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to restore file permissions: {e}") from e


@contextmanager
def readonly_file_context(file_path: Path) -> Generator[None, None, None]:
    """Context manager for temporarily making a file read-only.

    :param file_path: Path to file to make temporarily read-only.
    :type file_path: Path
    :yields: None: File is read-only during context.
    :ytype: None
    :return Generator[None, None, None]: Generator for context management.
    """
    try:
        # @@ STEP 1: Make file read-only. @@
        make_file_readonly(file_path)
        yield
    finally:
        # @@ STEP 2: Restore file permissions. @@
        restore_file_permissions(file_path)


def ensure_directory_exists(directory_path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    :param directory_path: Path to directory to ensure exists.
    :type directory_path: Path
    :return Path: Path to directory (guaranteed to exist).
    :raises FilesystemTestServiceError: If directory creation fails.
    """
    try:
        # @@ STEP 1: Create directory with parents if needed. @@
        directory_path.mkdir(parents=True, exist_ok=True)
        return directory_path
    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to create directory: {e}") from e


def create_plugin_file(plugin_dir: Path, plugin_name: str, plugin_content: str) -> Path:
    """Create a plugin file with specified content.

    :param plugin_dir: Directory to create plugin file in.
    :type plugin_dir: Path
    :param plugin_name: Name of plugin file (without .py extension).
    :type plugin_name: str
    :param plugin_content: Content to write to plugin file.
    :type plugin_content: str
    :return Path: Path to created plugin file.
    :raises FilesystemTestServiceError: If plugin file creation fails.
    """
    try:
        # @@ STEP 1: Ensure plugin directory exists. @@
        ensure_directory_exists(plugin_dir)

        # @@ STEP 2: Create plugin file with content. @@
        plugin_file = plugin_dir / f"{plugin_name}.py"
        plugin_file.write_text(plugin_content)
        return plugin_file

    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to create plugin file: {e}") from e


def create_broken_plugin_file(plugin_dir: Path, plugin_name: str) -> Path:
    """Create a plugin file with invalid Python syntax for error testing.

    :param plugin_dir: Directory to create broken plugin file in.
    :type plugin_dir: Path
    :param plugin_name: Name of plugin file (without .py extension).
    :type plugin_name: str
    :return Path: Path to created broken plugin file.
    :raises FilesystemTestServiceError: If broken plugin file creation fails.
    """
    try:
        # @@ STEP 1: Create broken plugin content with invalid syntax. @@
        broken_content = f"def {plugin_name}(self invalid syntax"

        # @@ STEP 2: Create plugin file with broken content. @@
        return create_plugin_file(plugin_dir, plugin_name, broken_content)

    except Exception as e:
        raise FilesystemTestServiceError(f"Failed to create broken plugin file: {e}") from e
