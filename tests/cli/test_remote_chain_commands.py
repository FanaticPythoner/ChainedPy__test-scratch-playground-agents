"""
Tests for project-local remote chain CLI commands.

Tests all remote chain management CLI commands including:
- list-remote-chains
- update-remote-chains
- check-remote-updates
- remote-chain-status
"""
from __future__ import annotations

# 1. Standard library imports
import json
import shutil
import tempfile
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# 2. Third-party imports

# 3. Internal constants
from chainedpy.constants import REMOTE_CHAIN_META_FILE_NAME

# 4. ChainedPy services
from chainedpy.services.command_handlers import (
    handle_list_remote_chains, handle_update_remote_chains,
    handle_check_remote_updates, handle_remote_chain_status
)

# 5. ChainedPy internal modules
# (none)

# 6. Test utilities
from tests.utils.test_helpers import integration_test


class BaseRemoteChainTestCase:
    """Base test case for remote chain CLI commands with real project setup.

    :raises OSError: If temporary directory creation fails.
    """

    def setup_method(self):
        """Set up test environment with temporary project directory.

        :raises OSError: If directory creation or file writing fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary directory structure. @@
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 2: Create a basic ChainedPy project. @@
        config_content = """
project:
  base_project: https://example.com/base_chain
  summary: Test project with remote base
"""
        # || S.S. 2.1: Write project configuration file. ||
        (self.project_dir / "chainedpy.yaml").write_text(config_content)
        # || S.S. 2.2: Write project initialization file. ||
        (self.project_dir / "__init__.py").write_text("# Test project")

    def teardown_method(self):
        """Clean up test environment.

        :return None: None
        """
        # @@ STEP 1: Remove temporary directory if it exists. @@
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_mock_remote_chain(self, name: str, url: str):
        """Create a mock remote chain directory in the project.

        :param name: Name of the remote chain.
        :type name: str
        :param url: URL of the remote chain.
        :type url: str
        :raises OSError: If directory creation or file writing fails.
        :return Path: Path to created chain directory.
        """
        # @@ STEP 1: Create chain directory. @@
        chain_dir = self.project_dir / name
        chain_dir.mkdir(exist_ok=True)

        # @@ STEP 2: Create chain files. @@
        (chain_dir / "__init__.py").write_text("# Remote chain")
        (chain_dir / f"{name}_chain.py").write_text(f"# {name} chain implementation")

        # @@ STEP 3: Create metadata. @@
        metadata = {
            "url": url,
            "downloaded_at": datetime.now().isoformat(),
            "dependencies": [],
            "files": ["__init__.py", f"{name}_chain.py"],
            "ttl_hours": 24,
            "local_path": str(chain_dir),
            "size_mb": 1.0
        }

        # @@ STEP 4: Write metadata file. @@
        metadata_file = chain_dir / REMOTE_CHAIN_META_FILE_NAME
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # @@ STEP 5: Return chain directory path. @@
        return chain_dir


class TestListRemoteChainsCommand(BaseRemoteChainTestCase):
    """Test list-remote-chains CLI command."""

    def test_list_remote_chains_no_remote_base(self, capsys):
        """Test list-remote-chains when project has no remote base.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If expected message not found in output.
        :return None: None
        """
        # @@ STEP 1: Update config to have local base project. @@
        config_content = """
project:
  base_project: chainedpy
  summary: Test project with local base
