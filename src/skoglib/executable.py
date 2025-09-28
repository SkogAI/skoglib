"""Core executable runner functionality for skoglib.

This module provides the main `run_executable` function for launching and
managing subprocess execution with proper error handling and result capture.

The primary interface consists of:
- `run_executable`: Main function for executing external programs
- `ExecutionResult`: Structured result object with execution details
- Exception handling for common failure scenarios

Key Features:
- Comprehensive error handling with specific exception types
- Output capture with optional console passthrough
- Timeout support with proper cleanup
- Environment variable management
- Working directory control
- Performance monitoring and logging integration

Basic Usage Examples:
    Simple command execution:

    >>> from skoglib import run_executable
    >>> result = run_executable("echo", ["Hello, World!"])
    >>> print(result.stdout.strip())
    Hello, World!

    Error handling:

    >>> from skoglib import run_executable, ExecutionError
    >>> try:
    ...     result = run_executable("false")  # Always fails
    ... except ExecutionError as e:
    ...     print(f"Command failed: {e.exit_code}")
    Command failed: 1

    With timeout and working directory:

    >>> result = run_executable(
    ...     "pwd",
    ...     cwd="/tmp",
    ...     timeout=5.0
    ... )
    >>> "/tmp" in result.stdout
    True

Advanced Usage:
    Environment variables and complex scenarios:

    >>> result = run_executable(
    ...     "python",
    ...     ["-c", "import os; print(os.environ.get('CUSTOM_VAR', 'not_found'))"],
    ...     env_vars={"CUSTOM_VAR": "test_value"}
    ... )
    >>> "test_value" in result.stdout
    True

    Non-blocking execution with manual error checking:

    >>> result = run_executable("false", check_exit_code=False)
    >>> if not result.success:
    ...     print(f"Exit code: {result.exit_code}")
    Exit code: 1
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
    """Result of an executable run operation.

    This dataclass encapsulates all information about an executable's execution,
    providing structured access to output, timing, metadata, and convenience
    properties for common analysis patterns.

    The result object serves as the primary interface between the library and
    calling code, offering both raw execution data and processed information
    to support various use cases from simple success checking to detailed
    performance analysis.

    Attributes:
        executable: Name or path of the executed command
        args: List of arguments passed to the executable
        exit_code: Process exit code (0 indicates success)
        stdout: Standard output captured from the execution
        stderr: Standard error output captured from the execution
        execution_time: Wall-clock time taken for execution in seconds
        cwd: Working directory used for execution (None if current directory)
        env_vars: Additional environment variables set for execution

    Examples:
        Basic usage with success checking:

        >>> result = run_executable("echo", ["Hello"])
        >>> if result.success:
        ...     print(f"Command output: {result.stdout.strip()}")
        Command output: Hello

        Detailed execution analysis:

        >>> result = run_executable("python", ["-c", "print('test')"])
        >>> print(f"Executed: {result.command_line}")
        >>> print(f"Exit code: {result.exit_code}")
        >>> print(f"Duration: {result.execution_time:.3f}s")
        Executed: python -c print('test')
        Exit code: 0
        Duration: 0.045s

        Error handling:

        >>> result = run_executable("false", check_exit_code=False)
        >>> if not result.success:
        ...     print(f"Command failed with code {result.exit_code}")
        Command failed with code 1
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
        """True if the executable completed successfully (exit code 0).

        This is the primary indicator of execution success and is equivalent
        to checking `exit_code == 0`. Most use cases should check this property
        rather than examining the exit code directly.

        Returns:
            True if exit_code is 0, False otherwise

        Example:
            >>> result = run_executable("echo", ["test"])
            >>> assert result.success  # Will pass for echo
            >>>
            >>> result = run_executable("false", check_exit_code=False)
            >>> assert not result.success  # Will pass since false returns 1
        """
        return self.exit_code == 0

    @property
    def command_line(self) -> str:
        """Return the full command line that was executed.

        Reconstructs the command line by combining the executable name with
        its arguments, separated by spaces. Useful for logging, debugging,
        and display purposes.

        Returns:
            Complete command line as it would appear in a shell

        Example:
            >>> result = run_executable("git", ["status", "--porcelain"])
            >>> print(result.command_line)
            git status --porcelain
        """
        if self.args:
            return f"{self.executable} {' '.join(self.args)}"
        return self.executable


def _find_executable(executable: Union[str, Path]) -> str:
    """Find executable in system PATH or validate absolute path.

    This internal function handles the resolution of executable names to full paths.
    It supports both absolute paths (which are validated for existence and execute
    permissions) and relative names (which are searched in the system PATH).

    Args:
        executable: Name or path of executable to find. Can be string or Path object.

    Returns:
        Absolute path to the executable as a string, ready for subprocess execution.

    Raises:
        ExecutableNotFoundError: If executable cannot be found in PATH or if the
            specified absolute path doesn't exist, isn't a file, or lacks execute
            permissions. The error includes relevant search paths for debugging.

    Examples:
        >>> _find_executable("python")  # doctest: +SKIP
        '/usr/bin/python'
        >>> _find_executable("/bin/ls")  # doctest: +SKIP
        '/bin/ls'
        >>> _find_executable("nonexistent")  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        ExecutableNotFoundError: Executable 'nonexistent' not found in paths: ...
    """
    # Convert to string for consistent handling
    exec_str = str(executable)

    # If it's an absolute path, check if it exists and is executable
    if Path(exec_str).is_absolute():
        exe_path = Path(exec_str)
        if not exe_path.exists():
            raise ExecutableNotFoundError(exec_str)
        if not exe_path.is_file():
            raise ExecutableNotFoundError(exec_str, search_paths=[str(exe_path.parent)])
        if not exe_path.stat().st_mode & 0o111:  # Check execute permission
            raise ExecutableNotFoundError(exec_str, search_paths=[str(exe_path.parent)])
        return str(exe_path)

    # Search in PATH
    import shutil

    exe_path_str = shutil.which(exec_str)
    if exe_path_str is None:
        # Get PATH for context
        import os

        path_env = os.environ.get("PATH", "")
        search_paths = path_env.split(os.pathsep) if path_env else []
        raise ExecutableNotFoundError(exec_str, search_paths)

    return exe_path_str


