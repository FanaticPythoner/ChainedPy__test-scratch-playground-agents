"""
CLI tests for ChainedPy project commands.

Tests CLI commands related to project creation, management, and configuration.
"""
import pytest
from unittest.mock import patch

from chainedpy.cli import main
from chainedpy.services.chain_traversal_service import ProjectInfo
from tests.services.mock_test_service import RemoteRepositoryMockService
from tests.utils.assertion_helpers import (
    assert_cli_success, assert_cli_failure, assert_cli_output_contains
)


class TestCreateProjectCommand:
    """Test create-project CLI command."""
    
    def test_create_project_help(self, capsys):
        """Test create-project help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["create-project", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "create-project",
            "--name",
            "--dest",
            "--base-project",
            "--summary",
            "remote URL"
        ]

        for content in expected_content:
            assert content in captured.out
    
    def test_create_project_basic(self, temp_workspace, capsys):
        """Test basic project creation via CLI.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        """
        # @@ STEP 1: Execute create-project command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-project",
                "--name", "test_project",
                "--dest", str(temp_workspace)
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify project was created. @@
        project_path = temp_workspace / "test_project"
        assert project_path.exists()
        assert (project_path / "chainedpy.yaml").exists()

        # @@ STEP 4: Check success message. @@
        assert_cli_output_contains(
            capsys,
            ["Project created", "test_project"]
        )
    
    def test_create_project_with_summary(self, temp_workspace, capsys):
        """Test project creation with custom summary.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Define custom summary. @@
        custom_summary = "Custom test project summary"

        # @@ STEP 2: Execute create-project command with summary. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-project",
                "--name", "custom_project",
                "--dest", str(temp_workspace),
                "--summary", custom_summary
            ])

        # @@ STEP 3: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 4: Verify project configuration contains custom summary. @@
        project_path = temp_workspace / "custom_project"
        config_content = (project_path / "chainedpy.yaml").read_text()
        # || S.S. 4.1: Check that custom summary is in config file. ||
        assert custom_summary in config_content
    
    def test_create_project_with_local_base(self, temp_workspace, capsys):
        """Test project creation with local base project.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Create base project first. @@
        with pytest.raises(SystemExit):
            main([
                "create-project",
                "--name", "base_project",
                "--dest", str(temp_workspace)
            ])

        # || S.S. 1.1: Get base project path. ||
        base_project_path = temp_workspace / "base_project"

        # @@ STEP 2: Create extending project with base project reference. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "create-project",
                "--name", "extending_project",
                "--dest", str(temp_workspace),
                "--base-project", str(base_project_path)
            ])

        # @@ STEP 3: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 4: Verify configuration contains base project reference. @@
        extending_project_path = temp_workspace / "extending_project"
        config_content = (extending_project_path / "chainedpy.yaml").read_text()
        # || S.S. 4.1: Check that relative path to base project is in config. ||
        assert "./base_project" in config_content
    
    def test_create_project_missing_required_args(self, capsys):
        """Test create-project with missing required arguments.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command fails due to missing arguments.
        :return None: None
        """
        # @@ STEP 1: Execute create-project command without required arguments. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["create-project"])

        # @@ STEP 2: Verify argparse returns error code for missing required args. @@
        assert exc_info.value.code == 2  # argparse returns 2 for missing required args

        # @@ STEP 3: Verify error message contains 'required' keyword. @@
        captured = capsys.readouterr()
        # || S.S. 3.1: Check error message in stderr. ||
        assert "required" in captured.err.lower()


class TestUpdateBaseProjectCommand:
    """Test update-base-project CLI command."""
    
    def test_update_base_project_help(self, capsys):
        """Test update-base-project help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI help command completes.
        :return None: None
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["update-base-project", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "update-base-project",
            "--project-path",
            "--new-base-project",
            "remote URL"
        ]

        # || S.S. 3.1: Verify each expected content item is present. ||
        for content in expected_content:
            assert content in captured.out
    
    def test_update_base_project_to_chainedpy(self, simple_project, capsys):
        """Test updating project to extend chainedpy directly.

        :param simple_project: Pytest fixture providing simple project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Execute update-base-project command to chainedpy. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "update-base-project",
                "--project-path", str(simple_project),
                "--new-base-project", "chainedpy"
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify configuration was updated. @@
        config_content = (simple_project / "chainedpy.yaml").read_text()
        # || S.S. 3.1: Check that base project is set to chainedpy. ||
        assert "base_project: chainedpy" in config_content

        # @@ STEP 4: Check success message. @@
        assert_cli_output_contains(
            capsys,
            ["Base project updated"]
        )
    
    def test_update_base_project_invalid_path(self, temp_workspace, capsys):
        """Test update-base-project with invalid project path.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command fails due to invalid path.
        :return None: None
        """
        # @@ STEP 1: Create path to nonexistent project. @@
        nonexistent_path = temp_workspace / "nonexistent"

        # @@ STEP 2: Execute update-base-project command with invalid path. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "update-base-project",
                "--project-path", str(nonexistent_path),
                "--new-base-project", "chainedpy"
            ])

        # @@ STEP 3: Verify command failure. @@
        assert_cli_failure(exc_info)

        # @@ STEP 4: Verify error message. @@
        assert_cli_output_contains(
            capsys,
            ["Project path does not exist"],
            check_stderr=True
        )


class TestShowProjectChainCommand:
    """Test show-project-chain CLI command."""
    
    def test_show_project_chain_help(self, capsys):
        """Test show-project-chain help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI help command completes.
        :return None: None
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["show-project-chain", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "show-project-chain",
            "--project-path"
        ]

        # || S.S. 3.1: Verify each expected content item is present. ||
        for content in expected_content:
            assert content in captured.out
    
    def test_show_project_chain_simple(self, simple_project, capsys):
        """Test showing project chain for simple project.

        :param simple_project: Pytest fixture providing simple project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Execute show-project-chain command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "show-project-chain",
                "--project-path", str(simple_project)
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify output contains expected chain information. @@
        captured = capsys.readouterr()
        # || S.S. 3.1: Check for chain header. ||
        assert "Project Inheritance Chain:" in captured.out
        # || S.S. 3.2: Check for project name. ||
        assert "simple_project" in captured.out
        # || S.S. 3.3: Check for base project. ||
        assert "chainedpy" in captured.out
    
    def test_show_project_chain_hierarchy(self, project_hierarchy, capsys):
        """Test showing project chain for complex hierarchy.

        :param project_hierarchy: Pytest fixture providing project hierarchy.
        :type project_hierarchy: Dict[str, Path]
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Get the ml_lib project from hierarchy. @@
        ml_lib = project_hierarchy['ml_lib']

        # @@ STEP 2: Execute show-project-chain command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "show-project-chain",
                "--project-path", str(ml_lib)
            ])

        # @@ STEP 3: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 4: Verify complete chain is displayed. @@
        captured = capsys.readouterr()
        output = captured.out

        # || S.S. 4.1: Check for all projects in the hierarchy. ||
        assert "ml_lib" in output
        assert "data_lib" in output
        assert "base_lib" in output
        assert "chainedpy" in output


