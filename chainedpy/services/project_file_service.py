"""Project File Service.

This service handles project file creation and management for ChainedPy projects.
It provides functionality for creating project structures, managing configuration files,
generating chain implementations, and maintaining project metadata. The service ensures
consistent project layout and proper file generation across all ChainedPy projects.

The service manages the creation of essential project files including __init__.py files,
chain implementation files, configuration files, and plugin directory structures.
All file operations use the filesystem service for consistent handling of both
local and remote filesystems.

Note:
    This service was extracted from project.py to centralize project file operations
    and maintain clean separation of concerns. It focuses specifically on file
    creation and management rather than project lifecycle operations.

Example:
    ```python
    from chainedpy.services.project_file_service import (
        create_project_structure, create_chain_file, create_config_file
    )
    from pathlib import Path

    # Create complete project structure
    project_path = Path("./my_project")
    create_project_structure(
        project_path,
        project_name="my_project",
        base_project="chainedpy",
        summary="My custom chain project"
    )

    # Create individual files
    create_chain_file(project_path, "my_project", "chainedpy")
    create_config_file(project_path, "chainedpy", "My project summary")

    # Ensure plugin directories exist
    ensure_plugin_directories(project_path)
    ```

See Also:
    - [create_project_structure][chainedpy.services.project_file_service.create_project_structure]: Create complete project layout
    - [create_chain_file][chainedpy.services.project_file_service.create_chain_file]: Create chain implementation files
    - [chainedpy.services.template_service][chainedpy.services.template_service]: Template rendering for file generation
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
from pathlib import Path

# @@ STEP 2: Import third-party modules. @@
# (none)

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    INIT_FILE_NAME, CHAIN_FILE_SUFFIX, CONFIG_FILE_NAME, DEFAULT_BASE_PROJECT,
    PLUGINS_DIR, THEN_DIR, AS_DIR, PROCESSORS_DIR,
    BASE_CHAIN_IMPORT, TEMPLATE_BASE_IMPORT_LOCAL
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.logging_service import get_logger
from chainedpy.services.template_service import (
    render_project_file, render_config_file, render_template, TemplateServiceError
)

# 5. ChainedPy internal modules
from chainedpy.exceptions import ProjectFileServiceError

# 6. TYPE_CHECKING imports (none)


def _ensure_pkg_init(path: Path) -> None:
    """Ensure package __init__.py file exists using fsspec.

    Example:
        ```python
        from chainedpy.services.project_file_service import _ensure_pkg_init
        from pathlib import Path
        import shutil

        # Create test directory
        test_dir = Path("test_package")
        test_dir.mkdir(exist_ok=True)

        # Ensure __init__.py exists
        _ensure_pkg_init(test_dir / "__init__.py")

        # Verify file was created
        init_file = test_dir / "__init__.py"
        assert init_file.exists()

        # File should contain basic package content
        content = init_file.read_text()
        assert "__all__" in content

        # Calling again should not overwrite
        init_file.write_text("# Custom content")
        _ensure_pkg_init(test_dir / "__init__.py")
        assert "# Custom content" in init_file.read_text()

        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
        ```

    :param path: Path to the __init__.py file.
    :type path: [Path][pathlib.Path]
    :raises ProjectFileServiceError: If file creation fails.
    """
    try:
        init_content = render_project_file("init_py")  # Note: "init_py" is the template type, not a file name
        path_str = str(path)
        if not fs_utils.exists(path_str):
            fs_utils.write_text(path_str, init_content)
        elif not path.is_file():
            # Note: For remote filesystems, we can't easily check if it's a file vs directory
            # This check is mainly for local filesystem validation
            raise ProjectFileServiceError(f"{path} is not a file")
    except TemplateServiceError as e:
        raise ProjectFileServiceError(f"Failed to create init file {path}: {e}") from e


def create_project_structure(project_path: Path) -> None:
    """Create the basic project directory structure.

    Example:
        ```python
        from chainedpy.services.project_file_service import create_project_structure
        from pathlib import Path
        import shutil

        # Create project structure
        project_path = Path("my_chain_project")
        create_project_structure(project_path)

        # Verify directory structure
        assert project_path.exists()
        assert (project_path / "plugins").exists()
        assert (project_path / "plugins" / "then").exists()
        assert (project_path / "plugins" / "as_").exists()
        assert (project_path / "plugins" / "processors").exists()

        # Verify __init__.py files
        assert (project_path / "__init__.py").exists()
        assert (project_path / "plugins" / "__init__.py").exists()
        assert (project_path / "plugins" / "then" / "__init__.py").exists()
        assert (project_path / "plugins" / "as_" / "__init__.py").exists()
        assert (project_path / "plugins" / "processors" / "__init__.py").exists()

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :raises ProjectFileServiceError: If structure creation fails.
    """
    try:
        # Create project structure using fsspec
        fs_utils.makedirs(str(project_path / PLUGINS_DIR / THEN_DIR), exist_ok=True)
        fs_utils.makedirs(str(project_path / PLUGINS_DIR / AS_DIR), exist_ok=True)
        fs_utils.makedirs(str(project_path / PLUGINS_DIR / PROCESSORS_DIR), exist_ok=True)

        _ensure_pkg_init(project_path / INIT_FILE_NAME)
        _ensure_pkg_init(project_path / PLUGINS_DIR / INIT_FILE_NAME)
        for sub in (THEN_DIR, AS_DIR, PROCESSORS_DIR):
            _ensure_pkg_init(project_path / PLUGINS_DIR / sub / INIT_FILE_NAME)
            
    except Exception as e:
        raise ProjectFileServiceError(f"Failed to create project structure: {e}") from e


def create_chain_file(project_path: Path, project_name: str, base_project: str) -> Path:
    """Create the project chain.py file.

    Example:
        ```python
        from chainedpy.services.project_file_service import create_chain_file, create_project_structure
        from pathlib import Path
        import shutil

        # Create project structure first
        project_path = Path("my_chain_project")
        create_project_structure(project_path)

        # Create chain file
        chain_file = create_chain_file(
            project_path,
            "my_chain_project",
            "chainedpy"
        )

        # Verify chain file was created
        assert chain_file.exists()
        assert chain_file.name == "my_chain_project_chain.py"

        # Verify content
        content = chain_file.read_text()
        assert "from chainedpy import Chain" in content
        assert "class Chain" in content
        assert "my_chain_project" in content

        # Create with custom base project
        custom_chain_file = create_chain_file(
            project_path,
            "custom_project",
            "my_base_project"
        )

        custom_content = custom_chain_file.read_text()
        assert "from my_base_project.my_base_project_chain import Chain" in custom_content

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param project_name: Name of the project.
    :type project_name: [str][str]
    :param base_project: Base project to extend from.
    :type base_project: [str][str]
    :return [Path][pathlib.Path]: Path to the created chain file.
    :raises ProjectFileServiceError: If chain file creation fails.
    """
    try:
        # Determine base import based on base_project
        if base_project == DEFAULT_BASE_PROJECT:
            base_import = BASE_CHAIN_IMPORT
        else:
            # Custom project - import from its chain module
            base_project_path = Path(base_project)
            if not base_project_path.is_absolute():
                # Resolve relative path relative to current project
                base_project_path = project_path.parent / base_project_path
                base_project_path = base_project_path.resolve()
            base_project_name = base_project_path.name
            base_import = render_template(TEMPLATE_BASE_IMPORT_LOCAL, base_project_name=base_project_name).strip()

        # Generate chain.py file using template
        chain_py = project_path / f"{project_name}{CHAIN_FILE_SUFFIX}"
        chain_content = render_project_file("chain_py", base_import=base_import)  # "chain_py" is template type
        
        fs_utils.write_text(str(chain_py), chain_content)
        get_logger().info(f"Created chain file: {chain_py}")

        return chain_py

    except TemplateServiceError as e:
        msg = f"Failed to render chain file template: {e}"
        raise ProjectFileServiceError(msg) from e
    except Exception as e:
        msg = f"Failed to create chain file: {e}"
        raise ProjectFileServiceError(msg) from e


def create_config_file(project_path: Path, base_project: str, summary: str) -> Path:
    """Create the project configuration file.

    Example:
        ```python
        from chainedpy.services.project_file_service import create_config_file, create_project_structure
        from pathlib import Path
        import shutil
        import yaml

        # Create project structure first
        project_path = Path("my_chain_project")
        create_project_structure(project_path)

        # Create config file
        config_file = create_config_file(
            project_path,
            "chainedpy",
            "My custom ChainedPy project"
        )

        # Verify config file was created
        assert config_file.exists()
        assert config_file.name == "chainedpy.yaml"

        # Verify YAML content
        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        assert config_data["project"]["base_project"] == "chainedpy"
        assert config_data["project"]["summary"] == "My custom ChainedPy project"

        # Create with custom base project
        custom_config = create_config_file(
            project_path,
            "../my_base_project",
            "Custom base project"
        )

        with open(custom_config) as f:
            custom_data = yaml.safe_load(f)

        assert custom_data["project"]["base_project"] == "../my_base_project"

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param base_project: Base project to extend from.
    :type base_project: [str][str]
    :param summary: Project summary description.
    :type summary: [str][str]
    :return [Path][pathlib.Path]: Path to the created config file.
    :raises ProjectFileServiceError: If config file creation fails.
    """
    try:
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

        # Generate config file using template
        config_file = project_path / CONFIG_FILE_NAME
        config_content = render_config_file(base_project=base_project, summary=summary)
        
        fs_utils.write_text(str(config_file), config_content)
        get_logger().info(f"Created config file: {config_file}")

        return config_file

    except TemplateServiceError as e:
        raise ProjectFileServiceError(f"Template rendering failed: {e}") from e
    except Exception as e:
        raise ProjectFileServiceError(f"Failed to create config file: {e}") from e


def create_project_files(project_path: Path, project_name: str, base_project: str, summary: str) -> None:
    """Create all project files for a new ChainedPy project.

    Example:
        ```python
        from chainedpy.services.project_file_service import create_project_files
        from pathlib import Path
        import shutil

        # Create complete project
        project_path = Path("my_complete_project")
        create_project_files(
            project_path,
            "my_complete_project",
            "chainedpy",
            "A complete ChainedPy project example"
        )

        # Verify all files were created
        assert project_path.exists()
        assert (project_path / "chainedpy.yaml").exists()
        assert (project_path / "my_complete_project_chain.py").exists()
        assert (project_path / "plugins").exists()
        assert (project_path / "__init__.py").exists()

        # Verify chain file content
        chain_file = project_path / "my_complete_project_chain.py"
        content = chain_file.read_text()
        assert "from chainedpy import Chain" in content
        assert "class Chain" in content

        # Verify config file content
        import yaml
        with open(project_path / "chainedpy.yaml") as f:
            config = yaml.safe_load(f)
        assert config["project"]["base_project"] == "chainedpy"
        assert config["project"]["summary"] == "A complete ChainedPy project example"

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param project_name: Name of the project.
    :type project_name: [str][str]
    :param base_project: Base project to extend from.
    :type base_project: [str][str]
    :param summary: Project summary description.
    :type summary: [str][str]
    :raises ProjectFileServiceError: If project file creation fails.
    """
    try:
        # Create directory structure
        create_project_structure(project_path)
        
        # Create configuration file
        create_config_file(project_path, base_project, summary)
        
        # Create chain file
        create_chain_file(project_path, project_name, base_project)
        
        get_logger().info(f"Successfully created all project files for {project_name}")

    except ProjectFileServiceError:
        raise
    except Exception as e:
        raise ProjectFileServiceError(f"Failed to create project files: {e}") from e


def update_chain_file(project_path: Path, project_name: str, base_project: str) -> Path:
    """Update an existing chain file with new base project.

    Example:
        ```python
        from chainedpy.services.project_file_service import create_project_files, update_chain_file
        from pathlib import Path
        import shutil

        # Create initial project
        project_path = Path("update_test_project")
        create_project_files(
            project_path,
            "update_test_project",
            "chainedpy",
            "Test project for updates"
        )

        # Verify initial chain file
        chain_file = project_path / "update_test_project_chain.py"
        initial_content = chain_file.read_text()
        assert "from chainedpy import Chain" in initial_content

        # Update to new base project
        updated_chain_file = update_chain_file(
            project_path,
            "update_test_project",
            "my_custom_base"
        )

        # Verify update
        assert updated_chain_file.exists()
        updated_content = updated_chain_file.read_text()
        assert "from my_custom_base.my_custom_base_chain import Chain" in updated_content
        assert "from chainedpy import Chain" not in updated_content

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project root.
    :type project_path: [Path][pathlib.Path]
    :param project_name: Name of the project.
    :type project_name: [str][str]
    :param base_project: New base project to extend from.
    :type base_project: [str][str]
    :return [Path][pathlib.Path]: Path to the updated chain file.
    :raises ProjectFileServiceError: If chain file update fails.
    """
    try:
        # Remove existing chain file if it exists
        chain_py = project_path / f"{project_name}{CHAIN_FILE_SUFFIX}"
        if chain_py.exists():
            chain_py.unlink()
            
        # Create new chain file
        return create_chain_file(project_path, project_name, base_project)
        
    except Exception as e:
        raise ProjectFileServiceError(f"Failed to update chain file: {e}") from e
