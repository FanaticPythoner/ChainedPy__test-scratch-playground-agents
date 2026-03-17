"""
Mock test service for ChainedPy tests.

Provides centralized mocking utilities and patterns for testing,
following ChainedPy's service patterns.
"""
from __future__ import annotations

from typing import Dict, Any, Optional, Callable
from unittest.mock import Mock, MagicMock



class MockTestServiceError(Exception):
    """Exception raised when mock test operations fail."""
    pass


class FilesystemMockService:
    """Service for mocking filesystem operations.

    :raises Exception: If filesystem mock service operations fail.
    """

    @staticmethod
    def mock_filesystem_for_remote_url(url: str, fs_type: str = "github") -> tuple[Mock, Mock]:
        """Create mocks for filesystem operations with remote URLs.

        :param url: Remote URL to mock.
        :type url: str
        :param fs_type: Type of filesystem to mock, defaults to "github".
        :type fs_type: str, optional
        :return tuple[Mock, Mock]: Tuple of (mock_get_fs, mock_fs).
        """
        # @@ STEP 1: Create filesystem mock. @@
        mock_fs = MagicMock()

        # @@ STEP 2: Create get_fs mock returning filesystem mock. @@
        mock_get_fs = Mock(return_value=(mock_fs, fs_type))

        # @@ STEP 3: Return both mocks. @@
        return mock_get_fs, mock_fs

    @staticmethod
    def mock_valid_remote_config(base_project: str = "chainedpy",
                                summary: str = "Valid remote ChainedPy project") -> Dict[str, str]:
        """Create a mock valid remote project configuration.

        :param base_project: Base project value for mock config, defaults to "chainedpy".
        :type base_project: str, optional
        :param summary: Summary value for mock config, defaults to "Valid remote ChainedPy project".
        :type summary: str, optional
        :return Dict[str, str]: Mock configuration dictionary (Dictionary representing valid remote config).
        """
        return {
            'base_project': base_project,
            'summary': summary
        }
    
    @staticmethod
    def mock_invalid_remote_config() -> Dict[str, Any]:
        """Create a mock invalid remote project configuration.

        :return Dict[str, Any]: Empty dictionary representing invalid remote config.
        """
        # @@ STEP 1: Return empty dictionary for invalid config. @@
        return {}

    @staticmethod
    def create_filesystem_side_effect(url_mappings: Dict[str, tuple[str, Dict[str, Any]]]) -> Callable:
        """Create a side effect function for mocking filesystem operations with multiple URLs.

        :param url_mappings: Dictionary mapping URLs to (fs_type, config) tuples.
        :type url_mappings: Dict[str, tuple[str, Dict[str, Any]]]
        :return Callable: Side effect function for mock_get_fs.
        """
        # @@ STEP 1: Define side effect function. @@
        def side_effect(path, _):
            # || S.S. 1.1: Check each URL pattern for match. ||
            for url_pattern, (fs_type, config) in url_mappings.items():
                if url_pattern in path:
                    return MagicMock(), fs_type
            # || S.S. 1.2: Return default for unmatched paths. ||
            return None, "local"

        # @@ STEP 2: Return side effect function. @@
        return side_effect

    @staticmethod
    def create_config_side_effect(url_mappings: Dict[str, Dict[str, Any]]) -> Callable:
        """Create a side effect function for mocking config reading with multiple URLs.

        :param url_mappings: Dictionary mapping URL patterns to config dictionaries.
        :type url_mappings: Dict[str, Dict[str, Any]]
        :return Callable: Side effect function for mock_read_config.
        """
        # @@ STEP 1: Define side effect function. @@
        def side_effect(_, path, creds=None):
            # || S.S. 1.1: Check each URL pattern for match. ||
            for url_pattern, config in url_mappings.items():
                if url_pattern in path:
                    return config
            # || S.S. 1.2: Return default local config for unmatched paths. ||
            return {
                'base_project': 'chainedpy',
                'summary': 'Local test project'
            }

        # @@ STEP 2: Return side effect function. @@
        return side_effect


