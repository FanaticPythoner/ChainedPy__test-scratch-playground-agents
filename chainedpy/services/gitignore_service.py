"""Gitignore Service.

This service handles creation and management of .gitignore files for ChainedPy projects.
It ensures that downloaded remote chains, sensitive files, and build artifacts are properly
excluded from version control. The service provides intelligent gitignore management that
respects existing entries while adding ChainedPy-specific exclusions.

The service automatically handles common Python exclusions, environment files, and
ChainedPy-specific patterns like downloaded remote chains. It can update existing
gitignore files without duplicating entries or disrupting user customizations.

Note:
    The service uses template-based generation to ensure consistent formatting
    and proper commenting of gitignore sections. It preserves existing user
    content while adding necessary ChainedPy exclusions.

Example:
    ```python
    from chainedpy.services.gitignore_service import (
        create_project_gitignore, add_remote_chain_entry
    )
    from pathlib import Path

    # Create gitignore for new project
    project_path = Path("./my_project")
    created = create_project_gitignore(project_path, include_env=True)

    # Add specific remote chain exclusion
    add_remote_chain_entry(project_path, "downloaded_chain_name")

    # Update gitignore with custom entries
    update_gitignore_with_entries(
        project_path,
        ["*.log", "temp/", "cache/"],
        "Custom application files"
    )
    ```

See Also:
    - [create_project_gitignore][chainedpy.services.gitignore_service.create_project_gitignore]: Create project gitignore files
    - [add_remote_chain_entry][chainedpy.services.gitignore_service.add_remote_chain_entry]: Add remote chain exclusions
    - [chainedpy.services.template_service][chainedpy.services.template_service]: Template rendering for gitignore entries
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
from pathlib import Path

# @@ STEP 2: Import third-party modules. @@
# (none)

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    GITIGNORE_ENV_COMMENT, GITIGNORE_ENV_FILE, GITIGNORE_ENV_LOCAL, GITIGNORE_ENV_WILDCARD,
    GITIGNORE_PYTHON_COMMENT, GITIGNORE_PYTHON_ENTRIES,
    GITIGNORE_FILE_NAME, GITIGNORE_PROJECT_HEADER, GITIGNORE_REMOTE_CHAIN_COMMENT,
    TEMPLATE_GITIGNORE_ENTRY,
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.logging_service import get_logger
from chainedpy.services.template_service import render_template

# 5. ChainedPy internal modules
from chainedpy.exceptions import GitignoreServiceError

# 6. TYPE_CHECKING imports (none)


def create_project_gitignore(project_path: Path, include_env: bool = True) -> bool:
    """Create or update .gitignore file for a ChainedPy project.

    Example:
        ```python
        from chainedpy.services.gitignore_service import create_project_gitignore
        from pathlib import Path
        import shutil

        # Create test project directory
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)

        # Create gitignore with env files
        success = create_project_gitignore(project_path, include_env=True)
        assert success == True

        # Verify gitignore file was created
        gitignore_file = project_path / ".gitignore"
        assert gitignore_file.exists()

        # Verify content includes Python patterns
        content = gitignore_file.read_text()
        assert "__pycache__/" in content
        assert "*.pyc" in content
        assert ".env" in content
        assert "*.pyi" in content

        # Create without env files
        gitignore_file.unlink()
        success = create_project_gitignore(project_path, include_env=False)
        assert success == True

        content = gitignore_file.read_text()
        assert "__pycache__/" in content
        assert ".env" not in content

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param include_env: Whether to include .env files in gitignore, defaults to True.
    :type include_env: [bool][bool], optional
    :return [bool][bool]: True if gitignore was created/updated, False if it already existed with all entries.
    :raises GitignoreServiceError: If gitignore creation fails.
    """
    try:
        gitignore_path = project_path / GITIGNORE_FILE_NAME
        gitignore_path_str = str(gitignore_path)
        
        # Read existing gitignore content if it exists
        existing_content = ""
        if fs_utils.exists(gitignore_path_str):
            existing_content = fs_utils.read_text(gitignore_path_str)
        
        # Define entries to add
        entries_to_add = []
        
        if include_env and GITIGNORE_ENV_FILE not in existing_content:
            entries_to_add.extend([
                GITIGNORE_ENV_COMMENT,
                GITIGNORE_ENV_FILE,
                GITIGNORE_ENV_LOCAL,
                GITIGNORE_ENV_WILDCARD,
                ""
            ])
        
        # Remote chains will be added individually via add_chain_to_gitignore function
        
        # Add Python common entries if not present
        python_entries = [GITIGNORE_PYTHON_COMMENT] + GITIGNORE_PYTHON_ENTRIES + [""]
        
        # Only add Python entries if __pycache__ is not already ignored
        if GITIGNORE_PYTHON_ENTRIES[0] not in existing_content:  # "__pycache__/" is first entry
            entries_to_add.extend(python_entries)
        
        # If no new entries to add, return False
        if not entries_to_add:
            get_logger().debug(f"Gitignore already up to date: {gitignore_path}")
            return False
        
        # Prepare new content
        new_content = existing_content
        if existing_content and not existing_content.endswith('\n'):
            new_content += '\n'
        
        # Add header if this is a new file
        if not existing_content:
            new_content = GITIGNORE_PROJECT_HEADER + "\n"
        
        new_content += '\n'.join(entries_to_add)
        
        # Write the updated gitignore
        fs_utils.write_text(gitignore_path_str, new_content)
        
        get_logger().info(f"Created/updated .gitignore: {gitignore_path}")
        return True

    except Exception as e:
        error_msg = f"Failed to create project gitignore: {e}"
        raise GitignoreServiceError(error_msg) from e


def add_chain_to_gitignore(project_path: Path, chain_name: str) -> bool:
    """Add a remote chain directory to the project's .gitignore file.

    Example:
        ```python
        from chainedpy.services.gitignore_service import add_chain_to_gitignore, create_project_gitignore
        from pathlib import Path
        import shutil

        # Create test project with gitignore
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)
        create_project_gitignore(project_path)

        # Add remote chain to gitignore
        success = add_chain_to_gitignore(project_path, "remote_chain")
        assert success == True

        # Verify chain directory was added
        gitignore_file = project_path / ".gitignore"
        content = gitignore_file.read_text()
        assert "remote_chain/" in content
        assert "# Remote chain: remote_chain" in content

        # Adding same chain again should return False (already exists)
        success = add_chain_to_gitignore(project_path, "remote_chain")
        assert success == False

        # Add another chain
        success = add_chain_to_gitignore(project_path, "another_remote")
        assert success == True

        content = gitignore_file.read_text()
        assert "another_remote/" in content

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param chain_name: Name of the remote chain to exclude.
    :type chain_name: [str][str]
    :return [bool][bool]: True if entry was added, False if it already existed.
    :raises GitignoreServiceError: If adding entry fails.
    """
    entry = f"{chain_name}/"
    comment = GITIGNORE_REMOTE_CHAIN_COMMENT.format(chain_name)
    return add_gitignore_entry(project_path, entry, comment)


def add_gitignore_entry(project_path: Path, entry: str, comment: str = None) -> bool:
    """Add a single entry to the project's .gitignore file.

    Example:
        ```python
        from chainedpy.services.gitignore_service import add_gitignore_entry, create_project_gitignore
        from pathlib import Path
        import shutil

        # Create test project with gitignore
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)
        create_project_gitignore(project_path)

        # Add simple entry
        success = add_gitignore_entry(project_path, "*.log")
        assert success == True

        # Verify entry was added
        gitignore_file = project_path / ".gitignore"
        content = gitignore_file.read_text()
        assert "*.log" in content

        # Add entry with comment
        success = add_gitignore_entry(project_path, "temp/", "Temporary files")
        assert success == True

        content = gitignore_file.read_text()
        assert "temp/" in content
        assert "# Temporary files" in content

        # Adding same entry again should return False
        success = add_gitignore_entry(project_path, "*.log")
        assert success == False

        # Add multiple entries
        success = add_gitignore_entry(project_path, "build/", "Build directory")
        assert success == True
        success = add_gitignore_entry(project_path, "dist/", "Distribution directory")
        assert success == True

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param entry: Entry to add to gitignore.
    :type entry: [str][str]
    :param comment: Optional comment to add before the entry, defaults to None.
    :type comment: [str][str], optional
    :return [bool][bool]: True if entry was added, False if it already existed.
    :raises GitignoreServiceError: If adding entry fails.
    """
    try:
        gitignore_path = project_path / GITIGNORE_FILE_NAME
        gitignore_path_str = str(gitignore_path)
        
        # Read existing content
        existing_content = ""
        if fs_utils.exists(gitignore_path_str):
            existing_content = fs_utils.read_text(gitignore_path_str)
        
        # Check if entry already exists
        if entry in existing_content:
            get_logger().debug(f"Gitignore entry already exists: {entry}")
            return False
        
        # Prepare new content
        new_content = existing_content
        if existing_content and not existing_content.endswith('\n'):
            new_content += '\n'

        entry_content = render_template(TEMPLATE_GITIGNORE_ENTRY, entry=entry, comment=comment)
        new_content += f"\n{entry_content}\n"
        
        # Write the updated gitignore
        fs_utils.write_text(gitignore_path_str, new_content)
        
        get_logger().info(f"Added gitignore entry: {entry}")
        return True

    except Exception as e:
        error_msg = f"Failed to add gitignore entry: {e}"
        raise GitignoreServiceError(error_msg) from e


def remove_gitignore_entry(project_path: Path, entry: str) -> bool:
    """Remove an entry from the project's .gitignore file.

    Example:
        ```python
        from chainedpy.services.gitignore_service import (
            remove_gitignore_entry, add_gitignore_entry, create_project_gitignore
        )
        from pathlib import Path
        import shutil

        # Create test project with gitignore
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)
        create_project_gitignore(project_path)

        # Add some entries
        add_gitignore_entry(project_path, "*.log")
        add_gitignore_entry(project_path, "temp/", "Temporary files")
        add_gitignore_entry(project_path, "build/")

        # Verify entries exist
        gitignore_file = project_path / ".gitignore"
        content = gitignore_file.read_text()
        assert "*.log" in content
        assert "temp/" in content
        assert "build/" in content

        # Remove an entry
        success = remove_gitignore_entry(project_path, "*.log")
        assert success == True

        # Verify entry was removed
        content = gitignore_file.read_text()
        assert "*.log" not in content
        assert "temp/" in content  # Others should remain

        # Remove entry with comment
        success = remove_gitignore_entry(project_path, "temp/")
        assert success == True

        content = gitignore_file.read_text()
        assert "temp/" not in content
        assert "# Temporary files" not in content

        # Removing non-existent entry should return False
        success = remove_gitignore_entry(project_path, "nonexistent.txt")
        assert success == False

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param entry: Entry to remove from gitignore.
    :type entry: [str][str]
    :return [bool][bool]: True if entry was removed, False if it didn't exist.
    :raises GitignoreServiceError: If removing entry fails.
    """
    try:
        gitignore_path = project_path / GITIGNORE_FILE_NAME
        gitignore_path_str = str(gitignore_path)
        
        if not fs_utils.exists(gitignore_path_str):
            get_logger().debug(f"No gitignore file found: {gitignore_path}")
            return False
        
        # Read existing content
        existing_content = fs_utils.read_text(gitignore_path_str)
        
        # Check if entry exists
        if entry not in existing_content:
            get_logger().debug(f"Gitignore entry not found: {entry}")
            return False
        
        # Remove the entry (and any associated comment line)
        lines = existing_content.splitlines()
        new_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
                
            if line.strip() == entry:
                # Skip this line and check if previous line was a comment
                if new_lines and new_lines[-1].strip().startswith('#'):
                    new_lines.pop()  # Remove the comment line too
                continue
            
            new_lines.append(line)
        
        # Write the updated content
        new_content = '\n'.join(new_lines)
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
            
        fs_utils.write_text(gitignore_path_str, new_content)
        
        get_logger().info(f"Removed gitignore entry: {entry}")
        return True

    except Exception as e:
        error_msg = f"Failed to remove gitignore entry: {e}"
        raise GitignoreServiceError(error_msg) from e


def list_gitignore_entries(project_path: Path) -> list[str]:
    """List all entries in the project's .gitignore file.

    Example:
        ```python
        from chainedpy.services.gitignore_service import (
            list_gitignore_entries, add_gitignore_entry, create_project_gitignore
        )
        from pathlib import Path
        import shutil

        # Create test project with gitignore
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)
        create_project_gitignore(project_path)

        # List initial entries (from default gitignore)
        entries = list_gitignore_entries(project_path)
        assert isinstance(entries, list)
        assert "__pycache__/" in entries
        assert "*.pyc" in entries

        # Add custom entries
        add_gitignore_entry(project_path, "*.log")
        add_gitignore_entry(project_path, "temp/", "Temporary files")
        add_gitignore_entry(project_path, "build/")

        # List all entries
        entries = list_gitignore_entries(project_path)
        assert "*.log" in entries
        assert "temp/" in entries
        assert "build/" in entries

        # Comments should not be included
        assert "# Temporary files" not in entries

        # Empty project should return empty list
        empty_project = Path("empty_project")
        empty_project.mkdir(exist_ok=True)
        empty_entries = list_gitignore_entries(empty_project)
        assert empty_entries == []

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        shutil.rmtree(empty_project, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :return [list][list][[str][str]]: List of gitignore entries (excluding comments and empty lines).
    :raises GitignoreServiceError: If reading gitignore file fails.
    """
    gitignore_path = project_path / GITIGNORE_FILE_NAME
    gitignore_path_str = str(gitignore_path)

    if not fs_utils.exists(gitignore_path_str):
        return []

    content = fs_utils.read_text(gitignore_path_str)
    entries = []

    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            entries.append(line)

    return entries
