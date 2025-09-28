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
        context: Optional[Dict[str, Any]] = None,
        log_error: bool = True
    ) -> None:
        """
        Initialize a SkogAI error.
        
        Args:
            message: Human-readable error message
            context: Additional debugging context (optional)
            log_error: Whether to log this error when raised (default: True)
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        
        # Log error with context for debugging
        if log_error:
            if self.context:
                logger.error(f"{message} - Context: {self.context}")
            else:
                logger.error(message)
        
    def __str__(self) -> str:
        """Return string representation with context if available."""
        if not self.context:
            return self.message
            
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{self.message} (context: {context_str})"


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
        search_paths: Optional[List[str]] = None
    ) -> None:
        """
        Initialize an executable not found error.
        
        Args:
            executable: Name or path of the executable that was not found
            search_paths: List of paths that were searched (optional)
        """
        context: Dict[str, Any] = {"executable": executable}
        if search_paths:
            context["search_paths"] = search_paths
            
        message = f"Executable '{executable}' not found"
        if search_paths:
            message += f" in paths: {', '.join(search_paths)}"
            
        super().__init__(message, context)
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
        execution_time: Optional[float] = None
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
        context = {
            "executable": executable,
            "exit_code": exit_code,
        }
        
        if command_args:
            context["command_args"] = command_args
        if stdout:
            context["stdout"] = stdout
        if stderr:
            context["stderr"] = stderr
        if execution_time is not None:
            context["execution_time"] = execution_time
            
        cmd_str = executable
        if command_args:
            cmd_str += " " + " ".join(command_args)
            
        message = f"Command '{cmd_str}' failed with exit code {exit_code}"
        
        super().__init__(message, context)
        self.executable = executable
        self.exit_code = exit_code
        self.command_args = command_args or []
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time


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
        valid_values: Optional[List[Any]] = None
    ) -> None:
        """
        Initialize a configuration error.
        
        Args:
            message: Human-readable error message
            config_key: Name of the configuration key that's invalid (optional)
            config_value: The invalid value (optional)
            valid_values: List of valid values (optional)
        """
        context: Dict[str, Any] = {}
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = config_value
        if valid_values:
            context["valid_values"] = valid_values
            
        super().__init__(message, context)
        self.config_key = config_key
        self.config_value = config_value
        self.valid_values = valid_values or []