"""ChainedPy Exception Hierarchy.

This module provides a comprehensive error taxonomy for ChainedPy operations with proper error
propagation and recovery mechanisms. All exceptions maintain immutability and functional principles,
providing structured error handling throughout the ChainedPy ecosystem.

The exception hierarchy is designed with automatic logging capabilities to prevent double logging
and includes rich context information for debugging. Each exception class serves a specific
domain within ChainedPy, from core chain operations to service-specific errors.

Note:
    All exceptions inherit from [ChainError][chainedpy.exceptions.ChainError] which provides
    automatic logging and context management. This ensures consistent error handling
    across the entire codebase.

Example:
    ```python
    from chainedpy.exceptions import ChainError, ValidationError

    # Basic exception usage
    try:
        raise ChainError("Something went wrong", context={"step": 1})
    except ChainError as e:
        print(f"Error: {e.message}")
        print(f"Context: {e.context}")

    # Domain-specific exceptions
    try:
        raise ValidationError("Invalid input", context={"field": "name"})
    except ValidationError as e:
        print(f"Validation failed: {e}")
    ```

See Also:
    - [ChainError][chainedpy.exceptions.ChainError]: Base exception class
    - [ValidationError][chainedpy.exceptions.ValidationError]: Input validation errors
    - [chainedpy.services.logging_service][chainedpy.services.logging_service]: Logging service used by exceptions
"""

from typing import Any, Optional
import asyncio


class ChainError(Exception):
    """Base exception for all ChainedPy-related errors.

    Maintains immutability by storing error context without mutation.
    All ChainedPy exceptions inherit from this base class, providing
    consistent error handling and automatic logging capabilities.

    Automatically logs error messages when exceptions are created to prevent
    double logging in except blocks throughout the codebase. This ensures
    that all errors are properly recorded without requiring explicit logging
    at every catch site.

    :param message: The error message.
    :type message: [str][str]
    :param context: Additional error context, defaults to None.
    :type context: [Optional][typing.Optional][[dict][dict][[str][str], [Any][typing.Any]]], optional
    :param auto_log: Whether to automatically log the error, defaults to True.
    :type auto_log: [bool][bool], optional

    Example:
        ```python
        from chainedpy.exceptions import ChainError

        # Basic usage with message only
        raise ChainError("Operation failed")

        # With context information
        raise ChainError(
            "Chain execution failed",
            context={"step": 3, "input": "invalid_data"}
        )

        # Disable auto-logging for custom handling
        error = ChainError("Silent error", auto_log=False)
        # Handle logging manually if needed
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        context: Optional[dict[str, Any]] = None,
        auto_log: bool = True
    ) -> None:
        """Initialize ChainError with message and optional context.

        Example:
            ```python
            from chainedpy.exceptions import ChainError

            # Initialize with message only
            error = ChainError("Something went wrong")

            # Initialize with context
            error = ChainError(
                "Validation failed",
                context={"field": "email", "value": "invalid"}
            )

            # Initialize without auto-logging
            error = ChainError("Silent error", auto_log=False)
            ```

        :param message: The error message.
        :type message: [str][str]
        :param context: Additional error context, defaults to None.
        :type context: [Optional][typing.Optional][[dict][dict][[str][str], [Any][typing.Any]]], optional
        :param auto_log: Whether to automatically log the error, defaults to True.
        :type auto_log: [bool][bool], optional
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

        # @@ STEP 1: Auto-log error if enabled. @@
        if auto_log:
            self._log_error()

    def _log_error(self) -> None:
        """Log the error message automatically when exception is created.

        This prevents double logging when get_logger().error() is called
        in except blocks before raising ChainedPy exceptions.
        """
        try:
            # Import logging service to log the error.
            from chainedpy.services.logging_service import get_logger
            get_logger().error(str(self))
        except Exception:
            # If logging fails, don't break exception creation.
            # This is acceptable as the exception itself is more important.
            pass

    def __str__(self) -> str:
        """Return string representation of the error.

        :return str: Formatted error message with context if available.
        """
        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} (context: {context_str})"
        return self.message


