"""
Test ChainedPy update base project functionality.

This module tests the update_project_base function and related functionality
for changing which project a given project extends, including automatic
regeneration of chain.py and stub files.
"""
from __future__ import annotations

# 1. Standard library imports

# 2. Third-party imports

# 3. Internal constants
# (none)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils

# 5. ChainedPy internal modules
from chainedpy.project import (
    update_project_base,
    _read_project_config
)

# 6. Test utilities
from tests.services.project_test_service import create_test_project, create_project_chain, create_project_with_plugins
from tests.utils.assertion_helpers import assert_exception_with_message, assert_file_exists_with_content


class TestBasicUpdateFunctionality:
    """Test basic update base project functionality.

    :raises Exception: If basic update functionality testing fails.
    """

    def test_update_to_chainedpy(self, temp_workspace):
        """Test updating a project to extend chainedpy directly.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If update to chainedpy doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']

        # @@ STEP 2: Verify initial configuration. @@
        config = _read_project_config(ml_lib)
        assert config.base_project == "./data_lib"

        # @@ STEP 3: Update to extend chainedpy. @@
        update_project_base(ml_lib, "chainedpy", "Now extends chainedpy directly")

        # @@ STEP 4: Verify config was updated. @@
        config = _read_project_config(ml_lib)
        assert config.base_project == "chainedpy"
        assert config.summary == "Now extends chainedpy directly"
    
    def test_update_to_different_project(self, temp_workspace):
        """Test updating a project to extend a different project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If update to different project doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        base_lib = create_test_project(temp_workspace, "base_lib", summary="Base library")
        data_lib = create_test_project(temp_workspace, "data_lib", summary="Data processing library")
        ml_lib = create_test_project(temp_workspace, "ml_lib", base_project=str(data_lib),
                                   summary="Machine learning library")

        # @@ STEP 2: Update to extend base_lib instead of data_lib. @@
        update_project_base(ml_lib, str(base_lib), "Now extends base_lib")

        # @@ STEP 3: Verify config was updated. @@
        config = _read_project_config(ml_lib)
        assert config.base_project == "./base_lib"
        assert config.summary == "Now extends base_lib"

    def test_update_summary_only(self, temp_workspace):
        """Test updating only the summary without changing base project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If summary-only update doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']

        # @@ STEP 2: Get current base project. @@
        original_config = _read_project_config(ml_lib)
        original_base = original_config.base_project

        # @@ STEP 3: Update only summary. @@
        update_project_base(ml_lib, original_base, "Updated summary only")

        # @@ STEP 4: Verify base project unchanged, summary updated. @@
        config = _read_project_config(ml_lib)
        assert config.base_project == original_base
        assert config.summary == "Updated summary only"

    def test_update_with_none_summary(self, temp_workspace):
        """Test updating base project while preserving existing summary.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If update with None summary doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        base_lib = create_test_project(temp_workspace, "base_lib", summary="Base library")
        ml_lib = create_test_project(temp_workspace, "ml_lib", summary="Machine learning library")

        # @@ STEP 2: Get original summary. @@
        original_config = _read_project_config(ml_lib)
        original_summary = original_config.summary

        # @@ STEP 3: Update base project with None summary (should preserve existing). @@
        update_project_base(ml_lib, str(base_lib), None)

        # @@ STEP 4: Verify base project changed, summary preserved. @@
        config = _read_project_config(ml_lib)
        assert config.base_project == "./base_lib"
        assert config.summary == original_summary


