"""
Configuration management system for skoglib.

This module provides a robust configuration management system that supports
environment variable overrides, configuration validation, executable discovery,
and thread-safe access. Follows the "batteries included but minimal" philosophy.
"""

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from .exceptions import ConfigurationError
from .logging_config import get_logger


logger = get_logger("config")


@dataclass
class SkogAIConfig:
    """
    Main configuration class for SkogAI library.
    
    This dataclass provides sensible defaults while allowing customization
    through environment variables (with SKOGAI_ prefix) or direct instantiation.
    All access is thread-safe and configuration values are validated on creation.
    """
    
    # Execution settings
    default_timeout: int = 30
    max_output_size: int = 10 * 1024 * 1024  # 10MB
    
    # Logging configuration 
    log_level: str = "INFO"
    
    # Path configuration
    executable_search_paths: List[str] = field(default_factory=list)
    
    # Environment variable prefix
    env_prefix: str = "SKOGAI"
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_config()
        logger.debug("Configuration initialized with settings", extra={
            "timeout": self.default_timeout,
            "max_output_size": self.max_output_size,
            "log_level": self.log_level,
            "search_paths_count": len(self.executable_search_paths)
        })
    
    def _validate_config(self) -> None:
        """Validate configuration values and raise ConfigurationError if invalid."""
        # Validate timeout
        if not isinstance(self.default_timeout, int) or self.default_timeout <= 0:
            raise ConfigurationError(
                "default_timeout must be a positive integer",
                config_key="default_timeout", 
                config_value=self.default_timeout
            )
        
        # Validate max output size
        if not isinstance(self.max_output_size, int) or self.max_output_size <= 0:
            raise ConfigurationError(
                "max_output_size must be a positive integer",
                config_key="max_output_size",
                config_value=self.max_output_size
            )
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ConfigurationError(
                f"log_level must be one of: {', '.join(valid_log_levels)}",
                config_key="log_level",
                config_value=self.log_level,
                valid_values=valid_log_levels
            )
        
        # Validate executable search paths
        for path in self.executable_search_paths:
            if not isinstance(path, str):
                raise ConfigurationError(
                    "All executable_search_paths must be strings",
                    config_key="executable_search_paths",
                    config_value=path
                )
            
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Search path does not exist: {path}")
            elif not path_obj.is_dir():
                raise ConfigurationError(
                    f"Search path must be a directory: {path}",
                    config_key="executable_search_paths",
                    config_value=path
                )


# Thread-safe configuration singleton
_config_lock = threading.Lock()
_cached_config: Optional[SkogAIConfig] = None


def get_config() -> SkogAIConfig:
    """
    Get the global configuration instance with thread-safe access.
    
    Returns:
        The global SkogAIConfig instance, loaded from environment variables
        on first access and cached for subsequent calls.
    """
    global _cached_config
    
    if _cached_config is None:
        with _config_lock:
            # Double-checked locking pattern
            if _cached_config is None:
                _cached_config = load_config_from_env()
    
    return _cached_config


def reset_config() -> None:
    """
    Reset the cached configuration instance.
    
    This forces the next call to get_config() to reload from environment.
    Mainly used for testing purposes.
    """
    global _cached_config
    
    with _config_lock:
        _cached_config = None
        logger.debug("Configuration cache reset")


