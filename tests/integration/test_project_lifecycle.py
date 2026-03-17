"""
Integration tests for ChainedPy project lifecycle.

Tests the complete project lifecycle including creation, configuration,
updates, and file generation with real file system operations.
"""
from __future__ import annotations

# 1. Standard library imports
# (none)

# 2. Third-party imports
import pytest

# 3. Internal constants
from chainedpy.constants import CONFIG_FILE_NAME

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils

# 5. ChainedPy internal modules
from chainedpy.project import update_project_base, update_project_stub

# 6. Test utilities
from tests.services.project_test_service import (
    create_test_project, read_project_config, update_project_config,
    verify_project_structure, get_project_files
)
from tests.services.assertion_test_service import ProjectAssertionService
from tests.utils.assertion_helpers import (
    assert_project_structure, assert_config_values, assert_file_exists_with_content
)


class TestProjectCreation:
    """Test project creation with real file system operations.

    :raises Exception: If project creation testing fails.
    """

    def test_create_basic_project(self, temp_workspace):
        """Test creating a basic project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If basic project creation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create basic test project. @@
        project_path = create_test_project(temp_workspace, "basic_project")

        # @@ STEP 2: Verify project structure. @@
        assert_project_structure(project_path, "basic_project")

        # @@ STEP 3: Verify configuration. @@
        assert_config_values(project_path, "chainedpy", "Test project: basic_project")

    def test_create_project_with_custom_summary(self, temp_workspace):
        """Test creating a project with custom summary.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If project creation with custom summary doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define custom summary. @@
        custom_summary = "A specialized data processing library"
        # @@ STEP 2: Create project with custom summary. @@
        project_path = create_test_project(
            temp_workspace, "custom_project",
            summary=custom_summary
        )

        # @@ STEP 3: Verify project structure and configuration. @@
        assert_project_structure(project_path)
        assert_config_values(project_path, "chainedpy", custom_summary)

    def test_create_project_with_custom_base(self, temp_workspace):
        """Test creating a project with custom base project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If project creation with custom base doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create base project first. @@
        base_project = create_test_project(temp_workspace, "base_project")

        # @@ STEP 2: Create extending project. @@
        extending_project = create_test_project(
            temp_workspace, "extending_project",
            base_project=str(base_project),
            summary="Extended functionality"
        )

        # @@ STEP 3: Verify project structure and configuration. @@
        assert_project_structure(extending_project)
        # Base project path should be normalized to relative
        assert_config_values(extending_project, "./base_project", "Extended functionality")

    def test_create_multiple_projects(self, temp_workspace):
        """Test creating multiple projects in same workspace.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If multiple project creation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create multiple projects. @@
        projects = []
        for i in range(3):
            project_path = create_test_project(temp_workspace, f"project_{i}")
            projects.append(project_path)
            assert_project_structure(project_path)

        # @@ STEP 2: All projects should exist independently. @@
        for project_path in projects:
            assert project_path.exists()
            assert verify_project_structure(project_path)


