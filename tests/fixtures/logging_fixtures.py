"""
Logging fixtures for ChainedPy tests.

Provides centralized logging configuration and capture utilities
following ChainedPy's service patterns.
"""
from __future__ import annotations

# 1. Standard library imports
import logging
import uuid
from logging.handlers import MemoryHandler
from unittest.mock import Mock

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
# (none)

# 5. ChainedPy internal modules
from chainedpy.services.logging_service import get_logger

# 6. Test utilities
# (none)


@pytest.fixture
def caplog_debug(caplog):
    """Capture debug level logs for ChainedPy.

    This is the centralized replacement for the caplog_debug fixture
    that was duplicated across test files.

    :param caplog: Pytest caplog fixture.
    :type caplog: Any
    :return: Configured caplog fixture for debug level logging.
    """
    # @@ STEP 1: Set debug level for chainedpy logger. @@
    caplog.set_level(logging.DEBUG, logger="chainedpy")

    # @@ STEP 2: Return configured caplog. @@
    return caplog


@pytest.fixture
def caplog_info(caplog):
    """Capture info level logs for ChainedPy.

    :param caplog: Pytest caplog fixture.
    :type caplog: Any
    :return: Configured caplog fixture for info level logging.
    """
    # @@ STEP 1: Set info level for chainedpy logger. @@
    caplog.set_level(logging.INFO, logger="chainedpy")

    # @@ STEP 2: Return configured caplog. @@
    return caplog


@pytest.fixture
def caplog_warning(caplog):
    """Capture warning level logs for ChainedPy.

    :param caplog: Pytest caplog fixture.
    :type caplog: Any
    :return: Configured caplog fixture for warning level logging.
    """
    # @@ STEP 1: Set warning level for chainedpy logger. @@
    caplog.set_level(logging.WARNING, logger="chainedpy")

    # @@ STEP 2: Return configured caplog. @@
    return caplog


@pytest.fixture
def caplog_error(caplog):
    """Capture error level logs for ChainedPy.

    :param caplog: Pytest caplog fixture.
    :type caplog: Any
    :return: Configured caplog fixture for error level logging.
    """
    # @@ STEP 1: Set error level for chainedpy logger. @@
    caplog.set_level(logging.ERROR, logger="chainedpy")

    # @@ STEP 2: Return configured caplog. @@
    return caplog


@pytest.fixture
def isolated_logger():
    """Create an isolated logger for testing without affecting global state.

    :return logging.Logger: Isolated logger instance.
    :raises Exception: If logger cleanup fails.
    """
    # @@ STEP 1: Create a unique logger name for this test. @@
    logger_name = f"chainedpy_test_{uuid.uuid4().hex[:8]}"

    # @@ STEP 2: Create and configure logger. @@
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # @@ STEP 3: Add a memory handler to capture logs. @@
    memory_handler = MemoryHandler(capacity=1000)
    logger.addHandler(memory_handler)

    try:
        # @@ STEP 4: Yield logger for test usage. @@
        yield logger
    finally:
        # @@ STEP 5: Clean up logger resources. @@
        logger.removeHandler(memory_handler)
        # || S.S. 5.1: Remove logger from registry. ||
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]


@pytest.fixture
def suppress_logging():
    """Suppress all logging during test execution.

    :return: None, logging is suppressed during context.
    """
    # @@ STEP 1: Save original logging level. @@
    original_level = logging.root.level

    # @@ STEP 2: Disable all logging. @@
    logging.disable(logging.CRITICAL)

    try:
        # @@ STEP 3: Yield control to test. @@
        yield
    finally:
        # @@ STEP 4: Restore original logging level. @@
        logging.disable(original_level)


