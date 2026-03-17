"""
ChainedPy Test Configuration

Central configuration file for all ChainedPy tests.
Imports all fixtures and provides test configuration.
"""

import pytest

# Global test configuration - fixtures are loaded via pytest_plugins
pytest_plugins = [
    "tests.fixtures.workspace_fixtures",
    "tests.fixtures.project_fixtures",
    "tests.fixtures.mock_fixtures",
    "tests.fixtures.logging_fixtures",
    "tests.fixtures.cli_fixtures"
]


def pytest_configure(config):
    """Configure pytest with custom markers.

    :param config: Pytest configuration object.
    :type config: Any
    """
    # @@ STEP 1: Add custom test markers. @@
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "credentials: mark test as requiring specific credentials"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location.

    :param config: Pytest configuration object.
    :type config: Any
    :param items: List of test items.
    :type items: list
    """
    # @@ STEP 1: Add markers based on test directory location and test names. @@
    for item in items:
        # Add integration marker to tests in integration directory.
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add slow marker to tests that might be slow.
        if any(keyword in item.name.lower() for keyword in ["performance", "large", "stress"]):
            item.add_marker(pytest.mark.slow)

        # Add network marker to tests that use real repositories.
        if any(keyword in item.name.lower() for keyword in ["real_", "actual_", "live_"]):
            item.add_marker(pytest.mark.network)
