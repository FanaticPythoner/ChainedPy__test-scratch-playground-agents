"""
CLI fixtures for ChainedPy tests.

Provides centralized CLI testing utilities and fixtures
following ChainedPy's service patterns.
"""
from __future__ import annotations

# 1. Standard library imports
import sys
from io import StringIO
from typing import Dict, List, Optional, Any

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
# (none)

# 5. ChainedPy internal modules
from chainedpy.cli import main

# 6. Test utilities
from tests.services.data_test_service import TestDataFactory


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing ChainedPy CLI commands.

    :return Callable: Function to run CLI commands and capture results.
    :raises Exception: If CLI command execution fails unexpectedly.
    """
    def run_cli_command(args: List[str], expect_exit: bool = True) -> Dict[str, Any]:
        """Run a CLI command and capture results.

        :param args: List of command line arguments.
        :type args: List[str]
        :param expect_exit: Whether to expect SystemExit, defaults to True.
        :type expect_exit: bool, optional
        :raises Exception: If command execution fails unexpectedly.
        :return Dict[str, Any]: Dictionary with exit_code, stdout, stderr, and exception info.
        """
        # @@ STEP 1: Capture stdout and stderr. @@
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            # || S.S. 1.1: Redirect output streams. ||
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # @@ STEP 2: Execute CLI command. @@
            if expect_exit:
                # || S.S. 2.1: Execute with expected SystemExit. ||
                with pytest.raises(SystemExit) as exc_info:
                    main(args)
                exit_code = exc_info.value.code
                exception = exc_info
            else:
                # || S.S. 2.2: Execute without expected SystemExit. ||
                main(args)
                exit_code = 0
                exception = None

        except Exception as e:
            # @@ STEP 3: Handle unexpected exceptions. @@
            exit_code = 1
            exception = e
        finally:
            # @@ STEP 4: Restore original output streams. @@
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # @@ STEP 5: Return captured results. @@
        return {
            'exit_code': exit_code,
            'stdout': stdout_capture.getvalue(),
            'stderr': stderr_capture.getvalue(),
            'exception': exception
        }

    yield run_cli_command


@pytest.fixture
def cli_commands():
    """Get standard CLI command examples for testing.

    :return Dict[str, List[str]]: Dictionary mapping command types to argument lists.
    :raises Exception: If test data factory fails to create examples.
    """
    # @@ STEP 1: Create CLI command examples using test data factory. @@
    commands = TestDataFactory.create_cli_command_examples()

    # @@ STEP 2: Yield commands for test usage. @@
    yield commands


@pytest.fixture
def mock_cli_environment(monkeypatch, temp_workspace):
    """Create a mocked CLI environment for testing.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: Any
    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return: Dictionary with environment setup.
    :raises OSError: If directory creation fails.
    """
    # @@ STEP 1: Set up environment variables. @@
    env_vars = {
        'CHAINEDPY_ACTIVE_PROJECT': '',
        'CHAINEDPY_PROJECT_NAME': '',
        'CHAINEDPY_PROJECT_STACK': '',
        'HOME': str(temp_workspace),
        'USERPROFILE': str(temp_workspace)  # For Windows
    }

    # || S.S. 1.1: Apply environment variables using monkeypatch. ||
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # @@ STEP 2: Create home directory structure. @@
    home_dir = temp_workspace / 'home'
    home_dir.mkdir(exist_ok=True)

    # @@ STEP 3: Create chainedpy config directory. @@
    chainedpy_dir = home_dir / '.chainedpy'
    chainedpy_dir.mkdir(exist_ok=True)

    # @@ STEP 4: Yield environment setup dictionary. @@
    yield {
        'workspace': temp_workspace,
        'home_dir': home_dir,
        'chainedpy_dir': chainedpy_dir,
        'env_vars': env_vars
    }


@pytest.fixture
def cli_with_credentials(mock_cli_environment):
    """Create CLI environment with credential files.

    :param mock_cli_environment: Mock CLI environment fixture.
    :type mock_cli_environment: Dict[str, Any]
    :return Dict[str, Any]: Dictionary with CLI environment and credential files.
    :raises OSError: If credential file creation fails.
    """
    # @@ STEP 1: Get environment data from mock CLI environment. @@
    env_data = mock_cli_environment

    # @@ STEP 2: Create .env file with credentials. @@
    env_file = env_data['workspace'] / '.env'
    env_content = """GITHUB_TOKEN=test_github_token
