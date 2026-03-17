"""
Integration tests for project-local remote chain functionality.

Tests the new system where remote chains are downloaded directly to project directories
instead of using a global cache.
"""
from __future__ import annotations

# 1. Standard library imports
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# 2. Third-party imports
import pytest

# 3. Internal constants
from chainedpy.constants import (
    REMOTE_CHAIN_META_FILE_NAME, CONFIG_FILE_NAME, INIT_FILE_NAME, CHAIN_FILE_SUFFIX
)

# 4. ChainedPy services
from chainedpy.services.credential_service import (
    save_repository_credentials, load_repository_credentials
)
from chainedpy.services.project_remote_chain_service import (
    list_project_chains
)
from chainedpy.services.remote_chain_service import (
    download_remote_chain_to_project, resolve_dependencies_recursively,
    RemoteChainInfo, RemoteChainServiceError, _get_project_name_from_url
)

# 5. ChainedPy internal modules
# (none)

# 6. Test utilities
from tests.utils.test_helpers import integration_test, requires_network, requires_credentials


class TestProjectRemoteChainSystem:
    """Test the project-local remote chain system.

    :raises Exception: If project remote chain system testing fails.
    """

    def setup_method(self):
        """Set up test environment with temporary project directory.

        :raises OSError: If temporary directory creation fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary directory for testing. @@
        self.temp_dir = Path(tempfile.mkdtemp())
        # @@ STEP 2: Create project directory structure. @@
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create a basic project structure. @@
        (self.project_dir / "__init__.py").write_text("# Test project")
        (self.project_dir / "chainedpy.yaml").write_text("""
project:
  base_project: https://example.com/base_chain
  summary: Test project
""")

    def teardown_method(self):
        """Clean up test environment.

        :return None: None
        """
        # @@ STEP 1: Remove temporary directory if it exists. @@
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_project_name_extraction(self):
        """Test project name extraction from URLs.

        :raises AssertionError: If project name extraction doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Test first URL format. @@
        url1 = "https://raw.githubusercontent.com/user/repo/main/my_project"
        name1 = _get_project_name_from_url(url1)
        assert name1 == "my_project"

        # @@ STEP 2: Test second URL format. @@
        url2 = "https://github.com/user/repo/tree/main/another_project"
        name2 = _get_project_name_from_url(url2)
        assert name2 == "another_project"

    @patch('chainedpy.services.remote_chain_service._download_remote_files')
    @patch('chainedpy.services.remote_chain_service._extract_dependencies')
    def test_download_remote_chain_to_project_success(self, mock_extract_deps, mock_download_files):
        """Test successful remote chain download to project.

        :param mock_extract_deps: Mock for dependency extraction.
        :type mock_extract_deps: MagicMock
        :param mock_download_files: Mock for file download.
        :type mock_download_files: MagicMock
        :raises AssertionError: If remote chain download doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define repository URL. @@
        repo_url = "https://raw.githubusercontent.com/user/repo/main/project"

        # @@ STEP 2: Mock successful download. @@
        mock_download_files.return_value = ['__init__.py', 'chainedpy.yaml', 'project_chain.py']
        mock_extract_deps.return_value = []

        # @@ STEP 3: Download remote chain. @@
        chain_info = download_remote_chain_to_project(repo_url, self.project_dir)

        # @@ STEP 4: Verify chain info. @@
        assert isinstance(chain_info, RemoteChainInfo)
        assert chain_info.url == repo_url
        assert chain_info.local_path.exists()
        assert chain_info.local_path.parent == self.project_dir

        # @@ STEP 5: Verify metadata was created. @@
        metadata_file = chain_info.local_path / REMOTE_CHAIN_META_FILE_NAME
        assert metadata_file.exists()

    @patch('chainedpy.services.remote_chain_service._download_remote_files')
    def test_download_remote_chain_failure(self, mock_download_files):
        """Test remote chain download failure.

        :param mock_download_files: Mock for file download.
        :type mock_download_files: MagicMock
        :raises AssertionError: If remote chain download failure handling doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define nonexistent repository URL. @@
        repo_url = "https://raw.githubusercontent.com/user/nonexistent/main/project"

        # @@ STEP 2: Mock download failure. @@
        mock_download_files.side_effect = Exception("Network error")

        # @@ STEP 3: Verify exception is raised. @@
        with pytest.raises(RemoteChainServiceError):
            download_remote_chain_to_project(repo_url, self.project_dir)

    def test_list_project_chains_empty(self):
        """Test listing project chains when none exist.

        :raises AssertionError: If empty chain listing doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: List project chains from empty directory. @@
        chains = list_project_chains(self.project_dir)

        # @@ STEP 2: Verify no chains found. @@
        assert len(chains) == 0

    def test_list_project_chains_with_chains(self):
        """Test listing project chains when some exist.

        :raises AssertionError: If chain listing doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Create mock remote chain directories. @@
        chain1_dir = self.project_dir / "chain1"
        chain1_dir.mkdir()
        (chain1_dir / "__init__.py").write_text("# Chain 1")
        (chain1_dir / "chain1_chain.py").write_text("# Chain 1 implementation")

        chain2_dir = self.project_dir / "chain2"
        chain2_dir.mkdir()
        (chain2_dir / "__init__.py").write_text("# Chain 2")
        (chain2_dir / "chain2_chain.py").write_text("# Chain 2 implementation")

        # @@ STEP 2: Create metadata files. @@
        for chain_dir in [chain1_dir, chain2_dir]:
            metadata = {
                "url": f"https://example.com/{chain_dir.name}",
                "downloaded_at": datetime.now().isoformat(),
                "dependencies": [],
                "files": ["__init__.py", f"{chain_dir.name}_chain.py"],
                "ttl_hours": 24,
                "local_path": str(chain_dir),
                "size_mb": 1.0
            }
            metadata_file = chain_dir / REMOTE_CHAIN_META_FILE_NAME
            metadata_file.write_text(json.dumps(metadata, indent=2))

        # @@ STEP 3: List chains and verify results. @@
        chains = list_project_chains(self.project_dir)
        assert len(chains) == 2
        chain_names = [chain.name for chain in chains]
        assert "chain1" in chain_names
        assert "chain2" in chain_names