class TestProjectConfiguration:
    """Test project configuration management.

    :raises Exception: If project configuration testing fails.
    """

    def test_read_project_config(self, simple_project):
        """Test reading project configuration.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If reading project config doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Read project configuration. @@
        config = read_project_config(simple_project)

        # @@ STEP 2: Verify configuration values. @@
        assert config.base_project == "chainedpy"
        assert "simple_project" in config.summary

    def test_update_project_config(self, simple_project):
        """Test updating project configuration.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If updating project config doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define new configuration values. @@
        new_base = "new_base_project"
        # @@ STEP 2: Update project configuration. @@
        new_summary = "Updated summary"

        update_project_config(simple_project, new_base, new_summary)

        # @@ STEP 3: Verify update. @@
        config = read_project_config(simple_project)
        assert config.base_project == new_base
        assert config.summary == new_summary

    def test_config_file_format(self, simple_project):
        """Test that config file is properly formatted YAML.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If config file format is incorrect.
        :return None: None
        """
        # @@ STEP 1: Get config file path. @@
        config_file = simple_project / CONFIG_FILE_NAME

        # @@ STEP 2: Define expected content. @@
        expected_content = [
            "project:",
            "base_project:",
            "summary:"
        ]

        # @@ STEP 3: Verify file content. @@
        assert_file_exists_with_content(config_file, expected_content)

    def test_config_with_special_characters(self, temp_workspace):
        """Test configuration with special characters.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If special characters in config don't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project with special characters in summary. @@
        special_summary = 'Project with: special chars, quotes "test", and symbols @#$%'
        project_path = create_test_project(
            temp_workspace, "special_project",
            summary=special_summary
        )

        # @@ STEP 2: Verify special characters are preserved. @@
        config = read_project_config(project_path)
        assert config.summary == special_summary


class TestProjectHierarchy:
    """Test project hierarchy and inheritance.

    :raises Exception: If project hierarchy testing fails.
    """

    def test_create_project_hierarchy(self, project_hierarchy):
        """Test creating a complete project hierarchy.

        :param project_hierarchy: Project hierarchy fixture.
        :type project_hierarchy: Dict[str, Path]
        :raises AssertionError: If project hierarchy creation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Get hierarchy data. @@
        hierarchy = project_hierarchy

        # @@ STEP 2: Verify all projects exist. @@
        for project_name, project_path in hierarchy.items():
            if project_name != 'workspace':
                assert_project_structure(project_path)
        
        # Verify hierarchy relationships
        base_lib = hierarchy['base_lib']
        data_lib = hierarchy['data_lib']
        ml_lib = hierarchy['ml_lib']
        
        # Check base_lib extends chainedpy
        assert_config_values(base_lib, "chainedpy", "Base library for testing")
        
        # Check data_lib extends base_lib
        config = read_project_config(data_lib)
        assert config.base_project == "./base_lib"
        
        # Check ml_lib extends data_lib
        config = read_project_config(ml_lib)
        assert config.base_project == "./data_lib"
    
    def test_update_hierarchy_relationships(self, project_hierarchy):
        """Test updating relationships in project hierarchy.

        :param project_hierarchy: Project hierarchy fixture.
        :type project_hierarchy: Dict[str, Path]
        :raises AssertionError: If hierarchy relationship updates don't work correctly.
        :return None: None
        """
        # @@ STEP 1: Get hierarchy components. @@
        hierarchy = project_hierarchy
        ml_lib = hierarchy['ml_lib']
        base_lib = hierarchy['base_lib']

        # @@ STEP 2: Change ml_lib to extend base_lib directly. @@
        update_project_config(ml_lib, str(base_lib), "Now extends base_lib directly")

        # @@ STEP 3: Verify update. @@
        config = read_project_config(ml_lib)
        assert config.base_project == "./base_lib"
        assert config.summary == "Now extends base_lib directly"


class TestProjectFiles:
    """Test project file generation and management.

    :raises Exception: If project file testing fails.
    """

    def test_project_file_structure(self, simple_project):
        """Test that all required project files are created.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If required project files are missing.
        :return None: None
        """
        # @@ STEP 1: Get project files. @@
        files = get_project_files(simple_project)

        # @@ STEP 2: Check all required files exist. @@
        required_files = ['config', 'init', 'chain', 'stub']
        for file_type in required_files:
            assert files[file_type].exists(), f"Missing {file_type} file"

        # @@ STEP 3: Check all required directories exist. @@
        required_dirs = ['plugins_dir', 'then_dir', 'as_dir', 'processors_dir']
        for dir_type in required_dirs:
            assert files[dir_type].exists(), f"Missing {dir_type} directory"
            assert files[dir_type].is_dir(), f"{dir_type} is not a directory"

    def test_chain_file_content(self, simple_project):
        """Test that chain file has correct content.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If chain file content is incorrect.
        :return None: None
        """
        # @@ STEP 1: Get chain file. @@
        files = get_project_files(simple_project)
        chain_file = files['chain']

        # @@ STEP 2: Define expected content. @@
        expected_content = [
            "from chainedpy.chain import Chain",  # re-export runtime class
            "from importlib import import_module",
            "_plugins_dir = pathlib.Path(__file__)",
            "__all__ = ('Chain',)"
        ]

        # @@ STEP 3: Verify file content. @@
        assert_file_exists_with_content(chain_file, expected_content)

    def test_stub_file_content(self, simple_project):
        """Test that stub file has correct content.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If stub file content is incorrect.
        :return None: None
        """
        # @@ STEP 1: Get stub file. @@
        files = get_project_files(simple_project)
        stub_file = files['stub']

        # @@ STEP 2: Define expected content. @@
        expected_content = [
            "from chainedpy.chain import Chain as _BaseChain",
            f"class Chain(_BaseChain[_T]):"
        ]

        # @@ STEP 3: Verify file content. @@
        assert_file_exists_with_content(stub_file, expected_content)

    def test_init_file_content(self, simple_project):
        """Test that __init__.py file has correct content.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If __init__.py file content is incorrect.
        :return None: None
        """
        # @@ STEP 1: Get init file. @@
        files = get_project_files(simple_project)
        init_file = files['init']

        # @@ STEP 2: Define expected content. @@
        expected_content = [
            "# Auto-generated by ChainedPy CLI"
        ]

        # @@ STEP 3: Verify file content. @@
        assert_file_exists_with_content(init_file, expected_content)


