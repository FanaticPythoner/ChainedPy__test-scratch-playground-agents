"""
Mock fixtures for ChainedPy tests.

Provides centralized mock objects and patching utilities
following ChainedPy's service patterns.
"""
from __future__ import annotations
from typing import Dict
from unittest.mock import Mock, MagicMock, patch

import pytest
from tests.services.mock_test_service import (
    FilesystemMockService, CredentialMockService, RemoteRepositoryMockService
)


@pytest.fixture
def mock_filesystem():
    """Create a mock filesystem for testing.

    :return Mock: Mock filesystem object.
    """
    # @@ STEP 1: Create mock filesystem object. @@
    mock_fs = MagicMock()

    # @@ STEP 2: Yield mock filesystem for test usage. @@
    yield mock_fs


@pytest.fixture
def mock_remote_filesystem():
    """Create mocks for remote filesystem operations.

    :return Dict[str, Mock]: Dictionary with mock_get_fs and mock_fs.
    :raises Exception: If mock creation fails.
    """
    # @@ STEP 1: Create filesystem mocks for remote URL. @@
    mock_get_fs, mock_fs = FilesystemMockService.mock_filesystem_for_remote_url(
        "https://github.com/test/repo", "github"
    )

    # @@ STEP 2: Yield mock dictionary for test usage. @@
    yield {
        'mock_get_fs': mock_get_fs,
        'mock_fs': mock_fs
    }


@pytest.fixture
def mock_valid_remote_config():
    """Create a mock valid remote configuration.

    :return Dict[str, str]: Valid remote configuration dictionary.
    """
    # @@ STEP 1: Create valid remote configuration using mock service. @@
    config = FilesystemMockService.mock_valid_remote_config()

    # @@ STEP 2: Yield configuration for test usage. @@
    yield config


@pytest.fixture
def mock_invalid_remote_config():
    """Create a mock invalid remote configuration.

    :return Dict[str, Any]: Invalid remote configuration dictionary.
    """
    # @@ STEP 1: Create invalid remote configuration using mock service. @@
    config = FilesystemMockService.mock_invalid_remote_config()

    # @@ STEP 2: Yield configuration for test usage. @@
    yield config


@pytest.fixture
def mock_github_credentials():
    """Create mock GitHub credentials.

    :return Dict[str, str]: Mock GitHub credentials.
    """
    # @@ STEP 1: Create GitHub credentials using mock service. @@
    credentials = CredentialMockService.mock_credentials_with_github_token()

    # @@ STEP 2: Yield credentials for test usage. @@
    yield credentials


@pytest.fixture
def mock_gitlab_credentials():
    """Create mock GitLab credentials.

    :return Dict[str, str]: Mock GitLab credentials.
    """
    # @@ STEP 1: Create GitLab credentials using mock service. @@
    credentials = CredentialMockService.mock_credentials_with_gitlab_token()

    # @@ STEP 2: Yield credentials for test usage. @@
    yield credentials


@pytest.fixture
def mock_empty_credentials():
    """Create mock empty credentials.

    :return Dict[str, str]: Empty credentials dictionary.
    """
    # @@ STEP 1: Create empty credentials using mock service. @@
    credentials = CredentialMockService.mock_empty_credentials()

    # @@ STEP 2: Yield credentials for test usage. @@
    yield credentials


@pytest.fixture
def mock_public_repository():
    """Create mocks for successful public repository access.

    :return Dict[str, Mock]: Dictionary with filesystem and config mocks.
    :raises Exception: If mock creation fails.
    """
    # @@ STEP 1: Create mocks for public repository access. @@
    mock_get_fs, mock_read_config = RemoteRepositoryMockService.mock_public_repository_access()

    # @@ STEP 2: Yield mock dictionary for test usage. @@
    yield {
        'mock_get_fs': mock_get_fs,
        'mock_read_config': mock_read_config
    }


@pytest.fixture
def mock_private_repository_with_token():
    """Create mocks for successful private repository access with token.

    :return Dict[str, Mock]: Dictionary with filesystem and config mocks.
    :raises Exception: If mock creation fails.
    """
    # @@ STEP 1: Create mocks for private repository access with token. @@
    mock_get_fs, mock_read_config = RemoteRepositoryMockService.mock_private_repository_access_with_token()

    # @@ STEP 2: Yield mock dictionary for test usage. @@
    yield {
        'mock_get_fs': mock_get_fs,
        'mock_read_config': mock_read_config
    }


@pytest.fixture
def mock_private_repository_without_token():
    """Create mocks for failed private repository access without token.

    :return Dict[str, Mock]: Dictionary with filesystem and config mocks.
    :raises Exception: If mock creation fails.
    """
    # @@ STEP 1: Create mocks for private repository access without token. @@
    mock_get_fs, mock_read_config = RemoteRepositoryMockService.mock_private_repository_access_without_token()

    # @@ STEP 2: Yield mock dictionary for test usage. @@
    yield {
        'mock_get_fs': mock_get_fs,
        'mock_read_config': mock_read_config
    }


@pytest.fixture
def mock_invalid_repository():
    """Create mocks for invalid repository access.

    :return Dict[str, Mock]: Dictionary with filesystem and config mocks.
    :raises Exception: If mock creation fails.
    """
    # @@ STEP 1: Create mocks for invalid repository access. @@
    mock_get_fs, mock_read_config = RemoteRepositoryMockService.mock_invalid_repository_access()

    # @@ STEP 2: Yield mock dictionary for test usage. @@
    yield {
        'mock_get_fs': mock_get_fs,
        'mock_read_config': mock_read_config
    }