GITLAB_TOKEN=test_gitlab_token
GITLAB_PRIVATE_TOKEN=test_gitlab_private_token
FTP_USERNAME=test_ftp_user
FTP_PASSWORD=test_ftp_pass
"""
    # || S.S. 2.1: Write environment file content. ||
    env_file.write_text(env_content)

    # @@ STEP 3: Create .chainedpy.env file. @@
    chainedpy_env_file = env_data['home_dir'] / '.chainedpy.env'
    chainedpy_env_content = """GITHUB_TOKEN=chainedpy_github_token
GITLAB_TOKEN=chainedpy_gitlab_token
"""
    # || S.S. 3.1: Write chainedpy environment file content. ||
    chainedpy_env_file.write_text(chainedpy_env_content)

    # @@ STEP 4: Update environment data with credential files. @@
    env_data.update({
        'env_file': env_file,
        'chainedpy_env_file': chainedpy_env_file
    })

    # @@ STEP 5: Yield updated environment data. @@
    yield env_data


@pytest.fixture
def cli_help_tester():
    """Create a helper for testing CLI help messages.

    :return Callable: Function to test help messages.
    :raises SystemExit: When help command is executed.
    """
    def test_help_message(command: List[str], expected_content: List[str]) -> Dict[str, str]:
        """Test that help message contains expected content.

        :param command: CLI command with --help.
        :type command: List[str]
        :param expected_content: List of strings that should be in help output.
        :type expected_content: List[str]
        :raises SystemExit: When help command is executed.
        :return Dict[str, str]: Dictionary with captured output.
        """
        # @@ STEP 1: Execute help command and expect system exit. @@
        with pytest.raises(SystemExit) as exc_info:
            main(command + ["--help"])

        # @@ STEP 2: Verify help exits with code 0. @@
        assert exc_info.value.code == 0

        # @@ STEP 3: Return command and expected content for external capture. @@
        return {
            'command': command + ["--help"],
            'expected_content': expected_content
        }

    yield test_help_message


@pytest.fixture
def cli_output_validator():
    """Create a validator for CLI output.

    :return Callable: Function to validate CLI output.
    :raises AssertionError: If expected messages are not found in output.
    """
    def validate_output(capsys, expected_success: Optional[List[str]] = None,
                       expected_errors: Optional[List[str]] = None,
                       should_succeed: bool = True) -> Dict[str, str]:
        """Validate CLI output against expected messages.

        :param capsys: Pytest capsys fixture.
        :type capsys: Any
        :param expected_success: Expected success messages, defaults to None.
        :type expected_success: Optional[List[str]], optional
        :param expected_errors: Expected error messages, defaults to None.
        :type expected_errors: Optional[List[str]], optional
        :param should_succeed: Whether command should succeed, defaults to True.
        :type should_succeed: bool, optional
        :raises AssertionError: If expected messages are not found in output.
        :return Dict[str, str]: Dictionary with captured output.
        """
        # @@ STEP 1: Capture output from capsys. @@
        captured = capsys.readouterr()

        # @@ STEP 2: Validate success messages if command should succeed. @@
        if should_succeed and expected_success:
            for message in expected_success:
                assert message in captured.out or message in captured.err, \
                    f"Expected success message '{message}' not found in output"

        # @@ STEP 3: Validate error messages if command should fail. @@
        if not should_succeed and expected_errors:
            for message in expected_errors:
                assert message in captured.err, \
                    f"Expected error message '{message}' not found in error output"

        # @@ STEP 4: Return captured output. @@
        return {
            'stdout': captured.out,
            'stderr': captured.err
        }

    yield validate_output


@pytest.fixture
def cli_project_commands(temp_workspace):
    """Create CLI commands with proper workspace paths.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, List[str]]: Dictionary with CLI commands using real paths.
    """
    # @@ STEP 1: Create dictionary of project CLI commands. @@
    commands = {
        'create_project': [
            "create-project", "--name", "test_project",
            "--dest", str(temp_workspace)
        ],
        'create_project_with_base': [
            "create-project", "--name", "test_project",
            "--dest", str(temp_workspace),
            "--base-project", "https://github.com/user/repo"
        ],
        'create_project_with_summary': [
            "create-project", "--name", "test_project",
            "--dest", str(temp_workspace),
            "--summary", "Custom test project"
        ]
    }

    # @@ STEP 2: Yield commands for test usage. @@
    yield commands


@pytest.fixture
def cli_plugin_commands(simple_project):
    """Create CLI commands for plugin operations.

    :param simple_project: Simple project fixture.
    :type simple_project: Path
    :return Dict[str, List[str]]: Dictionary with plugin CLI commands.
    """
    # @@ STEP 1: Create dictionary of plugin CLI commands. @@
    commands = {
        'create_then_plugin': [
            "create-then-plugin", "--project-path", str(simple_project),
            "--name", "test_then"
        ],
        'create_as_plugin': [
            "create-as-plugin", "--project-path", str(simple_project),
            "--name", "test_as"
        ],
        'create_processor': [
            "create-processor", "--project-path", str(simple_project),
            "--name", "test_processor"
        ]
    }

    # @@ STEP 2: Yield commands for test usage. @@
    yield commands


@pytest.fixture
def cli_chain_commands(project_hierarchy):
    """Create CLI commands for chain operations.

    :param project_hierarchy: Project hierarchy fixture.
    :type project_hierarchy: Dict[str, Path]
    :return Dict[str, List[str]]: Dictionary with chain CLI commands.
    """
    # @@ STEP 1: Get project paths from hierarchy. @@
    ml_lib = project_hierarchy['ml_lib']
    data_lib = project_hierarchy['data_lib']

    # @@ STEP 2: Create dictionary of chain CLI commands. @@
    commands = {
        'show_project_chain': [
            "show-project-chain", "--project-path", str(ml_lib)
        ],
        'update_base_project': [
            "update-base-project", "--project-path", str(ml_lib),
            "--new-base-project", str(data_lib)
        ],
        'update_project_pyi': [
            "update-project-pyi", "--project-path", str(ml_lib)
        ]
    }

    # @@ STEP 3: Yield commands for test usage. @@
    yield commands


@pytest.fixture
def cli_cache_commands():
    """Create CLI commands for cache operations.

    :return Dict[str, List[str]]: Dictionary with cache CLI commands.
    """
    # @@ STEP 1: Create dictionary of cache CLI commands. @@
    commands = {
        'cache_list': ["cache-list"],
        'cache_status': ["cache-status"],
        'cache_clean': ["cache-clean"],
        'cache_clear': ["cache-clear"],
        'cache_refresh': ["cache-refresh"]
    }

    # @@ STEP 2: Yield commands for test usage. @@
    yield commands


@pytest.fixture
def mock_cli_exit():
    """Mock SystemExit for CLI testing.

    :return Callable: Function to create mock SystemExit.
    """
    def create_mock_exit(exit_code: int = 0):
        """Create a mock SystemExit with specified code.

        :param exit_code: Exit code for mock SystemExit, defaults to 0.
        :type exit_code: int, optional
        :return Exception: Mock SystemExit exception.
        """
        # @@ STEP 1: Create mock exception with exit code. @@
        mock_exit = Exception()
        mock_exit.code = exit_code

        # @@ STEP 2: Return mock exit exception. @@
        return mock_exit

    yield create_mock_exit
