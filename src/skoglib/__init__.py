"""
skoglib - A Python library for executable management and automation.

This library provides a "batteries included but minimal" approach to running
external executables with proper error handling, output capture, and logging.

Main API:
    run_executable: Execute external programs with structured results
    
Exception hierarchy:
    SkogAIError: Base exception class
    ExecutableNotFoundError: Executable not found in PATH
    ExecutionError: Execution failed with non-zero exit code
    ConfigurationError: Invalid configuration or parameters
"""

from .executable import run_executable, ExecutionResult
from .exceptions import (
    SkogAIError,
    ExecutableNotFoundError, 
    ExecutionError,
    ConfigurationError
)
from .logging_config import (
    configure_logging,
    configure_from_env,
    get_logger,
    get_performance_logger
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
    "ConfigurationError",
    
    # Logging configuration
    "configure_logging",
    "configure_from_env", 
    "get_logger",
    "get_performance_logger",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]


def main() -> None:
    """Main entry point for command-line usage."""
    import sys
    print(f"skoglib v{__version__}")
    print("Usage: python -m skoglib")
    print("For programmatic usage: from skoglib import run_executable")
    sys.exit(0)
