"""
Assertion helpers for ChainedPy tests.

Provides specialized assertion utilities for testing
following ChainedPy's service patterns.
"""
from __future__ import annotations

# 1. Standard library imports
import re
from pathlib import Path
from typing import Any, List, Dict, Optional, Union, Pattern, Callable

# 2. Third-party imports
import pytest

# 3. Internal constants
from chainedpy.constants import CONFIG_FILE_NAME

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils

# 5. ChainedPy internal modules
# (none)

# 6. Test utilities
from tests.services.project_test_service import read_project_config


def assert_file_exists_with_content(file_path: Path, expected_content: Union[str, List[str], Pattern]) -> None:
    """Assert that a file exists and contains expected content.

    :param file_path: Path to file to check.
    :type file_path: Path
    :param expected_content: String, list of strings, or regex pattern to match.
    :type expected_content: Union[str, List[str], Pattern]
    :raises AssertionError: If file doesn't exist or doesn't contain expected content.
    """
    # @@ STEP 1: Verify file exists and is a file. @@
    assert file_path.exists(), f"File does not exist: {file_path}"
    assert file_path.is_file(), f"Path is not a file: {file_path}"

    # @@ STEP 2: Read file content. @@
    content = fs_utils.read_text(str(file_path))

    # @@ STEP 3: Check content based on expected type. @@
    if isinstance(expected_content, Pattern):
        assert expected_content.search(content), \
            f"File {file_path} does not match pattern: {expected_content.pattern}"
    elif isinstance(expected_content, list):
        for expected in expected_content:
            assert expected in content, \
                f"File {file_path} does not contain: '{expected}'"
    else:
        assert expected_content in content, \
            f"File {file_path} does not contain: '{expected_content}'"


def assert_file_not_contains(file_path: Path, unexpected_content: Union[str, List[str]]) -> None:
    """
    Assert that a file does not contain unexpected content.
    
    Args:
        file_path: Path to file to check
        unexpected_content: String or list of strings that should not be in file
        
    Raises:
        AssertionError: If file contains unexpected content
    """
    assert file_path.exists(), f"File does not exist: {file_path}"

    content = fs_utils.read_text(str(file_path))
    
    if isinstance(unexpected_content, list):
        for unexpected in unexpected_content:
            assert unexpected not in content, \
                f"File {file_path} unexpectedly contains: '{unexpected}'"
    else:
        assert unexpected_content not in content, \
            f"File {file_path} unexpectedly contains: '{unexpected_content}'"


def assert_directory_structure(base_path: Path, expected_structure: Dict[str, Any]) -> None:
    """
    Assert that a directory has the expected structure.
    
    Args:
        base_path: Base directory path
        expected_structure: Dictionary describing expected structure
                          - Keys are file/directory names
                          - Values are None (file), {} (empty dir), or dict (substructure)
        
    Raises:
        AssertionError: If directory structure doesn't match expected
    """
    assert base_path.exists(), f"Base directory does not exist: {base_path}"
    assert base_path.is_dir(), f"Base path is not a directory: {base_path}"
    
    for name, expected_type in expected_structure.items():
        item_path = base_path / name
        
        if expected_type is None:
            # Expected to be a file
            assert item_path.exists(), f"Expected file does not exist: {item_path}"
            assert item_path.is_file(), f"Expected file is not a file: {item_path}"
        elif isinstance(expected_type, dict):
            # Expected to be a directory with substructure
            assert item_path.exists(), f"Expected directory does not exist: {item_path}"
            assert item_path.is_dir(), f"Expected directory is not a directory: {item_path}"
            
            if expected_type:  # Non-empty dict means check substructure
                assert_directory_structure(item_path, expected_type)
        else:
            # Expected to be an empty directory
            assert item_path.exists(), f"Expected directory does not exist: {item_path}"
            assert item_path.is_dir(), f"Expected directory is not a directory: {item_path}"


def assert_project_structure(project_path: Path, project_name: Optional[str] = None) -> None:
    """Assert that a project has the standard ChainedPy structure.

    :param project_path: Path to project directory.
    :type project_path: Path
    :param project_name: Optional project name (defaults to directory name), defaults to None.
    :type project_name: Optional[str], optional
    :raises AssertionError: If project structure is invalid.
    :return None: None
    """
    # @@ STEP 1: Determine project name. @@
    if project_name is None:
        project_name = project_path.name

    # @@ STEP 2: Define expected project structure. @@
    expected_structure = {
        CONFIG_FILE_NAME: None,
        "__init__.py": None,
        f"{project_name}_chain.py": None,
        f"{project_name}_chain.pyi": None,
        "plugins": {
            "then": {},
            "as_": {},
            "processors": {}
        }
    }

    # @@ STEP 3: Assert directory structure matches expected. @@
    assert_directory_structure(project_path, expected_structure)


