"""
File helpers for ChainedPy tests.

Provides file operation utilities for testing
following ChainedPy's service patterns.
"""
from __future__ import annotations

# 1. Standard library imports
import json
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional

# 2. Third-party imports
# (none)

# 3. Internal constants
from chainedpy.constants import CONFIG_FILE_NAME

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils

# 5. ChainedPy internal modules
# (none)

# 6. Test utilities
# (none)


def create_yaml_config(project_dir: Path, base_project: str = "chainedpy",
                      summary: str = "Test project") -> Path:
    """Create a YAML configuration file.

    :param project_dir: Directory to create config in.
    :type project_dir: Path
    :param base_project: Base project value, defaults to "chainedpy".
    :type base_project: str, optional
    :param summary: Summary value, defaults to "Test project".
    :type summary: str, optional
    :raises OSError: If file creation fails.
    :return Path: Path to created config file.
    """
    # @@ STEP 1: Define config file path. @@
    config_file = project_dir / CONFIG_FILE_NAME

    # @@ STEP 2: Create config content. @@
    config_content = f"""project:
  base_project: {base_project}
  summary: {summary}
"""

    # @@ STEP 3: Write config file. @@
    fs_utils.write_text(str(config_file), config_content)
    return config_file


def create_corrupted_yaml(project_dir: Path) -> Path:
    """Create a corrupted YAML file for error testing.

    :param project_dir: Directory to create corrupted config in.
    :type project_dir: Path
    :raises OSError: If file creation fails.
    :return Path: Path to created corrupted config file.
    """
    # @@ STEP 1: Define config file path. @@
    config_file = project_dir / CONFIG_FILE_NAME

    # @@ STEP 2: Write corrupted YAML content. @@
    fs_utils.write_text(str(config_file), "key: value\n  invalid: indentation")
    return config_file


def create_json_file(file_path: Path, data: Dict[str, Any]) -> Path:
    """Create a JSON file with specified data.

    :param file_path: Path where to create JSON file.
    :type file_path: Path
    :param data: Data to write to JSON file.
    :type data: Dict[str, Any]
    :raises OSError: If file creation fails.
    :return Path: Path to created JSON file.
    """
    # @@ STEP 1: Ensure parent directory exists. @@
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # @@ STEP 2: Convert data to JSON. @@
    content = json.dumps(data, indent=2)

    # @@ STEP 3: Write JSON file. @@
    fs_utils.write_text(str(file_path), content)
    return file_path


def create_python_file(file_path: Path, content: str) -> Path:
    """Create a Python file with specified content.

    :param file_path: Path where to create Python file.
    :type file_path: Path
    :param content: Python code content.
    :type content: str
    :raises OSError: If file creation fails.
    :return Path: Path to created Python file.
    """
    # @@ STEP 1: Ensure parent directory exists. @@
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # @@ STEP 2: Write Python file. @@
    fs_utils.write_text(str(file_path), content)
    return file_path


def create_empty_file(file_path: Path) -> Path:
    """Create an empty file.

    :param file_path: Path where to create empty file.
    :type file_path: Path
    :return Path: Path to created empty file.
    """
    # @@ STEP 1: Ensure parent directory exists. @@
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # @@ STEP 2: Create empty file. @@
    file_path.touch()
    return file_path


def create_directory_tree(base_path: Path, structure: Dict[str, Any]) -> Dict[str, Path]:
    """Create a directory tree from structure definition.

    :param base_path: Base directory path.
    :type base_path: Path
    :param structure: Dictionary defining structure - Keys are names, values are None (file), {} (dir), or dict (substructure).
    :type structure: Dict[str, Any]
    :return Dict[str, Path]: Dictionary mapping names to created paths.
    """
    # @@ STEP 1: Initialize created paths dictionary. @@
    created_paths = {}

    # @@ STEP 2: Process each item in structure. @@
    for name, content in structure.items():
        item_path = base_path / name

        # || S.S. 2.1: Handle different content types. ||
        if content is None:
            # Create file
            create_empty_file(item_path)
        elif isinstance(content, dict):
            # Create directory with substructure
            item_path.mkdir(parents=True, exist_ok=True)
            if content:  # Non-empty dict
                sub_paths = create_directory_tree(item_path, content)
                created_paths.update(sub_paths)
        else:
            # Create empty directory
            item_path.mkdir(parents=True, exist_ok=True)

        # || S.S. 2.2: Add path to created paths. ||
        created_paths[name] = item_path

    # @@ STEP 3: Return created paths dictionary. @@
    return created_paths


