"""
Test ChainedPy stub file (.pyi) generation functionality.

This module tests the generation of .pyi stub files with correct imports,
docstrings, plugin signatures, and inheritance from base projects.
"""
from __future__ import annotations

# 1. Standard library imports
import ast

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.stub_generation_service import (
    update_project_stub,
    generate_stub_content
)

# 5. ChainedPy internal modules
from chainedpy.project import (
    create_then_plugin,
    update_project_base
)

# 6. Test utilities
from tests.services.project_test_service import create_test_project, create_project_with_plugins
from tests.utils.assertion_helpers import assert_file_exists_with_content


class TestBasicStubGeneration:
    """Test basic stub file generation functionality.

    :raises Exception: If basic stub generation testing fails.
    """

    def test_stub_file_created(self, temp_workspace):
        """Test that stub file is created during project creation.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file creation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Verify stub file exists. @@
        stub_file = project / "test_project_chain.pyi"
        assert stub_file.exists()
        assert stub_file.is_file()

    def test_stub_file_basic_structure(self, temp_workspace):
        """Test basic structure of generated stub file.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file structure is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            [
                "from __future__ import annotations",
                "from typing import Any, Awaitable, Callable, TypeVar",
                "from chainedpy.chain import Chain as _BaseChain",
                "class Chain(_BaseChain[_T])",
                "from chainedpy.chain import _T  # _T",
                "from chainedpy.chain import _O  # _O"
            ]
        )
    
    def test_stub_file_header_comment(self, temp_workspace):
        """Test that stub file contains proper header comment.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file header comment is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Verify stub file contains proper header comment. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            [
                "Typed stub file (auto-generated) DO NOT EDIT BY HAND",
                "chainedpy update-project-pyi"
            ]
        )


class TestStubImports:
    """Test import generation in stub files.

    :raises Exception: If stub import testing fails.
    """

    def test_chainedpy_base_import(self, temp_workspace):
        """Test import when extending chainedpy.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If chainedpy base import is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Verify chainedpy base import. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["from chainedpy.chain import Chain as _BaseChain"]
        )

    def test_custom_project_base_import(self, temp_workspace):
        """Test import when extending custom project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If custom project base import is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create base and extending projects. @@
        base_project = create_test_project(temp_workspace, "base_project")
        extending_project = create_test_project(
            temp_workspace,
            "extending_project",
            base_project=str(base_project)
        )

        # @@ STEP 2: Verify custom project import. @@
        stub_file = extending_project / "extending_project_chain.pyi"
        content = stub_file.read_text(encoding='utf-8')

        assert "from base_project.base_project_chain import Chain as _BaseChain" in content
        assert "from chainedpy.chain import Chain as _BaseChain" not in content

    def test_import_after_base_project_update(self, temp_workspace):
        """Test that import is updated when base project changes.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If import update after base project change is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create base and test projects. @@
        base_project = create_test_project(temp_workspace, "base_project")
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Update to extend base_project. @@
        update_project_base(project, str(base_project), "Now extends base_project")

        # @@ STEP 3: Verify import was updated. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["from base_project.base_project_chain import Chain as _BaseChain"]
        )


class TestStubDocstrings:
    """Test docstring generation in stub files.

    :raises Exception: If stub docstring testing fails.
    """

    def test_default_summary_in_docstring(self, temp_workspace):
        """Test that default summary appears in docstring.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If default summary in docstring is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Verify default summary appears in docstring. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["Test project: test_project"]
        )

    def test_custom_summary_in_docstring(self, temp_workspace):
        """Test that custom summary appears in docstring.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If custom summary in docstring is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create test project with custom summary. @@
        custom_summary = "Advanced data processing pipeline"
        project = create_test_project(temp_workspace, "test_project", summary=custom_summary)

        # @@ STEP 2: Verify custom summary appears in docstring. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            [custom_summary]
        )

    def test_plugin_count_in_docstring(self, temp_workspace):
        """Test that plugin count is correctly shown in docstring.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If plugin count in docstring is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process", "validate"],
                                             as_plugins=["cached", "retried"])

        # @@ STEP 2: Verify plugin count is shown in docstring. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["4 additional plugin(s)"]  # 2 then_ + 2 as_ plugins
        )

    def test_plugin_listing_in_docstring(self, temp_workspace):
        """Test that plugins are listed in docstring.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If plugin listing in docstring is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process", "validate"],
                                             as_plugins=["cached", "retried"])

        # @@ STEP 2: Verify plugins are listed in docstring. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            [
                "Available then_* plugins (2):",
                "- .then_process(...)",
                "- .then_validate(...)",
                "Available as_* plugins (2):",
                "- .as_cached(...)",
                "- .as_retried(...)"
            ]
        )