"""
        (self.project_dir / "chainedpy.yaml").write_text(config_content)

        # @@ STEP 2: Execute command and verify output. @@
        args = Namespace(project_path=self.project_dir, verbose=False)
        handle_list_remote_chains(args)

        # @@ STEP 3: Verify no remote dependencies message. @@
        captured = capsys.readouterr()
        # || S.S. 3.1: Check for expected no dependencies message. ||
        assert "Project does not have remote dependencies" in captured.out

    def test_list_remote_chains_empty(self, capsys):
        """Test list-remote-chains when no remote chains are downloaded.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If expected empty message not found in output.
        :return None: None
        """
        # @@ STEP 1: Mock empty remote chains list. @@
        with patch('chainedpy.services.project_remote_chain_service.list_project_remote_chains') as mock_list:
            mock_list.return_value = []

            # @@ STEP 2: Execute list remote chains command. @@
            args = Namespace(project_path=self.project_dir, verbose=False)
            handle_list_remote_chains(args)

            # @@ STEP 3: Verify empty chains message. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for expected empty chains message. ||
            assert "No remote chains found in project" in captured.out

    def test_list_remote_chains_with_chains(self, capsys):
        """Test list-remote-chains with downloaded chains.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If expected chain information not found in output.
        :return None: None
        """
        # @@ STEP 1: Set up mock remote chains data. @@
        mock_chains = [
            {
                'name': 'base_chain',
                'url': 'https://example.com/base_chain',
                'local_path': str(self.project_dir / 'base_chain'),
                'last_updated': '2023-01-01 12:00:00',
                'size_mb': 2.5
            },
            {
                'name': 'dependency_chain',
                'url': 'https://example.com/dependency_chain',
                'local_path': str(self.project_dir / 'dependency_chain'),
                'last_updated': '2023-01-01 11:00:00',
                'size_mb': 1.8
            }
        ]

        # @@ STEP 2: Mock remote chains service and execute command. @@
        with patch('chainedpy.services.command_handlers.list_project_remote_chains') as mock_list:
            mock_list.return_value = mock_chains

            # || S.S. 2.1: Execute list command with mock data. ||
            args = Namespace(project_path=self.project_dir, verbose=False)
            handle_list_remote_chains(args)

            # @@ STEP 3: Verify chains are listed in output. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for project header. ||
            assert "Remote chains in project: test_project" in captured.out
            # || S.S. 3.2: Check for first chain. ||
            assert "1. base_chain" in captured.out
            # || S.S. 3.3: Check for second chain. ||
            assert "2. dependency_chain" in captured.out
            # || S.S. 3.4: Check for verbose instruction. ||
            assert "Use --verbose for detailed information" in captured.out

    def test_list_remote_chains_verbose(self, capsys):
        """Test list-remote-chains with verbose output.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If verbose output doesn't contain expected details.
        :return None: None
        """
        # @@ STEP 1: Set up mock remote chains data. @@
        mock_chains = [
            {
                'name': 'base_chain',
                'url': 'https://example.com/base_chain',
                'local_path': str(self.project_dir / 'base_chain'),
                'last_updated': '2023-01-01 12:00:00',
                'size_mb': 2.5
            }
        ]

        # @@ STEP 2: Mock remote chains service and execute verbose command. @@
        with patch('chainedpy.services.command_handlers.list_project_remote_chains') as mock_list:
            mock_list.return_value = mock_chains

            # || S.S. 2.1: Execute command with verbose flag. ||
            args = Namespace(project_path=self.project_dir, verbose=True)
            handle_list_remote_chains(args)

            # @@ STEP 3: Verify verbose output contains detailed information. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for URL information. ||
            assert "URL: https://example.com/base_chain" in captured.out
            # || S.S. 3.2: Check for local path information. ||
            assert "Local path:" in captured.out
            # || S.S. 3.3: Check for last updated timestamp. ||
            assert "Last updated: 2023-01-01 12:00:00" in captured.out
            # || S.S. 3.4: Check for size information. ||
            assert "Size: 2.50 MB" in captured.out


class TestUpdateRemoteChainsCommand(BaseRemoteChainTestCase):
    """Test update-remote-chains CLI command."""

    def test_update_remote_chains_no_remote_base(self, capsys):
        """Test update-remote-chains when project has no remote base.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected message.
        :return None: None
        """
        # @@ STEP 1: Update config to have local base project. @@
        config_content = """
project:
  base_project: chainedpy
  summary: Test project with local base
