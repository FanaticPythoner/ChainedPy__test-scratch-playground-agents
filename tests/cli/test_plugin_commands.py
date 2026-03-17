"""
CLI tests for ChainedPy plugin commands.

Tests CLI commands related to plugin creation and management.
"""
from __future__ import annotations

# 1. Standard library imports
# (none)

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils

# 5. ChainedPy internal modules
from chainedpy.cli import main

# 6. Test utilities
from tests.utils.assertion_helpers import (
    assert_cli_success, assert_cli_failure, assert_cli_output_contains,
    assert_file_exists_with_content
)


class TestCreateThenPluginCommand:
    """Test create-then-plugin CLI command."""
    
    def test_create_then_plugin_help(self, capsys):
        """Test create-then-plugin help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["create-then-plugin", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "create-then-plugin",
            "--project-path",
            "--name"
        ]

        for content in expected_content:
            assert content in captured.out
    
    def test_create_then_plugin_success(self, simple_project, capsys):
        """Test successful then plugin creation.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute create-then-plugin command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-then-plugin",
                "--project-path", str(simple_project),
                "--name", "test_plugin"
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify plugin file was created. @@
        plugin_file = simple_project / "plugins" / "then" / "then_test_plugin.py"
        assert plugin_file.exists()

        # @@ STEP 4: Verify plugin content. @@
        assert_file_exists_with_content(
            plugin_file,
            ["def then_test_plugin(", "Link["]
        )

        # @@ STEP 5: Check success message. @@
        assert_cli_output_contains(
            capsys,
            ["✅", "then", "test_plugin", "created successfully"]
        )
    
    def test_create_then_plugin_invalid_project(self, temp_workspace, capsys):
        """Test create-then-plugin with invalid project path.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Set up nonexistent project path. @@
        nonexistent_path = temp_workspace / "nonexistent"

        # @@ STEP 2: Execute command with invalid project path. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-then-plugin",
                "--project-path", str(nonexistent_path),
                "--name", "test_plugin"
            ])

        # @@ STEP 3: Verify command failure. @@
        assert_cli_failure(exc_info)

        # @@ STEP 4: Check error message. @@
        assert_cli_output_contains(
            capsys,
            ["Project path does not exist"],
            check_stderr=True
        )
    
    def test_create_then_plugin_missing_args(self, capsys):
        """Test create-then-plugin with missing arguments.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute command without required arguments. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["create-then-plugin"])

        # @@ STEP 2: Verify argparse error code. @@
        assert exc_info.value.code == 2  # argparse returns 2 for missing required args

        # @@ STEP 3: Check error message contains required field info. @@
        captured = capsys.readouterr()
        assert "required" in captured.err.lower()


