"""
Integration tests for ChainedPy error handling.

Tests error handling with real file system operations and actual error scenarios.
"""
from __future__ import annotations

# 1. Standard library imports
from unittest.mock import patch

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
from chainedpy.services.stub_generation_service import StubGenerationError

# 5. ChainedPy internal modules
from chainedpy.project import (
    update_project_base, _validate_base_project, update_project_stub
)
from chainedpy.services.logging_service import get_logger
# 6. Test utilities
from tests.services.project_test_service import create_test_project, read_project_config
from tests.services.filesystem_test_service import (
    create_corrupted_config_file, readonly_file_context
)
from tests.utils.assertion_helpers import (
    assert_exception_with_message, assert_logs_contain_messages
)


class TestCircularDependencyDetection:
    """Test circular dependency detection with real projects.

    :raises Exception: If circular dependency detection fails during testing.
    """

    def test_direct_circular_dependency(self, temp_workspace):
        """Test detection of direct circular dependency.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If direct circular dependency is not detected.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project_a = create_test_project(temp_workspace, "project_a")

        # @@ STEP 2: Try to make project_a extend itself. @@
        assert_exception_with_message(
            ValueError, "Circular dependency",
            _validate_base_project, str(project_a), project_a
        )

    def test_indirect_circular_dependency(self, temp_workspace):
        """Test detection of indirect circular dependency.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If indirect circular dependency is not detected.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        project_a = create_test_project(temp_workspace, "project_a")
        project_b = create_test_project(
            temp_workspace, "project_b", 
            base_project=str(project_a)
        )
        
        # Try to make project_a extend project_b (creating A -> B -> A cycle)
        assert_exception_with_message(
            ValueError, "Circular dependency",
            update_project_base, project_a, str(project_b), "Should fail"
        )
    
    def test_complex_circular_dependency(self, temp_workspace):
        """Test detection of complex circular dependency chain.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If complex circular dependency is not detected.
        :return None: None
        """
        # @@ STEP 1: Create chain: A -> B -> C. @@
        project_a = create_test_project(temp_workspace, "project_a")
        project_b = create_test_project(
            temp_workspace, "project_b",
            base_project=str(project_a)
        )
        project_c = create_test_project(
            temp_workspace, "project_c",
            base_project=str(project_b)
        )

        # @@ STEP 2: Try to make project_a extend project_c (creating A -> B -> C -> A cycle). @@
        assert_exception_with_message(
            ValueError, "Circular dependency",
            update_project_base, project_a, str(project_c), "Should fail"
        )


class TestFilePermissionErrors:
    """Test handling of file permission errors.

    :raises Exception: If file permission error handling fails during testing.
    """

    def test_readonly_config_file_error(self, simple_project, caplog_debug):
        """Test error handling when config file is read-only.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :param caplog_debug: Debug logging fixture.
        :type caplog_debug: Any
        :raises AssertionError: If readonly config file error is not handled correctly.
        :return None: None
        """
        # @@ STEP 1: Get config file path. @@
        config_file = simple_project / "chainedpy.yaml"

        # @@ STEP 2: Test with readonly config file. @@
        with readonly_file_context(config_file):
            with pytest.raises(RuntimeError, match="Failed to update configuration file"):
                update_project_base(simple_project, "chainedpy", "Should fail")

        # @@ STEP 3: Should log the error. @@
        assert_logs_contain_messages(
            caplog_debug,
            ["Failed to update configuration file"],
            log_level="ERROR"
        )

    def test_readonly_stub_file_error(self, simple_project, caplog_debug):
        """Test error handling when stub file is read-only.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :param caplog_debug: Debug logging fixture.
        :type caplog_debug: Any
        :raises AssertionError: If readonly stub file error is not handled correctly.
        :return None: None
        """
        # @@ STEP 1: Get stub file path. @@
        stub_file = simple_project / f"{simple_project.name}_chain.pyi"

        # @@ STEP 2: Test with readonly stub file. @@
        with readonly_file_context(stub_file):
            with pytest.raises(StubGenerationError, match="Failed to write stub file"):
                update_project_stub(simple_project)

        # @@ STEP 3: Should log the error. @@
        assert_logs_contain_messages(
            caplog_debug,
            ["Failed to write stub file"],
            log_level="ERROR"
        )