class ValidationError(ChainError):
    """Raised when synchronous validation fails.

    Used for argument type mismatches, invalid configurations,
    and other pre-execution validation failures. This exception
    is raised before chain execution begins when input validation
    detects problems that would prevent successful execution.

    Example:
        ```python
        from chainedpy.exceptions import ValidationError
        from chainedpy import Chain

        # Validation error from filter
        try:
            await (
                Chain(3)
                .then_filter(lambda x: x > 5)
            )
        except ValidationError as e:
            print(f"Validation failed: {e}")
            assert "filter" in str(e).lower()

        # Validation error from switch without default
        try:
            await (
                Chain("xyz")
                .then_switch(
                    key=lambda x: x[0],
                    cases={'a': "vowel", 'e': "vowel"}
                )
            )
        except ValidationError as e:
            print(f"No matching case: {e}")

        # Custom validation error
        raise ValidationError(
            "Invalid input format",
            context={"input": "bad_value", "expected": "good_value"}
        )
        ```
    """
    pass


class RetryExhausted(ChainError):
    """Raised when as_retry exhausts all attempts.

    Contains information about the number of attempts made and the final exception
    that caused the retry to fail permanently.

    :param attempts: Number of retry attempts made.
    :type attempts: int
    :param final_exception: The final exception that caused retry failure.
    :type final_exception: Exception
    :param delay: Delay between retry attempts, defaults to 1.0.
    :type delay: float, optional
    """

    def __init__(self, attempts: int, final_exception: Exception, delay: float = 1.0) -> None:
        """Initialize RetryExhausted with attempt details.

        :param attempts: Number of retry attempts made.
        :type attempts: int
        :param final_exception: The final exception that caused retry failure.
        :type final_exception: Exception
        :param delay: Delay between retry attempts, defaults to 1.0.
        :type delay: float, optional
        """
        message = f"Retry exhausted after {attempts} attempts"
        context = {
            "attempts": attempts,
            "delay": delay,
            "final_exception_type": type(final_exception).__name__,
            "final_exception_message": str(final_exception)
        }
        super().__init__(message, context=context, auto_log=True)
        self.attempts = attempts
        self.final_exception = final_exception
        self.delay = delay

class TimeoutExpired(ChainError):
    """Raised when as_timeout expires.

    Wraps asyncio.TimeoutError with additional context about the operation
    that timed out and the configured timeout duration.

    :param seconds: Timeout duration in seconds.
    :type seconds: float
    :param operation: Name of the operation that timed out, defaults to "unknown".
    :type operation: str, optional
    """

    def __init__(self, seconds: float, operation: str = "unknown") -> None:
        """Initialize TimeoutExpired with timeout details.

        :param seconds: Timeout duration in seconds.
        :type seconds: float
        :param operation: Name of the operation that timed out, defaults to "unknown".
        :type operation: str, optional
        """
        message = f"Operation '{operation}' timed out after {seconds} seconds"
        context = {
            "seconds": seconds,
            "operation": operation
        }
        super().__init__(message, context=context, auto_log=True)
        self.seconds = seconds
        self.operation = operation


class CacheError(ChainError):
    """Raised when as_cache encounters errors.

    Used for cache-related failures such as serialization errors,
    memory pressure, or cache corruption. This exception indicates
    that caching operations have failed but the underlying chain
    operation may still be retryable.

    Example:
        ```python
        from chainedpy.exceptions import CacheError
        from chainedpy import Chain

        # Cache error from serialization failure
        def unserializable_operation(x):
            # Returns something that can't be cached
            return lambda: x * 2  # Functions can't be serialized

        try:
            result = await (
                Chain(5)
                .then_map(unserializable_operation)
                .as_cache(ttl=60.0)
            )
        except CacheError as e:
            print(f"Cache failed: {e}")
            # Chain might still work without caching

        # Custom cache error
        raise CacheError(
            "Cache storage full",
            context={"cache_size": "100MB", "available": "0MB"}
        )
        ```
    """
    pass


