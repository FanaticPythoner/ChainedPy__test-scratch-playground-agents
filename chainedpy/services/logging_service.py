"""Centralized logging service for ChainedPy.

This service provides a single point for obtaining and configuring loggers throughout
the ChainedPy codebase, eliminating the need for scattered _get_logger() functions
in service files. It ensures consistent logging format, levels, and behavior across
all ChainedPy components.

The service creates a unified logger instance that is shared across all modules,
providing consistent formatting and output handling. It supports both console
and file logging with configurable levels and formats.

Note:
    This service replaces all individual _get_logger() functions that were
    previously scattered throughout service files. All modules should use
    [get_logger][chainedpy.services.logging_service.get_logger] from this service instead.

Example:
    ```python
    from chainedpy.services.logging_service import get_logger

    # Get the unified logger
    logger = get_logger()

    # Use standard logging methods
    logger.info("Operation completed successfully")
    logger.warning("Potential issue detected")
    logger.error("Operation failed", exc_info=True)

    # Logger is consistent across all modules
    def my_function():
        logger = get_logger()  # Same logger instance
        logger.debug("Debug information")
    ```

See Also:
    - [get_logger][chainedpy.services.logging_service.get_logger]: Main function to obtain logger
    - [LoggingServiceError][chainedpy.services.logging_service.LoggingServiceError]: Logging-specific exceptions
    - [chainedpy.exceptions][chainedpy.exceptions]: Exception classes that use this logger
"""
from __future__ import annotations

import logging
import sys
from typing import Optional
from pathlib import Path


class LoggingServiceError(Exception):
    """Exception raised when logging service operations fail."""
    pass


# @@ STEP 1: Define global logger instance. @@
_chainedpy_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get the unified ChainedPy logger with consistent formatting.

    This function replaces all _get_logger() functions throughout the codebase.
    The logger is created once and reused for all subsequent calls.

    Example:
        ```python
        from chainedpy.services.logging_service import get_logger

        # Get logger for current module
        logger = get_logger()

        # Use logger for different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Logger is configured with ChainedPy settings
        assert logger.name == "chainedpy"
        assert logger.level <= 20  # INFO level or lower

        # Multiple calls return same logger instance
        logger2 = get_logger()
        assert logger is logger2
        ```

    :return [logging.Logger][logging.Logger]: Configured ChainedPy logger instance.
    """
    global _chainedpy_logger

    # @@ STEP 1: Create logger if not already created. @@
    if _chainedpy_logger is None:
        _chainedpy_logger = _create_logger()

    return _chainedpy_logger


def _create_logger() -> logging.Logger:
    """Create and configure the ChainedPy logger.

    Example:
        ```python
        from chainedpy.services.logging_service import _create_logger

        # Create new logger instance
        logger = _create_logger()

        # Verify configuration
        assert logger.name == "chainedpy"
        assert logger.level == 20  # INFO level
        assert len(logger.handlers) > 0

        # Verify formatter
        handler = logger.handlers[0]
        assert handler.formatter is not None

        # Test logging
        logger.info("Test message")
        ```

    :return [logging.Logger][logging.Logger]: Configured logger instance.
    :raises LoggingServiceError: If logger configuration fails.
    """
    try:
        # @@ STEP 1: Create base logger. @@
        logger = logging.getLogger("chainedpy")

        # @@ STEP 2: Remove any existing handlers to avoid conflicts. @@
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        # @@ STEP 3: Configure console handler. @@
        # Console handler - explicitly set to stdout for CLI output compatibility.
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # @@ STEP 4: Configure file handler for debugging. @@
        try:
            log_file = Path.home() / ".chainedpy_debug.log"
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception:
            # If file logging fails, continue with console only.
            # This is acceptable as console logging is the primary requirement.
            pass

        # @@ STEP 5: Set logging level. @@
        logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logging.

        return logger

    except Exception as e:
        raise LoggingServiceError(f"Failed to create logger: {e}") from e


def reset_logger() -> None:
    """Reset the global logger instance.

    This is primarily used for testing purposes to ensure clean state.

    Example:
        ```python
        from chainedpy.services.logging_service import get_logger, reset_logger

        # Get initial logger
        logger1 = get_logger()
        logger1.info("First logger")

        # Reset logger
        reset_logger()

        # Get new logger (should be fresh instance)
        logger2 = get_logger()
        logger2.info("Second logger")

        # Verify reset worked
        assert logger1 is not logger2
        ```
    """
    global _chainedpy_logger
    _chainedpy_logger = None
