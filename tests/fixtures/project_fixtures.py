"""
Project fixtures for ChainedPy tests.

Provides centralized project creation and hierarchy setup fixtures
following ChainedPy's service patterns.
"""
from __future__ import annotations

# 1. Standard library imports

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
# (none)

# 5. ChainedPy internal modules
# (none)

# 6. Test utilities
from tests.services.filesystem_test_service import (
    create_config_file, create_corrupted_config_file, create_broken_plugin_file
)
from tests.services.project_test_service import (
    create_test_project, create_project_hierarchy,
    create_project_with_plugins, create_circular_dependency_scenario
)


@pytest.fixture
def simple_project(temp_workspace):
    """Create a simple test project.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to created simple project.
    """
    # @@ STEP 1: Create test project using helper function. @@
    project_path = create_test_project(temp_workspace, "simple_project")
    yield project_path


@pytest.fixture
def project_with_custom_summary(temp_workspace):
    """Create a project with custom summary.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to created project with custom summary.
    :raises Exception: If project creation fails.
    """
    # @@ STEP 1: Create test project with custom summary. @@
    project_path = create_test_project(
        temp_workspace, "custom_summary_project",
        summary="A specialized data processing library"
    )

    # @@ STEP 2: Yield project path for test usage. @@
    yield project_path


@pytest.fixture
def project_hierarchy(temp_workspace):
    """Create a standard project hierarchy for testing.

    Creates:
    - base_lib (extends chainedpy)
    - data_lib (extends base_lib)
    - ml_lib (extends data_lib)

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary mapping project names to their paths.
    :raises Exception: If hierarchy creation fails.
    """
    # @@ STEP 1: Create project hierarchy using helper function. @@
    hierarchy = create_project_hierarchy(temp_workspace)

    # @@ STEP 2: Yield hierarchy for test usage. @@
    yield hierarchy


@pytest.fixture
def project_with_then_plugins(temp_workspace):
    """Create a project with then plugins.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to project with then plugins.
    :raises Exception: If project creation fails.
    """
    # @@ STEP 1: Create project with then plugins using helper function. @@
    project_path = create_project_with_plugins(
        temp_workspace, "project_with_then",
        then_plugins=['double', 'transform', 'validate']
    )

    # @@ STEP 2: Yield project path for test usage. @@
    yield project_path


@pytest.fixture
def project_with_as_plugins(temp_workspace):
    """Create a project with as plugins.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to project with as plugins.
    :raises Exception: If project creation fails.
    """
    # @@ STEP 1: Create project with as plugins using helper function. @@
    project_path = create_project_with_plugins(
        temp_workspace, "project_with_as",
        as_plugins=['retry', 'timeout', 'cache']
    )

    # @@ STEP 2: Yield project path for test usage. @@
    yield project_path


@pytest.fixture
def project_with_all_plugins(temp_workspace):
    """Create a project with both then and as plugins.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to project with all plugin types.
    :raises Exception: If project creation fails.
    """
    # @@ STEP 1: Create project with both plugin types using helper function. @@
    project_path = create_project_with_plugins(
        temp_workspace, "project_with_all",
        then_plugins=['double', 'transform'],
        as_plugins=['retry', 'timeout']
    )

    # @@ STEP 2: Yield project path for test usage. @@
    yield project_path


@pytest.fixture
def circular_dependency_scenario(temp_workspace):
    """Create a scenario for testing circular dependency detection.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary with project paths for circular dependency testing.
    :raises Exception: If scenario creation fails.
    """
    # @@ STEP 1: Create circular dependency scenario using helper function. @@
    scenario = create_circular_dependency_scenario(temp_workspace)

    # @@ STEP 2: Yield scenario for test usage. @@
    yield scenario


@pytest.fixture
def complex_project_chain(temp_workspace):
    """Create a complex project inheritance chain for testing.

    Creates:
    - foundation (extends chainedpy)
    - utilities (extends foundation)
    - data_processing (extends utilities)
    - machine_learning (extends data_processing)
    - deep_learning (extends machine_learning)

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary mapping project names to their paths.
    :raises Exception: If project creation fails.
    """
    # @@ STEP 1: Initialize projects dictionary. @@
    projects = {}

    # @@ STEP 2: Create foundation project. @@
    projects['foundation'] = create_test_project(
        temp_workspace, "foundation",
        base_project="chainedpy",
        summary="Foundation library"
    )

    # @@ STEP 3: Create utilities extending foundation. @@
    projects['utilities'] = create_test_project(
        temp_workspace, "utilities",
        base_project=str(projects['foundation']),
        summary="Utility functions"
    )

    # @@ STEP 4: Create data_processing extending utilities. @@
    projects['data_processing'] = create_test_project(
        temp_workspace, "data_processing",
        base_project=str(projects['utilities']),
        summary="Data processing tools"
    )

    # @@ STEP 5: Create machine_learning extending data_processing. @@
    projects['machine_learning'] = create_test_project(
        temp_workspace, "machine_learning",
        base_project=str(projects['data_processing']),
        summary="Machine learning algorithms"
    )

    # @@ STEP 6: Create deep_learning extending machine_learning. @@
    projects['deep_learning'] = create_test_project(
        temp_workspace, "deep_learning",
        base_project=str(projects['machine_learning']),
        summary="Deep learning models"
    )

    # @@ STEP 7: Add workspace reference and yield projects. @@
    projects['workspace'] = temp_workspace
    yield projects