class ProcessorError(ChainError):
    """Raised when Proc enum operations fail.

    Contains information about the processor that failed and the input
    that caused the failure, maintaining immutability.

    :param processor_name: Name of the processor that failed.
    :type processor_name: str
    :param input_value: Input value that caused the failure.
    :type input_value: Any
    :param original_exception: The original exception that caused the failure.
    :type original_exception: Exception
    """

    def __init__(
        self,
        processor_name: str,
        input_value: Any,
        original_exception: Exception
    ) -> None:
        """Initialize ProcessorError with processor failure details.

        :param processor_name: Name of the processor that failed.
        :type processor_name: str
        :param input_value: Input value that caused the failure.
        :type input_value: Any
        :param original_exception: The original exception that caused the failure.
        :type original_exception: Exception
        """
        message = f"Processor '{processor_name}' failed"
        context = {
            "processor": processor_name,
            "input_type": type(input_value).__name__,
            "input_repr": repr(input_value)[:100],  # Truncate for safety.
            "original_exception_type": type(original_exception).__name__,
            "original_exception_message": str(original_exception)
        }
        super().__init__(message, context=context, auto_log=True)
        self.processor_name = processor_name
        self.input_value = input_value
        self.original_exception = original_exception


class ConcurrencyError(ChainError):
    """Raised when parallel operations encounter errors.

    Used for semaphore limit violations, gather failures,
    and other concurrency-related issues. This exception
    indicates problems with concurrent execution that may
    require adjusting concurrency limits or retry strategies.

    Example:
        ```python
        from chainedpy.exceptions import ConcurrencyError
        from chainedpy import Chain
        import asyncio

        # Concurrency error from resource limits
        async def resource_limited_operation(x):
            # Simulate resource contention
            if too_many_concurrent_operations():
                raise ConcurrencyError(
                    "Too many concurrent operations",
                    context={"current": 100, "limit": 50}
                )
            return x * 2

        try:
            result = await (
                Chain([1, 2, 3, 4, 5])
                .then_parallel_foreach(
                    transform=resource_limited_operation,
                    limit=10  # Too high for system
                )
            )
        except ConcurrencyError as e:
            print(f"Concurrency limit exceeded: {e}")

        # Custom concurrency error
        raise ConcurrencyError(
            "Semaphore acquisition failed",
            context={"timeout": 30, "waiters": 25}
        )
        ```
    """
    pass


class ExtensibilityError(ChainError):
    """Raised when plugin/extension operations fail.

    Used for plugin discovery failures, registration errors,
    and custom processor/wrapper integration issues. This exception
    indicates problems with the plugin system or custom extensions
    that prevent proper chain method registration or execution.

    Example:
        ```python
        from chainedpy.exceptions import ExtensibilityError
        from chainedpy.register import then

        # Plugin registration error
        try:
            @then("invalid_method")
            def create_invalid_link():
                # Missing required return type
                pass
        except ExtensibilityError as e:
            print(f"Plugin registration failed: {e}")

        # Custom processor integration error
        class BadProcessor:
            # Missing required methods
            pass

        try:
            register_custom_processor(BadProcessor())
        except ExtensibilityError as e:
            print(f"Processor integration failed: {e}")

        # Custom extensibility error
        raise ExtensibilityError(
            "Plugin discovery failed",
            context={"plugin_dir": "/path/to/plugins", "error": "permission_denied"}
        )
        ```
    """
    pass