class TestPluginSignatures:
    """Test plugin method signature generation.

    :raises Exception: If plugin signature testing fails.
    """

    def test_then_plugin_signatures(self, temp_workspace):
        """Test that then_ plugin signatures are generated.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If then plugin signatures are incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with then plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process", "validate"])

        # @@ STEP 2: Verify then plugin signatures are generated. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["def then_process(", "def then_validate("]
        )

    def test_as_plugin_signatures(self, temp_workspace):
        """Test that as_ plugin signatures are generated.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If as plugin signatures are incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with as plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             as_plugins=["cached", "retried"])

        # @@ STEP 2: Verify as plugin signatures are generated. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            ["def as_cached(", "def as_retried("]
        )

    def test_plugin_signature_format(self, temp_workspace):
        """Test the format of plugin signatures.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If plugin signature format is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process"])

        # @@ STEP 2: Check that signatures have proper format. @@
        stub_file = project / "test_project_chain.pyi"
        content = stub_file.read_text(encoding='utf-8')

        lines = content.split('\n')
        method_lines = [line for line in lines if line.strip().startswith('def ')]

        # @@ STEP 3: Verify signature format. @@
        for line in method_lines:
            # Should be properly indented
            assert line.startswith('    def ')
            # Should end with ellipsis
            assert line.strip().endswith(': ...')

    def test_empty_project_no_plugin_signatures(self, temp_workspace):
        """Test that projects without plugins include base chainedpy methods but no current project methods.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If empty project plugin handling is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create empty project. @@
        project = create_test_project(temp_workspace, "empty_project")

        # @@ STEP 2: Verify no plugin methods from this project. @@
        stub_file = project / "empty_project_chain.pyi"
        content = stub_file.read_text(encoding='utf-8')

        lines = content.split('\n')
        method_lines = [line for line in lines if line.strip().startswith('def ')]

        # @@ STEP 3: Should have base chainedpy methods (then_* and as_*). @@
        assert len(method_lines) > 0

        # Should not contain any current project plugin information in docstring
        assert "additional plugin(s) from this project:" not in content