def copy_file_with_modifications(source: Path, dest: Path,
                                modifications: Dict[str, str]) -> Path:
    """Copy a file and apply text modifications.

    :param source: Source file path.
    :type source: Path
    :param dest: Destination file path.
    :type dest: Path
    :param modifications: Dictionary of text replacements (old -> new).
    :type modifications: Dict[str, str]
    :return Path: Path to modified destination file.
    """
    # @@ STEP 1: Ensure destination directory exists. @@
    dest.parent.mkdir(parents=True, exist_ok=True)

    # @@ STEP 2: Read source file content. @@
    content = fs_utils.read_text(str(source))

    # @@ STEP 3: Apply modifications. @@
    for old_text, new_text in modifications.items():
        content = content.replace(old_text, new_text)

    # @@ STEP 4: Write modified content to destination. @@
    fs_utils.write_text(str(dest), content)
    return dest


def backup_file(file_path: Path, backup_suffix: str = ".backup") -> Path:
    """Create a backup of a file.

    :param file_path: Path to file to backup.
    :type file_path: Path
    :param backup_suffix: Suffix to add to backup file, defaults to ".backup".
    :type backup_suffix: str, optional
    :return Path: Path to backup file.
    """
    # @@ STEP 1: Create backup path with suffix. @@
    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)

    # @@ STEP 2: Copy file to backup location. @@
    shutil.copy2(file_path, backup_path)
    return backup_path


@contextmanager
def temporary_file_modification(file_path: Path, new_content: str):
    """Temporarily modify a file's content.

    :param file_path: Path to file to modify.
    :type file_path: Path
    :param new_content: New content for file.
    :type new_content: str
    :yields: Path to modified file (restored after context).
    :ytype: Path
    :return Generator[Path, None, None]: Generator for context management.
    """
    # @@ STEP 1: Backup original content. @@
    original_content = fs_utils.read_text(str(file_path)) if file_path.exists() else None

    try:
        # @@ STEP 2: Write new content. @@
        fs_utils.write_text(str(file_path), new_content)
        yield file_path
    finally:
        # @@ STEP 3: Restore original content. @@
        if original_content is not None:
            fs_utils.write_text(str(file_path), original_content)
        elif file_path.exists():
            file_path.unlink()