class FilesystemServiceError(ChainError):
    """Exception raised when filesystem operations fail.

    This exception is raised by the filesystem service when file operations
    encounter errors such as permission denied, file not found, network
    failures for remote files, or other I/O related issues.

    Example:
        ```python
        from chainedpy.exceptions import FilesystemServiceError
        from chainedpy.services import filesystem_service as fs
        from pathlib import Path

        # File not found error
        try:
            content = fs.read_text(Path("nonexistent.txt"))
        except FilesystemServiceError as e:
            print(f"File operation failed: {e}")
            assert "not found" in str(e).lower()

        # Permission error
        try:
            fs.write_text(Path("/root/protected.txt"), "content")
        except FilesystemServiceError as e:
            print(f"Permission denied: {e}")

        # Custom filesystem error
        raise FilesystemServiceError(
            "Remote file access failed",
            context={"url": "https://example.com/file.txt", "status": 404}
        )
        ```
    """
    pass


class ASTServiceError(ChainError):
    """Exception raised by AST service operations.

    This exception is raised when AST parsing, analysis, or code generation
    operations fail. Common causes include syntax errors in source code,
    malformed AST structures, or failures in stub generation.

    Example:
        ```python
        from chainedpy.exceptions import ASTServiceError
        from chainedpy.services import ast_service

        # Syntax error in source code
        try:
            tree = ast_service.parse_source_code("def invalid syntax:")
        except ASTServiceError as e:
            print(f"AST parsing failed: {e}")
            assert "syntax" in str(e).lower()

        # Method discovery error
        try:
            methods = ast_service.discover_chain_methods(Path("invalid.py"))
        except ASTServiceError as e:
            print(f"Method discovery failed: {e}")

        # Custom AST error
        raise ASTServiceError(
            "Stub generation failed",
            context={"file": "chain.py", "line": 42, "error": "invalid_signature"}
        )
        ```
    """
    pass


class ProjectValidationError(ChainError):
    """Exception raised when project validation fails.

    This exception is raised when ChainedPy project validation detects
    structural problems, missing required files, invalid configurations,
    or other issues that prevent a project from being used properly.

    Example:
        ```python
        from chainedpy.exceptions import ProjectValidationError
        from chainedpy.services.project_validation import validate_local_project
        from pathlib import Path

        # Missing configuration file
        try:
            validate_local_project("./incomplete_project")
        except ProjectValidationError as e:
            print(f"Project validation failed: {e}")
            assert "chainedpy.yaml" in str(e)

        # Invalid project structure
        try:
            validate_local_project("./malformed_project")
        except ProjectValidationError as e:
            print(f"Invalid structure: {e}")

        # Custom validation error
        raise ProjectValidationError(
            "Missing required chain file",
            context={"project": "my_project", "missing": "my_project_chain.py"}
        )
        ```
    """
    pass


class GitignoreServiceError(ChainError):
    """Exception raised when gitignore operations fail.

    This exception is raised when gitignore file creation, modification,
    or parsing operations encounter errors such as file permission issues,
    invalid patterns, or I/O failures.

    Example:
        ```python
        from chainedpy.exceptions import GitignoreServiceError
        from chainedpy.services.gitignore_service import create_project_gitignore
        from pathlib import Path

        # Permission error creating gitignore
        try:
            create_project_gitignore(Path("/root/protected_project"))
        except GitignoreServiceError as e:
            print(f"Gitignore creation failed: {e}")
            assert "permission" in str(e).lower()

        # Invalid gitignore pattern
        try:
            add_gitignore_pattern(Path("./project"), "[invalid regex")
        except GitignoreServiceError as e:
            print(f"Invalid pattern: {e}")

        # Custom gitignore error
        raise GitignoreServiceError(
            "Failed to update gitignore",
            context={"file": ".gitignore", "pattern": "*.tmp", "error": "readonly"}
        )
        ```
    """
    pass