def assert_config_values(project_path: Path, expected_base: str, expected_summary: str) -> None:
    """Assert that project configuration has expected values.

    :param project_path: Path to project directory.
    :type project_path: Path
    :param expected_base: Expected base project value.
    :type expected_base: str
    :param expected_summary: Expected summary value.
    :type expected_summary: str
    :raises AssertionError: If config values don't match.
    :return None: None
    """
    # @@ STEP 1: Read project configuration. @@
    config = read_project_config(project_path)

    # @@ STEP 2: Assert base project value matches. @@
    assert config.base_project == expected_base, \
        f"Expected base_project '{expected_base}', got '{config.base_project}'"

    # @@ STEP 3: Assert summary value matches. @@
    assert config.summary == expected_summary, \
        f"Expected summary '{expected_summary}', got '{config.summary}'"


def assert_exception_with_message(exception_type: type, expected_message: str,
                                callable_func: Callable, *args, **kwargs) -> None:
    """Assert that a function raises a specific exception with expected message.

    :param exception_type: Type of exception expected.
    :type exception_type: type
    :param expected_message: Expected message in exception (supports regex patterns).
    :type expected_message: str
    :param callable_func: Function to call.
    :type callable_func: Callable
    :param args: Arguments for function.
    :type args: Any
    :param kwargs: Keyword arguments for function.
    :type kwargs: Any
    :raises AssertionError: If exception is not raised or message doesn't match.
    :return None: None
    """
    # @@ STEP 1: Execute function and capture exception. @@
    with pytest.raises(exception_type) as exc_info:
        callable_func(*args, **kwargs)

    # @@ STEP 2: Get actual exception message. @@
    actual_message = str(exc_info.value)

    # @@ STEP 3: Check if expected message is regex or literal. @@
    regex_metacharacters = r'[.*+?^${}()|[\]\\]'
    if re.search(regex_metacharacters, expected_message):
        # || S.S. 3.1: Treat as regex pattern. ||
        if not re.search(expected_message, actual_message):
            raise AssertionError(
                f"Expected message pattern '{expected_message}' not found in: {actual_message}"
            )
    else:
        # || S.S. 3.2: Treat as literal string. ||
        if expected_message not in actual_message:
            raise AssertionError(
                f"Expected message '{expected_message}' not found in: {actual_message}"
            )


def assert_logs_contain_messages(caplog, expected_messages: List[str],
                               log_level: Optional[str] = None) -> None:
    """Assert that logs contain all expected messages.

    :param caplog: pytest caplog fixture.
    :type caplog: pytest.LoggingPlugin
    :param expected_messages: List of expected log messages.
    :type expected_messages: List[str]
    :param log_level: Optional log level to filter by, defaults to None.
    :type log_level: Optional[str], optional
    :raises AssertionError: If any expected message is not found.
    :return None: None
    """
    # @@ STEP 1: Get log records. @@
    records = caplog.records

    # @@ STEP 2: Filter by log level if specified. @@
    if log_level:
        records = [r for r in records if r.levelname == log_level.upper()]

    # @@ STEP 3: Extract log messages. @@
    log_messages = [record.message for record in records]

    # @@ STEP 4: Check each expected message is found. @@
    for expected_message in expected_messages:
        found = any(expected_message in message for message in log_messages)
        assert found, f"Expected log message '{expected_message}' not found in: {log_messages}"


def assert_no_error_logs(caplog) -> None:
    """Assert that no ERROR level logs were generated.

    :param caplog: pytest caplog fixture.
    :type caplog: pytest.LoggingPlugin
    :raises AssertionError: If ERROR logs are found.
    :return None: None
    """
    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert not error_records, f"Unexpected ERROR logs found: {[r.message for r in error_records]}"


def assert_cli_success(exit_info, expected_messages: Optional[List[str]] = None) -> None:
    """Assert that CLI command succeeded.

    :param exit_info: pytest SystemExit exception info.
    :type exit_info: pytest.ExceptionInfo
    :param expected_messages: Optional list of expected success messages, defaults to None.
    :type expected_messages: Optional[List[str]], optional
    :raises AssertionError: If CLI command failed.
    :return None: None
    """
    # @@ STEP 1: Check exit code is 0 for success. @@
    assert exit_info.value.code == 0, f"CLI command failed with exit code: {exit_info.value.code}"


def assert_cli_failure(exit_info, expected_error_code: int = 1) -> None:
    """Assert that CLI command failed with expected error code.

    :param exit_info: pytest SystemExit exception info.
    :type exit_info: pytest.ExceptionInfo
    :param expected_error_code: Expected error code, defaults to 1.
    :type expected_error_code: int, optional
    :raises AssertionError: If CLI command didn't fail as expected.
    :return None: None
    """
    # @@ STEP 1: Check exit code matches expected failure code. @@
    assert exit_info.value.code == expected_error_code, \
        f"Expected exit code {expected_error_code}, got {exit_info.value.code}"