class TestChainFileRegeneration:
    """Test that chain.py files are correctly regenerated.

    :raises Exception: If chain file regeneration testing fails.
    """

    def test_chain_file_updated_to_chainedpy(self, temp_workspace):
        """Test that chain.py is updated when changing to chainedpy.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If chain file update to chainedpy doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']
        chain_file = ml_lib / "ml_lib_chain.py"

        # @@ STEP 2: Verify initial import from data_lib. @@
        original_content = fs_utils.read_text(str(chain_file))
        assert "from data_lib.data_lib_chain import Chain" in original_content

        # @@ STEP 3: Update to chainedpy. @@
        update_project_base(ml_lib, "chainedpy", "Updated to chainedpy")

        # @@ STEP 4: Verify chain.py was updated. @@
        assert_file_exists_with_content(
            chain_file,
            ["from chainedpy.chain import Chain"]
        )

        # @@ STEP 5: Verify old import was removed. @@
        updated_content = fs_utils.read_text(str(chain_file))
        assert "from data_lib.data_lib_chain import Chain" not in updated_content

    def test_chain_file_updated_to_different_project(self, temp_workspace):
        """Test that chain.py is updated when changing to different project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If chain file update to different project doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        base_lib = create_test_project(temp_workspace, "base_lib")
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']
        chain_file = ml_lib / "ml_lib_chain.py"

        # @@ STEP 2: Update to base_lib. @@
        update_project_base(ml_lib, str(base_lib), "Updated to base_lib")

        # @@ STEP 3: Verify chain.py was updated. @@
        assert_file_exists_with_content(
            chain_file,
            ["from base_lib.base_lib_chain import Chain"]
        )

        # @@ STEP 4: Verify old import was removed. @@
        updated_content = fs_utils.read_text(str(chain_file))
        assert "from data_lib.data_lib_chain import Chain" not in updated_content

    def test_chain_file_structure_preserved(self, temp_workspace):
        """Test that chain.py file structure is preserved during update.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If chain file structure preservation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")

        # @@ STEP 2: Update project. @@
        update_project_base(ml_lib, "chainedpy", "Updated")

        # @@ STEP 3: Verify chain file structure is preserved. @@
        chain_file = ml_lib / "ml_lib_chain.py"
        assert_file_exists_with_content(
            chain_file,
            [
                "from importlib import import_module",
                "import pkgutil, pathlib",
                "_plugins_dir = pathlib.Path(__file__)",
                "__all__ = ('Chain',)"
            ]
        )


class TestStubFileRegeneration:
    """Test that .pyi stub files are correctly regenerated.

    :raises Exception: If stub file regeneration testing fails.
    """

    def test_stub_file_updated_to_chainedpy(self, temp_workspace):
        """Test that .pyi file is updated when changing to chainedpy.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file update to chainedpy doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']
        stub_file = ml_lib / "ml_lib_chain.pyi"

        # @@ STEP 2: Update to chainedpy. @@
        update_project_base(ml_lib, "chainedpy", "Updated to chainedpy")

        # @@ STEP 3: Verify stub file was updated. @@
        assert_file_exists_with_content(
            stub_file,
            ["from chainedpy.chain import Chain as _BaseChain"]
        )

        # @@ STEP 4: Verify old import was removed. @@
        stub_content = fs_utils.read_text(str(stub_file))
        assert "from data_lib.data_lib_chain import Chain as _BaseChain" not in stub_content

    def test_stub_file_updated_to_different_project(self, temp_workspace):
        """Test that .pyi file is updated when changing to different project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file update to different project doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        base_lib = create_test_project(temp_workspace, "base_lib")
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']
        stub_file = ml_lib / "ml_lib_chain.pyi"

        # @@ STEP 2: Update to base_lib. @@
        update_project_base(ml_lib, str(base_lib), "Updated to base_lib")

        # @@ STEP 3: Verify stub file was updated. @@
        assert_file_exists_with_content(
            stub_file,
            ["from base_lib.base_lib_chain import Chain as _BaseChain"]
        )

        # @@ STEP 4: Verify old import was removed. @@
        stub_content = fs_utils.read_text(str(stub_file))
        assert "from data_lib.data_lib_chain import Chain as _BaseChain" not in stub_content

    def test_stub_summary_updated(self, temp_workspace):
        """Test that stub file docstring reflects updated summary.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub summary update doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")

        # @@ STEP 2: Update with new summary. @@
        new_summary = "Advanced ML pipeline with custom features"
        update_project_base(ml_lib, "chainedpy", new_summary)

        # @@ STEP 3: Verify stub file contains new summary. @@
        stub_file = ml_lib / "ml_lib_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            [new_summary]
        )

    def test_stub_plugin_count_preserved(self, temp_workspace):
        """Test that plugin information is preserved in stub file.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub plugin preservation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        ml_lib = create_project_with_plugins(temp_workspace, "ml_lib", then_plugins=["train"])

        # @@ STEP 2: Update project (ml_lib has 1 plugin: then_train). @@
        update_project_base(ml_lib, "chainedpy", "Updated")

        # @@ STEP 3: Verify plugin information is preserved. @@
        stub_file = ml_lib / "ml_lib_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["1 additional plugin(s)", "then_train"]
        )


class TestErrorHandling:
    """Test error handling in update base project functionality.

    :raises Exception: If error handling testing fails.
    """

    def test_invalid_base_project_path(self, temp_workspace):
        """Test error handling for invalid base project paths.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If invalid base project error handling doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")

        # @@ STEP 2: Define nonexistent project path. @@
        nonexistent_path = temp_workspace / "nonexistent_project"

        # @@ STEP 3: Verify exception is raised for invalid path. @@
        assert_exception_with_message(
            ValueError, "Invalid base project",
            update_project_base, ml_lib, str(nonexistent_path), "Should fail"
        )

    def test_circular_dependency_prevention(self, temp_workspace):
        """Test that circular dependencies are prevented.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If circular dependency prevention doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project chain. @@
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']
        data_lib = project_chain['data_lib']

        # @@ STEP 2: Verify circular dependency is prevented (ml_lib extends data_lib, so data_lib cannot extend ml_lib). @@
        assert_exception_with_message(
            ValueError, "Invalid base project.*Circular dependency",
            update_project_base, data_lib, str(ml_lib), "Should create cycle"
        )

    def test_self_extension_prevention(self, temp_workspace):
        """Test that projects cannot extend themselves.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If self-extension prevention doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")

        # @@ STEP 2: Verify self-extension is prevented. @@
        assert_exception_with_message(
            ValueError, "Invalid base project.*Circular dependency",
            update_project_base, ml_lib, str(ml_lib), "Should fail"
        )