class TestRemoteProjectSupport:
    """Test CLI support for remote projects."""
    
    def test_create_project_with_valid_remote_url(self, temp_workspace, capsys):
        """Test create-project with valid remote repository.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Setup mocks for remote project validation. @@
        with patch('chainedpy.services.project_validation._get_filesystem') as mock_get_fs, \
             patch('chainedpy.services.project_validation._read_remote_config') as mock_read_config, \
             patch('chainedpy.services.remote_chain_service._download_remote_files') as mock_download_files, \
             patch('chainedpy.services.remote_chain_service._extract_dependencies') as mock_extract_deps, \
             patch('chainedpy.services.stub_generation_service.traverse_project_chain') as mock_traverse, \
             patch('chainedpy.project.set_global_project') as mock_set_global:

            # || S.S. 1.1: Mock valid remote project validation. ||
            mock_get_fs.return_value = (RemoteRepositoryMockService.mock_filesystem_for_remote_url(
                "https://github.com/user/valid_repo", "github"
            )[1], "github")
            mock_read_config.return_value = {
                'base_project': 'chainedpy',
                'summary': 'Valid remote ChainedPy project'
            }

            # || S.S. 1.2: Mock successful remote chain download. ||
            mock_download_files.return_value = ['__init__.py', 'chainedpy.yaml', 'valid_repo_chain.py']
            mock_extract_deps.return_value = []  # No dependencies

            # || S.S. 1.3: Mock project traversal. ||
            mock_traverse.return_value = [
                ProjectInfo(
                    name='test_project',
                    path=str(temp_workspace / 'test_project'),
                    base_project='https://github.com/user/valid_repo',
                    summary='Test project',
                    is_remote=False,
                    filesystem_type='local'
                )
            ]

            # @@ STEP 2: Execute create-project command with remote URL. @@
            with pytest.raises(SystemExit) as exc_info:
                main([
                    "create-project",
                    "--name", "test_project",
                    "--dest", str(temp_workspace),
                    "--base-project", "https://github.com/user/valid_repo"
                ])

            # @@ STEP 3: Verify command success. @@
            assert_cli_success(exc_info)

            # @@ STEP 4: Verify success messages. @@
            assert_cli_output_contains(
                capsys,
                ["✅ Validated remote base project", "Project created"]
            )
    
    def test_create_project_with_invalid_remote_url(self, temp_workspace, capsys):
        """Test create-project with invalid remote repository.

        :param temp_workspace: Pytest fixture providing temporary workspace.
        :type temp_workspace: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command fails due to invalid remote URL.
        :return None: None
        """
        # @@ STEP 1: Setup mocks for invalid remote project. @@
        with patch('chainedpy.services.project_validation._get_filesystem') as mock_get_fs, \
             patch('chainedpy.services.project_validation._read_remote_config') as mock_read_config:

            # || S.S. 1.1: Mock invalid remote project. ||
            mock_get_fs.return_value = (RemoteRepositoryMockService.mock_filesystem_for_remote_url(
                "https://github.com/user/invalid_repo", "github"
            )[1], "github")
            mock_read_config.return_value = {}  # Empty config = invalid project

            # @@ STEP 2: Execute create-project command with invalid remote URL. @@
            with pytest.raises(SystemExit) as exc_info:
                main([
                    "create-project",
                    "--name", "test_project",
                    "--dest", str(temp_workspace),
                    "--base-project", "https://github.com/user/invalid_repo"
                ])

            # @@ STEP 3: Verify command failure. @@
            assert_cli_failure(exc_info)

            # @@ STEP 4: Verify error messages. @@
            assert_cli_output_contains(
                capsys,
                ["not a valid ChainedPy project", "missing chainedpy.yaml"],
                check_stderr=True
            )
    
    def test_update_base_project_with_remote_url(self, simple_project, capsys):
        """Test update-base-project with remote repository.

        :param simple_project: Pytest fixture providing simple project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Setup mocks for remote project validation. @@
        with patch('chainedpy.services.project_validation._get_filesystem') as mock_get_fs, \
             patch('chainedpy.services.project_validation._read_remote_config') as mock_read_config, \
             patch('chainedpy.services.stub_generation_service.traverse_project_chain') as mock_traverse:

            # || S.S. 1.1: Mock valid remote project. ||
            mock_get_fs.return_value = (RemoteRepositoryMockService.mock_filesystem_for_remote_url(
                "https://github.com/user/valid_repo", "github"
            )[1], "github")
            mock_read_config.return_value = {
                'base_project': 'chainedpy',
                'summary': 'Valid remote ChainedPy project'
            }

            # || S.S. 1.2: Mock project traversal. ||
            mock_traverse.return_value = [
                ProjectInfo(
                    name='simple_project',
                    path=str(simple_project),
                    base_project='https://github.com/user/valid_repo',
                    summary='Test project',
                    is_remote=False,
                    filesystem_type='local'
                )
            ]

            # @@ STEP 2: Execute update-base-project command with remote URL. @@
            with pytest.raises(SystemExit) as exc_info:
                main([
                    "update-base-project",
                    "--project-path", str(simple_project),
                    "--new-base-project", "https://github.com/user/valid_repo"
                ])

            # @@ STEP 3: Verify command success. @@
            assert_cli_success(exc_info)

            # @@ STEP 4: Verify success messages. @@
            assert_cli_output_contains(
                capsys,
                ["✅ Validated remote base project", "Base project updated"]
            )