class TestProjectCredentialSystem:
    """Test project-local credential management.

    :raises Exception: If project credential system testing fails.
    """

    def setup_method(self):
        """Set up test environment.

        :raises OSError: If temporary directory creation fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary directory for testing. @@
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment.

        :return None: None
        """
        # @@ STEP 1: Remove temporary directory if it exists. @@
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_project_credentials(self):
        """Test saving and loading project-specific credentials.

        :raises AssertionError: If credential save/load doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define test credentials. @@
        repo_url = "https://github.com/user/private_repo"
        github_token = "test_token_123"

        # @@ STEP 2: Save credentials using real implementation. @@
        result = save_repository_credentials(repo_url, self.project_dir, github_token=github_token)
        assert result is True

        # @@ STEP 3: Load credentials using real implementation. @@
        credentials = load_repository_credentials(repo_url, self.project_dir)
        assert credentials.get('github_token') == github_token

    def test_credential_fallback_to_global(self):
        """Test fallback to global credentials when project-specific not found.

        :raises AssertionError: If credential fallback doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define test repository URL. @@
        repo_url = "https://github.com/user/public_repo"

        # @@ STEP 2: Set environment variable for global credentials. @@
        original_token = os.environ.get('GITHUB_TOKEN')
        os.environ['GITHUB_TOKEN'] = 'global_test_token'

        # @@ STEP 3: Test credential fallback. @@
        try:
            credentials = load_repository_credentials(repo_url, self.project_dir)
            assert credentials.get('github_token') == 'global_test_token'
        finally:
            # @@ STEP 4: Clean up environment. @@
            if original_token is not None:
                os.environ['GITHUB_TOKEN'] = original_token
            elif 'GITHUB_TOKEN' in os.environ:
                del os.environ['GITHUB_TOKEN']