@pytest.fixture
def project_with_remote_base(temp_workspace):
    """Create a project configured to extend a remote base project.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary with project path and config details.
    :raises OSError: If directory creation or file writing fails.
    """
    # @@ STEP 1: Create project directory. @@
    project_dir = temp_workspace / "remote_extending_project"
    project_dir.mkdir()

    # @@ STEP 2: Create basic project structure. @@
    (project_dir / "__init__.py").touch()

    # @@ STEP 3: Create config with remote base. @@
    remote_url = "https://github.com/FanaticPythoner/chainedpy_test_public_chain_simple"
    create_config_file(
        project_dir,
        base_project=remote_url,
        summary="Project extending remote base"
    )

    # @@ STEP 4: Yield project configuration for test usage. @@
    yield {
        'project': project_dir,
        'remote_url': remote_url,
        'workspace': temp_workspace
    }


@pytest.fixture
def projects_with_different_bases(temp_workspace):
    """Create multiple projects with different base project configurations.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary mapping project types to their paths.
    :raises OSError: If directory creation or file writing fails.
    """
    # @@ STEP 1: Initialize projects dictionary. @@
    projects = {}

    # @@ STEP 2: Project extending chainedpy directly. @@
    projects['chainedpy_project'] = create_test_project(
        temp_workspace, "chainedpy_project",
        base_project="chainedpy",
        summary="Direct chainedpy extension"
    )

    # @@ STEP 3: Project extending local project. @@
    projects['local_base_project'] = create_test_project(
        temp_workspace, "local_base_project",
        base_project=str(projects['chainedpy_project']),
        summary="Local project extension"
    )

    # @@ STEP 4: Project with relative path base. @@
    relative_project_dir = temp_workspace / "relative_base_project"
    relative_project_dir.mkdir()
    (relative_project_dir / "__init__.py").touch()
    create_config_file(
        relative_project_dir,
        base_project="./chainedpy_project",
        summary="Relative path extension"
    )
    projects['relative_base_project'] = relative_project_dir

    # @@ STEP 5: Project with remote base. @@
    remote_project_dir = temp_workspace / "remote_base_project"
    remote_project_dir.mkdir()
    (remote_project_dir / "__init__.py").touch()
    create_config_file(
        remote_project_dir,
        base_project="https://github.com/user/remote_project",
        summary="Remote project extension"
    )
    projects['remote_base_project'] = remote_project_dir

    # @@ STEP 6: Add workspace reference and yield projects. @@
    projects['workspace'] = temp_workspace
    yield projects


@pytest.fixture
def corrupted_project(temp_workspace):
    """Create a project with corrupted configuration for error testing.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to project with corrupted configuration.
    :raises OSError: If directory creation or file writing fails.
    """
    # @@ STEP 1: Create project directory. @@
    project_dir = temp_workspace / "corrupted_project"
    project_dir.mkdir()

    # @@ STEP 2: Create basic project structure. @@
    (project_dir / "__init__.py").touch()

    # @@ STEP 3: Create corrupted config file. @@
    create_corrupted_config_file(project_dir)

    # @@ STEP 4: Yield project directory for test usage. @@
    yield project_dir


@pytest.fixture
def project_with_broken_plugins(temp_workspace):
    """Create a project with broken plugins for error testing.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Path to project with broken plugins.
    :raises Exception: If project creation or plugin file creation fails.
    """
    # @@ STEP 1: Create test project using helper function. @@
    project_path = create_test_project(temp_workspace, "broken_plugins_project")

    # @@ STEP 2: Create broken then plugin. @@
    then_dir = project_path / "plugins" / "then"
    create_broken_plugin_file(then_dir, "then_broken")

    # @@ STEP 3: Create broken as plugin. @@
    as_dir = project_path / "plugins" / "as_"
    create_broken_plugin_file(as_dir, "as_broken")

    # @@ STEP 4: Yield project path for test usage. @@
    yield project_path