@contextmanager
def readonly_file(file_path: Path):
    """Temporarily make a file read-only.

    :param file_path: Path to file to make read-only.
    :type file_path: Path
    :yields: Path to read-only file (permissions restored after context).
    :ytype: Path
    :return Generator[Path, None, None]: Generator for context management.
    """
    # @@ STEP 1: Save original permissions. @@
    original_mode = file_path.stat().st_mode

    try:
        # @@ STEP 2: Make read-only. @@
        file_path.chmod(0o444)
        yield file_path
    finally:
        # @@ STEP 3: Restore original permissions. @@
        file_path.chmod(original_mode)


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes.

    :param file_path: Path to file.
    :type file_path: Path
    :return int: File size in bytes.
    """
    # @@ STEP 1: Return file size from stat. @@
    return file_path.stat().st_size


def get_directory_size(dir_path: Path) -> int:
    """Get total size of directory and all its contents.

    :param dir_path: Path to directory.
    :type dir_path: Path
    :return int: Total size in bytes.
    """
    # @@ STEP 1: Initialize total size. @@
    total_size = 0

    # @@ STEP 2: Get all files in directory recursively. @@
    pattern = str(dir_path / "**" / "*")
    matching_files = fs_utils.glob(pattern)

    # @@ STEP 3: Sum file sizes. @@
    for file_path_str in matching_files:
        file_path = Path(file_path_str)
        if file_path.is_file():
            total_size += get_file_size(file_path)

    # @@ STEP 4: Return total size. @@
    return total_size


def find_files_by_pattern(base_path: Path, pattern: str) -> List[Path]:
    """Find files matching a pattern.

    :param base_path: Base directory to search in.
    :type base_path: Path
    :param pattern: Glob pattern to match.
    :type pattern: str
    :return List[Path]: List of matching file paths.
    """
    # @@ STEP 1: Construct full pattern path. @@
    full_pattern = str(base_path / "**" / pattern)

    # @@ STEP 2: Find matching files. @@
    matching_files = fs_utils.glob(full_pattern)

    # @@ STEP 3: Return as Path objects. @@
    return [Path(file_path) for file_path in matching_files]


def find_files_by_extension(base_path: Path, extension: str) -> List[Path]:
    """Find files with specific extension.

    :param base_path: Base directory to search in.
    :type base_path: Path
    :param extension: File extension (with or without dot).
    :type extension: str
    :return List[Path]: List of matching file paths.
    """
    # @@ STEP 1: Ensure extension starts with dot. @@
    if not extension.startswith('.'):
        extension = '.' + extension

    # @@ STEP 2: Find files by pattern. @@
    return find_files_by_pattern(base_path, f"*{extension}")


def clean_directory(dir_path: Path, keep_patterns: Optional[List[str]] = None) -> int:
    """Clean directory contents, optionally keeping files matching patterns.

    :param dir_path: Directory to clean.
    :type dir_path: Path
    :param keep_patterns: Optional list of glob patterns for files to keep, defaults to None.
    :type keep_patterns: Optional[List[str]], optional
    :return int: Number of items removed.
    """
    # @@ STEP 1: Check if directory exists. @@
    if not dir_path.exists():
        return 0

    # @@ STEP 2: Initialize variables. @@
    keep_patterns = keep_patterns or []
    removed_count = 0

    # @@ STEP 3: Process each item in directory. @@
    for item in dir_path.iterdir():
        should_keep = False

        # || S.S. 3.1: Check if item matches any keep pattern. ||
        for pattern in keep_patterns:
            if item.match(pattern):
                should_keep = True
                break

        # || S.S. 3.2: Remove item if not keeping. ||
        if not should_keep:
            if item.is_file():
                item.unlink()
                removed_count += 1
            elif item.is_dir():
                shutil.rmtree(item)
                removed_count += 1

    # @@ STEP 4: Return count of removed items. @@
    return removed_count


def ensure_file_has_content(file_path: Path, required_content: str) -> bool:
    """Ensure a file contains required content, adding it if missing.

    :param file_path: Path to file to check.
    :type file_path: Path
    :param required_content: Content that must be present.
    :type required_content: str
    :return bool: True if content was added, False if already present.
    """
    # @@ STEP 1: Create file with content if it doesn't exist. @@
    if not file_path.exists():
        fs_utils.write_text(str(file_path), required_content)
        return True

    # @@ STEP 2: Check if content is already present. @@
    current_content = fs_utils.read_text(str(file_path))
    if required_content not in current_content:
        # || S.S. 2.1: Add required content to file. ||
        fs_utils.write_text(str(file_path), current_content + '\n' + required_content)
        return True

    # @@ STEP 3: Return False if content was already present. @@
    return False


def create_symlink_if_supported(target: Path, link_path: Path) -> bool:
    """Create a symbolic link if supported by the system.

    :param target: Target path for symlink.
    :type target: Path
    :param link_path: Path where to create symlink.
    :type link_path: Path
    :return bool: True if symlink was created, False if not supported.
    """
    try:
        # @@ STEP 1: Attempt to create symlink. @@
        link_path.symlink_to(target)
        return True
    except (OSError, NotImplementedError):
        # @@ STEP 2: Return False if symlinks not supported. @@
        return False