class TestStubRegeneration:
    """Test stub file regeneration functionality.

    :raises Exception: If stub regeneration testing fails.
    """

    def test_manual_stub_regeneration(self, temp_workspace):
        """Test manual regeneration of stub files.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If manual stub regeneration doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process"])

        stub_file = project / "test_project_chain.pyi"

        # @@ STEP 2: Modify stub file. @@
        stub_file.write_text("# Modified content")

        # @@ STEP 3: Regenerate. @@
        update_project_stub(project)

        # @@ STEP 4: Verify it was regenerated correctly. @@
        content = stub_file.read_text(encoding='utf-8')
        assert "# Modified content" not in content
        assert "class Chain(_BaseChain[_T])" in content

    def test_stub_regeneration_after_plugin_addition(self, temp_workspace):
        """Test that stub is updated when plugins are added.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub regeneration after plugin addition doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project without plugins. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Verify initial state (no plugins). @@
        stub_file = project / "test_project_chain.pyi"
        initial_content = fs_utils.read_text(str(stub_file))
        # Instead, verify it contains base chainedpy methods but no current project methods
        assert "from chainedpy.chain import Chain as _BaseChain" in initial_content
        assert "def then_" in initial_content  # Should have base chainedpy methods
        assert "additional plugin(s) from this project:" not in initial_content  # No current plugins section

        # @@ STEP 3: Add a plugin. @@
        create_then_plugin(project, "new_plugin")

        # @@ STEP 4: Verify stub was updated. @@
        updated_content = fs_utils.read_text(str(stub_file))
        assert "1 additional plugin(s) from this project:" in updated_content
        assert "def then_new_plugin(" in updated_content

    def test_stub_regeneration_preserves_structure(self, temp_workspace):
        """Test that regeneration preserves proper stub structure.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub regeneration structure preservation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process"],
                                             as_plugins=["cached"])

        # @@ STEP 2: Update project stub. @@
        update_project_stub(project)

        # @@ STEP 3: Verify structure is preserved. @@
        stub_file = project / "test_project_chain.pyi"
        assert_file_exists_with_content(
            stub_file,
            [
                "from __future__ import annotations",
                "class Chain(_BaseChain[_T])",
                "from chainedpy.chain import _T",  # TypeVars are imported, not declared locally
                "def then_process(",
                "def as_cached("
            ]
        )


class TestStubContentGeneration:
    """Test the generate_stub_content function specifically.

    :raises Exception: If stub content generation testing fails.
    """

    def test_stub_content_generation_chainedpy_base(self, temp_workspace):
        """Test stub content generation for chainedpy base.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub content generation for chainedpy base is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Generate stub content. @@
        content = generate_stub_content(project)

        # @@ STEP 3: Verify content. @@
        assert "from chainedpy.chain import Chain as _BaseChain" in content
        assert "Test project: test_project" in content

    def test_stub_content_generation_custom_base(self, temp_workspace):
        """Test stub content generation for custom base project.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub content generation for custom base is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create base and extending projects. @@
        base_project = create_test_project(temp_workspace, "base_project")
        extending_project = create_test_project(
            temp_workspace,
            "extending_project",
            base_project=str(base_project),
            summary="Custom summary"
        )

        # @@ STEP 2: Generate stub content. @@
        content = generate_stub_content(extending_project)

        # @@ STEP 3: Verify content. @@
        assert "from base_project.base_project_chain import Chain as _BaseChain" in content
        assert "Custom summary" in content

    def test_stub_content_generation_with_plugins(self, temp_workspace):
        """Test stub content generation with plugin information.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub content generation with plugins is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process", "validate"],
                                             as_plugins=["cached", "retried"])

        # @@ STEP 2: Generate stub content. @@
        content = generate_stub_content(project)

        # @@ STEP 3: Verify plugin information in content. @@
        assert "4 additional plugin(s) from this project:" in content
        assert "Available then_* plugins (2):" in content
        assert "Available as_* plugins (2):" in content
        assert "- .then_process(...)" in content
        assert "- .as_cached(...)" in content


class TestStubValidation:
    """Test validation of generated stub files.

    :raises Exception: If stub validation testing fails.
    """

    def test_stub_file_is_valid_python(self, temp_workspace):
        """Test that generated stub files are valid Python syntax.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file Python syntax validation fails.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process"],
                                             as_plugins=["cached"])

        # @@ STEP 2: Read stub file content. @@
        stub_file = project / "test_project_chain.pyi"
        content = fs_utils.read_text(str(stub_file))

        # @@ STEP 3: Verify it's parseable as Python. @@
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Generated stub file has invalid Python syntax: {e}")

    def test_stub_file_content_verification(self, temp_workspace):
        """Test that stub file content verification works.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file content verification doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Update project stub (should not raise any exceptions). @@
        result = update_project_stub(project, silent=True)

        # @@ STEP 3: Verify result. @@
        assert result == project / "test_project_chain.pyi"

    def test_stub_file_encoding(self, temp_workspace):
        """Test that stub files are properly encoded.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub file encoding is incorrect.
        :return None: None
        """
        # @@ STEP 1: Create project with plugins. @@
        project = create_project_with_plugins(temp_workspace, "test_project",
                                             then_plugins=["process"])

        # @@ STEP 2: Verify stub file is readable as UTF-8. @@
        stub_file = project / "test_project_chain.pyi"

        try:
            content = stub_file.read_text(encoding='utf-8')
            assert len(content) > 0
        except UnicodeDecodeError as e:
            pytest.fail(f"Stub file has encoding issues: {e}")