class RemoteChainServiceError(ChainError):
    """Exception raised when remote chain operations fail.

    This exception is raised when downloading, updating, or managing remote
    ChainedPy projects encounters errors such as network failures, authentication
    issues, invalid URLs, or repository access problems.

    Example:
        ```python
        from chainedpy.exceptions import RemoteChainServiceError
        from chainedpy.services.remote_chain_service import download_remote_chain
        from pathlib import Path

        # Network error downloading remote chain
        try:
            download_remote_chain(
                "https://invalid-url.com/chain",
                Path("./project")
            )
        except RemoteChainServiceError as e:
            print(f"Download failed: {e}")
            assert "network" in str(e).lower() or "url" in str(e).lower()

        # Authentication error
        try:
            download_remote_chain(
                "https://github.com/private/repo",
                Path("./project"),
                github_token="invalid_token"
            )
        except RemoteChainServiceError as e:
            print(f"Authentication failed: {e}")

        # Custom remote chain error
        raise RemoteChainServiceError(
            "Repository not found",
            context={"url": "https://github.com/user/repo", "status": 404}
        )
        ```
    """
    pass


class StubGenerationError(ChainError):
    """Exception raised when stub generation operations fail.

    This exception is raised when type stub (.pyi) file generation encounters
    errors such as AST parsing failures, template rendering issues, file I/O
    problems, or invalid method signatures during stub creation.

    Example:
        ```python
        from chainedpy.exceptions import StubGenerationError
        from chainedpy.services.stub_generation_service import generate_project_stub
        from pathlib import Path

        # Stub generation error from invalid source
        try:
            generate_project_stub(Path("./malformed_project"))
        except StubGenerationError as e:
            print(f"Stub generation failed: {e}")
            assert "generation" in str(e).lower()

        # Template rendering error
        try:
            generate_stub_with_invalid_template(Path("./project"))
        except StubGenerationError as e:
            print(f"Template error: {e}")

        # Custom stub generation error
        raise StubGenerationError(
            "Method signature extraction failed",
            context={"method": "then_custom", "file": "chain.py", "line": 42}
        )
        ```
    """
    pass


class ProjectRemoteChainServiceError(ChainError):
    """Exception raised when project remote chain operations fail.

    This exception is raised when project-specific remote chain management
    operations encounter errors such as dependency resolution failures,
    update conflicts, or integration issues within project directories.

    Example:
        ```python
        from chainedpy.exceptions import ProjectRemoteChainServiceError
        from chainedpy.services.project_remote_chain_service import update_project_chains
        from pathlib import Path

        # Dependency resolution error
        try:
            update_project_chains(Path("./project_with_conflicts"))
        except ProjectRemoteChainServiceError as e:
            print(f"Chain update failed: {e}")
            assert "dependency" in str(e).lower() or "conflict" in str(e).lower()

        # Integration error
        try:
            integrate_remote_chain(Path("./project"), "incompatible_chain")
        except ProjectRemoteChainServiceError as e:
            print(f"Integration failed: {e}")

        # Custom project remote chain error
        raise ProjectRemoteChainServiceError(
            "Circular dependency detected",
            context={"chain": "chain_a", "depends_on": "chain_b", "cycle": ["chain_a", "chain_b", "chain_a"]}
        )
        ```
    """
    pass


class ProjectLifecycleError(ChainError):
    """Exception raised when project lifecycle operations fail.

    This exception is raised when project creation, activation, deactivation,
    or other lifecycle management operations encounter errors such as file
    system issues, configuration problems, or state management failures.

    Example:
        ```python
        from chainedpy.exceptions import ProjectLifecycleError
        from chainedpy.services.project_lifecycle import create_project, activate_project
        from pathlib import Path

        # Project creation error
        try:
            create_project(
                name="invalid/name",  # Invalid characters
                dest=Path("./projects")
            )
        except ProjectLifecycleError as e:
            print(f"Project creation failed: {e}")
            assert "name" in str(e).lower()

        # Activation error
        try:
            activate_project(Path("./nonexistent_project"))
        except ProjectLifecycleError as e:
            print(f"Activation failed: {e}")

        # Custom lifecycle error
        raise ProjectLifecycleError(
            "Project state corruption detected",
            context={"project": "my_project", "state": "partially_activated", "action": "deactivate"}
        )
        ```
    """
    pass