class TestProjectPyiCommand:
    """Test update-project-pyi CLI command."""
    
    def test_update_project_pyi_help(self, capsys):
        """Test update-project-pyi help message.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI help command completes.
        :return None: None
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(["update-project-pyi", "--help"])

        # @@ STEP 2: Verify successful exit code. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Check that help message contains expected content. @@
        captured = capsys.readouterr()
        expected_content = [
            "update-project-pyi",
            "--project-path"
        ]

        # || S.S. 3.1: Verify each expected content item is present. ||
        for content in expected_content:
            assert content in captured.out
    
    def test_update_project_pyi_success(self, simple_project, capsys):
        """Test successful stub file update.

        :param simple_project: Pytest fixture providing simple project.
        :type simple_project: Path
        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises SystemExit: When CLI command completes.
        :return None: None
        """
        # @@ STEP 1: Execute update-project-pyi command. @@
        with pytest.raises(SystemExit) as exc_info:
            main([
                "update-project-pyi",
                "--project-path", str(simple_project)
            ])

        # @@ STEP 2: Verify command success. @@
        assert_cli_success(exc_info)

        # @@ STEP 3: Verify stub file was updated. @@
        stub_file = simple_project / f"{simple_project.name}_chain.pyi"
        # || S.S. 3.1: Check that stub file exists. ||
        assert stub_file.exists()

        # @@ STEP 4: Check success message. @@
        assert_cli_output_contains(
            capsys,
            ["Stub regenerated"]
        )
