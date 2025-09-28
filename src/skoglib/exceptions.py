"""Custom exception hierarchy for skoglib.

This module defines the complete exception hierarchy used throughout the skoglib
library, providing clear error messages, structured debugging context, and
integrated logging for comprehensive error handling.

The exception hierarchy follows Python best practices with a clear inheritance
structure that allows for both specific and general exception handling patterns.

Exception Hierarchy:
    SkogAIError (base)
    ├── ExecutableNotFoundError (executable not in PATH)
    ├── ExecutionError (execution failed/timeout)
    └── ConfigurationError (invalid parameters)

Key Features:
- Automatic logging integration with context preservation
- Structured error context for debugging
- Clear inheritance hierarchy for flexible error handling
- Performance-conscious design with optional logging

Usage Examples:
    Basic exception handling:

    >>> from skoglib import run_executable, ExecutableNotFoundError
    >>> try:
    ...     result = run_executable("nonexistent_command")
    ... except ExecutableNotFoundError as e:
    ...     print(f"Command not found: {e.executable}")
    ...     print(f"Searched in: {e.search_paths}")

    Catching all skoglib errors:

    >>> from skoglib import run_executable, SkogAIError
    >>> try:
    ...     result = run_executable("some_command", invalid_args=True)
    ... except SkogAIError as e:
    ...     print(f"Library error: {e}")
    ...     print(f"Context: {e.context}")

    Execution error handling:

    >>> from skoglib import run_executable, ExecutionError
    >>> try:
    ...     result = run_executable("false")  # Always fails
    ... except ExecutionError as e:
    ...     print(f"Exit code: {e.exit_code}")
    ...     print(f"Command: {e.executable} {' '.join(e.command_args)}")
    ...     print(f"Duration: {e.execution_time:.3f}s")
"""

import time
import logging
from typing import Optional, Dict, Any, List
from .logging_config import get_logger


# Logger for exception module
logger = get_logger("exceptions")


