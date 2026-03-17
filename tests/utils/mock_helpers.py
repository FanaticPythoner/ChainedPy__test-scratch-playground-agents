"""
Mock helpers for ChainedPy tests.

Provides mock creation and management utilities for testing
following ChainedPy's service patterns.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Callable, Union
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path


def create_mock_filesystem(fs_type: str = "local") -> tuple[Mock, Mock]:
    """
    Create a mock filesystem for testing.
    
    Args:
        fs_type: Type of filesystem to mock
        
    Returns:
        Tuple of (mock_get_filesystem, mock_filesystem)
    """
    mock_fs = MagicMock()
    mock_get_fs = Mock(return_value=(mock_fs, fs_type))
    return mock_get_fs, mock_fs


def create_mock_config(base_project: str = "chainedpy", 
                      summary: str = "Test project") -> Dict[str, str]:
    """
    Create a mock project configuration.
    
    Args:
        base_project: Base project value
        summary: Summary value
        
    Returns:
        Mock configuration dictionary
    """
    return {
        'base_project': base_project,
        'summary': summary
    }


def create_mock_credentials(credential_type: str = "github") -> Dict[str, str]:
    """Create mock credentials for testing.

    :param credential_type: Type of credentials (github, gitlab, etc.), defaults to "github".
    :type credential_type: str, optional
    :return Dict[str, str]: Mock credentials dictionary.
    """
    # @@ STEP 1: Define credentials mapping. @@
    credentials_map = {
        'github': {'github_token': 'test_github_token'},
        'gitlab': {'gitlab_token': 'test_gitlab_token'},
        'ftp': {'ftp_username': 'test_user', 'ftp_password': 'test_pass'},
        'sftp': {'sftp_username': 'test_user', 'sftp_password': 'test_pass'},
        'empty': {}
    }

    # @@ STEP 2: Return credentials for requested type. @@
    return credentials_map.get(credential_type, {})


def create_mock_chain_traversal(project_configs: Dict[str, Dict[str, str]]) -> tuple[Mock, Mock]:
    """Create mocks for chain traversal operations.

    :param project_configs: Dictionary mapping project paths to their configs.
    :type project_configs: Dict[str, Dict[str, str]]
    :return tuple[Mock, Mock]: Tuple of (mock_get_filesystem, mock_read_config).
    """
    # @@ STEP 1: Define filesystem side effect function. @@
    def filesystem_side_effect(path, _):
        if "github.com" in path or "gitlab.com" in path:
            return MagicMock(), "github"
        return MagicMock(), "local"

    # @@ STEP 2: Define config side effect function. @@
    def config_side_effect(_, path, creds=None):
        for project_path, config in project_configs.items():
            if project_path in path:
                return config
        return create_mock_config()

    # @@ STEP 3: Create mock objects with side effects. @@
    mock_get_fs = Mock(side_effect=filesystem_side_effect)
    mock_read_config = Mock(side_effect=config_side_effect)

    # @@ STEP 4: Return mock objects. @@
    return mock_get_fs, mock_read_config


def create_mock_cli_exit(exit_code: int = 0) -> Mock:
    """Create a mock SystemExit for CLI testing.

    :param exit_code: Exit code to mock, defaults to 0.
    :type exit_code: int, optional
    :return Mock: Mock SystemExit object.
    """
    # @@ STEP 1: Create mock SystemExit object. @@
    mock_exit = Mock()
    mock_exit.value.code = exit_code

    # @@ STEP 2: Return mock exit object. @@
    return mock_exit


def create_mock_logger() -> Mock:
    """Create a mock logger for testing.

    :return Mock: Mock logger with all logging methods.
    """
    # @@ STEP 1: Create mock logger with all logging methods. @@
    mock_logger = Mock()
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.critical = Mock()

    # @@ STEP 2: Return configured mock logger. @@
    return mock_logger


def create_mock_project_config(base_project: str = "chainedpy",
                             summary: str = "Test project") -> Mock:
    """Create a mock ProjectConfig object.

    :param base_project: Base project value, defaults to "chainedpy".
    :type base_project: str, optional
    :param summary: Summary value, defaults to "Test project".
    :type summary: str, optional
    :return Mock: Mock ProjectConfig object.
    """
    # @@ STEP 1: Create mock config with specified values. @@
    mock_config = Mock()
    mock_config.base_project = base_project
    mock_config.summary = summary

    # @@ STEP 2: Return configured mock config. @@
    return mock_config


def create_failing_mock(exception_type: type = Exception,
                       message: str = "Mock failure") -> Mock:
    """Create a mock that raises an exception when called.

    :param exception_type: Type of exception to raise, defaults to Exception.
    :type exception_type: type, optional
    :param message: Exception message, defaults to "Mock failure".
    :type message: str, optional
    :return Mock: Mock that raises exception.
    """
    # @@ STEP 1: Create mock with exception side effect. @@
    mock = Mock()
    mock.side_effect = exception_type(message)

    # @@ STEP 2: Return failing mock. @@
    return mock


def create_async_mock(return_value: Any = None) -> AsyncMock:
    """Create an async mock for testing async functions.

    :param return_value: Value to return from async mock, defaults to None.
    :type return_value: Any, optional
    :return AsyncMock: AsyncMock object.
    """
    # @@ STEP 1: Create async mock. @@
    mock = AsyncMock()

    # @@ STEP 2: Set return value if provided. @@
    if return_value is not None:
        mock.return_value = return_value

    # @@ STEP 3: Return configured async mock. @@
    return mock


def patch_multiple_functions(patches: Dict[str, Any]) -> Dict[str, Mock]:
    """
    Create multiple patches for testing.
    
    Args:
        patches: Dictionary mapping function paths to mock values/side effects
        
    Returns:
        Dictionary mapping function names to mock objects
    """
    mocks = {}
    
    for func_path, mock_value in patches.items():
        if callable(mock_value):
            mock = Mock(side_effect=mock_value)
        else:
            mock = Mock(return_value=mock_value)
        
        # Extract function name from path
        func_name = func_path.split('.')[-1]
        mocks[func_name] = mock
    
    return mocks


def create_mock_file_operations() -> Dict[str, Mock]:
    """
    Create mocks for common file operations.
    
    Returns:
        Dictionary with mocked file operation functions
    """
    return {
        'read_text': Mock(return_value="test content"),
        'write_text': Mock(),
        'exists': Mock(return_value=True),
        'mkdir': Mock(),
        'unlink': Mock(),
        'chmod': Mock()
    }


def create_mock_subprocess(returncode: int = 0, stdout: str = "", 
                         stderr: str = "") -> Mock:
    """
    Create a mock subprocess result.
    
    Args:
        returncode: Return code to mock
        stdout: Standard output to mock
        stderr: Standard error to mock
        
    Returns:
        Mock subprocess result
    """
    mock_result = Mock()
    mock_result.returncode = returncode
    mock_result.stdout = stdout
    mock_result.stderr = stderr
    return mock_result


def create_mock_http_response(status_code: int = 200, content: str = "",
                            headers: Optional[Dict[str, str]] = None) -> Mock:
    """
    Create a mock HTTP response.
    
    Args:
        status_code: HTTP status code
        content: Response content
        headers: Response headers
        
    Returns:
        Mock HTTP response
    """
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.text = content
    mock_response.content = content.encode()
    mock_response.headers = headers or {}
    return mock_response


def create_mock_cache_info(chain_name: str = "test_chain", 
                         size_mb: float = 1.0,
                         is_expired: bool = False) -> Mock:
    """
    Create a mock CachedChainInfo object.
    
    Args:
        chain_name: Name of cached chain
        size_mb: Size in MB
        is_expired: Whether cache is expired
        
    Returns:
        Mock CachedChainInfo object
    """
    mock_info = Mock()
    mock_info.chain_name = chain_name
    mock_info.size_mb = size_mb
    mock_info.is_expired = is_expired
    mock_info.cache_path = f"/tmp/cache/{chain_name}"
    return mock_info


def create_mock_environment_variables(env_vars: Dict[str, str]) -> Mock:
    """
    Create a mock for environment variables.
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        Mock that behaves like os.environ
    """
    mock_env = Mock()
    mock_env.get = lambda key, default=None: env_vars.get(key, default)
    mock_env.__getitem__ = lambda key: env_vars[key]
    mock_env.__contains__ = lambda key: key in env_vars
    return mock_env


def create_conditional_mock(condition_func: Callable, 
                          true_value: Any, false_value: Any) -> Mock:
    """
    Create a mock that returns different values based on a condition.
    
    Args:
        condition_func: Function that determines which value to return
        true_value: Value to return when condition is True
        false_value: Value to return when condition is False
        
    Returns:
        Mock with conditional behavior
    """
    def side_effect(*args, **kwargs):
        if condition_func(*args, **kwargs):
            return true_value
        return false_value
    
    mock = Mock(side_effect=side_effect)
    return mock


def create_call_counting_mock(max_calls: int = 1) -> Mock:
    """
    Create a mock that tracks call count and can fail after max calls.
    
    Args:
        max_calls: Maximum number of calls before failing
        
    Returns:
        Mock with call counting behavior
    """
    call_count = {'count': 0}
    
    def side_effect(*args, **kwargs):
        call_count['count'] += 1
        if call_count['count'] > max_calls:
            raise Exception(f"Mock called too many times: {call_count['count']}")
        return f"call_{call_count['count']}"
    
    mock = Mock(side_effect=side_effect)
    mock.call_count = call_count
    return mock


def create_mock_with_attributes(**attributes) -> Mock:
    """
    Create a mock with specified attributes.
    
    Args:
        **attributes: Attributes to set on the mock
        
    Returns:
        Mock with specified attributes
    """
    mock = Mock()
    for name, value in attributes.items():
        setattr(mock, name, value)
    return mock