class TestFileVerification:
    """Test that file operations are properly verified.

    :raises Exception: If file verification testing fails.
    """

    def test_config_file_verification(self, temp_workspace):
        """Test that config file changes are verified.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If config file verification doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")

        # @@ STEP 2: Update project (should succeed and verify correctly). @@
        update_project_base(ml_lib, "chainedpy", "Verified update")

        # @@ STEP 3: Verify the change actually took effect. @@
        config = _read_project_config(ml_lib)
        assert config.base_project == "chainedpy"
        assert config.summary == "Verified update"

    def test_chain_file_verification(self, temp_workspace):
        """Test that chain.py file changes are verified.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If chain file verification doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")
        chain_file = ml_lib / "ml_lib_chain.py"

        # @@ STEP 2: Update project. @@
        update_project_base(ml_lib, "chainedpy", "Verified update")

        # @@ STEP 3: Verify the chain file was actually updated. @@
        assert_file_exists_with_content(
            chain_file,
            ["from chainedpy.chain import Chain"]
        )

    def test_stub_file_verification(self, temp_workspace):
        """Test that stub file changes are verified.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file verification doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        ml_lib = create_test_project(temp_workspace, "ml_lib")
        stub_file = ml_lib / "ml_lib_chain.pyi"

        # @@ STEP 2: Update project. @@
        update_project_base(ml_lib, "chainedpy", "Verified update")

        # @@ STEP 3: Verify the stub file was actually updated. @@
        assert_file_exists_with_content(
            stub_file,
            ["from chainedpy.chain import Chain as _BaseChain", "Verified update"]
        )


class TestComplexScenarios:
    """Test complex update scenarios.

    :raises Exception: If complex scenario testing fails.
    """

    def test_multiple_updates_in_sequence(self, temp_workspace):
        """Test multiple updates to the same project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If multiple sequential updates don't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        base_lib = create_test_project(temp_workspace, "base_lib")
        project_chain = create_project_chain(temp_workspace, ["data_lib", "ml_lib"])
        ml_lib = project_chain['ml_lib']

        # @@ STEP 2: Update 1: ml_lib → chainedpy (Start: ml_lib → data_lib). @@
        update_project_base(ml_lib, "chainedpy", "First update")
        config = _read_project_config(ml_lib)
        assert config.base_project == "chainedpy"

        # @@ STEP 3: Update 2: ml_lib → base_lib. @@
        update_project_base(ml_lib, str(base_lib), "Second update")
        config = _read_project_config(ml_lib)
        assert config.base_project == "./base_lib"

        # @@ STEP 4: Update 3: ml_lib → chainedpy again. @@
        update_project_base(ml_lib, "chainedpy", "Third update")
        config = _read_project_config(ml_lib)
        assert config.base_project == "chainedpy"

    def test_update_affects_dependent_projects(self, temp_workspace):
        """Test that updating a project doesn't break dependent projects.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If dependent project handling doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create chain: A → chainedpy, B → A, C → B. @@
        project_chain = create_project_chain(temp_workspace, ["project_a", "project_b", "project_c"])
        project_a = project_chain['project_a']
        project_b = project_chain['project_b']
        project_c = project_chain['project_c']

        # @@ STEP 2: Update A to extend something else (this should not break B or C). @@
        # Since we don't have another project, update A's summary only
        update_project_base(project_a, "chainedpy", "Updated A")

        # @@ STEP 3: Verify B and C are still valid. @@
        config_b = _read_project_config(project_b)
        config_c = _read_project_config(project_c)

        assert config_b.base_project == "./project_a"
        assert config_c.base_project == "./project_b"