@pytest.fixture
def mock_chain_traversal_service():
    """Create comprehensive mocks for chain traversal service.

    :return Dict[str, Mock]: Dictionary with all chain traversal mocks.
    :raises Exception: If patching fails.
    """
    # @@ STEP 1: Patch chain traversal service methods. @@
    with patch('chainedpy.services.chain_traversal_service._get_filesystem') as mock_get_fs, \
         patch('chainedpy.services.chain_traversal_service._read_remote_config') as mock_read_config:

        # @@ STEP 2: Set up default behavior for mocks. @@
        mock_get_fs.return_value = (MagicMock(), "local")
        mock_read_config.return_value = {
            'base_project': 'chainedpy',
            'summary': 'Test project'
        }

        # @@ STEP 3: Yield mock dictionary for test usage. @@
        yield {
            'mock_get_fs': mock_get_fs,
            'mock_read_config': mock_read_config
        }


@pytest.fixture
def mock_remote_chain_service():
    """Create comprehensive mocks for remote chain service.

    :return Dict[str, Mock]: Dictionary with all remote chain service mocks.
    :raises Exception: If patching fails.
    """
    # @@ STEP 1: Patch remote chain service methods. @@
    with patch('chainedpy.services.remote_chain_service.download_remote_chain') as mock_download, \
         patch('chainedpy.services.remote_chain_service.resolve_dependencies_recursively') as mock_resolve, \
         patch('chainedpy.services.remote_chain_service.list_cached_chains') as mock_list, \
         patch('chainedpy.services.remote_chain_service.clean_expired_cache') as mock_clean:

        # @@ STEP 2: Set up default behavior for mocks. @@
        mock_download.return_value = "/tmp/cached/chain"
        mock_resolve.return_value = []
        mock_list.return_value = []
        mock_clean.return_value = 0

        # @@ STEP 3: Yield mock dictionary for test usage. @@
        yield {
            'mock_download': mock_download,
            'mock_resolve': mock_resolve,
            'mock_list': mock_list,
            'mock_clean': mock_clean
        }


@pytest.fixture
def mock_credential_service():
    """Create comprehensive mocks for credential service.

    :return Dict[str, Mock]: Dictionary with all credential service mocks.
    :raises Exception: If patching fails.
    """
    # @@ STEP 1: Patch credential service methods. @@
    with patch('chainedpy.services.credential_service.load_repository_credentials') as mock_load_repo, \
         patch('chainedpy.services.credential_service.validate_credentials') as mock_validate, \
         patch('chainedpy.services.credential_service.get_credential_file_path') as mock_get_path:

        # @@ STEP 2: Set up default behavior for mocks. @@
        mock_load_repo.return_value = {}
        mock_validate.return_value = True
        mock_get_path.return_value = "/tmp/.env"

        # @@ STEP 3: Yield mock dictionary for test usage. @@
        yield {
            'mock_load_repo': mock_load_repo,
            'mock_validate': mock_validate,
            'mock_get_path': mock_get_path
        }


@pytest.fixture
def mock_filesystem_service():
    """Create comprehensive mocks for filesystem service.

    :return Dict[str, Mock]: Dictionary with all filesystem service mocks.
    :raises Exception: If patching fails.
    """
    # @@ STEP 1: Patch filesystem service methods. @@
    with patch('chainedpy.services.filesystem_service.get_filesystem') as mock_get_fs, \
         patch('chainedpy.services.filesystem_service.read_text') as mock_read, \
         patch('chainedpy.services.filesystem_service.write_text') as mock_write, \
         patch('chainedpy.services.filesystem_service.exists') as mock_exists:

        # @@ STEP 2: Set up default behavior for mocks. @@
        mock_get_fs.return_value = (MagicMock(), "local")
        mock_read.return_value = "test content"
        mock_write.return_value = None
        mock_exists.return_value = True

        # @@ STEP 3: Yield mock dictionary for test usage. @@
        yield {
            'mock_get_fs': mock_get_fs,
            'mock_read': mock_read,
            'mock_write': mock_write,
            'mock_exists': mock_exists
        }


@pytest.fixture
def mock_project_operations():
    """Create mocks for project operations that might fail.

    :return Dict[str, Mock]: Dictionary with project operation mocks.
    :raises Exception: If patching fails.
    """
    # @@ STEP 1: Patch project operation methods. @@
    with patch('chainedpy.project._write_project_config') as mock_write_config, \
         patch('chainedpy.project._read_project_config') as mock_read_config, \
         patch('chainedpy.project.update_project_stub') as mock_update_stub:

        # @@ STEP 2: Set up default behavior for mocks. @@
        mock_write_config.return_value = None
        mock_read_config.return_value = Mock(base_project="chainedpy", summary="Test")
        mock_update_stub.return_value = Mock()

        # @@ STEP 3: Yield mock dictionary for test usage. @@
        yield {
            'mock_write_config': mock_write_config,
            'mock_read_config': mock_read_config,
            'mock_update_stub': mock_update_stub
        }


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Create a fixture for mocking environment variables.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: Any
    :return Callable: Function to set environment variables for testing.
    """
    def set_env_vars(env_dict: Dict[str, str]):
        """Set environment variables for testing.

        :param env_dict: Dictionary of environment variables to set.
        :type env_dict: Dict[str, str]
        """
        # @@ STEP 1: Set each environment variable. @@
        for key, value in env_dict.items():
            monkeypatch.setenv(key, value)

    def clear_env_vars(env_keys: list):
        """Clear environment variables for testing.

        :param env_keys: List of environment variable keys to clear.
        :type env_keys: list
        """
        # @@ STEP 1: Clear each environment variable. @@
        for key in env_keys:
            monkeypatch.delenv(key, raising=False)

    # @@ STEP 2: Yield helper functions for test usage. @@
    yield {
        'set': set_env_vars,
        'clear': clear_env_vars
    }
