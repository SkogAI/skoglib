"""
Core executable runner functionality for skoglib.

This module provides the main `run_executable` function for launching and
managing subprocess execution with proper error handling and result capture.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Union, List
from dataclasses import dataclass

from .exceptions import ExecutableNotFoundError, ExecutionError, ConfigurationError
from .logging_config import get_logger, get_performance_logger


logger = get_logger("executable")


@dataclass
class ExecutionResult:
    """
    Container for executable execution results.
    
    This dataclass holds all information about an executable's execution,
    including output, timing, and metadata for analysis and debugging.
    """
    executable: str
    args: List[str]
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    cwd: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    
    @property
    def success(self) -> bool:
        """Return True if execution was successful (exit code 0)."""
        return self.exit_code == 0
        
    @property
    def command_line(self) -> str:
        """Return the full command line that was executed."""
        if self.args:
            return f"{self.executable} {' '.join(self.args)}"
        return self.executable


def _find_executable(executable: str) -> str:
    """
    Find executable in system PATH or validate absolute path.
    
    Args:
        executable: Name or path of executable to find
        
    Returns:
        Absolute path to the executable
        
    Raises:
        ExecutableNotFoundError: If executable cannot be found
    """
    # If it's an absolute path, check if it exists and is executable
    if Path(executable).is_absolute():
        exe_path = Path(executable)
        if not exe_path.exists():
            raise ExecutableNotFoundError(executable)
        if not exe_path.is_file():
            raise ExecutableNotFoundError(
                executable, 
                search_paths=[str(exe_path.parent)]
            )
        if not exe_path.stat().st_mode & 0o111:  # Check execute permission
            raise ExecutableNotFoundError(
                executable,
                search_paths=[str(exe_path.parent)]
            )
        return str(exe_path)
    
    # Search in PATH
    import shutil
    exe_path_str = shutil.which(executable)
    if exe_path_str is None:
        # Get PATH for context
        import os
        path_env = os.environ.get('PATH', '')
        search_paths = path_env.split(os.pathsep) if path_env else []
        raise ExecutableNotFoundError(executable, search_paths)
        
    return exe_path_str


def run_executable(
    executable: str,
    args: Optional[List[str]] = None,
    cwd: Optional[Union[str, Path]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    capture_output: bool = True,
    check_exit_code: bool = True
) -> ExecutionResult:
    """
    Run an executable and return structured results.
    
    This is the main entry point for executing external programs. It handles
    subprocess management, error handling, output capture, and timing.
    
    Args:
        executable: Name or path of the executable to run
        args: List of arguments to pass to the executable (optional)
        cwd: Working directory for execution (optional)
        env_vars: Additional environment variables (optional)  
        timeout: Maximum execution time in seconds (optional)
        capture_output: Whether to capture stdout/stderr (default: True)
        check_exit_code: Whether to raise ExecutionError on non-zero exit (default: True)
        
    Returns:
        ExecutionResult with execution details and output
        
    Raises:
        ExecutableNotFoundError: If the executable cannot be found
        ExecutionError: If execution fails and check_exit_code is True
        ConfigurationError: If parameters are invalid
        
    Example:
        >>> result = run_executable("ls", ["-la"], cwd="/tmp")
        >>> print(result.stdout)
        >>> if result.success:
        >>>     print("Command succeeded!")
    """
    # Validate and normalize parameters
    args = args or []
    
    if not isinstance(args, list):
        raise ConfigurationError(
            "args must be a list of strings", 
            config_key="args",
            config_value=type(args).__name__
        )
        
    if timeout is not None and timeout <= 0:
        raise ConfigurationError(
            "timeout must be positive",
            config_key="timeout", 
            config_value=timeout,
            valid_values=["positive float/int"]
        )
    
    # Find and validate executable
    executable_path = _find_executable(executable)
    
    # Prepare working directory
    work_dir: Optional[str] = None
    if cwd:
        work_dir_path = Path(cwd)
        if not work_dir_path.exists():
            raise ConfigurationError(
                f"Working directory does not exist: {work_dir_path}",
                config_key="cwd",
                config_value=str(work_dir_path)
            )
        work_dir = str(work_dir_path)
    
    # Prepare environment
    import os
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    # Build command
    command = [executable_path] + args
    
    logger.debug(f"Executing: {' '.join(command)}")
    if work_dir:
        logger.debug(f"Working directory: {work_dir}")
    if env_vars:
        logger.debug(f"Additional env vars: {list(env_vars.keys())}")
    
    # Execute with timing and performance logging
    start_time = time.time()
    
    with get_performance_logger(f"execute_{executable}") as perf_logger:
        try:
            result = subprocess.run(
                command,
                cwd=work_dir,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            
            logger.debug(f"Execution completed in {execution_time:.3f}s with exit code {result.returncode}")
            
            # Create result object
            exec_result = ExecutionResult(
                executable=executable,
                args=args,
                exit_code=result.returncode,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                execution_time=execution_time,
                cwd=work_dir,
                env_vars=env_vars
            )
            
            # Check for execution errors
            if check_exit_code and result.returncode != 0:
                raise ExecutionError(
                    executable=executable,
                    exit_code=result.returncode,
                    command_args=args,
                    stdout=result.stdout if capture_output else None,
                    stderr=result.stderr if capture_output else None,
                    execution_time=execution_time
                )
                
            return exec_result
            
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            logger.warning(f"Command timed out after {execution_time:.3f}s")
            
            raise ExecutionError(
                executable=executable,
                exit_code=-1,  # Use -1 to indicate timeout
                command_args=args,
                stdout=e.stdout.decode('utf-8') if e.stdout else None,
                stderr=e.stderr.decode('utf-8') if e.stderr else None,
                execution_time=execution_time
            ) from e
            
        except OSError as e:
            execution_time = time.time() - start_time
            logger.error(f"OS error during execution: {e}")
            
            # This might be a permission issue or other OS-level problem
            raise ExecutionError(
                executable=executable,
                exit_code=-2,  # Use -2 to indicate OS error
                command_args=args,
                stderr=str(e),
                execution_time=execution_time
            ) from e