class TestCorruptedConfigHandling:
    """Test handling of corrupted configuration files.

    :raises Exception: If corrupted config file handling fails during testing.
    """

    def test_corrupted_config_fallback(self, temp_workspace, caplog_debug):
        """Test fallback behavior with corrupted config file.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :param caplog_debug: Debug logging fixture.
        :type caplog_debug: Any
        :raises AssertionError: If corrupted config fallback doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project directory. @@
        project_dir = temp_workspace / "corrupted_project"
        project_dir.mkdir()

        # @@ STEP 2: Create basic project structure. @@
        (project_dir / "__init__.py").touch()

        # @@ STEP 3: Create corrupted config file. @@
        create_corrupted_config_file(project_dir)

        # @@ STEP 4: Reading config should fall back to defaults and log error. @@
        config = read_project_config(project_dir)

        # @@ STEP 5: Verify fallback values. @@
        assert config.base_project == "chainedpy"
        assert config.summary == "ChainedPy project: corrupted_project"

        # @@ STEP 6: Should log the error. @@
        assert_logs_contain_messages(
            caplog_debug,
            ["Failed to read config from"],
            log_level="ERROR"
        )

    def test_missing_config_file_fallback(self, temp_workspace):
        """Test fallback behavior when config file is missing.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If missing config fallback doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create project directory without config. @@
        project_dir = temp_workspace / "no_config_project"
        project_dir.mkdir()

        # @@ STEP 2: Reading config should return defaults. @@
        config = read_project_config(project_dir)

        # @@ STEP 3: Verify default values. @@
        assert config.base_project == "chainedpy"
        assert config.summary == "ChainedPy project: no_config_project"


class TestInvalidProjectPaths:
    """Test handling of invalid project paths.

    :raises Exception: If invalid project path handling fails during testing.
    """

    def test_nonexistent_project_path(self, temp_workspace):
        """Test error handling for nonexistent project paths.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If nonexistent project path error is not handled correctly.
        :return None: None
        """
        # @@ STEP 1: Create paths for nonexistent and existing projects. @@
        nonexistent = temp_workspace / "nonexistent"
        existing_project = create_test_project(temp_workspace, "existing_project")

        # @@ STEP 2: Verify error is raised for nonexistent base project. @@
        assert_exception_with_message(
            ValueError, "Invalid base project",
            update_project_base, existing_project, str(nonexistent), "Should fail"
        )

    def test_invalid_base_project_path(self, temp_workspace):
        """Test error handling for invalid base project paths.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If invalid base project path error is not handled correctly.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Define invalid paths. @@
        invalid_paths = [
            "",  # Empty string
            "   ",  # Whitespace only
            "/nonexistent/path",  # Nonexistent absolute path
            "./nonexistent/relative"  # Nonexistent relative path
        ]

        # @@ STEP 3: Test each invalid path. @@
        for invalid_path in invalid_paths:
            if invalid_path.strip():  # Non-empty paths
                assert_exception_with_message(
                    ValueError, "Invalid base project",
                    update_project_base, project, invalid_path, "Should fail"
                )


class TestBrokenPluginHandling:
    """Test handling of broken plugin files.

    :raises Exception: If broken plugin handling fails during testing.
    """

    def test_broken_plugin_signature_extraction(self, project_with_broken_plugins, caplog_debug):
        """Test that broken plugins cause system to fail instead of generating fallbacks.

        :param project_with_broken_plugins: Project with broken plugins fixture.
        :type project_with_broken_plugins: Path
        :param caplog_debug: Debug logging fixture.
        :type caplog_debug: Any
        :raises AssertionError: If broken plugin handling doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Update stub file - should fail when encountering broken plugins. @@
        with pytest.raises(StubGenerationError, match="Failed to parse plugin file.*invalid syntax"):
            update_project_stub(project_with_broken_plugins)

        # @@ STEP 2: Should log the errors before failing. @@
        assert_logs_contain_messages(
            caplog_debug,
            ["Failed to discover methods", "Failed to parse plugin file"],
            log_level="ERROR"
        )