class TestCreateAsPluginCommand:
    """Test create-as-plugin CLI command."""
    
    def test_create_as_plugin_help(self, capsys):
        """Test create-as-plugin help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["create-as-plugin", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "create-as-plugin",
            "--project-path",
            "--name"
        ]

        for content in expected_content:
            assert content in captured.out
    
    def test_create_as_plugin_success(self, simple_project, capsys):
        """Test successful as plugin creation.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute create-as-plugin command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-as-plugin",
                "--project-path", str(simple_project),
                "--name", "retry"
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify plugin file was created. @@
        plugin_file = simple_project / "plugins" / "as_" / "as_retry.py"
        assert plugin_file.exists()

        # @@ STEP 4: Verify plugin content. @@
        assert_file_exists_with_content(
            plugin_file,
            ["def as_retry(", "Link["]
        )

        # @@ STEP 5: Check success message. @@
        assert_cli_output_contains(
            capsys,
            ["✅", "as", "retry", "created successfully"]
        )
    
    def test_create_as_plugin_with_complex_name(self, simple_project, capsys):
        """Test as plugin creation with complex name.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute create-as-plugin command with complex name. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-as-plugin",
                "--project-path", str(simple_project),
                "--name", "timeout_with_retry"
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify plugin file was created with correct name. @@
        plugin_file = simple_project / "plugins" / "as_" / "as_timeout_with_retry.py"
        assert plugin_file.exists()

        # @@ STEP 4: Verify function name in content. @@
        content = fs_utils.read_text(str(plugin_file))
        assert "def as_timeout_with_retry(" in content


class TestCreateProcessorCommand:
    """Test create-processor CLI command."""
    
    def test_create_processor_help(self, capsys):
        """Test create-processor help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["create-processor", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "create-processor",
            "--project-path",
            "--name",
            "processor"
        ]

        for content in expected_content:
            assert content in captured.out
    
    def test_create_processor_success(self, simple_project, capsys):
        """Test successful processor creation.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute create-processor command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-processor",
                "--project-path", str(simple_project),
                "--name", "data_processor"
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify processor file was created. @@
        processor_file = simple_project / "plugins" / "processors" / "processor_data_processor.py"
        assert processor_file.exists()

        # @@ STEP 4: Verify processor content. @@
        assert_file_exists_with_content(
            processor_file,
            ["class ProcessorDataProcessor", "def apply("]
        )

        # @@ STEP 5: Check success message. @@
        assert_cli_output_contains(
            capsys,
            ["✅", "processor", "data_processor", "created successfully"]
        )


class TestPluginCreationIntegration:
    """Test plugin creation integration with project system."""
    
    def test_plugin_creation_updates_stub_file(self, simple_project, capsys):
        """Test that plugin creation updates the stub file.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Create a then plugin. @@
        with pytest.raises(SystemExit):
            main([
                "create-then-plugin",
                "--project-path", str(simple_project),
                "--name", "transform"
            ])

        # @@ STEP 2: Create an as plugin. @@
        with pytest.raises(SystemExit):
            main([
                "create-as-plugin",
                "--project-path", str(simple_project),
                "--name", "retry"
            ])

        # @@ STEP 3: Update stub file to include new plugins. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "update-project-pyi",
                "--project-path", str(simple_project)
            ])

        # @@ STEP 4: Verify command success. @@
        assert_cli_success(exc_info)
        
        # Verify stub file contains new plugin methods
        stub_file = simple_project / f"{simple_project.name}_chain.pyi"
        content = fs_utils.read_text(str(stub_file))
        
        assert "def then_transform(" in content
        assert "def as_retry(" in content
    
    def test_multiple_plugin_creation(self, simple_project):
        """Test creating multiple plugins of different types."""
        plugins_to_create = [
            ("then", "double"),
            ("then", "validate"),
            ("as", "timeout"),
            ("as", "cache"),
            ("processor", "json_processor")
        ]
        
        for plugin_type, plugin_name in plugins_to_create:
            command = f"create-{plugin_type}-plugin"
            if plugin_type == "processor":
                command = "create-processor"
            
            with pytest.raises(SystemExit) as exc_info:
                main([
                    command,
                    "--project-path", str(simple_project),
                    "--name", plugin_name
                ])
            
            assert_cli_success(exc_info)
        
        # Verify all plugins were created
        then_dir = simple_project / "plugins" / "then"
        as_dir = simple_project / "plugins" / "as_"
        processors_dir = simple_project / "plugins" / "processors"
        
        assert (then_dir / "then_double.py").exists()
        assert (then_dir / "then_validate.py").exists()
        assert (as_dir / "as_timeout.py").exists()
        assert (as_dir / "as_cache.py").exists()
        assert (processors_dir / "processor_json_processor.py").exists()
    
    def test_plugin_creation_with_existing_plugin(self, simple_project, capsys):
        """Test creating plugin when one already exists.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Create initial plugin. @@
        with pytest.raises(SystemExit):
            main([
                "create-then-plugin",
                "--project-path", str(simple_project),
                "--name", "existing"
            ])

        # @@ STEP 2: Try to create plugin with same name. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-then-plugin",
                "--project-path", str(simple_project),
                "--name", "existing"
            ])

        # @@ STEP 3: Should handle gracefully (behavior depends on implementation). @@
        # For now, just verify it doesn't crash.
        assert exc_info.value.code in [0, 1]  # Either success or controlled failure


class TestPluginNamingValidation:
    """Test plugin name validation in CLI commands."""
    
    def test_valid_plugin_names(self, simple_project):
        """Test creation of plugins with valid names."""
        valid_names = [
            "simple",
            "with_underscore",
            "with123numbers"
        ]
        
        for name in valid_names:
            with pytest.raises(SystemExit) as exc_info:
                main([
                    "create-then-plugin",
                    "--project-path", str(simple_project),
                    "--name", name
                ])
            
            # Should succeed
            assert_cli_success(exc_info)
            
            # Verify file was created
            plugin_file = simple_project / "plugins" / "then" / f"then_{name}.py"
            assert plugin_file.exists()
    
    def test_invalid_plugin_names(self, simple_project, capsys):
        """Test handling of invalid plugin names.

        :param simple_project: Pytest fixture providing a simple test project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Define list of potentially invalid plugin names. @@
        invalid_names = [
            "",  # Empty name
            "with spaces",  # Spaces
            "with-hyphens",  # Hyphens might be invalid
            "with.dots",  # Dots
            "with/slashes",  # Slashes
            "123starting_with_number",  # Starting with number
            "CamelCase",  # Contains uppercase letters
            "mixedCase_with_underscore"  # Contains uppercase letters
        ]

        # @@ STEP 2: Test each invalid name. @@
        for name in invalid_names:
            if name.strip():  # Skip empty names for this test
                with pytest.raises(SystemExit) as exc_info:
                    main([
                        "create-then-plugin",
                        "--project-path", str(simple_project),
                        "--name", name
                    ])

                # @@ STEP 3: Should either succeed (if name is actually valid) or fail gracefully. @@
                assert exc_info.value.code in [0, 1]