class CredentialMockService:
    """Service for mocking credential operations.

    :raises Exception: If credential mock service operations fail.
    """

    @staticmethod
    def mock_credentials_with_github_token(token: str = "test_token") -> Dict[str, str]:
        """Create mock credentials with GitHub token.

        :param token: GitHub token value to mock, defaults to "test_token".
        :type token: str, optional
        :return Dict[str, str]: Dictionary with mocked GitHub credentials.
        """
        # @@ STEP 1: Return GitHub token credentials. @@
        return {
            'github_token': token
        }

    @staticmethod
    def mock_credentials_with_gitlab_token(token: str = "test_gitlab_token") -> Dict[str, str]:
        """Create mock credentials with GitLab token.

        :param token: GitLab token value to mock, defaults to "test_gitlab_token".
        :type token: str, optional
        :return Dict[str, str]: Dictionary with mocked GitLab credentials.
        """
        # @@ STEP 1: Return GitLab token credentials. @@
        return {
            'gitlab_token': token
        }

    @staticmethod
    def mock_empty_credentials() -> Dict[str, str]:
        """Create mock empty credentials.

        :return Dict[str, str]: Empty credentials dictionary.
        """
        # @@ STEP 1: Return empty credentials dictionary. @@
        return {}


class CLIMockService:
    """Service for mocking CLI operations.

    :raises Exception: If CLI mock service operations fail.
    """

    @staticmethod
    def mock_cli_success_exit() -> Mock:
        """Create a mock for successful CLI exit.

        :return Mock: Mock SystemExit with code 0.
        """
        # @@ STEP 1: Create mock exit with success code. @@
        mock_exit = Mock()
        mock_exit.value.code = 0
        return mock_exit

    @staticmethod
    def mock_cli_failure_exit() -> Mock:
        """Create a mock for failed CLI exit.

        :return Mock: Mock SystemExit with code 1.
        """
        # @@ STEP 1: Create mock exit with failure code. @@
        mock_exit = Mock()
        mock_exit.value.code = 1
        return mock_exit

    @staticmethod
    def capture_cli_output(capsys, expected_success_messages: Optional[list] = None,
                          expected_error_messages: Optional[list] = None) -> Dict[str, str]:
        """Capture and validate CLI output.

        :param capsys: pytest capsys fixture.
        :type capsys: pytest.CaptureFixture
        :param expected_success_messages: List of expected success messages, defaults to None.
        :type expected_success_messages: Optional[list], optional
        :param expected_error_messages: List of expected error messages, defaults to None.
        :type expected_error_messages: Optional[list], optional
        :return Dict[str, str]: Dictionary with captured stdout and stderr.
        """
        # @@ STEP 1: Capture CLI output. @@
        captured = capsys.readouterr()

        # @@ STEP 2: Validate expected success messages if provided. @@
        if expected_success_messages:
            for message in expected_success_messages:
                assert message in captured.out or message in captured.err

        # @@ STEP 3: Validate expected error messages if provided. @@
        if expected_error_messages:
            for message in expected_error_messages:
                assert message in captured.err

        # @@ STEP 4: Return captured output. @@
        return {
            'stdout': captured.out,
            'stderr': captured.err
        }