class TestDependencyResolution:
    """Test recursive dependency resolution for project-local chains.

    :raises Exception: If dependency resolution testing fails.
    """

    def setup_method(self):
        """Set up test environment.

        :raises OSError: If temporary directory creation fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary directory for testing. @@
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment.

        :return None: None
        """
        # @@ STEP 1: Remove temporary directory if it exists. @@
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('chainedpy.services.remote_chain_service.download_remote_chain_to_project')
    def test_recursive_dependency_resolution(self, mock_download):
        """Test recursive dependency resolution.

        :param mock_download: Mock for download function.
        :type mock_download: MagicMock
        :raises AssertionError: If recursive dependency resolution doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Mock chain hierarchy: A -> B -> chainedpy. @@
        chain_a_info = MagicMock()
        chain_a_info.dependencies = ["https://example.com/chain_b"]
        chain_a_info.local_path = self.project_dir / "chain_a"

        chain_b_info = MagicMock()
        chain_b_info.dependencies = []
        chain_b_info.local_path = self.project_dir / "chain_b"

        # @@ STEP 2: Define mock download side effect. @@
        def mock_download_side_effect(url, project_path, **kwargs):
            if "chain_a" in url:
                return chain_a_info
            elif "chain_b" in url:
                return chain_b_info
            else:
                raise Exception(f"Unknown URL: {url}")

        mock_download.side_effect = mock_download_side_effect

        # @@ STEP 3: Resolve dependencies recursively. @@
        resolved_chains = resolve_dependencies_recursively("https://example.com/chain_a", self.project_dir)

        # @@ STEP 4: Verify both chains were downloaded. @@
        assert len(resolved_chains) == 2
        assert mock_download.call_count == 2

    @patch('chainedpy.services.remote_chain_service.download_remote_chain_to_project')
    def test_circular_dependency_detection(self, mock_download):
        """Test circular dependency detection.

        :param mock_download: Mock for download function.
        :type mock_download: MagicMock
        :raises AssertionError: If circular dependency detection doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Mock circular dependency: A -> B -> A. @@
        chain_a_info = MagicMock()
        chain_a_info.dependencies = ["https://example.com/chain_b"]
        chain_a_info.local_path = self.project_dir / "chain_a"

        chain_b_info = MagicMock()
        chain_b_info.dependencies = ["https://example.com/chain_a"]  # Circular!
        chain_b_info.local_path = self.project_dir / "chain_b"

        # @@ STEP 2: Define mock download side effect. @@
        def mock_download_side_effect(url, project_path, **kwargs):
            if "chain_a" in url:
                return chain_a_info
            elif "chain_b" in url:
                return chain_b_info
            else:
                raise Exception(f"Unknown URL: {url}")

        mock_download.side_effect = mock_download_side_effect

        # @@ STEP 3: Verify circular dependency is detected. @@
        with pytest.raises(RemoteChainServiceError, match="Circular dependency"):
            resolve_dependencies_recursively("https://example.com/chain_a", self.project_dir)


class TestRealRepositoryIntegration:
    """Test integration with real GitHub/GitLab repositories.

    :raises Exception: If real repository integration testing fails.
    """

    def setup_method(self):
        """Set up test environment.

        :raises OSError: If temporary directory creation fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary directory for testing. @@
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment.

        :return None: None
        """
        # @@ STEP 1: Remove temporary directory if it exists. @@
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @integration_test
    @requires_network
    def test_download_real_public_repository(self):
        """Test downloading from a real public repository.

        :raises AssertionError: If real public repository download doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define public repository URL. @@
        public_repo_url = "https://raw.githubusercontent.com/FanaticPythoner/chainedpy_test_public_chain_simple/main/mypublicchain1"

        # @@ STEP 2: Download from real public repository. @@
        chain_info = download_remote_chain_to_project(public_repo_url, self.project_dir)

        # @@ STEP 3: Verify download was successful. @@
        assert isinstance(chain_info, RemoteChainInfo)
        assert chain_info.url == public_repo_url
        assert chain_info.local_path.exists()

        # @@ STEP 4: Verify required files were downloaded. @@
        assert (chain_info.local_path / INIT_FILE_NAME).exists()
        assert (chain_info.local_path / CONFIG_FILE_NAME).exists()

        # @@ STEP 5: Check for chain file (name depends on project structure). @@
        chain_files = list(chain_info.local_path.glob(f"*{CHAIN_FILE_SUFFIX}"))
        assert len(chain_files) > 0

    @integration_test
    @requires_credentials('github')
    def test_download_real_private_repository_with_auth(self):
        """Test downloading from a real private repository with authentication.

        :raises AssertionError: If real private repository download doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define private repository URL and get token. @@
        private_repo_url = "https://raw.githubusercontent.com/FanaticPythoner/chainedpy_test_private_chain_simple/main/myprivatechain1"
        github_token = os.environ.get('GITHUB_TOKEN')

        # @@ STEP 2: Save repository-specific credentials. @@
        save_repository_credentials(private_repo_url, self.project_dir, github_token=github_token)

        # @@ STEP 3: Download from real private repository. @@
        chain_info = download_remote_chain_to_project(private_repo_url, self.project_dir)

        # @@ STEP 4: Verify download was successful. @@
        assert isinstance(chain_info, RemoteChainInfo)
        assert chain_info.url == private_repo_url
        assert chain_info.local_path.exists()

        # @@ STEP 5: Verify required files were downloaded. @@
        assert (chain_info.local_path / INIT_FILE_NAME).exists()
        assert (chain_info.local_path / CONFIG_FILE_NAME).exists()

    @integration_test
    @requires_network
    def test_download_nonexistent_repository(self):
        """Test downloading from a nonexistent repository.

        :raises AssertionError: If nonexistent repository error handling doesn't work correctly.
        :return None: None
        """
        # @@ STEP 1: Define nonexistent repository URL. @@
        nonexistent_url = "https://raw.githubusercontent.com/nonexistent/repo/main/project"

        # @@ STEP 2: Verify exception is raised for nonexistent repository. @@
        with pytest.raises(RemoteChainServiceError):
            download_remote_chain_to_project(nonexistent_url, self.project_dir)
