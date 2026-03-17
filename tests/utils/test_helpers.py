"""
Test helpers for ChainedPy tests.

Provides common helper functions for test setup and validation
following ChainedPy's service patterns.
"""
from __future__ import annotations

# 1. Standard library imports
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from unittest.mock import patch

# 2. Third-party imports
import pytest

# 3. Internal constants
from chainedpy.constants import CONFIG_FILE_NAME

# 4. ChainedPy services
# (none)

# 5. ChainedPy internal modules

# 6. Test utilities
# (none)


def add_parent_to_path() -> None:
    """Add parent directory to Python path for imports.

    This replaces the common pattern found in many test files.

    :return None: None
    """
    # @@ STEP 1: Get parent directory path. @@
    parent_dir = os.path.join(os.path.dirname(__file__), '..', '..')

    # @@ STEP 2: Add to sys.path if not already present. @@
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)


def safe_import(module_name: str, fallback: Optional[Any] = None) -> Any:
    """Safely import a module with fallback.

    :param module_name: Name of module to import.
    :type module_name: str
    :param fallback: Fallback value if import fails, defaults to None.
    :type fallback: Optional[Any], optional
    :return Any: Imported module or fallback value.
    """
    # @@ STEP 1: Try to import module. @@
    try:
        return __import__(module_name)
    except ImportError:
        # @@ STEP 2: Return fallback if import fails. @@
        return fallback


def create_test_context(workspace: Path, project_name: str = "test_project") -> Dict[str, Any]:
    """Create a standard test context with common setup.

    :param workspace: Path to test workspace.
    :type workspace: Path
    :param project_name: Name of test project, defaults to "test_project".
    :type project_name: str, optional
    :return Dict[str, Any]: Dictionary with test context information.
    """
    # @@ STEP 1: Create test context dictionary. @@
    return {
        'workspace': workspace,
        'project_name': project_name,
        'project_dir': workspace / project_name,
        'config_file': workspace / project_name / CONFIG_FILE_NAME,
        'plugins_dir': workspace / project_name / 'plugins',
        'then_dir': workspace / project_name / 'plugins' / 'then',
        'as_dir': workspace / project_name / 'plugins' / 'as_',
        'processors_dir': workspace / project_name / 'plugins' / 'processors'
    }


def validate_test_environment() -> Dict[str, bool]:
    """
    Validate that the test environment is properly set up.
    
    Returns:
        Dictionary with validation results
    """
    validations = {}
    
    # Check Python version
    validations['python_version'] = sys.version_info >= (3, 8)
    
    # Check required modules
    required_modules = ['pytest', 'pathlib', 'tempfile', 'unittest.mock']
    for module in required_modules:
        validations[f'module_{module}'] = safe_import(module) is not None
    
    # Check ChainedPy imports
    try:
        # All imports already at top
        validations['chainedpy_imports'] = True
    except ImportError:
        validations['chainedpy_imports'] = False
    
    return validations


def skip_if_missing_dependency(dependency: str, reason: Optional[str] = None) -> Callable:
    """
    Decorator to skip test if dependency is missing.
    
    Args:
        dependency: Name of dependency to check
        reason: Optional reason for skipping
        
    Returns:
        Decorator function
    """
    def decorator(func):
        if safe_import(dependency) is None:
            skip_reason = reason or f"Missing dependency: {dependency}"
            return pytest.mark.skip(reason=skip_reason)(func)
        return func
    
    return decorator


def requires_network(func: Callable) -> Callable:
    """
    Decorator to mark tests that require network access.
    
    Args:
        func: Test function to decorate
        
    Returns:
        Decorated function with network requirement marker
    """
    return pytest.mark.network(func)


def requires_credentials(credential_type: str) -> Callable:
    """
    Decorator to mark tests that require specific credentials.
    
    Args:
        credential_type: Type of credentials required (e.g., 'github', 'gitlab')
        
    Returns:
        Decorator function
    """
    def decorator(func):
        return pytest.mark.credentials(credential_type)(func)
    
    return decorator


def integration_test(func: Callable) -> Callable:
    """
    Decorator to mark integration tests.
    
    Args:
        func: Test function to decorate
        
    Returns:
        Decorated function with integration test marker
    """
    return pytest.mark.integration(func)


def slow_test(func: Callable) -> Callable:
    """
    Decorator to mark slow tests.
    
    Args:
        func: Test function to decorate
        
    Returns:
        Decorated function with slow test marker
    """
    return pytest.mark.slow(func)


def parametrize_with_data(data_factory: Callable, *args, **kwargs) -> Callable:
    """
    Decorator to parametrize tests with data from factory function.
    
    Args:
        data_factory: Function that returns test data
        *args: Arguments to pass to data factory
        **kwargs: Keyword arguments to pass to data factory
        
    Returns:
        Decorator function
    """
    def decorator(func):
        test_data = data_factory(*args, **kwargs)
        if isinstance(test_data, dict):
            # Convert dict to list of tuples for parametrize
            test_data = list(test_data.items())
        return pytest.mark.parametrize("test_input,expected", test_data)(func)
    
    return decorator


def with_temp_env_vars(env_vars: Dict[str, str]) -> Callable:
    """
    Decorator to temporarily set environment variables during test.
    
    Args:
        env_vars: Dictionary of environment variables to set
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with patch.dict(os.environ, env_vars):
                return func(*args, **kwargs)
        return wrapper
    
    return decorator


def capture_function_calls(target_function: str) -> Callable:
    """
    Decorator to capture calls to a specific function during test.
    
    Args:
        target_function: Full path to function to capture (e.g., 'module.function')
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with patch(target_function) as mock_func:
                result = func(*args, **kwargs)
                # Add call information to result if it's a dict
                if isinstance(result, dict):
                    result['captured_calls'] = mock_func.call_args_list
                return result
        return wrapper
    
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 0.1) -> Callable:
    """
    Decorator to retry test on failure (useful for flaky tests).
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                    else:
                        raise last_exception
        
        return wrapper
    
    return decorator
