"""
Custom exception hierarchy for skoglib.

This module defines the exception classes used throughout the skoglib library,
providing clear error messages and proper debugging context with logging integration.
"""

import time
from typing import Optional, Dict, Any, List
from .logging_config import get_logger


# Logger for exception module
logger = get_logger("exceptions")


class SkogAIError(Exception):
    """
    Base exception class for all skoglib-related errors.
    
    This is the root exception that all other skoglib exceptions inherit from.
    It provides consistent error handling and context information.
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,  # Backward compatibility
        log_error: bool = True
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
            raise ValueError("Cannot specify both 'details' and 'context'. Use 'details' (preferred).")
        
        self.details = details or context or {}
        self.context = self.details  # Maintain backward compatibility
        self.timestamp = time.time()
        
        # Log error with details for debugging
        if log_error:
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
            "timestamp": self.timestamp
        }


class ExecutableNotFoundError(SkogAIError):
    """
    Raised when a required executable cannot be found in the system PATH.
    
    This error indicates that the executable specified for running was not
    found in the system PATH or at the specified absolute path.
    """
    
    def __init__(
        self, 
        executable: str, 
        search_paths: Optional[List[str]] = None,
        log_error: bool = True
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
                "Verify the executable name is correct"
            ]
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
    """
    Raised when an executable runs but fails with a non-zero exit code.
    
    This error captures the execution details including exit code, stdout,
    stderr, and timing information for debugging purposes.
    """
    
    def __init__(
        self, 
        executable: str,
        exit_code: int,
        command_args: Optional[list[str]] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        execution_time: Optional[float] = None,
        log_error: bool = True
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
                "Consult the tool's documentation for exit code meanings"
            ]
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
        log_error: bool = True
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
                "Consider breaking large tasks into smaller chunks"
            ]
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
        self,
        executable: str,
        file_mode: Optional[str] = None,
        log_error: bool = True
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
                "Check if the file is in a restricted directory"
            ]
        }
        
        if file_mode:
            details["file_mode"] = file_mode
            
        message = f"Permission denied: Cannot execute '{executable}'"
        
        # Call SkogAIError directly to avoid ExecutableNotFoundError's logic
        SkogAIError.__init__(self, message, details, log_error=log_error)
        self.executable = executable
        self.file_mode = file_mode


class ConfigurationError(SkogAIError):
    """
    Raised when there is an issue with configuration or setup.
    
    This error indicates problems with library configuration, environment
    setup, or invalid parameter combinations that prevent proper operation.
    """
    
    def __init__(
        self, 
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        valid_values: Optional[List[Any]] = None,
        log_error: bool = True
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
                "Consult documentation for valid configuration options"
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