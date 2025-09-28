"""skoglib - A Python library for executable management and automation.

This library provides a "batteries included but minimal" approach to running
external executables with proper error handling, output capture, and logging.
It's designed to make subprocess management both powerful and simple, with
comprehensive type safety and clear error handling.

Key Features:
- Simple, type-safe API with comprehensive error handling
- Structured execution results with convenient properties
- Timeout support with proper cleanup
- Environment variable and working directory management
- Performance monitoring and logging integration
- Cross-platform compatibility

Quick Start:
    Basic command execution:
    
    >>> from skoglib import run_executable
    >>> result = run_executable("echo", ["Hello, World!"])
    >>> if result.success:
    ...     print(result.stdout.strip())
    Hello, World!
    
    With error handling:
    
    >>> from skoglib import run_executable, ExecutionError
    >>> try:
    ...     result = run_executable("false")  # Command that always fails
    ... except ExecutionError as e:
    ...     print(f"Command failed with exit code {e.exit_code}")
    Command failed with exit code 1
    
    Advanced usage with timeout and environment:
    
    >>> result = run_executable(
    ...     "python", 
    ...     ["-c", "import os; print(os.environ.get('TEST'))"],
    ...     env_vars={"TEST": "example"},
    ...     timeout=10.0
    ... )
    >>> print(result.stdout.strip())
    example

Main API:
    run_executable: Execute external programs with structured results
    ExecutionResult: Structured result object with execution details
    
Exception hierarchy:
    SkogAIError: Base exception class for all library errors
    ExecutableNotFoundError: Executable not found in PATH
    ExecutionError: Execution failed with non-zero exit code  
    ConfigurationError: Invalid configuration or parameters

Configuration and Logging:
    The library includes optional logging configuration and performance
    monitoring capabilities. Logging is performance-conscious and can
    be configured globally or per-module.
    
    >>> from skoglib import configure_logging
    >>> configure_logging(level="DEBUG")  # Enable detailed logging
"""

from .executable import run_executable, ExecutionResult
from .exceptions import (
    SkogAIError,
    ExecutableNotFoundError, 
    ExecutionError,
    TimeoutError,
    PermissionError,
    ConfigurationError
)
from .logging_config import (
    configure_logging,
    configure_from_env,
    get_logger,
    get_performance_logger
)
from .config import (
    SkogAIConfig,
    get_config,
    reset_config,
    find_executable,
    validate_executable,
    resolve_path,
    merge_configs
)

# Package metadata
__version__ = "0.1.0"
__author__ = "Emil Skogsund"
__email__ = "emil@skogsund.se"

# Public API - single import pattern for immediate value
__all__ = [
    # Main functionality
    "run_executable",
    "ExecutionResult",
    
    # Exception hierarchy
    "SkogAIError",
    "ExecutableNotFoundError",
    "ExecutionError", 
    "TimeoutError",
    "PermissionError",
    "ConfigurationError",
    
    # Logging configuration
    "configure_logging",
    "configure_from_env", 
    "get_logger",
    "get_performance_logger",
    
    # Configuration management
    "SkogAIConfig",
    "get_config",
    "reset_config",
    "find_executable",
    "validate_executable",
    "resolve_path",
    "merge_configs",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]


def main() -> None:
    """Main entry point for command-line usage.
    
    Provides basic information about the library and guidance for
    programmatic usage. This function is called when the library
    is executed as a module (`python -m skoglib`) or via the
    installed `skoglib` command.
    
    The CLI interface is intentionally minimal - the library is
    designed primarily for programmatic use within Python applications.
    
    Examples:
        Command line usage:
        
        $ python -m skoglib
        skoglib v0.1.0
        Usage: python -m skoglib
        For programmatic usage: from skoglib import run_executable
        
        $ skoglib
        skoglib v0.1.0
        Usage: python -m skoglib  
        For programmatic usage: from skoglib import run_executable
    """
    import sys
    print(f"skoglib v{__version__}")
    print("Usage: python -m skoglib")
    print("For programmatic usage: from skoglib import run_executable")
    sys.exit(0)