class TestLoggingSystem:
    """Test the unified logging system.

    :raises Exception: If logging system testing fails.
    """

    def test_logger_creation(self):
        """Test that logger is created correctly.

        :raises AssertionError: If logger creation doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Get logger instance. @@
        logger = get_logger()

        # @@ STEP 2: Verify logger properties. @@
        assert logger.name == "chainedpy"
        assert len(logger.handlers) >= 1  # At least console handler

    def test_logger_singleton_behavior(self):
        """Test that multiple calls return the same logger instance.

        :raises AssertionError: If logger singleton behavior doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Get two logger instances. @@
        logger1 = get_logger()
        logger2 = get_logger()

        # @@ STEP 2: Verify they are the same instance. @@
        assert logger1 is logger2

    def test_no_silent_failures(self, temp_workspace, caplog_debug):
        """Test that there are no silent failures in the system.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :param caplog_debug: Debug logging fixture.
        :type caplog_debug: Any
        :raises AssertionError: If silent failures are detected.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create a scenario that might cause exceptions. @@
        config_file = project / "chainedpy.yaml"
        config_file.write_text("key: value\n  invalid: indentation")

        # @@ STEP 3: Read config - should log error but not crash. @@
        config = read_project_config(project)

        # @@ STEP 4: Should have logged the error. @@
        error_records = [r for r in caplog_debug.records if r.levelname == "ERROR"]
        assert len(error_records) > 0, "Expected error to be logged"
        
        # Should still return valid config (fallback)
        assert config.base_project == "chainedpy"


class TestFailFastBehavior:
    """Test that the system fails fast with clear errors.

    :raises Exception: If fail-fast behavior testing fails.
    """

    def test_validation_errors_not_swallowed(self, temp_workspace):
        """Test that validation errors are properly raised.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If validation errors are swallowed.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project_a = create_test_project(temp_workspace, "project_a")

        # @@ STEP 2: Self-extension should raise clear error immediately. @@
        with pytest.raises(ValueError, match="Circular dependency"):
            _validate_base_project(str(project_a), project_a)

    def test_file_operation_errors_not_swallowed(self, simple_project):
        """Test that file operation errors are properly raised.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If file operation errors are swallowed.
        :return None: None
        """
        # @@ STEP 1: Mock file write operation to fail. @@
        with patch('chainedpy.project._write_project_config') as mock_write:
            mock_write.side_effect = PermissionError("Permission denied")

            # @@ STEP 2: Should raise clear error, not fail silently. @@
            with pytest.raises(RuntimeError, match="Failed to update configuration file"):
                update_project_base(simple_project, "chainedpy", "Should fail")


class TestErrorMessages:
    """Test that error messages are clear and helpful.

    :raises Exception: If error message testing fails.
    """

    def test_circular_dependency_error_message(self, temp_workspace):
        """Test that circular dependency errors have clear messages.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If error messages are not clear.
        :return None: None
        """
        # @@ STEP 1: Create test projects. @@
        project_a = create_test_project(temp_workspace, "project_a")
        project_b = create_test_project(
            temp_workspace, "project_b",
            base_project=str(project_a)
        )

        # @@ STEP 2: Attempt circular dependency and capture error. @@
        with pytest.raises(ValueError) as exc_info:
            update_project_base(project_a, str(project_b), "Should fail")

        # @@ STEP 3: Verify error message content. @@
        error_msg = str(exc_info.value)
        assert "Circular dependency" in error_msg
        assert "project_a" in error_msg
        assert "cannot extend itself" in error_msg

    def test_file_permission_error_message(self, simple_project):
        """Test that file permission errors have clear messages.

        :param simple_project: Simple project fixture.
        :type simple_project: Path
        :raises AssertionError: If error messages are not clear.
        :return None: None
        """
        # @@ STEP 1: Get config file path. @@
        config_file = simple_project / "chainedpy.yaml"

        # @@ STEP 2: Test with readonly file and capture error. @@
        with readonly_file_context(config_file):
            with pytest.raises(RuntimeError) as exc_info:
                update_project_base(simple_project, "chainedpy", "Should fail")

            # @@ STEP 3: Verify error message content. @@
            error_msg = str(exc_info.value)
            assert "Failed to update configuration file" in error_msg