"""
        (self.project_dir / "chainedpy.yaml").write_text(config_content)

        # @@ STEP 2: Execute update remote chains command. @@
        args = Namespace(project_path=self.project_dir, force=False)
        handle_update_remote_chains(args)

        # @@ STEP 3: Verify no remote dependencies message. @@
        captured = capsys.readouterr()
        # || S.S. 3.1: Check for expected message about no remote dependencies. ||
        assert "Project does not have remote dependencies" in captured.out

    def test_update_remote_chains_no_changes(self, capsys):
        """Test update-remote-chains when no changes are detected.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected up-to-date message.
        :return None: None
        """
        # @@ STEP 1: Mock no changes detected. @@
        with patch('chainedpy.services.command_handlers.detect_chain_changes') as mock_detect:
            mock_detect.return_value = False

            # @@ STEP 2: Execute update remote chains command. @@
            args = Namespace(project_path=self.project_dir, force=False)
            handle_update_remote_chains(args)

            # @@ STEP 3: Verify up-to-date message. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for up-to-date confirmation message. ||
            assert "Remote chains are up to date!" in captured.out

    def test_update_remote_chains_with_changes(self, capsys):
        """Test update-remote-chains when changes are detected.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected update messages.
        :return None: None
        """
        # @@ STEP 1: Set up mock updated chains data. @@
        mock_updated_chains = [
            Path(self.project_dir / 'base_chain'),
            Path(self.project_dir / 'dependency_chain')
        ]

        # @@ STEP 2: Mock services for chain update detection and execution. @@
        with patch('chainedpy.services.command_handlers.detect_chain_changes') as mock_detect, \
             patch('chainedpy.services.command_handlers.update_project_chains') as mock_update, \
             patch('chainedpy.services.command_handlers.get_project_chain_import') as mock_import, \
             patch('chainedpy.services.command_handlers._update_chain_file_with_import') as mock_update_file:

            # || S.S. 2.1: Configure mocks for successful update. ||
            mock_detect.return_value = True
            mock_update.return_value = mock_updated_chains
            mock_import.return_value = "from base_chain.base_chain_chain import Chain"

            # @@ STEP 3: Execute update remote chains command. @@
            args = Namespace(project_path=self.project_dir, force=False)
            handle_update_remote_chains(args)

            # @@ STEP 4: Verify update success messages. @@
            captured = capsys.readouterr()
            # || S.S. 4.1: Check for changes detection message. ||
            assert "Changes detected in remote chains" in captured.out
            # || S.S. 4.2: Check for successful update count. ||
            assert "Successfully updated 2 remote chain(s)" in captured.out
            # || S.S. 4.3: Check for specific chain names. ||
            assert "base_chain" in captured.out
            assert "dependency_chain" in captured.out
            # || S.S. 4.4: Check for overall success message. ||
            assert "Remote chains updated successfully!" in captured.out


class TestCheckRemoteUpdatesCommand(BaseRemoteChainTestCase):
    """Test check-remote-updates CLI command."""

    def test_check_remote_updates_no_changes(self, capsys):
        """Test check-remote-updates when no changes are available.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected up-to-date message.
        :return None: None
        """
        # @@ STEP 1: Mock no changes detected. @@
        with patch('chainedpy.services.command_handlers.detect_chain_changes') as mock_detect:
            mock_detect.return_value = False

            # @@ STEP 2: Execute check remote updates command. @@
            args = Namespace(project_path=self.project_dir)
            handle_check_remote_updates(args)

            # @@ STEP 3: Verify up-to-date message. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for up-to-date confirmation message. ||
            assert "Remote chains are up to date!" in captured.out

    def test_check_remote_updates_with_changes(self, capsys):
        """Test check-remote-updates when changes are available.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected update messages.
        :return None: None
        """
        # @@ STEP 1: Mock changes detected. @@
        with patch('chainedpy.services.command_handlers.detect_chain_changes') as mock_detect:
            mock_detect.return_value = True

            # @@ STEP 2: Execute check remote updates command. @@
            args = Namespace(project_path=self.project_dir)
            handle_check_remote_updates(args)

            # @@ STEP 3: Verify updates available messages. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for updates available message. ||
            assert "Updates available for remote chains!" in captured.out
            # || S.S. 3.2: Check for instruction to run update command. ||
            assert "Run 'chainedpy update-remote-chains' to download updates" in captured.out


class TestRemoteChainStatusCommand(BaseRemoteChainTestCase):
    """Test remote-chain-status CLI command."""

    def test_remote_chain_status_empty(self, capsys):
        """Test remote-chain-status when no remote chains exist.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected empty status messages.
        :return None: None
        """
        # @@ STEP 1: Set up mock status for empty remote chains. @@
        mock_status = {
            'project_name': 'test_project',
            'project_path': str(self.project_dir),
            'base_url': 'https://example.com/base_chain',
            'remote_chains': []
        }

        # @@ STEP 2: Mock status service and execute command. @@
        with patch('chainedpy.services.command_handlers.get_remote_chain_status') as mock_status_func:
            mock_status_func.return_value = mock_status

            # || S.S. 2.1: Execute remote chain status command. ||
            args = Namespace(project_path=self.project_dir)
            handle_remote_chain_status(args)

            # @@ STEP 3: Verify empty status output. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for project status header. ||
            assert "Remote Chain Status for: test_project" in captured.out
            # || S.S. 3.2: Check for no remote chains message. ||
            assert "No remote chains found" in captured.out

    def test_remote_chain_status_with_chains(self, capsys):
        """Test remote-chain-status with remote chains.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected chain status information.
        :return None: None
        """
        # @@ STEP 1: Set up mock status with remote chains. @@
        mock_status = {
            'project_name': 'test_project',
            'project_path': str(self.project_dir),
            'base_url': 'https://example.com/base_chain',
            'remote_chains': [
                {
                    'name': 'base_chain',
                    'url': 'https://example.com/base_chain',
                    'local_path': str(self.project_dir / 'base_chain'),
                    'last_updated': '2023-01-01 12:00:00',
                    'size_mb': 2.5,
                    'status': 'downloaded',
                    'has_updates': True
                }
            ]
        }

        # @@ STEP 2: Mock status service and execute command. @@
        with patch('chainedpy.services.command_handlers.get_remote_chain_status') as mock_status_func:
            mock_status_func.return_value = mock_status

            # || S.S. 2.1: Execute remote chain status command. ||
            args = Namespace(project_path=self.project_dir)
            handle_remote_chain_status(args)

            # @@ STEP 3: Verify chain status output. @@
            captured = capsys.readouterr()
            # || S.S. 3.1: Check for project status header. ||
            assert "Remote Chain Status for: test_project" in captured.out
            # || S.S. 3.2: Check for chain name. ||
            assert "base_chain" in captured.out
            # || S.S. 3.3: Check for updates available message. ||
            assert "Updates available!" in captured.out
            # || S.S. 3.4: Check for total chains count. ||
            assert "Total chains: 1" in captured.out
            # || S.S. 3.5: Check for chains with updates count. ||
            assert "Chains with updates: 1" in captured.out


# Real integration tests - These test actual operations without mocking
class TestRealRemoteChainOperations:
    """Real integration tests for remote chain operations - NO MOCKING.

    These tests perform actual operations without mocking to verify
    end-to-end functionality of remote chain commands.

    :raises Exception: If real operations fail during testing.
    """

    @integration_test
    def test_real_list_remote_chains_empty_project(self, capsys):
        """Test list-remote-chains with real empty project.

        :param capsys: Pytest fixture for capturing stdout/stderr.
        :type capsys: Any
        :raises AssertionError: If output doesn't contain expected no dependencies message.
        :return None: None
        """
        # @@ STEP 1: Create temporary project directory. @@
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "test_project"
            project_dir.mkdir()

            # @@ STEP 2: Create project without remote dependencies. @@
            config_content = """
project:
  base_project: chainedpy
  summary: Test project with local base
"""
            (project_dir / "chainedpy.yaml").write_text(config_content)

            # @@ STEP 3: Execute real list remote chains command. @@
            args = Namespace(project_path=project_dir, verbose=False)
            handle_list_remote_chains(args)

            # @@ STEP 4: Verify no remote dependencies message. @@
            captured = capsys.readouterr()
            # || S.S. 4.1: Check for expected no dependencies message. ||
            assert "Project does not have remote dependencies" in captured.out
