"""
Assertion test service for ChainedPy tests.

Provides centralized assertion helpers and validation utilities
for testing, following ChainedPy's service patterns.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union


from .project_test_service import get_project_files


class AssertionTestServiceError(Exception):
    """Exception raised when assertion test operations fail."""
    pass


class ProjectAssertionService:
    """Service for project-related assertions.

    :raises Exception: If project assertion service operations fail.
    """

    @staticmethod
    def assert_project_exists(project_path: Path) -> None:
        """Assert that a project directory exists.

        :param project_path: Path to project directory.
        :type project_path: Path
        :raises AssertionError: If project does not exist.
        :return None: None
        """
        # @@ STEP 1: Verify project directory exists and is a directory. @@
        assert project_path.exists(), f"Project directory does not exist: {project_path}"
        assert project_path.is_dir(), f"Project path is not a directory: {project_path}"

    @staticmethod
    def assert_project_structure(project_path: Path) -> None:
        """Assert that a project has the expected file structure.

        :param project_path: Path to project directory.
        :type project_path: Path
        :raises AssertionError: If project structure is invalid.
        :return None: None
        """
        # @@ STEP 1: Verify project exists. @@
        ProjectAssertionService.assert_project_exists(project_path)
        # @@ STEP 2: Get project files. @@
        files = get_project_files(project_path)

        # @@ STEP 3: Assert required files exist. @@
        assert files['config'].exists(), f"Config file missing: {files['config']}"
        assert files['init'].exists(), f"Init file missing: {files['init']}"
        assert files['chain'].exists(), f"Chain file missing: {files['chain']}"
        assert files['stub'].exists(), f"Stub file missing: {files['stub']}"

        # @@ STEP 4: Assert required directories exist. @@
        assert files['plugins_dir'].exists(), f"Plugins directory missing: {files['plugins_dir']}"
        assert files['then_dir'].exists(), f"Then plugins directory missing: {files['then_dir']}"
        assert files['as_dir'].exists(), f"As plugins directory missing: {files['as_dir']}"
        processors_dir_msg = f"Processors directory missing: {files['processors_dir']}"
        assert files['processors_dir'].exists(), processors_dir_msg

    @staticmethod
    def assert_config_values(project_path: Path, expected_base_project: str,
                           expected_summary: str) -> None:
        """Assert that project configuration has expected values.

        :param project_path: Path to project directory.
        :type project_path: Path
        :param expected_base_project: Expected base project value.
        :type expected_base_project: str
        :param expected_summary: Expected summary value.
        :type expected_summary: str
        :raises AssertionError: If config values don't match expected.
        :return None: None
        """
        # @@ STEP 1: Import and read project config. @@
        from .project_test_service import read_project_config

        config = read_project_config(project_path)

        # @@ STEP 2: Assert base project matches. @@
        assert config.base_project == expected_base_project, \
            f"Expected base_project '{expected_base_project}', got '{config.base_project}'"

        # @@ STEP 3: Assert summary matches. @@
        assert config.summary == expected_summary, \
            f"Expected summary '{expected_summary}', got '{config.summary}'"

    @staticmethod
    def assert_file_contains(file_path: Path, expected_content: Union[str, List[str]]) -> None:
        """Assert that a file contains expected content.

        :param file_path: Path to file to check.
        :type file_path: Path
        :param expected_content: String or list of strings that should be in file.
        :type expected_content: Union[str, List[str]]
        :raises AssertionError: If file doesn't contain expected content.
        :return None: None
        """
        # @@ STEP 1: Verify file exists. @@
        assert file_path.exists(), f"File does not exist: {file_path}"

        # @@ STEP 2: Read file content. @@
        from chainedpy.services import filesystem_service as fs_utils
        content = fs_utils.read_text(str(file_path))

        # @@ STEP 3: Normalize expected content to list. @@
        if isinstance(expected_content, str):
            expected_content = [expected_content]

        # @@ STEP 4: Check each expected string is in content. @@
        for expected in expected_content:
            assert expected in content, \
                f"File {file_path} does not contain expected content: '{expected}'"

    @staticmethod
    def assert_file_not_contains(file_path: Path, unexpected_content: Union[str, List[str]]) -> None:
        """Assert that a file does not contain unexpected content.

        :param file_path: Path to file to check.
        :type file_path: Path
        :param unexpected_content: String or list of strings that should not be in file.
        :type unexpected_content: Union[str, List[str]]
        :raises AssertionError: If file contains unexpected content.
        :return None: None
        """
        # @@ STEP 1: Verify file exists. @@
        assert file_path.exists(), f"File does not exist: {file_path}"

        # @@ STEP 2: Read file content. @@
        from chainedpy.services import filesystem_service as fs_utils
        content = fs_utils.read_text(str(file_path))

        # @@ STEP 3: Normalize unexpected content to list. @@
        if isinstance(unexpected_content, str):
            unexpected_content = [unexpected_content]

        # @@ STEP 4: Check each unexpected string is not in content. @@
        for unexpected in unexpected_content:
            assert unexpected not in content, \
                f"File {file_path} contains unexpected content: '{unexpected}'"


class ErrorAssertionService:
    """Service for error-related assertions.

    :raises Exception: If error assertion service operations fail.
    """

    @staticmethod
    def assert_exception_raised(exception_type: type, expected_message: str,
                              callable_func: callable, *args, **kwargs) -> None:
        """Assert that a specific exception is raised with expected message.

        :param exception_type: Type of exception expected.
        :type exception_type: type
        :param expected_message: Expected message in exception.
        :type expected_message: str
        :param callable_func: Function to call that should raise exception.
        :type callable_func: callable
        :param args: Arguments to pass to callable_func.
        :param kwargs: Keyword arguments to pass to callable_func.
        :raises AssertionError: If exception is not raised or message doesn't match.
        :return None: None
        """
        try:
            callable_func(*args, **kwargs)
            assert False, f"Expected {exception_type.__name__} to be raised"
        except exception_type as e:
            assert expected_message in str(e), \
                f"Expected message '{expected_message}' not found in exception: {str(e)}"
        except Exception as e:
            assert False, f"Expected {exception_type.__name__}, got {type(e).__name__}: {str(e)}"
    
    @staticmethod
    def assert_logs_contain(caplog, expected_messages: List[str],
                          log_level: Optional[str] = None) -> None:
        """Assert that logs contain expected messages.

        :param caplog: pytest caplog fixture.
        :type caplog: pytest.LoggingPlugin
        :param expected_messages: List of expected log messages.
        :type expected_messages: List[str]
        :param log_level: Optional log level to filter by, defaults to None.
        :type log_level: Optional[str], optional
        :raises AssertionError: If expected messages are not found in logs.
        :return None: None
        """
        # @@ STEP 1: Get log records. @@
        log_records = caplog.records

        # @@ STEP 2: Filter by log level if specified. @@
        if log_level:
            log_records = [r for r in log_records if r.levelname == log_level.upper()]

        # @@ STEP 3: Extract log messages. @@
        log_messages = [record.message for record in log_records]

        # @@ STEP 4: Check each expected message is found. @@
        for expected_message in expected_messages:
            found = any(expected_message in message for message in log_messages)
            assert found, (
                f"Expected log message '{expected_message}' not found in logs: {log_messages}"
            )

    @staticmethod
    def assert_no_silent_failures(caplog) -> None:
        """Assert that there are no silent failures (errors without proper logging).

        :param caplog: pytest caplog fixture.
        :type caplog: pytest.LoggingPlugin
        :raises AssertionError: If silent failures are detected.
        :return None: None
        """
        # @@ STEP 1: Check that any ERROR level logs are properly formatted. @@
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]

        # @@ STEP 2: Validate each error record. @@
        for record in error_records:
            # || S.S. 2.1: Error messages should not be empty. ||
            assert record.message.strip(), f"Empty error message found: {record}"

            # || S.S. 2.2: Error messages should contain meaningful information. ||
            assert len(record.message.strip()) > 10, \
                f"Error message too short (possible silent failure): {record.message}"


class CLIAssertionService:
    """Service for CLI-related assertions.

    :raises Exception: If CLI assertion service operations fail.
    """

    @staticmethod
    def assert_cli_success(exit_info, capsys, expected_messages: Optional[List[str]] = None) -> None:
        """Assert that CLI command succeeded.

        :param exit_info: pytest SystemExit exception info.
        :type exit_info: pytest.ExceptionInfo
        :param capsys: pytest capsys fixture.
        :type capsys: pytest.CaptureFixture
        :param expected_messages: Optional list of expected success messages, defaults to None.
        :type expected_messages: Optional[List[str]], optional
        :raises AssertionError: If CLI command did not succeed.
        :return None: None
        """
        # @@ STEP 1: Assert exit code is 0 (success). @@
        assert exit_info.value.code == 0, f"CLI command failed with exit code: {exit_info.value.code}"

        # @@ STEP 2: Check expected messages if provided. @@
        if expected_messages:
            # || S.S. 2.1: Capture output. ||
            captured = capsys.readouterr()
            output = captured.out + captured.err

            # || S.S. 2.2: Check each expected message is in output. ||
            for message in expected_messages:
                assert message in output, f"Expected message '{message}' not found in CLI output"
    @staticmethod
    def assert_cli_failure(exit_info, capsys,
                          expected_error_messages: Optional[List[str]] = None) -> None:
        """Assert that CLI command failed.

        :param exit_info: pytest SystemExit exception info.
        :type exit_info: pytest.ExceptionInfo
        :param capsys: pytest capsys fixture.
        :type capsys: pytest.CaptureFixture
        :param expected_error_messages: Optional list of expected error messages, defaults to None.
        :type expected_error_messages: Optional[List[str]], optional
        :raises AssertionError: If CLI command did not fail as expected.
        :return None: None
        """
        # @@ STEP 1: Assert exit code is not 0 (failure). @@
        assert exit_info.value.code != 0, (
            f"CLI command unexpectedly succeeded with exit code: {exit_info.value.code}"
        )

        # @@ STEP 2: Check expected error messages if provided. @@
        if expected_error_messages:
            # || S.S. 2.1: Capture error output. ||
            captured = capsys.readouterr()
            error_output = captured.err

            # || S.S. 2.2: Check each expected error message is in output. ||
            for message in expected_error_messages:
                assert message in error_output, (
                    f"Expected error message '{message}' not found in CLI error output"
                )


class RemoteRepositoryAssertionService:
    """Service for remote repository-related assertions.

    :raises Exception: If remote repository assertion service operations fail.
    """

    @staticmethod
    def assert_remote_project_validation(capsys, should_succeed: bool = True) -> None:
        """Assert remote project validation results.

        :param capsys: pytest capsys fixture.
        :type capsys: pytest.CaptureFixture
        :param should_succeed: Whether validation should succeed, defaults to True.
        :type should_succeed: bool, optional
        :raises AssertionError: If validation result doesn't match expected.
        :return None: None
        """
        # @@ STEP 1: Capture output. @@
        captured = capsys.readouterr()
        output = captured.out + captured.err

        # @@ STEP 2: Check validation result based on expected outcome. @@
        if should_succeed:
            # || S.S. 2.1: Assert successful validation message. ||
            assert "✅ Validated remote base project" in output, \
                "Expected successful remote project validation message"
        else:
            # || S.S. 2.2: Assert failed validation messages. ||
            assert "not a valid ChainedPy project" in output, \
                "Expected failed remote project validation message"
            assert "missing chainedpy.yaml" in output, \
                "Expected missing config file error message"
