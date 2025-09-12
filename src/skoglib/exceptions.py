"""
Custom exception hierarchy for skoglib.

This module defines the exception classes used throughout the skoglib library,
providing clear error messages and proper debugging context with logging integration.
"""

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
    """
    Raised when a required executable cannot be found in the system PATH.
    
    This error indicates that the executable specified for running was not
    found in the system PATH or at the specified absolute path.
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