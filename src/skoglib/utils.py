"""
Common utilities for skoglib.

This module provides utility functions that complement the configuration system,
focusing on performance timing and other general-purpose utilities not covered
by the configuration management.
"""

import time
import functools
from typing import Any, Callable, Tuple, TypeVar, Dict, Optional
from pathlib import Path

from .logging_config import get_logger


logger = get_logger("utils")

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])


def time_execution(func: Callable[[], Any]) -> Tuple[Any, float]:
    """
    Execute a function and measure its execution time.

    Args:
        func: Function to execute (should be a callable with no arguments)

    Returns:
        Tuple containing (function_result, execution_time_in_seconds)

    Example:
        >>> result, duration = time_execution(lambda: expensive_computation())
        >>> print(f"Computation took {format_duration(duration)}")
    """
    start_time = time.perf_counter()

    try:
        result = func()
        end_time = time.perf_counter()
        duration = end_time - start_time

        logger.debug(
            "Function execution completed",
            extra={
                "function": getattr(func, "__name__", str(func)),
                "duration_seconds": duration,
            },
        )

        return result, duration

    except Exception as e:
        end_time = time.perf_counter()
        duration = end_time - start_time

        logger.error(
            "Function execution failed",
            extra={
                "function": getattr(func, "__name__", str(func)),
                "duration_seconds": duration,
                "error": str(e),
            },
        )

        raise


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds (float)

    Returns:
        Formatted duration string with appropriate unit

    Examples:
        >>> format_duration(0.001234)
        '1.23ms'
        >>> format_duration(1.5)
        '1.50s'
        >>> format_duration(61.2)
        '1m 1.20s'
        >>> format_duration(3661.5)
        '1h 1m 1.50s'
    """
    if seconds < 0:
        return "0.00s"

    # Handle zero exactly
    if seconds == 0:
        return "0.00s"

    # Handle microseconds (< 1ms)
    if seconds < 0.001:
        microseconds = seconds * 1_000_000
        return f"{microseconds:.0f}μs"

    # Handle milliseconds (< 1s)
    if seconds < 1.0:
        milliseconds = seconds * 1000
        return f"{milliseconds:.2f}ms"

    # Handle seconds only (< 1 minute)
    if seconds < 60:
        return f"{seconds:.2f}s"

    # Handle minutes and seconds (< 1 hour)
    if seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"

    # Handle hours, minutes, and seconds
    hours = int(seconds // 3600)
    remaining_seconds = seconds % 3600
    minutes = int(remaining_seconds // 60)
    remaining_seconds = remaining_seconds % 60

    return f"{hours}h {minutes}m {remaining_seconds:.2f}s"


def timing_decorator(func: F) -> F:
    """
    Decorator to automatically time function execution and log the results.

    Args:
        func: Function to wrap with timing

    Returns:
        Wrapped function that logs execution time

    Example:
        >>> @timing_decorator
        ... def slow_function():
        ...     time.sleep(1)
        ...     return "done"
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time

            logger.debug(
                f"Function '{func.__name__}' completed",
                extra={
                    "function": func.__name__,
                    "duration_seconds": duration,
                    "formatted_duration": format_duration(duration),
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                },
            )

            return result

        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time

            logger.error(
                f"Function '{func.__name__}' failed",
                extra={
                    "function": func.__name__,
                    "duration_seconds": duration,
                    "formatted_duration": format_duration(duration),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            raise

    return wrapper  # type: ignore


def safe_dict_get(
    dictionary: Dict[str, Any],
    key: str,
    default: Any = None,
    expected_type: Optional[type] = None,
) -> Any:
    """
    Safely get a value from a dictionary with optional type checking.

    Args:
        dictionary: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found
        expected_type: Optional type to validate against

    Returns:
        Value from dictionary or default

    Raises:
        TypeError: If value exists but is not of expected_type

    Example:
        >>> config = {"timeout": "30", "debug": True}
        >>> safe_dict_get(config, "timeout", 0, int)  # TypeError: not an int
        >>> safe_dict_get(config, "missing", "default")  # "default"
    """
    value = dictionary.get(key, default)

    if expected_type is not None and value is not None:
        if not isinstance(value, expected_type):
            logger.warning(
                f"Type mismatch for key '{key}'",
                extra={
                    "key": key,
                    "expected_type": expected_type.__name__,
                    "actual_type": type(value).__name__,
                    "value": value,
                },
            )
            raise TypeError(
                f"Expected {expected_type.__name__} for key '{key}', "
                f"got {type(value).__name__}: {value}"
            )

    return value


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it and any parent directories if needed.

    Args:
        path: Directory path to ensure exists

    Returns:
        The path as a Path object

    Raises:
        OSError: If directory cannot be created

    Example:
        >>> ensure_directory(Path("/tmp/my/deep/directory"))
        Path('/tmp/my/deep/directory')
    """
    try:
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Directory ensured: {path_obj}")
        return path_obj

    except OSError as e:
        logger.error(
            f"Failed to create directory: {path}",
            extra={"path": str(path), "error": str(e)},
        )
        raise


def bytes_to_human_readable(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string

    Examples:
        >>> bytes_to_human_readable(1024)
        '1.00 KB'
        >>> bytes_to_human_readable(1536)
        '1.50 KB'
        >>> bytes_to_human_readable(1048576)
        '1.00 MB'
    """
    if size_bytes < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"
