"""
Test suite for skoglib.executable module.

Tests core executable runner functionality including successful execution,
error scenarios, timeout handling, and edge cases.
"""

import os
import tempfile
import time
from unittest import TestCase
from unittest.mock import patch

from skoglib.executable import run_executable, ExecutionResult, _find_executable
from skoglib.exceptions import (
    ExecutableNotFoundError,
    ExecutionError,
    ConfigurationError,
)


class TestExecutionResult(TestCase):
    """Test the ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """Test creating an ExecutionResult with all fields."""
        result = ExecutionResult(
            executable="echo",
            args=["Hello", "World"],
            exit_code=0,
            stdout="Hello World\n",
            stderr="",
            execution_time=0.05,
            cwd="/tmp",
            env_vars={"TEST": "value"},
        )

        self.assertEqual(result.executable, "echo")
        self.assertEqual(result.args, ["Hello", "World"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "Hello World\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.execution_time, 0.05)
        self.assertEqual(result.cwd, "/tmp")
        self.assertEqual(result.env_vars, {"TEST": "value"})

    def test_success_property(self):
        """Test the success property for various exit codes."""
        # Successful execution
        result = ExecutionResult("echo", [], 0, "", "", 0.1)
        self.assertTrue(result.success)

        # Failed execution
        result = ExecutionResult("false", [], 1, "", "", 0.1)
        self.assertFalse(result.success)

        # Another failure code
        result = ExecutionResult("cmd", [], 42, "", "", 0.1)
        self.assertFalse(result.success)

    def test_command_line_property(self):
        """Test the command_line property formatting."""
        # With arguments
        result = ExecutionResult("git", ["status", "--porcelain"], 0, "", "", 0.1)
        self.assertEqual(result.command_line, "git status --porcelain")

        # Without arguments
        result = ExecutionResult("whoami", [], 0, "", "", 0.1)
        self.assertEqual(result.command_line, "whoami")

        # Empty args list
        result = ExecutionResult("pwd", [], 0, "", "", 0.1)
        self.assertEqual(result.command_line, "pwd")


class TestFindExecutable(TestCase):
    """Test the _find_executable function."""

    def test_find_absolute_path_executable(self):
        """Test finding executable with absolute path."""
        # Create a temporary executable
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write("#!/usr/bin/env python3\nprint('test')\n")
            tmp_path = tmp.name

        try:
            # Make it executable
            os.chmod(tmp_path, 0o755)

            # Test finding it
            found_path = _find_executable(tmp_path)
            self.assertEqual(found_path, tmp_path)
        finally:
            # Clean up
            os.unlink(tmp_path)

    def test_find_executable_in_path(self):
        """Test finding executable in system PATH."""
        # Test with a common system executable
        found_path = _find_executable("echo")
        self.assertTrue(found_path.endswith("/echo") or found_path.endswith("echo"))
        self.assertTrue(os.path.exists(found_path))

    def test_executable_not_found_absolute_path(self):
        """Test exception when absolute path doesn't exist."""
        with self.assertRaises(ExecutableNotFoundError) as cm:
            _find_executable("/nonexistent/path/to/executable")

        self.assertIn("/nonexistent/path/to/executable", str(cm.exception))

    def test_executable_not_found_in_path(self):
        """Test exception when executable not found in PATH."""
        with self.assertRaises(ExecutableNotFoundError) as cm:
            _find_executable("nonexistent_command_12345")

        self.assertIn("nonexistent_command_12345", str(cm.exception))
        self.assertIn("not found", str(cm.exception))

    def test_non_executable_file(self):
        """Test exception when file exists but is not executable."""
        # Create a temporary non-executable file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("not executable")
            tmp_path = tmp.name

        try:
            # Make it non-executable
            os.chmod(tmp_path, 0o644)

            with self.assertRaises(ExecutableNotFoundError):
                _find_executable(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestRunExecutable(TestCase):
    """Test the main run_executable function."""

    def test_successful_execution(self):
        """Test successful executable execution."""
        result = run_executable("echo", ["Hello", "World"])

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Hello World", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertGreater(result.execution_time, 0)
        self.assertEqual(result.executable, "echo")
        self.assertEqual(result.args, ["Hello", "World"])

    def test_execution_with_no_args(self):
        """Test execution without arguments."""
        result = run_executable("whoami")

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertGreater(len(result.stdout.strip()), 0)
        self.assertEqual(result.args, [])

    def test_execution_with_working_directory(self):
        """Test execution with custom working directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = run_executable("pwd", cwd=tmp_dir)

            self.assertTrue(result.success)
            self.assertIn(tmp_dir, result.stdout)
            self.assertEqual(result.cwd, tmp_dir)

    def test_execution_with_environment_variables(self):
        """Test execution with custom environment variables."""
        env_vars = {"TEST_VAR": "test_value_12345"}
        result = run_executable("printenv", ["TEST_VAR"], env_vars=env_vars)

        self.assertTrue(result.success)
        self.assertIn("test_value_12345", result.stdout)
        self.assertEqual(result.env_vars, env_vars)

    def test_execution_failure_with_check(self):
        """Test execution failure with check_exit_code=True."""
        with self.assertRaises(ExecutionError) as cm:
            run_executable("bash", ["-c", "exit 42"])

        exception = cm.exception
        self.assertEqual(exception.exit_code, 42)
        self.assertEqual(exception.executable, "bash")
        self.assertEqual(exception.command_args, ["-c", "exit 42"])

    def test_execution_failure_without_check(self):
        """Test execution failure with check_exit_code=False."""
        result = run_executable("bash", ["-c", "exit 42"], check_exit_code=False)

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 42)
        self.assertGreater(result.execution_time, 0)

    def test_timeout_handling(self):
        """Test timeout handling."""
        with self.assertRaises(ExecutionError) as cm:
            run_executable("sleep", ["2"], timeout=0.5)

        exception = cm.exception
        self.assertEqual(exception.exit_code, -1)  # Timeout indicator
        self.assertGreater(exception.execution_time, 0.4)  # Should be close to timeout

    def test_timeout_with_no_output(self):
        """Test timeout handling when there is no output (stdout/stderr are None).
        
        This is a regression test for the bug where TimeoutExpired.stdout/stderr
        being None would cause an AttributeError when trying to decode.
        """
        with self.assertRaises(ExecutionError) as cm:
            # Command that times out without producing output
            run_executable("sleep", ["2"], timeout=0.1)

        exception = cm.exception
        self.assertEqual(exception.exit_code, -1)  # Timeout indicator
        # stdout and stderr should be None when no output was captured
        self.assertIsNone(exception.stdout)
        self.assertIsNone(exception.stderr)

    def test_timeout_with_partial_output(self):
        """Test timeout handling when there is partial output before timeout.
        
        This tests that partial output from before timeout is properly captured
        and decoded from bytes to string.
        """
        with self.assertRaises(ExecutionError) as cm:
            # Command that produces output then sleeps
            run_executable("bash", ["-c", "echo 'partial output'; sleep 2"], timeout=0.1)

        exception = cm.exception
        self.assertEqual(exception.exit_code, -1)  # Timeout indicator
        # Should have captured the partial output that was produced before timeout
        self.assertIsNotNone(exception.stdout)
        self.assertIn("partial output", exception.stdout)

    def test_capture_output_disabled(self):
        """Test execution with output capture disabled."""
        result = run_executable("echo", ["test"], capture_output=False)

        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_stderr_capture(self):
        """Test capturing stderr output."""
        result = run_executable(
            "bash", ["-c", "echo 'error' >&2"], check_exit_code=False
        )

        self.assertTrue(result.success)  # bash itself succeeds
        self.assertIn("error", result.stderr)

    def test_invalid_arguments_type(self):
        """Test error handling for invalid arguments type."""
        with self.assertRaises(ConfigurationError) as cm:
            run_executable("echo", "not a list")

        self.assertIn("args must be a list", str(cm.exception))

    def test_invalid_timeout(self):
        """Test error handling for invalid timeout."""
        with self.assertRaises(ConfigurationError) as cm:
            run_executable("echo", timeout=-1)

        self.assertIn("timeout must be positive", str(cm.exception))

    def test_invalid_working_directory(self):
        """Test error handling for invalid working directory."""
        with self.assertRaises(ConfigurationError) as cm:
            run_executable("echo", cwd="/nonexistent/directory")

        self.assertIn("Working directory does not exist", str(cm.exception))

    def test_executable_not_found(self):
        """Test error handling when executable is not found."""
        with self.assertRaises(ExecutableNotFoundError) as cm:
            run_executable("nonexistent_command_12345")

        self.assertIn("nonexistent_command_12345", str(cm.exception))


class TestExecutableEdgeCases(TestCase):
    """Test edge cases and error scenarios."""

    def test_empty_args_list(self):
        """Test execution with empty args list."""
        result = run_executable("echo", [])

        self.assertTrue(result.success)
        self.assertEqual(result.args, [])

    def test_args_with_special_characters(self):
        """Test execution with special characters in arguments."""
        special_text = "Hello $USER & echo 'test'"
        result = run_executable("echo", [special_text])

        self.assertTrue(result.success)
        self.assertIn(special_text, result.stdout)

    def test_large_output_handling(self):
        """Test handling of large output."""
        # Generate a reasonably large output (not too large to avoid timeouts)
        large_text = "x" * 1000
        result = run_executable("echo", [large_text])

        self.assertTrue(result.success)
        self.assertIn(large_text, result.stdout)

    def test_execution_timing_accuracy(self):
        """Test that execution timing is reasonably accurate."""
        start_time = time.time()
        result = run_executable("sleep", ["0.1"])
        end_time = time.time()

        self.assertTrue(result.success)
        # Execution time should be at least 0.1 seconds but not too much more
        self.assertGreaterEqual(result.execution_time, 0.09)
        self.assertLessEqual(result.execution_time, end_time - start_time + 0.1)

    @patch("subprocess.run")
    def test_os_error_handling(self, mock_run):
        """Test handling of OS errors during execution."""
        mock_run.side_effect = OSError("Permission denied")

        with self.assertRaises(ExecutionError) as cm:
            run_executable("echo", ["test"])

        exception = cm.exception
        self.assertEqual(exception.exit_code, -2)  # OS error indicator
        self.assertIn("Permission denied", exception.stderr)

    def test_none_values_handling(self):
        """Test handling of None values for optional parameters."""
        result = run_executable(
            "echo", args=None, cwd=None, env_vars=None, timeout=None
        )

        self.assertTrue(result.success)
        self.assertEqual(result.args, [])
        self.assertIsNone(result.cwd)
        self.assertIsNone(result.env_vars)


if __name__ == "__main__":
    import unittest

    unittest.main()
