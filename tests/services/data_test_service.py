"""
Data test service for ChainedPy tests.

Provides centralized test data factories and management utilities
for testing, following ChainedPy's service patterns.
"""
from __future__ import annotations

from typing import Dict, Any, List

from chainedpy.constants import (
    PLUGIN_PREFIX_THEN, PLUGIN_PREFIX_AS, 
    PLUGIN_PREFIX_PROCESSOR
)


class DataTestServiceError(Exception):
    """Exception raised when data test operations fail."""
    pass


class ConfigDataFactory:
    """Factory for creating test configuration data.

    :raises Exception: If configuration data factory operations fail.
    """

    @staticmethod
    def create_basic_config(base_project: str = "chainedpy",
                          summary: str = "Test project") -> str:
        """Create basic YAML configuration content.

        :param base_project: Base project value, defaults to "chainedpy".
        :type base_project: str, optional
        :param summary: Summary value, defaults to "Test project".
        :type summary: str, optional
        :return str: YAML configuration content as string.
        """
        # @@ STEP 1: Generate YAML configuration content. @@
        return f"""project:
  base_project: {base_project}
  summary: {summary}
"""

    @staticmethod
    def create_config_with_relative_base(relative_path: str = "./other_project",
                                       summary: str = "Project extending other_project") -> str:
        """Create YAML configuration with relative base project path.

        :param relative_path: Relative path to base project, defaults to "./other_project".
        :type relative_path: str, optional
        :param summary: Summary value, defaults to "Project extending other_project".
        :type summary: str, optional
        :return str: YAML configuration content as string.
        """
        # @@ STEP 1: Generate YAML configuration with relative base. @@
        return f"""project:
  base_project: {relative_path}
  summary: {summary}
"""

    @staticmethod
    def create_config_with_remote_base(remote_url: str,
                                     summary: str = "Project extending remote base") -> str:
        """Create YAML configuration with remote base project URL.

        :param remote_url: Remote URL to base project.
        :type remote_url: str
        :param summary: Summary value, defaults to "Project extending remote base".
        :type summary: str, optional
        :return str: YAML configuration content as string.
        """

        return f"""project:
  base_project: {remote_url}
  summary: {summary}
"""
    
    @staticmethod
    def create_corrupted_config() -> str:
        """Create corrupted YAML configuration for error testing.

        :return str: Corrupted YAML configuration content as string.
        """
        # @@ STEP 1: Return corrupted YAML with invalid indentation. @@
        return "key: value\n  invalid: indentation"

    @staticmethod
    def create_config_with_special_characters() -> str:
        """Create YAML configuration with special characters for testing.

        :return str: YAML configuration with special characters.
        """
        # @@ STEP 1: Define summary with special characters. @@
        special_summary = 'Project with: special chars, quotes "test", and symbols @#$%'

        # @@ STEP 2: Generate YAML configuration with special characters. @@
        return f"""project:
  base_project: chainedpy
  summary: {special_summary}
"""


