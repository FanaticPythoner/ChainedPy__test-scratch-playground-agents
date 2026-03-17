"""
Project test service for ChainedPy tests.

Provides centralized project creation, setup, and management utilities
for testing, following ChainedPy's service patterns.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, List

from chainedpy.project import (
    create_project, create_then_plugin, create_as_plugin,
    _read_project_config, _write_project_config, ProjectConfig
)
from chainedpy.constants import (
    CONFIG_FILE_NAME, PLUGINS_DIR, PLUGINS_THEN_PATH, PLUGINS_AS_PATH, PLUGINS_PROCESSORS_PATH
)



class ProjectTestServiceError(Exception):
    """Exception raised when project test operations fail."""
    pass


def create_test_project(workspace: Path, project_name: str,
                       base_project: str = "chainedpy",
                       summary: Optional[str] = None) -> Path:
    """Create a test project with specified configuration.

    :param workspace: Workspace directory to create project in.
    :type workspace: Path
    :param project_name: Name of project to create.
    :type project_name: str
    :param base_project: Base project for the new project, defaults to "chainedpy".
    :type base_project: str, optional
    :param summary: Custom summary for the project, defaults to None.
    :type summary: Optional[str], optional
    :return Path: Path to created project directory.
    :raises ProjectTestServiceError: If project creation fails.
    """
    try:
        if summary is None:
            summary = f"Test project: {project_name}"
            
        project_path = create_project(
            workspace, project_name, 
            base_project=base_project, 
            summary=summary
        )
        return project_path
        
    except Exception as e:
        raise ProjectTestServiceError(f"Failed to create test project: {e}") from e


def create_project_chain(workspace: Path, project_names: List[str]) -> Dict[str, Path]:
    """Create a chain of projects where each extends the previous one.

    :param workspace: Workspace directory to create projects in.
    :type workspace: Path
    :param project_names: List of project names in order (first extends chainedpy).
    :type project_names: List[str]
    :return Dict[str, Path]: Dictionary mapping project names to their Path objects.
    :raises ProjectTestServiceError: If project chain creation fails.
    """
    try:
        # @@ STEP 1: Initialize projects dictionary. @@
        projects = {}

        # @@ STEP 2: Create each project in the chain. @@
        for i, name in enumerate(project_names):
            # || S.S. 2.1: Determine base project for current project. ||
            if i == 0:
                # First project extends chainedpy
                base_project = "chainedpy"
            else:
                # Subsequent projects extend the previous one
                base_project = f"./{project_names[i-1]}"

            # || S.S. 2.2: Create project with appropriate base. ||
            project_path = create_test_project(
                workspace, name,
                base_project=base_project,
                summary=f"Project {name}"
            )
            projects[name] = project_path

        # @@ STEP 3: Return projects dictionary. @@
        return projects

    except Exception as e:
        raise ProjectTestServiceError(f"Failed to create project chain: {e}") from e


def create_project_hierarchy(workspace: Path) -> Dict[str, Path]:
    """Create a standard project hierarchy for testing.

    Creates:
    - base_lib (extends chainedpy)
    - data_lib (extends base_lib)
    - ml_lib (extends data_lib)

    :param workspace: Workspace directory to create hierarchy in.
    :type workspace: Path
    :return Dict[str, Path]: Dictionary mapping project names to their paths.
    :raises ProjectTestServiceError: If hierarchy creation fails.
    """
    try:
        # @@ STEP 1: Initialize hierarchy dictionary. @@
        hierarchy = {}

        # @@ STEP 2: Create base library. @@
        hierarchy['base_lib'] = create_test_project(
            workspace, "base_lib",
            base_project="chainedpy",
            summary="Base library for testing"
        )

        # @@ STEP 3: Create data library extending base. @@
        hierarchy['data_lib'] = create_test_project(
            workspace, "data_lib",
            base_project=str(hierarchy['base_lib']),
            summary="Data processing library"
        )

        # @@ STEP 4: Create ML library extending data. @@
        hierarchy['ml_lib'] = create_test_project(
            workspace, "ml_lib",
            base_project=str(hierarchy['data_lib']),
            summary="Machine learning library"
        )

        # @@ STEP 5: Add workspace to hierarchy and return. @@
        hierarchy['workspace'] = workspace
        return hierarchy

    except Exception as e:
        raise ProjectTestServiceError(f"Failed to create project hierarchy: {e}") from e


def create_project_with_plugins(workspace: Path, project_name: str,
                               then_plugins: Optional[List[str]] = None,
                               as_plugins: Optional[List[str]] = None) -> Path:
    """Create a test project with specified plugins.

    :param workspace: Workspace directory to create project in.
    :type workspace: Path
    :param project_name: Name of project to create.
    :type project_name: str
    :param then_plugins: List of then plugin names to create, defaults to None.
    :type then_plugins: Optional[List[str]], optional
    :param as_plugins: List of as plugin names to create, defaults to None.
    :type as_plugins: Optional[List[str]], optional
    :return Path: Path to created project directory.
    :raises ProjectTestServiceError: If project with plugins creation fails.
    """
    try:
        # @@ STEP 1: Create base project. @@
        project_path = create_test_project(workspace, project_name)

        # @@ STEP 2: Create then plugins if specified. @@
        if then_plugins:
            for plugin_name in then_plugins:
                create_then_plugin(project_path, plugin_name)

        # @@ STEP 3: Create as plugins if specified. @@
        if as_plugins:
            for plugin_name in as_plugins:
                create_as_plugin(project_path, plugin_name)

        # @@ STEP 4: Return project path. @@
        return project_path

    except Exception as e:
        raise ProjectTestServiceError(f"Failed to create project with plugins: {e}") from e


def update_project_config(project_path: Path, base_project: str, summary: str) -> None:
    """Update a project's configuration.

    :param project_path: Path to project directory.
    :type project_path: Path
    :param base_project: New base project value.
    :type base_project: str
    :param summary: New summary value.
    :type summary: str
    :raises ProjectTestServiceError: If config update fails.
    :return None: None
    """
    try:
        # @@ STEP 1: Write updated project configuration. @@
        _write_project_config(project_path, base_project, summary)
    except Exception as e:
        raise ProjectTestServiceError(f"Failed to update project config: {e}") from e


def read_project_config(project_path: Path) -> ProjectConfig:
    """Read a project's configuration.

    :param project_path: Path to project directory.
    :type project_path: Path
    :return ProjectConfig: ProjectConfig object with project configuration.
    :raises ProjectTestServiceError: If config reading fails.
    """
    try:
        # @@ STEP 1: Read and return project configuration. @@
        return _read_project_config(project_path)
    except Exception as e:
        raise ProjectTestServiceError(f"Failed to read project config: {e}") from e


def create_circular_dependency_scenario(workspace: Path) -> Dict[str, Path]:
    """Create a scenario for testing circular dependency detection.

    :param workspace: Workspace directory to create scenario in.
    :type workspace: Path
    :return Dict[str, Path]: Dictionary with project paths for circular dependency testing.
    :raises ProjectTestServiceError: If scenario creation fails.
    """
    try:
        # @@ STEP 1: Initialize scenario dictionary. @@
        scenario = {}

        # @@ STEP 2: Create project A. @@
        scenario['project_a'] = create_test_project(
            workspace, "project_a",
            summary="Project A for circular dependency testing"
        )

        # @@ STEP 3: Create project B extending A. @@
        scenario['project_b'] = create_test_project(
            workspace, "project_b",
            base_project=str(scenario['project_a']),
            summary="Project B extending A"
        )

        # @@ STEP 4: Add workspace and return scenario. @@
        scenario['workspace'] = workspace
        return scenario

    except Exception as e:
        raise ProjectTestServiceError(f"Failed to create circular dependency scenario: {e}") from e


def get_project_files(project_path: Path) -> Dict[str, Path]:
    """Get paths to all standard project files.

    :param project_path: Path to project directory.
    :type project_path: Path
    :return Dict[str, Path]: Dictionary mapping file types to their paths.
    """
    # @@ STEP 1: Get project name from path. @@
    project_name = project_path.name

    # @@ STEP 2: Return dictionary of project file paths. @@
    return {
        'config': project_path / CONFIG_FILE_NAME,
        'init': project_path / "__init__.py",
        'chain': project_path / f"{project_name}_chain.py",
        'stub': project_path / f"{project_name}_chain.pyi",
        'plugins_dir': project_path / PLUGINS_DIR,
        'then_dir': project_path / PLUGINS_THEN_PATH,
        'as_dir': project_path / PLUGINS_AS_PATH,
        'processors_dir': project_path / PLUGINS_PROCESSORS_PATH
    }


def verify_project_structure(project_path: Path) -> bool:
    """Verify that a project has the expected file structure.

    :param project_path: Path to project directory to verify.
    :type project_path: Path
    :return bool: True if project structure is valid, False otherwise.
    """
    try:
        # @@ STEP 1: Get project files. @@
        files = get_project_files(project_path)

        # @@ STEP 2: Check required files exist. @@
        required_files = ['config', 'init', 'chain', 'stub']
        for file_type in required_files:
            if not files[file_type].exists():
                return False

        # @@ STEP 3: Check required directories exist. @@
        required_dirs = ['plugins_dir', 'then_dir', 'as_dir', 'processors_dir']
        for dir_type in required_dirs:
            if not files[dir_type].exists():
                return False

        # @@ STEP 4: Return True if all checks passed. @@
        return True

    except Exception:
        # @@ STEP 5: Return False on any exception. @@
        return False