def run_executable(
    executable: Union[str, Path],
    args: Optional[List[str]] = None,
    cwd: Optional[Union[str, Path]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    capture_output: bool = True,
    check_exit_code: bool = True,
) -> ExecutionResult:
    """Run a skoglib executable with specified arguments and environment.

    This function provides a robust interface for executing external programs
    with comprehensive error handling, output capture, and performance monitoring.
    It serves as the primary entry point for the skoglib library's executable
    management functionality.

    Args:
        executable: Path to the executable or command name. Can be an absolute path,
            relative path, or command name to search in system PATH.
        args: List of command-line arguments to pass to the executable.
        cwd: Working directory for execution. The executable will run from this
            directory. If None, uses the current working directory.
        env_vars: Environment variables to set/override for the execution.
            These are merged with the current environment.
        timeout: Maximum execution time in seconds. If the executable takes longer
            than this, it will be terminated and raise ExecutionError.
        capture_output: Whether to capture stdout/stderr. If False, output will
            be printed directly to console and not captured in the result.
        check_exit_code: Whether to raise ExecutionError on non-zero exit codes.
            If False, failed executions return a result with success=False.

    Returns:
        ExecutionResult containing exit code, output, timing information, and
        metadata about the execution. The result object provides both raw data
        and convenient properties for common use cases.

    Raises:
        ExecutableNotFoundError: If the executable cannot be found in the system
            PATH or at the specified absolute path. Includes search paths in the
            error message for debugging.
        ExecutionError: If execution fails (non-zero exit code) and check_exit_code
            is True, or if the execution times out. Contains detailed execution
            context including stdout, stderr, and timing information.
        ConfigurationError: If arguments are invalid (e.g., args is not a list,
            timeout is negative, working directory doesn't exist).

    Examples:
        Basic command execution:

        >>> result = run_executable("echo", ["Hello", "World"])
        >>> if result.success:
        ...     print(f"Output: {result.stdout.strip()}")
        Output: Hello World

        With working directory and environment:

        >>> result = run_executable(
        ...     "python",
        ...     ["-c", "import os; print(os.getcwd(), os.environ.get('TEST_VAR'))"],
        ...     cwd="/tmp",
        ...     env_vars={"TEST_VAR": "example"}
        ... )
        >>> print(result.stdout.strip())
        /tmp example

        Error handling:

        >>> try:
        ...     result = run_executable("false")  # Command that always fails
        ... except ExecutionError as e:
        ...     print(f"Command failed with exit code {e.exit_code}")
        Command failed with exit code 1

        Timeout handling:

        >>> try:
        ...     result = run_executable("sleep", ["10"], timeout=1.0)
        ... except ExecutionError as e:
        ...     print(f"Command timed out after {e.execution_time:.1f}s")
        Command timed out after 1.0s

        Without exit code checking:

        >>> result = run_executable("false", check_exit_code=False)
        >>> print(f"Success: {result.success}, Exit code: {result.exit_code}")
        Success: False, Exit code: 1
    """
    # Validate and normalize parameters
    args = args or []

    if not isinstance(args, list):
        raise ConfigurationError(
            "args must be a list of strings",
            config_key="args",
            config_value=type(args).__name__,
        )

    if timeout is not None and timeout <= 0:
        raise ConfigurationError(
            "timeout must be positive",
            config_key="timeout",
            config_value=timeout,
            valid_values=["positive float/int"],
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
                config_value=str(work_dir_path),
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

    with get_performance_logger(f"execute_{executable}"):
        try:
            result = subprocess.run(
                command,
                cwd=work_dir,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )
            execution_time = time.time() - start_time

            logger.debug(
                f"Execution completed in {execution_time:.3f}s with exit code {result.returncode}"
            )

            # Create result object
            exec_result = ExecutionResult(
                executable=str(executable),
                args=args,
                exit_code=result.returncode,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                execution_time=execution_time,
                cwd=work_dir,
                env_vars=env_vars,
            )

            # Check for execution errors
            if check_exit_code and result.returncode != 0:
                raise ExecutionError(
                    executable=str(executable),
                    exit_code=result.returncode,
                    command_args=args,
                    stdout=result.stdout if capture_output else None,
                    stderr=result.stderr if capture_output else None,
                    execution_time=execution_time,
                )

            return exec_result

        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            logger.warning(f"Command timed out after {execution_time:.3f}s")

            raise ExecutionError(
                executable=str(executable),
                exit_code=-1,  # Use -1 to indicate timeout
                command_args=args,
                stdout=e.stdout.decode("utf-8") if e.stdout else None,
                stderr=e.stderr.decode("utf-8") if e.stderr else None,
                execution_time=execution_time,
            ) from e

        except OSError as e:
            execution_time = time.time() - start_time
            logger.error(f"OS error during execution: {e}")

            # This might be a permission issue or other OS-level problem
            raise ExecutionError(
                executable=str(executable),
                exit_code=-2,  # Use -2 to indicate OS error
                command_args=args,
                stderr=str(e),
                execution_time=execution_time,
            ) from e