def load_config_from_env() -> SkogAIConfig:
    """
    Load configuration from environment variables.
    
    Environment variables should be prefixed with SKOGAI_ (configurable).
    Type conversion is performed automatically based on the dataclass field types.
    
    Returns:
        SkogAIConfig instance with values from environment or defaults.
    """
    env_prefix = "SKOGAI"  # Could be overridden but keeping simple for now
    
    config_values: Dict[str, Any] = {}
    
    # Parse timeout
    timeout_var = f"{env_prefix}_DEFAULT_TIMEOUT"
    if timeout_var in os.environ:
        try:
            config_values["default_timeout"] = int(os.environ[timeout_var])
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid value for {timeout_var}: must be an integer",
                config_key="default_timeout",
                config_value=os.environ[timeout_var]
            ) from e
    
    # Parse max output size
    max_size_var = f"{env_prefix}_MAX_OUTPUT_SIZE"
    if max_size_var in os.environ:
        try:
            config_values["max_output_size"] = int(os.environ[max_size_var])
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid value for {max_size_var}: must be an integer",
                config_key="max_output_size", 
                config_value=os.environ[max_size_var]
            ) from e
    
    # Parse log level
    log_level_var = f"{env_prefix}_LOG_LEVEL"
    if log_level_var in os.environ:
        config_values["log_level"] = os.environ[log_level_var].upper()
    
    # Parse search paths (colon-separated like PATH)
    search_paths_var = f"{env_prefix}_SEARCH_PATHS"
    if search_paths_var in os.environ:
        paths = os.environ[search_paths_var].split(":")
        # Filter out empty strings
        config_values["executable_search_paths"] = [p for p in paths if p.strip()]
    
    logger.debug(f"Loaded configuration from environment variables with prefix {env_prefix}")
    return SkogAIConfig(**config_values)


def find_executable(name: str, search_paths: Optional[List[str]] = None) -> Optional[str]:
    """
    Find executable in system PATH and optional additional search paths.
    
    Args:
        name: Name of the executable to find
        search_paths: Additional paths to search (optional)
        
    Returns:
        Full path to executable if found, None otherwise
    """
    logger.debug(f"Searching for executable: {name}")
    
    # If name is already an absolute path, validate it
    if os.path.isabs(name):
        if os.path.isfile(name) and os.access(name, os.X_OK):
            logger.debug(f"Found executable at absolute path: {name}")
            return name
        else:
            logger.debug(f"Absolute path not executable or not found: {name}")
            return None
    
    # Build search paths: additional paths first, then system PATH
    all_paths = []
    if search_paths:
        all_paths.extend(search_paths)
    
    # Add system PATH
    system_path = os.environ.get("PATH", "")
    if system_path:
        all_paths.extend(system_path.split(os.pathsep))
    
    # Search each path
    for path in all_paths:
        if not path.strip():
            continue
            
        full_path = Path(path) / name
        if full_path.is_file() and os.access(full_path, os.X_OK):
            result = str(full_path)
            logger.debug(f"Found executable: {name} -> {result}")
            return result
    
    logger.debug(f"Executable not found: {name}")
    return None


def validate_executable(path: str) -> bool:
    """
    Validate that a path points to an executable file.
    
    Args:
        path: Path to validate
        
    Returns:
        True if path is an executable file, False otherwise
    """
    try:
        path_obj = Path(path)
        is_valid = path_obj.is_file() and os.access(path_obj, os.X_OK)
        logger.debug(f"Executable validation: {path} -> {is_valid}")
        return is_valid
    except (OSError, ValueError) as e:
        logger.debug(f"Executable validation failed for {path}: {e}")
        return False


def resolve_path(path: Union[str, Path], base_dir: Optional[str] = None) -> Path:
    """
    Resolve a path to an absolute Path object.
    
    Args:
        path: Path to resolve (string or Path object)
        base_dir: Base directory for relative paths (optional, defaults to cwd)
        
    Returns:
        Absolute Path object
    """
    path_obj = Path(path)
    
    if path_obj.is_absolute():
        return path_obj
    
    # Handle relative paths
    if base_dir:
        base_path = Path(base_dir)
        return (base_path / path_obj).resolve()
    else:
        return path_obj.resolve()


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries with later ones taking precedence.
    
    Args:
        *configs: Variable number of configuration dictionaries
        
    Returns:
        Merged configuration dictionary
    """
    result: Dict[str, Any] = {}
    
    for config in configs:
        if config:
            result.update(config)
    
    return result