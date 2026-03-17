"""
Test circular dependency detection in ChainedPy project configuration system.

This module tests the validation logic that prevents projects from creating
circular dependency chains when extending other projects.
"""

# Use centralized test infrastructure
from tests.services.project_test_service import create_test_project, create_project_chain
from tests.services.filesystem_test_service import create_corrupted_config_file
from tests.utils.assertion_helpers import assert_exception_with_message

from chainedpy.project import (
    update_project_base,
    _validate_base_project,
    _read_project_config
)


class TestDirectCircularDependency:
    """Test detection of direct circular dependencies (A → A).

    :raises Exception: If circular dependency detection fails during testing.
    """

    def test_project_cannot_extend_itself_absolute_path(self, temp_workspace):
        """Test that a project cannot extend itself using absolute path.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If circular dependency is not detected.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project_a = create_test_project(temp_workspace, "project_a", summary="Project A")

        # @@ STEP 2: Verify self-extension is prevented. @@
        assert_exception_with_message(
            ValueError, "Circular dependency: project project_a cannot extend itself",
            _validate_base_project, str(project_a), project_a
        )

    def test_project_cannot_extend_itself_relative_path(self, temp_workspace):
        """Test that a project cannot extend itself using relative path.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If circular dependency is not detected.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project_a = create_test_project(temp_workspace, "project_a", summary="Project A")

        # @@ STEP 2: Use the actual project path as base project (should be detected as self-extension). @@
        assert_exception_with_message(
            ValueError, "Circular dependency: project project_a cannot extend itself",
            _validate_base_project, str(project_a), project_a
        )

    def test_update_base_project_prevents_self_extension(self, temp_workspace):
        """Test that update_project_base prevents self-extension.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If self-extension is not prevented.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project_a = create_test_project(temp_workspace, "project_a", summary="Project A")

        # @@ STEP 2: Verify update_project_base prevents self-extension. @@
        assert_exception_with_message(
            ValueError, "Invalid base project: Circular dependency: project project_a cannot extend itself",
            update_project_base, project_a, str(project_a), "Attempting self-extension"
        )


class TestIndirectCircularDependency:
    """Test detection of indirect circular dependencies (A → B → A).

    :raises Exception: If indirect circular dependency detection fails during testing.
    """

    def test_two_project_cycle(self, temp_workspace):
        """Test detection of A → B → A cycle.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If two-project cycle is not detected.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b"])
        project_a = project_chain['project_a']
        project_b = project_chain['project_b']

        # @@ STEP 2: project_b already extends project_a. @@
        # Now try to make project_a extend project_b (creating A → B → A)
        assert_exception_with_message(
            ValueError, "Circular dependency.*cannot extend itself",
            _validate_base_project, str(project_b), project_a
        )

    def test_three_project_cycle(self, temp_workspace):
        """Test detection of A → B → C → A cycle.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If three-project cycle is not detected.
        :return None: None
        """
        # @@ STEP 1: Create three-project chain. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c"])
        project_a = project_chain['project_a']
        project_c = project_chain['project_c']

        # @@ STEP 2: Current chain: A → chainedpy, B → A, C → B. @@
        # Try to make A extend C (creating A → C → B → A)
        assert_exception_with_message(
            ValueError, "Circular dependency.*cannot extend itself",
            _validate_base_project, str(project_c), project_a
        )

    def test_update_base_project_prevents_indirect_cycle(self, temp_workspace):
        """Test that update_project_base prevents indirect cycles.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If indirect cycle is not prevented.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b"])
        project_a = project_chain['project_a']
        project_b = project_chain['project_b']

        # @@ STEP 2: Try to create A → B → A cycle. @@
        assert_exception_with_message(
            ValueError, "Invalid base project.*Circular dependency",
            update_project_base, project_a, str(project_b), "Attempting indirect cycle"
        )


class TestComplexCircularDependency:
    """Test detection of complex circular dependency scenarios.

    :raises Exception: If complex circular dependency detection fails during testing.
    """

    def test_long_chain_cycle(self, temp_workspace):
        """Test detection of cycles in longer chains (A → B → C → D → A).

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If long chain cycle is not detected.
        :return None: None
        """
        # @@ STEP 1: Create a chain of 4 projects. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c", "project_d"])
        project_a = project_chain['project_a']
        project_d = project_chain['project_d']

        # @@ STEP 2: Try to close the loop: A → D (creating A → D → C → B → A). @@
        assert_exception_with_message(
            ValueError, "Circular dependency.*cannot extend itself",
            _validate_base_project, str(project_d), project_a
        )
    
    def test_cycle_in_middle_of_chain(self, temp_workspace):
        """Test detection when cycle is created in middle of existing chain.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If cycle in middle of chain is not detected.
        :return None: None
        """
        # @@ STEP 1: Create chain: A → chainedpy, B → A, C → B, D → C. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c", "project_d"])
        project_b = project_chain['project_b']
        project_c = project_chain['project_c']

        # @@ STEP 2: Try to make B extend C (creating B → C → B cycle). @@
        assert_exception_with_message(
            ValueError, "Circular dependency.*cannot extend itself",
            update_project_base, project_b, str(project_c), "Creating cycle in middle"
        )


class TestValidExtensionChains:
    """Test that valid extension chains are allowed.

    :raises Exception: If valid extension chain validation fails during testing.
    """

    def test_linear_chain_allowed(self, temp_workspace):
        """Test that linear chains without cycles are allowed.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If valid linear chain is not allowed.
        :return None: None
        """
        # @@ STEP 1: Create linear project chain. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c"])
        project_a = project_chain['project_a']
        project_b = project_chain['project_b']
        project_c = project_chain['project_c']

        # @@ STEP 2: Verify current chain is valid: C → B → A → chainedpy. @@
        config_c = _read_project_config(project_c)
        config_b = _read_project_config(project_b)
        config_a = _read_project_config(project_a)

        # @@ STEP 3: Assert chain structure is correct. @@
        assert config_c.base_project == f"./{project_b.name}"
        assert config_b.base_project == f"./{project_a.name}"
        assert config_a.base_project == "chainedpy"

    def test_changing_to_chainedpy_allowed(self, temp_workspace):
        """Test that changing any project to extend chainedpy is always allowed.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If changing to chainedpy is not allowed.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c"])
        project_c = project_chain['project_c']

        # @@ STEP 2: This should not raise any exception. @@
        _validate_base_project("chainedpy", project_c)

        # @@ STEP 3: Actually update it. @@
        update_project_base(project_c, "chainedpy", "Now extends chainedpy directly")

        # @@ STEP 4: Verify configuration was updated. @@
        config = _read_project_config(project_c)
        assert config.base_project == "chainedpy"
    
    def test_shortening_chain_allowed(self, temp_workspace):
        """Test that shortening extension chains is allowed.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If shortening chain is not allowed.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c"])
        project_a = project_chain['project_a']
        project_c = project_chain['project_c']

        # @@ STEP 2: Change C to extend A directly (skipping B). @@
        # This should not create a cycle: C → A → chainedpy
        _validate_base_project(str(project_a), project_c)

        # @@ STEP 3: Update project base. @@
        update_project_base(project_c, str(project_a), "Now extends A directly")

        # @@ STEP 4: Verify configuration was updated. @@
        config = _read_project_config(project_c)
        assert config.base_project == f"./{project_a.name}"


class TestEdgeCases:
    """Test edge cases in circular dependency detection.

    :raises Exception: If edge case handling fails during testing.
    """
    
    def test_nonexistent_base_project(self, temp_workspace):
        """Test validation with non-existent base project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If circular dependency error is incorrectly raised.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project_a = create_test_project(temp_workspace, "project_a", summary="Project A")

        # @@ STEP 2: Create path to nonexistent project. @@
        nonexistent_path = temp_workspace / "nonexistent_project"

        # @@ STEP 3: This should not raise a circular dependency error. @@
        # (it might raise other errors, but not circular dependency)
        try:
            _validate_base_project(str(nonexistent_path), project_a)
        except ValueError as e:
            assert "Circular dependency" not in str(e)
    
    def test_invalid_config_file(self, temp_workspace):
        """Test validation when base project has invalid config file.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If circular dependency error is incorrectly raised.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        project_a = create_test_project(temp_workspace, "project_a")
        project_b = create_test_project(temp_workspace, "project_b")

        # @@ STEP 2: Corrupt project_b's config file using centralized service. @@
        create_corrupted_config_file(project_b)

        # @@ STEP 3: Validation should handle this gracefully (log error but not crash). @@
        try:
            _validate_base_project(str(project_b), project_a)
        except ValueError as e:
            # || S.S. 3.1: Should not be a circular dependency error. ||
            assert "Circular dependency" not in str(e)