@pytest.fixture
def log_capture():
    """Capture logs in a list for detailed inspection.

    :return List[logging.LogRecord]: List that will contain log records.
    :raises Exception: If handler cleanup fails.
    """
    # @@ STEP 1: Create list to store log records. @@
    log_records = []

    # @@ STEP 2: Define custom handler class. @@
    class ListHandler(logging.Handler):
        def emit(self, record):
            """Emit log record to list."""
            log_records.append(record)

    # @@ STEP 3: Create and configure handler. @@
    handler = ListHandler()
    handler.setLevel(logging.DEBUG)

    # @@ STEP 4: Add handler to chainedpy logger. @@
    chainedpy_logger = logging.getLogger("chainedpy")
    chainedpy_logger.addHandler(handler)

    try:
        # @@ STEP 5: Yield log records list for test usage. @@
        yield log_records
    finally:
        # @@ STEP 6: Clean up handler. @@
        chainedpy_logger.removeHandler(handler)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing logging calls without actual logging.

    :return Mock: Mock logger object.
    """
    # @@ STEP 1: Create mock logger object. @@
    mock_logger = Mock()

    # @@ STEP 2: Configure mock methods for all log levels. @@
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.critical = Mock()

    # @@ STEP 3: Yield mock logger for test usage. @@
    yield mock_logger


@pytest.fixture
def logger_with_file_handler(temp_workspace):
    """Create a logger with file handler for testing file logging.

    :param temp_workspace: Temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Any]: Dictionary with logger and log file path.
    :raises OSError: If log file creation fails.
    """
    # @@ STEP 1: Create unique logger name. @@
    logger_name = f"chainedpy_file_test_{uuid.uuid4().hex[:8]}"

    # @@ STEP 2: Create and configure logger. @@
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # @@ STEP 3: Create log file. @@
    log_file = temp_workspace / "test.log"

    # @@ STEP 4: Add file handler with formatter. @@
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # || S.S. 4.1: Add handler to logger. ||
    logger.addHandler(file_handler)

    try:
        # @@ STEP 5: Yield logger configuration for test usage. @@
        yield {
            'logger': logger,
            'log_file': log_file,
            'handler': file_handler
        }
    finally:
        # @@ STEP 6: Clean up logger resources. @@
        logger.removeHandler(file_handler)
        file_handler.close()
        # || S.S. 6.1: Remove logger from registry. ||
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]


@pytest.fixture
def chainedpy_logger():
    """Get the actual ChainedPy logger for testing.

    :return logging.Logger: The ChainedPy logger instance.
    """
    # @@ STEP 1: Get ChainedPy logger using service. @@
    logger = get_logger()

    # @@ STEP 2: Yield logger for test usage. @@
    yield logger


@pytest.fixture
def log_level_context():
    """Create a context manager for temporarily changing log levels.

    :return Callable: Function to temporarily change log level.
    """
    # @@ STEP 1: Initialize storage for original log levels. @@
    original_levels = {}

    def set_log_level(logger_name: str, level: int):
        """Temporarily set log level for a logger.

        :param logger_name: Name of the logger.
        :type logger_name: str
        :param level: Log level to set.
        :type level: int
        """
        # || S.S. 1.1: Get logger and store original level. ||
        logger = logging.getLogger(logger_name)
        if logger_name not in original_levels:
            original_levels[logger_name] = logger.level
        # || S.S. 1.2: Set new log level. ||
        logger.setLevel(level)

    def restore_log_levels():
        """Restore original log levels."""
        # || S.S. 2.1: Restore all original log levels. ||
        for logger_name, level in original_levels.items():
            logging.getLogger(logger_name).setLevel(level)

    try:
        # @@ STEP 2: Yield log level setter function. @@
        yield set_log_level
    finally:
        # @@ STEP 3: Restore original log levels. @@
        restore_log_levels()


@pytest.fixture
def no_log_propagation():
    """Disable log propagation for ChainedPy logger during test.

    :return: None, log propagation is disabled during context.
    """
    # @@ STEP 1: Get ChainedPy logger and save original propagation setting. @@
    chainedpy_logger = logging.getLogger("chainedpy")
    original_propagate = chainedpy_logger.propagate

    # @@ STEP 2: Disable log propagation. @@
    chainedpy_logger.propagate = False

    try:
        # @@ STEP 3: Yield control to test. @@
        yield
    finally:
        # @@ STEP 4: Restore original propagation setting. @@
        chainedpy_logger.propagate = original_propagate