class SkogAIError(Exception):
    """Base exception class for all skoglib-related errors.

    This is the root exception that all other skoglib exceptions inherit from,
    providing consistent error handling, context preservation, and optional
    logging integration. It serves as a catch-all for any library-related
    issues while maintaining detailed debugging information.

    The base class handles automatic logging, context preservation, and
    provides a consistent interface for error inspection across all
    skoglib exception types.

    Attributes:
        message: Human-readable error description
        context: Dictionary containing debugging context and metadata

    Examples:
        Creating a custom error with context:

        >>> error = SkogAIError("Something went wrong", {
        ...     "operation": "test",
        ...     "parameters": {"timeout": 30}
        ... })
        >>> print(error.message)
        Something went wrong
        >>> print(error.context["operation"])
        test

        Handling any skoglib error:

        >>> try:
        ...     # Some skoglib operation
        ...     pass
        ... except SkogAIError as e:
        ...     print(f"Library error: {e}")
        ...     if e.context:
        ...         print(f"Additional context: {e.context}")
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,  # Backward compatibility
        log_error: bool = True,
    ) -> None:
        """
        Initialize a SkogAI error.

        Args:
            message: Human-readable error message
            details: Additional debugging details (optional)
            context: Additional debugging context (deprecated, use details)
            log_error: Whether to log this error when raised (default: True)
        """
        super().__init__(message)
        self.message = message

        # Support both details and context for backward compatibility
        if details is not None and context is not None:
            raise ValueError(
                "Cannot specify both 'details' and 'context'. Use 'details' (preferred)."
            )

        self.details = details or context or {}
        self.context = self.details  # Maintain backward compatibility
        self.timestamp = time.time()

        # Log error with details for debugging
        # Check if logger is enabled for ERROR level to avoid expensive operations
        if log_error and logger.isEnabledFor(logging.ERROR):
            if self.details:
                # Use "Context:" for backward compatibility with existing tests
                logger.error(f"{message} - Context: {self.details}")
            else:
                logger.error(message)

    def __str__(self) -> str:
        """Return string representation with details if available."""
        if not self.details:
            return self.message

        details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
        # Use "context:" for backward compatibility with existing tests
        return f"{self.message} (context: {details_str})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/debugging."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self.message),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class ExecutableNotFoundError(SkogAIError):
    """Raised when a required executable cannot be found in the system PATH.

    This error indicates that the executable specified for running was not
    found in the system PATH or at the specified absolute path. It includes
    comprehensive debugging information including the search paths that were
    examined, making it easier to diagnose PATH-related issues.

    This is typically the most common error when using skoglib, occurring
    when dependencies are not installed or PATH is not configured correctly.

    Attributes:
        executable: Name or path of the executable that was not found
        search_paths: List of directories that were searched for the executable

    Examples:
        Handling missing executables:

        >>> from skoglib import run_executable, ExecutableNotFoundError
        >>> try:
        ...     result = run_executable("nonexistent_tool")
        ... except ExecutableNotFoundError as e:
        ...     print(f"Missing executable: {e.executable}")
        ...     print(f"Searched in {len(e.search_paths)} directories")
        ...     # Could suggest installation or PATH fixes

        Checking if a tool is available:

        >>> def is_tool_available(tool_name):
        ...     try:
        ...         run_executable(tool_name, ["--version"])
        ...         return True
        ...     except ExecutableNotFoundError:
        ...         return False
        >>> if not is_tool_available("git"):
        ...     print("Git is not installed or not in PATH")
    """

    def __init__(
        self,
        executable: str,
        search_paths: Optional[List[str]] = None,
        log_error: bool = True,
    ) -> None:
        """
        Initialize an executable not found error.

        Args:
            executable: Name or path of the executable that was not found
            search_paths: List of paths that were searched (optional)
        """
        details: Dict[str, Any] = {
            "executable": executable,
            "suggestions": [
                "Install the tool using your package manager",
                "Check if the executable is in your PATH variable",
                "Use absolute path to the executable",
                "Verify the executable name is correct",
            ],
        }
        if search_paths:
            details["search_paths"] = search_paths

        message = f"Executable '{executable}' not found in PATH or specified location"
        if search_paths:
            message += f" (searched: {', '.join(search_paths)})"

        super().__init__(message, details, log_error=log_error)
        self.executable = executable
        self.search_paths = search_paths or []


class ExecutionError(SkogAIError):
    """Raised when an executable runs but fails with a non-zero exit code.

    This error captures comprehensive execution details including exit code,
    stdout, stderr, and timing information for debugging purposes. It's raised
    when `check_exit_code=True` (default) and the executed program returns
    a non-zero exit code, or when execution times out.

    The error provides complete context about the failed execution, making it
    easier to diagnose what went wrong and potentially recover or provide
    meaningful feedback to users.

    Attributes:
        executable: Name of the executable that failed
        exit_code: Non-zero exit code returned by the executable
        command_args: Arguments passed to the executable
        stdout: Standard output from the execution (may be None if not captured)
        stderr: Standard error from the execution (may be None if not captured)
        execution_time: Time taken for execution in seconds (may be None)

    Special Exit Codes:
        -1: Execution timeout (subprocess.TimeoutExpired)
        -2: OS-level error (OSError during execution)

    Examples:
        Handling execution failures:

        >>> from skoglib import run_executable, ExecutionError
        >>> try:
        ...     result = run_executable("grep", ["nonexistent_pattern", "/dev/null"])
        ... except ExecutionError as e:
        ...     if e.exit_code == 1:  # grep returns 1 for no matches
        ...         print("Pattern not found (expected)")
        ...     else:
        ...         print(f"Unexpected error: {e.stderr}")

        Timeout handling:

        >>> try:
        ...     result = run_executable("sleep", ["10"], timeout=1.0)
        ... except ExecutionError as e:
        ...     if e.exit_code == -1:
        ...         print(f"Command timed out after {e.execution_time:.1f}s")
        ...     else:
        ...         print(f"Command failed: {e}")

        Capturing detailed error information:

        >>> try:
        ...     result = run_executable("python", ["-c", "import sys; sys.exit(42)"])
        ... except ExecutionError as e:
        ...     print(f"Python script failed with code {e.exit_code}")
        ...     print(f"Command: {e.executable} {' '.join(e.command_args)}")
        ...     print(f"Execution time: {e.execution_time:.3f}s")
    """

    def __init__(
        self,
        executable: str,
        exit_code: int,
        command_args: Optional[list[str]] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        execution_time: Optional[float] = None,
        log_error: bool = True,
    ) -> None:
        """
        Initialize an execution error.

        Args:
            executable: Name of the executable that failed
            exit_code: Non-zero exit code returned by the executable
            command_args: Arguments passed to the executable (optional)
            stdout: Standard output from the execution (optional)
            stderr: Standard error from the execution (optional)
            execution_time: Time taken for execution in seconds (optional)
        """
        details = {
            "executable": executable,
            "exit_code": exit_code,
            "suggestions": [
                "Check the command arguments for correctness",
                "Verify input data and file permissions",
                "Review stderr output for specific error details",
                "Consult the tool's documentation for exit code meanings",
            ],
        }

        if command_args:
            details["command_args"] = command_args
        if stdout:
            details["stdout"] = stdout
        if stderr:
            details["stderr"] = stderr
        if execution_time is not None:
            details["execution_time"] = execution_time

        cmd_str = executable
        if command_args:
            cmd_str += " " + " ".join(command_args)

        message = f"Command '{cmd_str}' failed with exit code {exit_code}"

        super().__init__(message, details, log_error=log_error)
        self.executable = executable
        self.exit_code = exit_code
        self.command_args = command_args or []
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time


class TimeoutError(ExecutionError):
    """
    Raised when executable execution times out.

    This error indicates that the executable did not complete within
    the specified timeout period and was terminated.
    """

    def __init__(
        self,
        executable: str,
        timeout: float,
        command_args: Optional[list[str]] = None,
        partial_stdout: Optional[str] = None,
        partial_stderr: Optional[str] = None,
        log_error: bool = True,
    ) -> None:
        """
        Initialize a timeout error.

        Args:
            executable: Name of the executable that timed out
            timeout: Timeout duration in seconds that was exceeded
            command_args: Arguments passed to the executable (optional)
            partial_stdout: Partial stdout captured before timeout (optional)
            partial_stderr: Partial stderr captured before timeout (optional)
        """
        details = {
            "timeout": timeout,
            "suggestions": [
                f"Increase timeout (currently {timeout}s)",
                "Check for hanging processes or infinite loops",
                "Verify input data doesn't cause processing delays",
                "Consider breaking large tasks into smaller chunks",
            ],
        }

        if command_args:
            details["command_args"] = command_args
        if partial_stdout:
            details["partial_stdout"] = partial_stdout
        if partial_stderr:
            details["partial_stderr"] = partial_stderr

        cmd_str = executable
        if command_args:
            cmd_str += " " + " ".join(command_args)

        message = f"Command '{cmd_str}' timed out after {timeout} seconds"

        # Call SkogAIError directly to avoid ExecutionError's exit_code requirement
        SkogAIError.__init__(self, message, details, log_error=log_error)
        self.executable = executable
        self.timeout = timeout
        self.command_args = command_args or []
        self.partial_stdout = partial_stdout
        self.partial_stderr = partial_stderr


class PermissionError(ExecutableNotFoundError):
    """
    Raised when executable exists but cannot be executed due to permissions.

    This error indicates that the executable was found but the current user
    lacks the necessary permissions to execute it.
    """

    def __init__(
        self, executable: str, file_mode: Optional[str] = None, log_error: bool = True
    ) -> None:
        """
        Initialize a permission error.

        Args:
            executable: Path to the executable that cannot be executed
            file_mode: File permissions in octal format (optional)
        """
        details = {
            "executable": executable,
            "suggestions": [
                "Check if the file has execute permissions (chmod +x)",
                "Run with appropriate privileges (sudo if needed)",
                "Verify you own the file or have group access",
                "Check if the file is in a restricted directory",
            ],
        }

        if file_mode:
            details["file_mode"] = file_mode

        message = f"Permission denied: Cannot execute '{executable}'"

        # Call SkogAIError directly to avoid ExecutableNotFoundError's logic
        SkogAIError.__init__(self, message, details, log_error=log_error)
        self.executable = executable
        self.file_mode = file_mode


class ConfigurationError(SkogAIError):
    """Raised when there is an issue with configuration or setup.

    This error indicates problems with library configuration, environment
    setup, or invalid parameter combinations that prevent proper operation.
    It's designed to catch user input errors early and provide clear
    guidance on how to fix the issue.

    Configuration errors are preventable by validating inputs before
    execution. The error includes specific information about what
    configuration is invalid and, when possible, what values are valid.

    Attributes:
        config_key: Name of the configuration parameter that's invalid
        config_value: The invalid value that was provided
        valid_values: List of valid values or constraints (when applicable)

    Examples:
        Invalid parameter types:

        >>> from skoglib import run_executable, ConfigurationError
        >>> try:
        ...     result = run_executable("echo", "not_a_list")  # args must be list
        ... except ConfigurationError as e:
        ...     print(f"Invalid {e.config_key}: {e.config_value}")
        ...     print("Expected: list of strings")

        Invalid timeout values:

        >>> try:
        ...     result = run_executable("echo", ["test"], timeout=-5)
        ... except ConfigurationError as e:
        ...     print(f"Invalid timeout: {e.config_value}")
        ...     print(f"Must be: {e.valid_values}")

        Working directory issues:

        >>> try:
        ...     result = run_executable("pwd", cwd="/nonexistent/directory")
        ... except ConfigurationError as e:
        ...     print(f"Working directory error: {e}")
        ...     # Could suggest creating the directory or using existing path
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        valid_values: Optional[List[Any]] = None,
        log_error: bool = True,
    ) -> None:
        """
        Initialize a configuration error.

        Args:
            message: Human-readable error message
            config_key: Name of the configuration key that's invalid (optional)
            config_value: The invalid value (optional)
            valid_values: List of valid values (optional)
        """
        details: Dict[str, Any] = {
            "suggestions": [
                "Check configuration file syntax and values",
                "Verify environment variables are set correctly",
                "Review parameter combinations for conflicts",
                "Consult documentation for valid configuration options",
            ]
        }
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value
        if valid_values:
            details["valid_values"] = valid_values

        super().__init__(message, details, log_error=log_error)
        self.config_key = config_key
        self.config_value = config_value
        self.valid_values = valid_values or []
