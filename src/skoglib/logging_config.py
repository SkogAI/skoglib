"""
Logging configuration for skoglib.

Provides performance-conscious logging integration with Python's standard logging library.
Follows fail-fast design principles with minimal import overhead.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Any, Union, Type
import time
import os

# Performance tracking for debugging import overhead
_import_start = time.perf_counter()

# Default configuration constants
DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DETAILED_FORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s"

# Logger name prefix for all skoglib loggers
LOGGER_PREFIX = "skoglib"


class SkogLibFormatter(logging.Formatter):
    """
    Custom formatter for skoglib that provides structured logging capabilities.
    
    Supports both simple and detailed formats based on log level and configuration.
    """
    
    def __init__(self, detailed: bool = False):
        """
        Initialize the formatter.
        
        Args:
            detailed: If True, use detailed format with line numbers and function names
        """
        self.detailed = detailed
        self.simple_format = DEFAULT_FORMAT
        self.detailed_format = DETAILED_FORMAT
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with appropriate detail level."""
        # Use detailed format for DEBUG level or when explicitly requested
        if self.detailed or record.levelno <= logging.DEBUG:
            self._style._fmt = self.detailed_format
        else:
            self._style._fmt = self.simple_format
        
        return super().format(record)


class PerformanceLogger:
    """
    Context manager for performance logging with minimal overhead.
    
    Only logs timing information when DEBUG level is enabled.
    """
    
    def __init__(self, logger: logging.Logger, operation: str, threshold_ms: float = 10.0):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance to use
            operation: Description of the operation being timed
            threshold_ms: Only log if operation takes longer than this (in milliseconds)
        """
        self.logger = logger
        self.operation = operation
        self.threshold_ms = threshold_ms
        self.start_time: Optional[float] = None
    
    def __enter__(self) -> "PerformanceLogger":
        if self.logger.isEnabledFor(logging.DEBUG):
            self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            if duration_ms >= self.threshold_ms:
                self.logger.debug(f"{self.operation} completed in {duration_ms:.2f}ms")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the skoglib prefix.
    
    Args:
        name: Logger name (will be prefixed with 'skoglib.')
        
    Returns:
        Configured logger instance
    """
    # Special case: "root" returns the base skoglib logger for backward compatibility
    if name == "root":
        return logging.getLogger(LOGGER_PREFIX)
    
    if not name.startswith(LOGGER_PREFIX):
        name = f"{LOGGER_PREFIX}.{name}"
    
    return logging.getLogger(name)


def configure_logging(
    level: Union[int, str] = DEFAULT_LOG_LEVEL,
    format_style: str = "simple",
    output: Optional[Union[str, Path]] = None,
    console: bool = True,
    force: bool = False
) -> None:
    """
    Configure logging for skoglib.
    
    This is the main configuration entry point. It sets up formatters, handlers,
    and the root skoglib logger with sensible defaults.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) 
        format_style: 'simple' or 'detailed' formatting
        output: Optional file path for log output
        console: Whether to log to console (default: True)
        force: Force reconfiguration even if already configured
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)
    
    # Get the base skoglib logger (parent of all skoglib loggers)
    root_logger = logging.getLogger(LOGGER_PREFIX)
    
    # Only configure once unless forced
    if root_logger.handlers and not force:
        return
    
    # Clear existing handlers if forcing reconfiguration
    if force:
        root_logger.handlers.clear()
    
    # Create formatter
    detailed = format_style == "detailed"
    formatter = SkogLibFormatter(detailed=detailed)
    
    # Configure console handler
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
    
    # Configure file handler if requested
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent log files from growing too large
        file_handler = logging.handlers.RotatingFileHandler(
            output_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    
    # Set the logger level
    root_logger.setLevel(level)
    
    # Log configuration completion at DEBUG level
    root_logger.debug(f"Logging configured: level={logging.getLevelName(level)}, "
                     f"format={format_style}, console={console}, file={output}")


def configure_from_env() -> None:
    """
    Configure logging based on environment variables.
    
    Supported environment variables:
    - SKOGLIB_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - SKOGLIB_LOG_FORMAT: Format style ('simple' or 'detailed')
    - SKOGLIB_LOG_FILE: File path for log output
    - SKOGLIB_LOG_CONSOLE: Whether to enable console logging ('true'/'false')
    """
    level = os.getenv("SKOGLIB_LOG_LEVEL", "WARNING").upper()
    format_style = os.getenv("SKOGLIB_LOG_FORMAT", "simple").lower()
    log_file = os.getenv("SKOGLIB_LOG_FILE")
    console = os.getenv("SKOGLIB_LOG_CONSOLE", "true").lower() == "true"
    
    # Validate format style
    if format_style not in ("simple", "detailed"):
        format_style = "simple"
    
    configure_logging(
        level=level,
        format_style=format_style,
        output=log_file,
        console=console
    )


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Create a performance logger for timing operations.
    
    Args:
        name: Name of the operation being timed
        
    Returns:
        PerformanceLogger context manager
    """
    logger = get_logger("performance")
    return PerformanceLogger(logger, name)


# Initialize default logging configuration with minimal overhead
# Only configure if not already done and not in testing environment
if not os.getenv("PYTEST_CURRENT_TEST") and not logging.getLogger(LOGGER_PREFIX).handlers:
    try:
        configure_from_env()
    except Exception:
        # Fail silently on configuration errors to maintain library reliability
        # Users can explicitly configure logging if needed
        pass

# Track import time for performance monitoring
_import_duration = (time.perf_counter() - _import_start) * 1000

# Only log import time if we're in debug mode and logging is configured
_debug_logger = logging.getLogger(f"{LOGGER_PREFIX}.import")
if _debug_logger.isEnabledFor(logging.DEBUG):
    _debug_logger.debug(f"logging_config imported in {_import_duration:.2f}ms")

# Export public interface
__all__ = [
    "configure_logging",
    "configure_from_env", 
    "get_logger",
    "get_performance_logger",
    "PerformanceLogger",
    "SkogLibFormatter",
    "DEFAULT_LOG_LEVEL",
    "LOGGER_PREFIX"
]