class TestProjectValidation:
    """Test project validation and error handling.

    :raises Exception: If project validation testing fails.
    """

    def test_verify_valid_project_structure(self, simple_project):
        """Test verification of valid project structure.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If valid project structure verification fails.
        :return None: None
        """
        # @@ STEP 1: Verify valid project structure. @@
        assert verify_project_structure(simple_project) == True

    def test_verify_invalid_project_structure(self, temp_workspace):
        """Test verification of invalid project structure.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If invalid project structure verification fails.
        :return None: None
        """
        # @@ STEP 1: Create incomplete project. @@
        incomplete_project = temp_workspace / "incomplete_project"
        incomplete_project.mkdir()

        # @@ STEP 2: Only create some files. @@
        (incomplete_project / "__init__.py").touch()

        # @@ STEP 3: Verify structure is invalid. @@
        assert verify_project_structure(incomplete_project) == False

    def test_project_assertion_service(self, simple_project):
        """Test ProjectAssertionService functionality.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If ProjectAssertionService doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Test project exists assertion. @@
        ProjectAssertionService.assert_project_exists(simple_project)

        # @@ STEP 2: Test project structure assertion. @@
        ProjectAssertionService.assert_project_structure(simple_project)

        # @@ STEP 3: Test config values assertion. @@
        ProjectAssertionService.assert_config_values(
            simple_project, "chainedpy", "Test project: simple_project"
        )
    
    def test_project_assertion_failures(self, temp_workspace):
        """Test that project assertions fail appropriately.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If project assertion failures don't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create path to nonexistent project. @@
        nonexistent_project = temp_workspace / "nonexistent"

        # @@ STEP 2: Verify assertion fails for nonexistent project. @@
        with pytest.raises(AssertionError, match="does not exist"):
            ProjectAssertionService.assert_project_exists(nonexistent_project)


class TestProjectUpdates:
    """Test project update operations.

    :raises Exception: If project update testing fails.
    """

    def test_update_project_base(self, project_hierarchy):
        """Test updating project base with real file operations.

        :param project_hierarchy: Project hierarchy fixture.
        :type project_hierarchy: Dict[str, Path]
        :raises AssertionError: If project base update doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Get hierarchy components. @@
        hierarchy = project_hierarchy
        ml_lib = hierarchy['ml_lib']

        # @@ STEP 2: Update to extend chainedpy directly. @@
        update_project_base(ml_lib, "chainedpy", "Now extends chainedpy directly")

        # @@ STEP 3: Verify configuration was updated. @@
        config = read_project_config(ml_lib)
        assert config.base_project == "chainedpy"
        assert config.summary == "Now extends chainedpy directly"

        # @@ STEP 4: Verify files were regenerated. @@
        files = get_project_files(ml_lib)

        # @@ STEP 5: Chain file should import from chainedpy. @@
        assert_file_exists_with_content(
            files['chain'],
            ["from chainedpy.chain import Chain"]
        )

        # @@ STEP 6: Stub file should be updated. @@
        assert_file_exists_with_content(
            files['stub'],
            ["from chainedpy.chain import Chain as _BaseChain"]
        )

    def test_update_project_stub(self, simple_project):
        """Test updating project stub file.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If project stub update doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Update stub file. @@
        result = update_project_stub(simple_project)

        # @@ STEP 2: Verify stub file exists and is a file. @@
        assert result.exists()
        assert result.is_file()

        # @@ STEP 3: Verify content. @@
        content = fs_utils.read_text(str(result))
        assert "class Chain(_BaseChain[_T])" in content