def assert_cli_output_contains(capsys, expected_messages: List[str],
                             check_stderr: bool = True) -> None:
    """Assert that CLI output contains expected messages.

    :param capsys: pytest capsys fixture.
    :type capsys: pytest.CaptureFixture
    :param expected_messages: List of expected messages.
    :type expected_messages: List[str]
    :param check_stderr: Whether to check stderr in addition to stdout, defaults to True.
    :type check_stderr: bool, optional
    :raises AssertionError: If expected messages are not found.
    :return None: None
    """
    # @@ STEP 1: Capture CLI output. @@
    captured = capsys.readouterr()
    output = captured.out

    # @@ STEP 2: Include stderr if requested. @@
    if check_stderr:
        output += captured.err

    # @@ STEP 3: Check each expected message is present. @@
    for message in expected_messages:
        assert message in output, f"Expected message '{message}' not found in CLI output"


def assert_remote_validation_success(capsys) -> None:
    """Assert that remote project validation succeeded.

    :param capsys: pytest capsys fixture.
    :type capsys: pytest.CaptureFixture
    :raises AssertionError: If remote validation failed.
    :return None: None
    """
    # @@ STEP 1: Capture CLI output. @@
    captured = capsys.readouterr()
    output = captured.out + captured.err

    # @@ STEP 2: Check for successful validation message. @@
    assert "✅ Validated remote base project" in output, \
        "Expected successful remote project validation message"


def assert_remote_validation_failure(capsys) -> None:
    """Assert that remote project validation failed.

    :param capsys: pytest capsys fixture.
    :type capsys: pytest.CaptureFixture
    :raises AssertionError: If validation didn't fail as expected.
    :return None: None
    """
    # @@ STEP 1: Capture CLI output. @@
    captured = capsys.readouterr()
    output = captured.out + captured.err

    # @@ STEP 2: Check for failure messages. @@
    assert "not a valid ChainedPy project" in output, \
        "Expected failed remote project validation message"
    assert "missing chainedpy.yaml" in output, \
        "Expected missing config file error message"


def assert_plugin_signature_in_stub(stub_file: Path, plugin_name: str,
                                  expected_signature: Optional[str] = None) -> None:
    """Assert that plugin signature is correctly generated in stub file.

    :param stub_file: Path to stub file.
    :type stub_file: Path
    :param plugin_name: Name of plugin to check.
    :type plugin_name: str
    :param expected_signature: Optional expected signature pattern, defaults to None.
    :type expected_signature: Optional[str], optional
    :raises AssertionError: If plugin signature is not found or incorrect.
    :return None: None
    """
    # @@ STEP 1: Verify stub file exists. @@
    assert stub_file.exists(), f"Stub file does not exist: {stub_file}"

    # @@ STEP 2: Read stub file content. @@
    content = stub_file.read_text(encoding='utf-8')

    # @@ STEP 3: Check that plugin method is defined. @@
    assert f"def {plugin_name}(" in content, \
        f"Plugin method '{plugin_name}' not found in stub file"

    # @@ STEP 4: Check expected signature if provided. @@
    if expected_signature:
        assert expected_signature in content, \
            f"Expected signature '{expected_signature}' not found in stub file"


def assert_chain_file_imports(chain_file: Path, expected_base_import: str) -> None:
    """Assert that chain file has correct imports.

    :param chain_file: Path to chain file.
    :type chain_file: Path
    :param expected_base_import: Expected base import statement.
    :type expected_base_import: str
    :raises AssertionError: If imports are incorrect.
    :return None: None
    """
    # @@ STEP 1: Verify chain file exists. @@
    assert chain_file.exists(), f"Chain file does not exist: {chain_file}"

    # @@ STEP 2: Read file content and check for expected import. @@
    content = chain_file.read_text(encoding='utf-8')
    assert expected_base_import in content, \
        f"Expected import '{expected_base_import}' not found in chain file"


def assert_circular_dependency_error(func: Callable, *args, **kwargs) -> None:
    """Assert that function raises circular dependency error.

    :param func: Function to call.
    :type func: Callable
    :param args: Arguments for function.
    :type args: Any
    :param kwargs: Keyword arguments for function.
    :type kwargs: Any
    :raises AssertionError: If circular dependency error is not raised.
    :return None: None
    """
    # @@ STEP 1: Assert that function raises circular dependency error. @@
    assert_exception_with_message(
        ValueError, "Circular dependency", func, *args, **kwargs
    )
