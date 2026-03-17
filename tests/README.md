# ChainedPy Test Suite

This document describes the organization and usage of the ChainedPy test suite.

## Test Structure

The test suite is organized into distinct categories based on testing scope and purpose:

### Unit Tests (`tests/unit/`)
Pure unit tests focusing on individual components in isolation:
- `test_project_config.py` - ProjectConfig dataclass and validation logic
- `test_validation_logic.py` - Validation functions in isolation

### Integration Tests (`tests/integration/`)
Tests for component interactions and real system behavior:
- `test_project_lifecycle.py` - Complete project lifecycle testing
- `test_error_handling.py` - Error handling with real scenarios
- `test_chain_traversal.py` - Chain dependency traversal logic
- `test_circular_dependencies.py` - Circular dependency detection
- `test_stub_generation.py` - Stub file generation functionality
- `test_project_updates.py` - Project update mechanisms
- `test_remote_dependencies.py` - Remote dependency resolution

### CLI Tests (`tests/cli/`)
Command-line interface specific testing:
- `test_project_commands.py` - Project-related CLI commands
- `test_plugin_commands.py` - Plugin-related CLI commands
- `test_cache_commands.py` - Cache management commands

## Test Infrastructure

### Services (`tests/services/`)
Centralized test services following ChainedPy's service patterns:

- **`filesystem_test_service.py`** - File system operations and temporary workspace management
- **`project_test_service.py`** - Project creation, setup, and management utilities  
- **`mock_test_service.py`** - Centralized mocking utilities and patterns
- **`assertion_test_service.py`** - Reusable assertion helpers and validation
- **`data_test_service.py`** - Test data factories and management

### Fixtures (`tests/fixtures/`)
Reusable test fixtures available via `conftest.py`:

- **`workspace_fixtures.py`** - Temporary workspace and directory management
- **`project_fixtures.py`** - Project creation and hierarchy setup
- **`mock_fixtures.py`** - Mock objects and patching utilities
- **`logging_fixtures.py`** - Logging configuration and capture
- **`cli_fixtures.py`** - CLI testing utilities

### Utilities (`tests/utils/`)
Helper functions for common test patterns:

- **`test_helpers.py`** - Common helper functions for test setup
- **`assertion_helpers.py`** - Specialized assertion utilities
- **`file_helpers.py`** - File operation utilities for testing
- **`mock_helpers.py`** - Mock creation and management utilities
- **`data_helpers.py`** - Test data creation and manipulation

## Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/cli/           # CLI tests only

# Run with specific markers
pytest -m "not slow_test"    # Skip slow tests
pytest -m "integration_test" # Integration tests only
pytest -m "requires_network" # Network-dependent tests
```

## Test Markers

The following pytest markers are available:

- `@integration_test` - Marks integration tests
- `@requires_network` - Tests requiring network access  
- `@requires_credentials('service_name')` - Tests requiring specific credentials
- `@slow_test` - Slow running tests

## Writing Tests

### Using Test Services

```python
from tests.services.project_test_service import create_test_project
from tests.services.assertion_test_service import ProjectAssertionService

def test_project_functionality(temp_workspace):
    # Create a test project
    project = create_test_project(temp_workspace, "my_test_project")
    
    # Perform operations
    # ...
    
    # Assert results
    ProjectAssertionService.assert_project_structure(project)
```

### Using Fixtures

```python
def test_with_fixtures(temp_workspace, simple_project):
    """Test using centralized fixtures."""
    # temp_workspace provides a clean temporary directory
    # simple_project provides a pre-configured test project
    
    assert simple_project.root_path.exists()
    assert (simple_project.root_path / CONFIG_FILE_NAME).exists()
```

### Using Assertion Helpers

```python
from tests.utils.assertion_helpers import assert_exception_with_message

def test_error_handling():
    # Test that a specific exception is raised with expected message
    assert_exception_with_message(
        ValueError, 
        "Expected error message",
        function_that_should_fail, 
        arg1, 
        arg2
    )
```

### Using Mock Services

```python
from tests.services.mock_test_service import MockTestService

def test_with_mocks():
    # Create mocked dependencies
    mock_service = MockTestService.create_mock_filesystem()
    
    # Use in your test
    # ...
```

## Best Practices

1. **Choose the Right Test Type**
   - Use unit tests for testing individual functions/methods in isolation
   - Use integration tests for testing component interactions
   - Use CLI tests for testing command-line interface behavior

2. **Use Centralized Infrastructure**
   - Leverage existing services, fixtures, and utilities
   - Avoid duplicating test setup code
   - Use constants from `chainedpy.constants` instead of hardcoded values

3. **Test Organization**
   - Keep tests focused on a single aspect of functionality
   - Use descriptive test names that explain what is being tested
   - Group related tests in the same file

4. **Mocking Strategy**
   - Mock external dependencies in unit tests
   - Use real implementations in integration tests
   - Leverage `MockTestService` for consistent mocking patterns

5. **Error Testing**
   - Test both success and failure cases
   - Verify specific error messages and types
   - Use assertion helpers for consistent error checking

## Available Test Data

The test suite provides various test data factories through `data_test_service.py`:

- Sample project configurations
- Test chain definitions
- Mock dependency structures
- Sample plugin configurations

## Debugging Tests

For verbose test output:
```bash
pytest -v                    # Verbose mode
pytest -vv                   # Very verbose mode
pytest --tb=short           # Short traceback format
pytest --pdb                # Drop into debugger on failures
pytest -k "test_name"       # Run tests matching pattern
```

## Coverage Reports

Generate test coverage reports:
```bash
pytest --cov=chainedpy --cov-report=html
# View coverage report in htmlcov/index.html
```