class ChainTraversalError(ChainError):
    """Exception raised during chain traversal.

    This exception is raised when traversing project inheritance chains
    encounters errors such as circular dependencies, missing base projects,
    or infinite recursion in the project hierarchy.

    Example:
        ```python
        from chainedpy.exceptions import ChainTraversalError
        from chainedpy.services.chain_traversal_service import get_project_chain
        from pathlib import Path

        # Circular dependency error
        try:
            # Project A inherits from B, B inherits from A
            chain_info = get_project_chain(Path("./circular_project"))
        except ChainTraversalError as e:
            print(f"Chain traversal failed: {e}")
            assert "circular" in str(e).lower()

        # Missing base project
        try:
            chain_info = get_project_chain(Path("./orphaned_project"))
        except ChainTraversalError as e:
            print(f"Missing base: {e}")

        # Custom traversal error
        raise ChainTraversalError(
            "Maximum traversal depth exceeded",
            context={"depth": 100, "limit": 50, "current_project": "deep_project"}
        )
        ```
    """
    pass


class ProjectFileServiceError(ChainError):
    """Exception raised when project file operations fail.

    This exception is raised when project file creation, modification, or
    management operations encounter errors such as template rendering failures,
    file permission issues, or invalid project structures.

    Example:
        ```python
        from chainedpy.exceptions import ProjectFileServiceError
        from chainedpy.services.project_file_service import create_project_structure
        from pathlib import Path

        # File creation error
        try:
            create_project_structure(
                Path("/root/protected"),  # No permission
                "my_project",
                "chainedpy",
                "Test project"
            )
        except ProjectFileServiceError as e:
            print(f"File creation failed: {e}")
            assert "permission" in str(e).lower()

        # Template rendering error
        try:
            create_chain_file_with_invalid_template(Path("./project"))
        except ProjectFileServiceError as e:
            print(f"Template error: {e}")

        # Custom project file error
        raise ProjectFileServiceError(
            "Chain file generation failed",
            context={"template": "chain_py.j2", "project": "my_project", "error": "missing_variable"}
        )
        ```
    """
    pass


class CredentialServiceError(ChainError):
    """Exception raised when credential operations fail.

    This exception is raised when credential management operations encounter
    errors such as missing environment variables, invalid tokens, credential
    file access issues, or authentication failures.

    Example:
        ```python
        from chainedpy.exceptions import CredentialServiceError
        from chainedpy.services.credential_service import load_credentials_for_url
        from pathlib import Path

        # Missing credentials error
        try:
            credentials = load_credentials_for_url(
                "https://github.com/private/repo",
                Path("./project_without_env")
            )
        except CredentialServiceError as e:
            print(f"Credentials missing: {e}")
            assert "token" in str(e).lower() or "credential" in str(e).lower()

        # Invalid token format
        try:
            validate_github_token("invalid_token_format")
        except CredentialServiceError as e:
            print(f"Invalid token: {e}")

        # Custom credential error
        raise CredentialServiceError(
            "Environment file creation failed",
            context={"file": ".env", "project": "my_project", "error": "readonly_filesystem"}
        )
        ```
    """
    pass


class TemplateServiceError(ChainError):
    """Exception raised when template operations fail.

    This exception is raised when Jinja2 template rendering, loading, or
    processing operations encounter errors such as template syntax errors,
    missing variables, template not found, or rendering failures.

    Example:
        ```python
        from chainedpy.exceptions import TemplateServiceError
        from chainedpy.services.template_service import render_template

        # Template not found error
        try:
            content = render_template("nonexistent_template.j2", {})
        except TemplateServiceError as e:
            print(f"Template not found: {e}")
            assert "not found" in str(e).lower()

        # Missing variable error
        try:
            content = render_template(
                "project/chain_py.j2",
                {}  # Missing required variables
            )
        except TemplateServiceError as e:
            print(f"Missing variables: {e}")

        # Custom template error
        raise TemplateServiceError(
            "Template syntax error",
            context={"template": "custom.j2", "line": 15, "error": "unexpected_token"}
        )
        ```
    """
    pass


