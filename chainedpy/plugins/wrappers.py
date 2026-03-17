"""Built-in wrapper operations for ChainedPy.

This module provides as_* methods for adding behavior to chain operations without
changing their core functionality. It implements common cross-cutting concerns like
retry logic, timeouts, logging, caching, and error handling that can be applied
to any chain operation.

The wrappers are registered using the [as_][chainedpy.register.as_] decorator, making them automatically
available on [Chain][chainedpy.chain.Chain] instances. Each wrapper preserves the input and output types
of the wrapped operation while adding additional behavior.

Note:
    Wrappers can be chained together to combine multiple behaviors. For example,
    you can add both retry and timeout behavior to the same operation.

Example:
    ```python
    from chainedpy import Chain

    # Add retry behavior to a transformation
    result = await (
        Chain("https://api.example.com/data")
        .then_map(fetch_data)
        .as_retry(attempts=5, delay=2.0)  # Retry up to 5 times
        .then_map(parse_json)
    )

    # Combine multiple wrappers
    result = await (
        Chain("slow-operation")
        .then_map(expensive_computation)
        .as_timeout(seconds=30.0)         # Add timeout
        .as_retry(attempts=3)             # Add retry
        .as_cache(ttl=300)                # Add caching
    )
    ```

See Also:
    - [as_retry][chainedpy.plugins.wrappers.as_retry]: Retry wrapper with exponential backoff
    - [as_timeout][chainedpy.plugins.wrappers.as_timeout]: Timeout wrapper for operations
    - [as_cache][chainedpy.plugins.wrappers.as_cache]: Caching wrapper for expensive operations
    - [chainedpy.register.as_][chainedpy.register.as_]: Registration decorator used by this module
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict

from ..register import as_ # pylint: disable=relative-beyond-top-level
from ..link import Link, Wrapper # pylint: disable=relative-beyond-top-level
from ..exceptions import RetryExhausted, TimeoutExpired, CacheError # pylint: disable=relative-beyond-top-level


@as_("retry")
def as_retry(*, attempts: int = 3, delay: float = 1.0) -> Wrapper[Any, Any]:
    """Retry wrapper with exponential backoff.

    Example:
        ```python
        from chainedpy import Chain
        from chainedpy.plugins.wrappers import as_retry
        import random

        # Function that fails sometimes
        def unreliable_function(x):
            if random.random() < 0.7:  # 70% chance of failure
                raise ValueError("Random failure")
            return x * 2

        # Use retry wrapper
        try:
            result = await (
                Chain(5)
                .then_map(unreliable_function)
                .as_retry(attempts=5, delay=0.1)
            )
            print(f"Success: {result}")
        except ValueError:
            print("Failed after all retries")

        # Retry with different settings
        result = await (
            Chain("hello")
            .then_map(str.upper)
            .as_retry(attempts=2, delay=0.5)
        )
        assert result == "HELLO"
        ```

    :param attempts: Number of retry attempts, defaults to 3.
    :type attempts: [int][int], optional
    :param delay: Initial delay between retries in seconds, defaults to 1.0.
    :type delay: [float][float], optional
    :return [Wrapper][chainedpy.link.Wrapper][[Any][typing.Any], [Any][typing.Any]]: Wrapper that adds retry behavior.
    """
    class RetryWrapper(Wrapper[Any, Any]):
        """Wrapper implementation for retry behavior.""" # TODO: Fix to use Sphinx / correct docstring style.

        def wrap(self, inner: Link[Any, Any]) -> Link[Any, Any]:
            """Wrap a link with retry behavior.

            :param inner: Link to wrap with retry logic.
            :type inner: Link[Any, Any]
            :return Link[Any, Any]: Link with retry behavior.
            """
            class RetryLink(Link[Any, Any]):
                """Link implementation with retry logic."""
                name = f"retry({inner.name})"

                async def __call__(self, arg: Any) -> Any:
                    """Execute with retry logic and exponential backoff.

                    :param arg: Input argument.
                    :type arg: Any
                    :return Any: Result from successful execution.
                    :raises RetryExhausted: If all retry attempts fail.
                    """
                    # @@ STEP 1: Initialize retry state. @@
                    last_exception = None
                    current_delay = delay

                    # @@ STEP 2: Attempt execution with retries. @@
                    for attempt in range(attempts):
                        try:
                            return await inner(arg)
                        except Exception as e:
                            last_exception = e
                            if attempt < attempts - 1:  # Not the last attempt.
                                await asyncio.sleep(current_delay)
                                current_delay *= 2  # Exponential backoff.
                            else:
                                break

                    # @@ STEP 3: Raise retry exhausted exception. @@
                    raise RetryExhausted(attempts, last_exception, delay) from last_exception

            return RetryLink()

    return RetryWrapper()


@as_("timeout")
def as_timeout(seconds: float) -> Wrapper[Any, Any]:
    """Timeout wrapper.

    Example:
        ```python
        from chainedpy import Chain
        from chainedpy.plugins.wrappers import as_timeout
        import asyncio

        # Fast operation (should succeed)
        result = await (
            Chain("hello")
            .then_map(str.upper)
            .as_timeout(1.0)  # 1 second timeout
        )
        assert result == "HELLO"

        # Slow operation (should timeout)
        async def slow_operation(x):
            await asyncio.sleep(2.0)  # Takes 2 seconds
            return x * 2

        try:
            result = await (
                Chain(5)
                .then_map(slow_operation)
                .as_timeout(1.0)  # 1 second timeout
            )
        except asyncio.TimeoutError:
            print("Operation timed out as expected")

        # Quick timeout
        result = await (
            Chain(42)
            .then_map(lambda x: x + 1)
            .as_timeout(0.1)  # Very short timeout
        )
        assert result == 43
        ```

    :param seconds: Timeout duration in seconds.
    :type seconds: [float][float]
    :return [Wrapper][chainedpy.link.Wrapper][[Any][typing.Any], [Any][typing.Any]]: Wrapper that adds timeout behavior.
    """
    class TimeoutWrapper(Wrapper[Any, Any]):
        """Wrapper implementation for timeout behavior."""

        def wrap(self, inner: Link[Any, Any]) -> Link[Any, Any]:
            """Wrap a link with timeout behavior.

            :param inner: Link to wrap with timeout logic.
            :type inner: Link[Any, Any]
            :return Link[Any, Any]: Link with timeout behavior.
            """
            class TimeoutLink(Link[Any, Any]):
                """Link implementation with timeout logic."""
                name = f"timeout({inner.name})"

                async def __call__(self, arg: Any) -> Any:
                    """Execute with timeout.

                    :param arg: Input argument.
                    :type arg: Any
                    :return Any: Result from execution within timeout.
                    :raises TimeoutExpired: If execution exceeds timeout.
                    """
                    try:
                        return await asyncio.wait_for(inner(arg), timeout=seconds)
                    except asyncio.TimeoutError as e:
                        raise TimeoutExpired(seconds, inner.name) from e

            return TimeoutLink()

    return TimeoutWrapper()


@as_("log")
def as_log(label: str = "", *, level: int = logging.DEBUG) -> Wrapper[Any, Any]:
    """Logging wrapper.

    Example:
        ```python
        from chainedpy import Chain
        from chainedpy.plugins.wrappers import as_log
        import logging

        # Enable debug logging to see output
        logging.basicConfig(level=logging.DEBUG)

        # Log with default label
        result = await (
            Chain(5)
            .then_map(lambda x: x * 2)
            .as_log()
        )
        assert result == 10
        # Logs: "Input: 5" and "Output: 10"

        # Log with custom label
        result = await (
            Chain("hello")
            .then_map(str.upper)
            .as_log("UPPERCASE", level=logging.INFO)
        )
        assert result == "HELLO"
        # Logs: "UPPERCASE Input: hello" and "UPPERCASE Output: HELLO"

        # Log with warning level
        result = await (
            Chain([1, 2, 3])
            .then_map(sum)
            .as_log("SUM", level=logging.WARNING)
        )
        assert result == 6
        ```

    :param label: Optional label for log messages, defaults to "".
    :type label: [str][str], optional
    :param level: Logging level, defaults to logging.DEBUG.
    :type level: [int][int], optional
    :return [Wrapper][chainedpy.link.Wrapper][[Any][typing.Any], [Any][typing.Any]]: Wrapper that adds logging behavior.
    """
    class LogWrapper(Wrapper[Any, Any]):
        """Wrapper implementation for logging behavior."""

        def wrap(self, inner: Link[Any, Any]) -> Link[Any, Any]:
            """Wrap a link with logging behavior.

            :param inner: Link to wrap with logging logic.
            :type inner: Link[Any, Any]
            :return Link[Any, Any]: Link with logging behavior.
            """
            class LogLink(Link[Any, Any]):
                """Link implementation with logging logic."""
                name = f"log({inner.name})"

                async def __call__(self, arg: Any) -> Any:
                    """Execute with logging.

                    :param arg: Input argument.
                    :type arg: Any
                    :return Any: Result from execution.
                    """
                    # @@ STEP 1: Initialize logging. @@
                    logger = logging.getLogger("chainedpy")
                    prefix = f"[{label}] " if label else ""

                    logger.log(level, f"{prefix}Input: {arg!r}")
                    start_time = time.perf_counter()

                    # @@ STEP 2: Execute and log result or error. @@
                    try:
                        result = await inner(arg)
                        end_time = time.perf_counter()
                        duration = (end_time - start_time) * 1000  # Convert to ms.

                        logger.log(level, f"{prefix}Output: {result!r} (took {duration:.2f}ms)")
                        return result
                    except Exception as e:
                        end_time = time.perf_counter()
                        duration = (end_time - start_time) * 1000

                        logger.log(level, f"{prefix}Error: {e!r} (took {duration:.2f}ms)")
                        raise

            return LogLink()

    return LogWrapper()


# @@ STEP 1: Define simple cache implementation. @@
_cache: Dict[tuple, tuple[Any, float]] = {}  # (key) -> (value, expiry_time)


@as_("cache")
def as_cache(*, ttl: float = 60.0) -> Wrapper[Any, Any]:
    """TTL-based caching wrapper.

    Example:
        ```python
        from chainedpy import Chain
        from chainedpy.plugins.wrappers import as_cache
        import time

        # Cache expensive computation
        def expensive_computation(x):
            time.sleep(0.1)  # Simulate expensive operation
            return x * x

        # First call takes time, subsequent calls are cached
        start_time = time.time()
        result1 = await (
            Chain(5)
            .then_map(expensive_computation)
            .as_cache(ttl=30.0)  # Cache for 30 seconds
        )
        first_duration = time.time() - start_time

        # This should be much faster (cached)
        start_time = time.time()
        result2 = await (
            Chain(5)
            .then_map(expensive_computation)
            .as_cache(ttl=30.0)
        )
        second_duration = time.time() - start_time

        assert result1 == result2 == 25
        assert second_duration < first_duration

        # Cache with short TTL
        result = await (
            Chain("hello")
            .then_map(str.upper)
            .as_cache(ttl=1.0)  # Cache for 1 second
        )
        assert result == "HELLO"
        ```

    :param ttl: Time-to-live for cached values in seconds, defaults to 60.0.
    :type ttl: [float][float], optional
    :return [Wrapper][chainedpy.link.Wrapper][[Any][typing.Any], [Any][typing.Any]]: Wrapper that adds caching behavior.
    """
    class CacheWrapper(Wrapper[Any, Any]):
        """Wrapper implementation for caching behavior."""

        def wrap(self, inner: Link[Any, Any]) -> Link[Any, Any]:
            """Wrap a link with caching behavior.

            :param inner: Link to wrap with caching logic.
            :type inner: Link[Any, Any]
            :return Link[Any, Any]: Link with caching behavior.
            """
            class CacheLink(Link[Any, Any]):
                """Link implementation with caching logic."""
                name = f"cache({inner.name})"

                async def __call__(self, arg: Any) -> Any:
                    """Execute with caching.

                    :param arg: Input argument.
                    :type arg: Any
                    :return Any: Cached or computed result.
                    :raises CacheError: If caching fails.
                    """
                    # @@ STEP 1: Create cache key. @@
                    try:
                        # Try to create a hashable key.
                        if isinstance(arg, (str, int, float, bool, type(None))):
                            cache_key = (inner.name, arg)
                        elif isinstance(arg, (list, tuple)):
                            cache_key = (inner.name, tuple(arg))
                        elif isinstance(arg, dict):
                            cache_key = (inner.name, tuple(sorted(arg.items())))
                        else:
                            # For unhashable types, skip caching.
                            return await inner(arg)
                    except (TypeError, ValueError):
                        # If we can't create a key, skip caching.
                        return await inner(arg)

                    current_time = time.time()

                    # @@ STEP 2: Check if we have a valid cached result. @@
                    if cache_key in _cache:
                        cached_value, expiry_time = _cache[cache_key]
                        if current_time < expiry_time:
                            return cached_value
                        else:
                            # Expired, remove from cache.
                            del _cache[cache_key]

                    # @@ STEP 3: Execute and cache the result. @@
                    try:
                        result = await inner(arg)
                        expiry_time = current_time + ttl
                        _cache[cache_key] = (result, expiry_time)
                        return result
                    except Exception as e:
                        raise CacheError(f"Failed to cache result: {e}") from e

            return CacheLink()

    return CacheWrapper()


@as_("on_error")
def as_on_error(handler: Callable[[Exception], Any | Awaitable[Any]]) -> Wrapper[Any, Any]:
    """Error handling wrapper.

    Example:
        ```python
        from chainedpy import Chain
        from chainedpy.plugins.wrappers import as_on_error

        # Handle errors with fallback value
        def error_handler(error):
            print(f"Error occurred: {error}")
            return "fallback_value"

        result = await (
            Chain("input")
            .then_map(lambda x: 1 / 0)  # Will raise ZeroDivisionError
            .as_on_error(error_handler)
        )
        assert result == "fallback_value"

        # Handle errors with async handler
        async def async_error_handler(error):
            return f"Handled: {type(error).__name__}"

        result = await (
            Chain(42)
            .then_map(lambda x: x.invalid_method())  # AttributeError
            .as_on_error(async_error_handler)
        )
        assert result == "Handled: AttributeError"

        # No error case
        result = await (
            Chain(10)
            .then_map(lambda x: x * 2)
            .as_on_error(error_handler)
        )
        assert result == 20  # Handler not called
        ```

    :param handler: Function to handle exceptions.
    :type handler: [Callable][typing.Callable][[Exception], [Any][typing.Any] | [Awaitable][typing.Awaitable][[Any][typing.Any]]]
    :return [Wrapper][chainedpy.link.Wrapper][[Any][typing.Any], [Any][typing.Any]]: Wrapper that adds error handling behavior.
    """
    class ErrorWrapper(Wrapper[Any, Any]):
        """Wrapper implementation for error handling behavior."""

        def wrap(self, inner: Link[Any, Any]) -> Link[Any, Any]:
            """Wrap a link with error handling behavior.

            :param inner: Link to wrap with error handling logic.
            :type inner: Link[Any, Any]
            :return Link[Any, Any]: Link with error handling behavior.
            """
            class ErrorLink(Link[Any, Any]):
                """Link implementation with error handling logic."""
                name = f"on_error({inner.name})"

                async def __call__(self, arg: Any) -> Any:
                    """Execute with error handling.

                    :param arg: Input argument.
                    :type arg: Any
                    :return Any: Result from execution or error handler.
                    """
                    try:
                        return await inner(arg)
                    except Exception as e:
                        # Call the error handler.
                        result = handler(e)
                        if asyncio.iscoroutine(result):
                            return await result
                        else:
                            return result

            return ErrorLink()

    return ErrorWrapper()