class RemoteRepositoryMockService:
    """Service for mocking remote repository operations.

    :raises Exception: If remote repository mock service operations fail.
    """

    # Real repository URLs for testing
    PUBLIC_REPO_URL = (
        "https://raw.githubusercontent.com/FanaticPythoner/"
        "chainedpy_test_public_chain_simple/main/mypublicchain1"
    )
    PRIVATE_REPO_URL = (
        "https://raw.githubusercontent.com/FanaticPythoner/"
        "chainedpy_test_private_chain_simple/main/myprivatechain1"
    )
    INVALID_REPO_URL = "https://github.com/nonexistent/invalid_repo_12345"

    @staticmethod
    def mock_public_repository_access() -> tuple[Mock, Mock]:
        """Create mocks for successful public repository access.

        :return tuple[Mock, Mock]: Tuple of (mock_get_fs, mock_read_config).
        """
        # @@ STEP 1: Create filesystem mock for public repository. @@
        mock_get_fs, mock_fs = FilesystemMockService.mock_filesystem_for_remote_url(
            RemoteRepositoryMockService.PUBLIC_REPO_URL, "github"
        )

        # @@ STEP 2: Create config mock for public repository. @@
        mock_read_config = Mock(return_value=FilesystemMockService.mock_valid_remote_config(
            "chainedpy", "Public test repository"
        ))

        # @@ STEP 3: Return both mocks. @@
        return mock_get_fs, mock_read_config

    @staticmethod
    def mock_private_repository_access_with_token() -> tuple[Mock, Mock]:
        """Create mocks for successful private repository access with token.

        :return tuple[Mock, Mock]: Tuple of (mock_get_fs, mock_read_config).
        """
        # @@ STEP 1: Create filesystem mock for private repository. @@
        mock_get_fs, mock_fs = FilesystemMockService.mock_filesystem_for_remote_url(
            RemoteRepositoryMockService.PRIVATE_REPO_URL, "github"
        )

        # @@ STEP 2: Create config mock for private repository. @@
        mock_read_config = Mock(return_value=FilesystemMockService.mock_valid_remote_config(
            "chainedpy", "Private test repository"
        ))

        # @@ STEP 3: Return both mocks. @@
        return mock_get_fs, mock_read_config
    @staticmethod
    def mock_private_repository_access_without_token() -> tuple[Mock, Mock]:
        """Create mocks for failed private repository access without token.

        :return tuple[Mock, Mock]: Tuple of (mock_get_fs, mock_read_config).
        """
        # @@ STEP 1: Create filesystem mock for private repository. @@
        mock_get_fs, mock_fs = FilesystemMockService.mock_filesystem_for_remote_url(
            RemoteRepositoryMockService.PRIVATE_REPO_URL, "github"
        )

        # @@ STEP 2: Create invalid config mock for failed access. @@
        mock_read_config = Mock(return_value=FilesystemMockService.mock_invalid_remote_config())

        # @@ STEP 3: Return both mocks. @@
        return mock_get_fs, mock_read_config

    @staticmethod
    def mock_invalid_repository_access() -> tuple[Mock, Mock]:
        """Create mocks for invalid repository access.

        :return tuple[Mock, Mock]: Tuple of (mock_get_fs, mock_read_config).
        """
        # @@ STEP 1: Create filesystem mock for invalid repository. @@
        mock_get_fs, mock_fs = FilesystemMockService.mock_filesystem_for_remote_url(
            RemoteRepositoryMockService.INVALID_REPO_URL, "github"
        )

        # @@ STEP 2: Create invalid config mock. @@
        mock_read_config = Mock(return_value=FilesystemMockService.mock_invalid_remote_config())

        # @@ STEP 3: Return both mocks. @@
        return mock_get_fs, mock_read_config

    @staticmethod
    def mock_filesystem_for_remote_url(url: str, fs_type: str = "github") -> tuple[Mock, Mock]:
        """Delegate to FilesystemMockService for backward compatibility.

        :param url: Remote URL to mock.
        :type url: str
        :param fs_type: Type of filesystem to mock, defaults to "github".
        :type fs_type: str, optional
        :return tuple[Mock, Mock]: Tuple of (mock_get_fs, mock_fs).
        """
        # @@ STEP 1: Delegate to FilesystemMockService. @@
        return FilesystemMockService.mock_filesystem_for_remote_url(url, fs_type)

    @staticmethod
    def mock_mixed_local_remote_chain() -> Dict[str, Any]:
        """Create mock data for mixed local/remote chain testing.

        :return Dict[str, Any]: Dictionary with mock chain data.
        """
        # @@ STEP 1: Return mock chain data for mixed scenarios. @@
        return {
            'local_project': {
                'base_project': 'chainedpy',
                'summary': 'Local project in mixed chain'
            },
            'remote_project': {
                'base_project': './local_project',
                'summary': 'Remote project extending local'
            }
        }

    @staticmethod
    def get_test_urls() -> Dict[str, str]:
        """Get test URLs for various scenarios.

        :return Dict[str, str]: Dictionary mapping scenario names to URLs.
        """
        # @@ STEP 1: Return dictionary of test URLs. @@
        return {
            'public_repo': RemoteRepositoryMockService.PUBLIC_REPO_URL,
            'private_repo': RemoteRepositoryMockService.PRIVATE_REPO_URL,
            'invalid_repo': RemoteRepositoryMockService.INVALID_REPO_URL,
            'public_config_url': f"{RemoteRepositoryMockService.PUBLIC_REPO_URL}/chainedpy.yaml",
            'invalid_config_url': f"{RemoteRepositoryMockService.INVALID_REPO_URL}/chainedpy.yaml"
        }