class PluginDataFactory:
    """Factory for creating test plugin data.

    :raises Exception: If plugin data factory operations fail.
    """

    @staticmethod
    def create_then_plugin_content(plugin_name: str,
                                 description: str = "Test then plugin") -> str:
        """Create content for a then plugin.

        :param plugin_name: Name of the plugin (without prefix).
        :type plugin_name: str
        :param description: Description for the plugin, defaults to "Test then plugin".
        :type description: str, optional
        :return str: Python code content for then plugin.
        """
        # @@ STEP 1: Generate full plugin name with prefix. @@
        full_name = f"{PLUGIN_PREFIX_THEN}{plugin_name}"

        # @@ STEP 2: Generate plugin content template. @@
        return f'''"""
{description}
"""
from typing import Any, Callable
from chainedpy.chain import Chain


def {full_name}(self, func: Callable[[Any], Any]) -> Chain[Any]:
    """
    {description}

    Args:
        func: Function to apply to the chain value

    Returns:
        New Chain with transformed value
    """
    return self.then_map(func)
'''
    @staticmethod
    def create_as_plugin_content(plugin_name: str,
                               description: str = "Test as plugin") -> str:
        """Create content for an as plugin.

        :param plugin_name: Name of the plugin (without prefix).
        :type plugin_name: str
        :param description: Description for the plugin, defaults to "Test as plugin".
        :type description: str, optional
        :return str: Python code content for as plugin.
        """
        # @@ STEP 1: Generate full plugin name with prefix. @@
        full_name = f"{PLUGIN_PREFIX_AS}{plugin_name}"

        # @@ STEP 2: Generate plugin content template. @@
        return f'''"""
{description}
"""
from typing import Any
from chainedpy.chain import Chain


def {full_name}(self, *args: Any, **kwargs: Any) -> Chain[Any]:
    """
    {description}

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        New Chain with modified behavior
    """
    return self
'''

    @staticmethod
    def create_processor_plugin_content(plugin_name: str,
                                      description: str = "Test processor plugin") -> str:
        """Create content for a processor plugin.

        :param plugin_name: Name of the plugin (without prefix).
        :type plugin_name: str
        :param description: Description for the plugin, defaults to "Test processor plugin".
        :type description: str, optional
        :return str: Python code content for processor plugin.
        """
        # @@ STEP 1: Generate full plugin name with prefix. @@
        full_name = f"{PLUGIN_PREFIX_PROCESSOR}{plugin_name}"

        # @@ STEP 2: Generate processor class content template. @@
        return f'''"""
{description}
"""
from typing import Any


class {full_name.title()}:
    """
    {description}
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the processor."""
        pass

    def process(self, value: Any) -> Any:
        """
        Process the input value.

        Args:
            value: Input value to process

        Returns:
            Processed value
        """
        return value
'''

    @staticmethod
    def create_broken_plugin_content(plugin_name: str) -> str:
        """Create broken plugin content for error testing.

        :param plugin_name: Name of the plugin.
        :type plugin_name: str
        :return str: Broken Python code content.
        """
        # @@ STEP 1: Return intentionally broken Python syntax. @@
        return f"def {plugin_name}(self invalid syntax"