class ShellIntegrationError(ChainError):
    """Exception raised when shell integration operations fail.

    This exception is raised when shell script generation, shell detection,
    environment variable management, or shell configuration operations
    encounter errors such as unsupported shells or permission issues.

    Example:
        ```python
        from chainedpy.exceptions import ShellIntegrationError
        from chainedpy.services.shell_integration import generate_activation_script
        from pathlib import Path

        # Unsupported shell error
        try:
            script = generate_activation_script(
                Path("./project"),
                "unsupported_shell"
            )
        except ShellIntegrationError as e:
            print(f"Shell not supported: {e}")
            assert "unsupported" in str(e).lower()

        # Shell configuration error
        try:
            initialize_shell_integration("bash", force=True)
        except ShellIntegrationError as e:
            print(f"Shell integration failed: {e}")

        # Custom shell integration error
        raise ShellIntegrationError(
            "Shell script generation failed",
            context={"shell": "zsh", "project": "my_project", "error": "template_missing"}
        )
        ```
    """
    pass


# @@ STEP 2: Define exception mapping utilities. @@

def wrap_asyncio_error(exc: Exception, context: Optional[dict[str, Any]] = None) -> ChainError:
    """Convert common asyncio exceptions to ChainedPy exceptions.

    Maintains the original exception as context while providing
    ChainedPy-specific error handling.

    :param exc: The asyncio exception to wrap.
    :type exc: Exception
    :param context: Additional error context, defaults to None.
    :type context: Optional[dict[str, Any]], optional
    :return ChainError: Wrapped ChainedPy exception.
    """
    if isinstance(exc, asyncio.TimeoutError):
        return TimeoutExpired(
            seconds=context.get("timeout", 0.0) if context else 0.0,
            operation=context.get("operation", "unknown") if context else "unknown"
        )
    elif isinstance(exc, asyncio.CancelledError):
        return ConcurrencyError(
            "Operation was cancelled",
            context={"original_exception": str(exc), **(context or {})}
        )
    else:
        return ChainError(
            f"Asyncio error: {exc}",
            context={"original_exception_type": type(exc).__name__, **(context or {})}
        )


# @@ STEP 3: Define error recovery utilities. @@

def is_recoverable_error(exc: Exception) -> bool:
    """Determine if an exception is recoverable by retry mechanisms.

    Returns True for transient errors that might succeed on retry,
    False for permanent errors that should not be retried.

    :param exc: The exception to check for recoverability.
    :type exc: Exception
    :return bool: True if the error is recoverable, False otherwise.
    """
    # Network-related errors are typically recoverable.
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True

    # ChainedPy timeout errors are recoverable.
    if isinstance(exc, TimeoutExpired):
        return True

    # Validation and processor errors are typically not recoverable.
    if isinstance(exc, (ValidationError, ProcessorError)):
        return False

    # Default to not recoverable for safety.
    return False


def create_error_context(
    operation: str,
    input_value: Any = None,
    **kwargs: Any
) -> dict[str, Any]:
    """Create standardized error context for ChainedPy exceptions.

    Provides consistent error context formatting across the library.

    :param operation: Name of the operation that failed.
    :type operation: str
    :param input_value: Input value that caused the error, defaults to None.
    :type input_value: Any, optional
    :param kwargs: Additional context parameters.
    :type kwargs: Any
    :return dict[str, Any]: Standardized error context dictionary.
    """
    context = {"operation": operation, **kwargs}

    if input_value is not None:
        context.update({
            "input_type": type(input_value).__name__,
            "input_repr": repr(input_value)[:100]  # Truncate for safety.
        })

    return context