class TestDataFactory:
    """Factory for creating various test data structures.

    :raises Exception: If test data factory operations fail.
    """

    @staticmethod
    def create_sample_config_data():
        """Create sample configuration data for testing.

        :return List[Dict[str, str]]: List of valid configuration dictionaries.
        """
        # @@ STEP 1: Return list of sample configuration data. @@
        return [
            {
                'base_project': 'chainedpy',
                'summary': 'Basic ChainedPy project'
            },
            {
                'base_project': './other_project',
                'summary': 'Project extending another project'
            },
            {
                'base_project': 'chainedpy',
                'summary': 'Data processing pipeline'
            },
            {
                'base_project': './base_lib',
                'summary': 'Machine learning utilities'
            }
        ]

    @staticmethod
    def create_project_names() -> List[str]:
        """Create a list of standard test project names.

        :return List[str]: List of project names for testing.
        """
        # @@ STEP 1: Return list of standard test project names. @@
        return [
            "test_project",
            "base_lib",
            "data_lib",
            "ml_lib",
            "project_a",
            "project_b",
            "extending_project",
            "corrupted_project"
        ]

    @staticmethod
    def create_plugin_names() -> Dict[str, List[str]]:
        """Create lists of standard test plugin names by type.

        :return Dict[str, List[str]]: Dictionary mapping plugin types to lists of plugin names.
        """
        # @@ STEP 1: Return dictionary of plugin names by type. @@
        return {
            'then': [
                'double', 'transform', 'process', 'filter', 'validate'
            ],
            'as': [
                'retry', 'timeout', 'cache', 'log', 'debug'
            ],
            'processors': [
                'data_processor', 'text_processor', 'json_processor'
            ]
        }
    @staticmethod
    def create_remote_repository_urls() -> Dict[str, str]:
        """Create dictionary of test remote repository URLs.

        :return Dict[str, str]: Dictionary mapping repository types to URLs.
        """
        # @@ STEP 1: Return dictionary of test repository URLs. @@
        return {
            'public_github': (
                "https://raw.githubusercontent.com/FanaticPythoner/"
                "chainedpy_test_public_chain_simple/main/mypublicchain1"
            ),
            'private_github': (
                "https://raw.githubusercontent.com/FanaticPythoner/"
                "chainedpy_test_private_chain_simple/main/myprivatechain1"
            ),
            'invalid_github': "https://github.com/nonexistent/invalid_repo_12345",
            'public_repo_base': (
                "https://github.com/FanaticPythoner/chainedpy_test_public_chain_simple"
                "/tree/main/mypublicchain1"
            ),
            'private_repo_base': (
                "https://github.com/FanaticPythoner/chainedpy_test_private_chain_simple"
                "/tree/main/myprivatechain1"
            ),
            # Add aliases that tests are looking for
            'invalid_repo': "https://github.com/nonexistent/invalid_repo_12345",
            'public_config_url': (
                "https://raw.githubusercontent.com/FanaticPythoner/"
                "chainedpy_test_public_chain_simple/main/mypublicchain1/chainedpy.yaml"
            ),
            'invalid_config_url': "https://github.com/nonexistent/invalid_repo_12345/chainedpy.yaml"
        }

    @staticmethod
    def create_test_credentials() -> Dict[str, Dict[str, str]]:
        """Create test credential configurations.

        :return Dict[str, Dict[str, str]]: Dictionary mapping credential types to credential dictionaries.
        """
        # @@ STEP 1: Return dictionary of test credential configurations. @@
        return {
            'github_token': {'github_token': 'test_github_token'},
            'gitlab_token': {'gitlab_token': 'test_gitlab_token'},
            'empty': {},
            'multiple': {
                'github_token': 'test_github_token',
                'gitlab_token': 'test_gitlab_token',
                'ftp_username': 'test_user',
                'ftp_password': 'test_pass'
            }
        }
    @staticmethod
    def create_cli_command_examples() -> Dict[str, List[str]]:
        """Create examples of CLI commands for testing.

        :return Dict[str, List[str]]: Dictionary mapping command types to command argument lists.
        """
        # @@ STEP 1: Return dictionary of CLI command examples. @@
        return {
            'create_project': [
                "create-project", "--name", "test_project",
                "--dest", "/tmp/workspace"
            ],
            'create_project_with_base': [
                "create-project", "--name", "test_project",
                "--dest", "/tmp/workspace",
                "--base-project", "https://github.com/user/repo"
            ],
            'update_base_project': [
                "update-base-project", "--project-path", "/tmp/project",
                "--new-base-project", "chainedpy"
            ],
            'show_project_chain': [
                "show-project-chain", "--project-path", "/tmp/project"
            ],
            'create_then_plugin': [
                "create-then-plugin", "--project-path", "/tmp/project",
                "--name", "test_plugin"
            ]
        }

    @staticmethod
    def create_error_scenarios() -> Dict[str, Dict[str, Any]]:
        """Create error scenario data for testing.

        :return Dict[str, Dict[str, Any]]: Dictionary mapping error types to scenario data.
        """
        # @@ STEP 1: Return dictionary of error scenario data. @@
        return {
            'circular_dependency': {
                'description': 'Project tries to extend itself',
                'expected_exception': ValueError,
                'expected_message': 'Circular dependency'
            },
            'invalid_project_path': {
                'description': 'Project path does not exist',
                'expected_exception': ValueError,
                'expected_message': 'Invalid base project'
            },
            'permission_denied': {
                'description': 'File permission error',
                'expected_exception': RuntimeError,
                'expected_message': 'Failed to update configuration file'
            },
            'corrupted_config': {
                'description': 'YAML parsing error',
                'expected_fallback': True,
                'expected_log_level': 'ERROR'
            }
        }
