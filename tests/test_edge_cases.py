"""
Test suite for edge cases and critical scenarios not covered in main tests.

This test file addresses specific edge cases identified in issue #44:
1. TimeoutExpired with None stdout/stderr (critical - would catch bug from #37)
2. Large output vs max_output_size scenarios
3. Concurrent subprocess execution
4. Windows path edge cases

All tests are verbose for debugging purposes and use real execution (no mocking).
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest import TestCase
from concurrent.futures import ThreadPoolExecutor, as_completed

from skoglib.executable import run_executable, ExecutionResult
from skoglib.exceptions import ExecutionError, ExecutableNotFoundError


class TestTimeoutWithNoneOutput(TestCase):
    """Test timeout scenarios with None stdout/stderr.

    Critical tests that would have caught the timeout decoding bug in #37.
    The bug was in executable.py:422-423 where e.stdout and e.stderr could be None
    but the code tried to decode them without checking.
    """

    def test_timeout_with_no_output_capture(self):
        """Test timeout when capture_output=False results in None stdout/stderr.

        This is the critical test case that would have caught bug #37.
        When capture_output=False, subprocess.TimeoutExpired.stdout and .stderr
        are None, and attempting to decode them causes AttributeError.
        """
        print("\n[VERBOSE] Testing timeout with capture_output=False")
        print("[VERBOSE] This should handle None stdout/stderr gracefully")

        with self.assertRaises(ExecutionError) as cm:
            result = run_executable(
                "sleep",
                ["2"],
                timeout=0.5,
                capture_output=False  # This causes stdout/stderr to be None
            )

        exception = cm.exception
        print(f"[VERBOSE] Caught ExecutionError: {exception}")
        print(f"[VERBOSE] Exit code: {exception.exit_code}")
        print(f"[VERBOSE] Stdout: {exception.stdout}")
        print(f"[VERBOSE] Stderr: {exception.stderr}")

        # Verify exception attributes
        self.assertEqual(exception.exit_code, -1, "Timeout should use exit code -1")
        self.assertIsNone(exception.stdout, "Stdout should be None when not captured")
        self.assertIsNone(exception.stderr, "Stderr should be None when not captured")
        self.assertGreater(exception.execution_time, 0.4, "Should track execution time")
        self.assertLess(exception.execution_time, 1.0, "Should not wait for full sleep")

    def test_timeout_with_captured_output(self):
        """Test timeout with output capture enabled for comparison.

        This test verifies that timeout handling works correctly when output
        is captured, providing a baseline for comparison with the no-capture case.
        """
        print("\n[VERBOSE] Testing timeout with capture_output=True")

        with self.assertRaises(ExecutionError) as cm:
            # Create a command that produces some output before timeout
            result = run_executable(
                "bash",
                ["-c", "echo 'starting'; sleep 2; echo 'done'"],
                timeout=0.5,
                capture_output=True
            )

        exception = cm.exception
        print(f"[VERBOSE] Caught ExecutionError: {exception}")
        print(f"[VERBOSE] Stdout captured: {repr(exception.stdout)}")
        print(f"[VERBOSE] Stderr captured: {repr(exception.stderr)}")

        # Verify we captured partial output before timeout
        self.assertEqual(exception.exit_code, -1)
        # stdout/stderr might be empty strings or contain partial output
        # The key is they should NOT be None
        self.assertIsNotNone(exception.stdout, "Stdout should not be None when captured")
        self.assertIsNotNone(exception.stderr, "Stderr should not be None when captured")

    def test_timeout_with_no_output_produced(self):
        """Test timeout when command produces no output at all.

        Tests the case where a command times out without producing any output,
        ensuring we handle empty output correctly.
        """
        print("\n[VERBOSE] Testing timeout with command that produces no output")

        with self.assertRaises(ExecutionError) as cm:
            result = run_executable(
                "sleep",
                ["2"],
                timeout=0.3,
                capture_output=True
            )

        exception = cm.exception
        print(f"[VERBOSE] Exception stdout: {repr(exception.stdout)}")
        print(f"[VERBOSE] Exception stderr: {repr(exception.stderr)}")

        # Should have empty strings, not None, when capture is enabled
        self.assertEqual(exception.exit_code, -1)
        self.assertEqual(exception.stdout, "", "Should be empty string for no output")
        self.assertEqual(exception.stderr, "", "Should be empty string for no stderr")


class TestLargeOutput(TestCase):
    """Test handling of large output streams.

    Tests memory protection and proper handling when output exceeds typical sizes.
    Note: Currently no max_output_size limit is implemented in the library,
    so these tests document current behavior.
    """

    def test_large_stdout_output(self):
        """Test handling of large stdout output (1MB+).

        Verifies that large output is captured correctly without truncation
        or memory issues. If max_output_size were implemented, this would
        test that behavior.
        """
        print("\n[VERBOSE] Testing large stdout output (1MB+)")

        # Generate 1MB of output (1024 * 1024 bytes)
        large_size = 1024 * 1024
        print(f"[VERBOSE] Generating {large_size} bytes of output")

        result = run_executable(
            "python3",
            ["-c", f"print('x' * {large_size})"],
            timeout=10.0
        )

        print(f"[VERBOSE] Captured {len(result.stdout)} bytes")
        print(f"[VERBOSE] Exit code: {result.exit_code}")
        print(f"[VERBOSE] Execution time: {result.execution_time:.3f}s")

        self.assertTrue(result.success)
        self.assertGreater(len(result.stdout), large_size, "Should capture all output")
        self.assertIn('x', result.stdout, "Output should contain expected character")

    def test_large_stderr_output(self):
        """Test handling of large stderr output.

        Ensures stderr can handle large volumes of data without issues.
        """
        print("\n[VERBOSE] Testing large stderr output")

        large_size = 512 * 1024  # 512KB
        print(f"[VERBOSE] Generating {large_size} bytes on stderr")

        result = run_executable(
            "python3",
            ["-c", f"import sys; sys.stderr.write('e' * {large_size})"],
            timeout=10.0,
            check_exit_code=False
        )

        print(f"[VERBOSE] Captured {len(result.stderr)} bytes on stderr")
        print(f"[VERBOSE] Execution time: {result.execution_time:.3f}s")

        self.assertTrue(result.success)
        self.assertGreater(len(result.stderr), large_size * 0.9, "Should capture most/all stderr")

    def test_combined_large_output(self):
        """Test handling when both stdout and stderr are large.

        Verifies that the library can handle large volumes on both streams
        simultaneously without deadlocks or data loss.
        """
        print("\n[VERBOSE] Testing combined large stdout and stderr")

        size = 256 * 1024  # 256KB each
        print(f"[VERBOSE] Generating {size} bytes on both stdout and stderr")

        result = run_executable(
            "python3",
            ["-c", f"import sys; print('o' * {size}); sys.stderr.write('e' * {size})"],
            timeout=10.0
        )

        print(f"[VERBOSE] Stdout: {len(result.stdout)} bytes")
        print(f"[VERBOSE] Stderr: {len(result.stderr)} bytes")
        print(f"[VERBOSE] Total: {len(result.stdout) + len(result.stderr)} bytes")

        self.assertTrue(result.success)
        self.assertGreater(len(result.stdout), size * 0.9)
        self.assertGreater(len(result.stderr), size * 0.9)


class TestConcurrentExecution(TestCase):
    """Test concurrent subprocess execution scenarios.

    Verifies thread safety and proper resource management when running
    multiple subprocesses simultaneously.
    """

    def test_concurrent_simple_commands(self):
        """Test running multiple simple commands concurrently.

        Verifies basic thread safety with simple, fast commands.
        """
        print("\n[VERBOSE] Testing concurrent execution of 10 simple commands")

        num_concurrent = 10
        results = []

        def run_echo(i):
            print(f"[VERBOSE] Thread {i}: Starting execution")
            result = run_executable("echo", [f"test_{i}"])
            print(f"[VERBOSE] Thread {i}: Completed in {result.execution_time:.3f}s")
            return result

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_echo, i) for i in range(num_concurrent)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        print(f"[VERBOSE] All {len(results)} commands completed")

        # Verify all succeeded
        self.assertEqual(len(results), num_concurrent)
        for i, result in enumerate(results):
            self.assertTrue(result.success, f"Command {i} should succeed")
            self.assertIn("test_", result.stdout, f"Command {i} should have correct output")

    def test_concurrent_with_different_commands(self):
        """Test running different types of commands concurrently.

        Ensures proper isolation between different command types.
        """
        print("\n[VERBOSE] Testing concurrent execution of different command types")

        def run_whoami():
            print("[VERBOSE] Running whoami")
            return run_executable("whoami")

        def run_pwd():
            print("[VERBOSE] Running pwd")
            return run_executable("pwd")

        def run_echo():
            print("[VERBOSE] Running echo")
            return run_executable("echo", ["test"])

        def run_date():
            print("[VERBOSE] Running date")
            return run_executable("date")

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_whoami = executor.submit(run_whoami)
            future_pwd = executor.submit(run_pwd)
            future_echo = executor.submit(run_echo)
            future_date = executor.submit(run_date)

            results = {
                'whoami': future_whoami.result(),
                'pwd': future_pwd.result(),
                'echo': future_echo.result(),
                'date': future_date.result()
            }

        print("[VERBOSE] All different commands completed")
        for cmd, result in results.items():
            print(f"[VERBOSE] {cmd}: exit_code={result.exit_code}, time={result.execution_time:.3f}s")
            self.assertTrue(result.success, f"{cmd} should succeed")

    def test_concurrent_with_working_directories(self):
        """Test concurrent execution with different working directories.

        Verifies that working directory handling is thread-safe and properly
        isolated between concurrent executions.
        """
        print("\n[VERBOSE] Testing concurrent execution with different working directories")

        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            dirs = []
            for i in range(5):
                dir_path = Path(tmpdir) / f"dir_{i}"
                dir_path.mkdir()
                dirs.append(str(dir_path))

            print(f"[VERBOSE] Created {len(dirs)} temporary directories")

            def run_pwd_in_dir(dir_path, index):
                print(f"[VERBOSE] Thread {index}: Running pwd in {dir_path}")
                result = run_executable("pwd", cwd=dir_path)
                print(f"[VERBOSE] Thread {index}: Got {result.stdout.strip()}")
                return result, dir_path

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(run_pwd_in_dir, dir_path, i)
                    for i, dir_path in enumerate(dirs)
                ]

                for future in as_completed(futures):
                    result, expected_dir = future.result()
                    self.assertTrue(result.success)
                    self.assertIn(expected_dir, result.stdout,
                                "Output should match working directory")

    def test_concurrent_with_timeouts(self):
        """Test concurrent execution where some commands timeout.

        Verifies that timeout handling works correctly when multiple
        commands are running concurrently.
        """
        print("\n[VERBOSE] Testing concurrent execution with mixed timeouts")

        def run_with_timeout(sleep_time, timeout, index):
            print(f"[VERBOSE] Thread {index}: sleep={sleep_time}s, timeout={timeout}s")
            try:
                result = run_executable("sleep", [str(sleep_time)], timeout=timeout)
                print(f"[VERBOSE] Thread {index}: Completed successfully")
                return ("success", result)
            except ExecutionError as e:
                print(f"[VERBOSE] Thread {index}: Timed out as expected")
                return ("timeout", e)

        # Mix of commands that complete and timeout
        test_cases = [
            (0.1, 1.0, 0),  # Should complete
            (2.0, 0.5, 1),  # Should timeout
            (0.2, 1.0, 2),  # Should complete
            (2.0, 0.3, 3),  # Should timeout
            (0.1, 1.0, 4),  # Should complete
        ]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(run_with_timeout, sleep_time, timeout, index)
                for sleep_time, timeout, index in test_cases
            ]

            results = [future.result() for future in as_completed(futures)]

        print(f"[VERBOSE] Completed {len(results)} concurrent operations")

        # Verify we got the expected mix of successes and timeouts
        successes = [r for r in results if r[0] == "success"]
        timeouts = [r for r in results if r[0] == "timeout"]

        print(f"[VERBOSE] Successes: {len(successes)}, Timeouts: {len(timeouts)}")

        self.assertEqual(len(successes), 3, "Should have 3 successful completions")
        self.assertEqual(len(timeouts), 2, "Should have 2 timeouts")


class TestWindowsPathEdgeCases(TestCase):
    """Test Windows-specific path edge cases.

    These tests are platform-aware and will skip on non-Windows systems
    where the edge cases don't apply. On Windows, they verify proper
    handling of Windows-specific path formats.
    """

    def setUp(self):
        """Check if we're on Windows for conditional test execution."""
        self.is_windows = sys.platform.startswith('win')
        if self.is_windows:
            print(f"\n[VERBOSE] Running on Windows: {sys.platform}")
        else:
            print(f"\n[VERBOSE] Running on {sys.platform} (skipping Windows-specific tests)")

    def test_windows_absolute_path_with_drive_letter(self):
        """Test executable path with Windows drive letter (C:\\path\\to\\exe).

        Skipped on non-Windows systems.
        """
        if not self.is_windows:
            self.skipTest("Windows-specific test")

        print("[VERBOSE] Testing Windows absolute path with drive letter")

        # Test with system executable using absolute path
        # Use where.exe to find an executable, then test it
        result = run_executable("where", ["cmd.exe"])
        cmd_path = result.stdout.strip().split('\n')[0]

        print(f"[VERBOSE] Found cmd.exe at: {cmd_path}")
        self.assertRegex(cmd_path, r'^[A-Z]:\\', "Should have drive letter")

        # Now execute using absolute path
        result = run_executable(cmd_path, ["/c", "echo", "test"])
        print(f"[VERBOSE] Execution result: {result.stdout.strip()}")
        self.assertTrue(result.success)

    def test_windows_unc_path(self):
        """Test UNC path handling (\\\\server\\share\\path).

        Skipped on non-Windows systems or if no UNC path available.
        """
        if not self.is_windows:
            self.skipTest("Windows-specific test")

        print("[VERBOSE] Testing Windows UNC path handling")

        # We can't easily test actual UNC paths in CI, but we can test
        # that the path validation doesn't crash on UNC-style paths
        unc_path = r"\\server\share\nonexistent.exe"
        print(f"[VERBOSE] Testing with UNC path: {unc_path}")

        with self.assertRaises(ExecutableNotFoundError) as cm:
            run_executable(unc_path)

        print(f"[VERBOSE] Got expected error: {cm.exception}")
        self.assertIn(unc_path, str(cm.exception))

    def test_windows_path_with_spaces(self):
        """Test executable path containing spaces.

        Works on all platforms but particularly important on Windows
        where Program Files paths contain spaces.
        """
        print("[VERBOSE] Testing path with spaces")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory with spaces
            space_dir = Path(tmpdir) / "dir with spaces"
            space_dir.mkdir()

            script_path = space_dir / "test_script.sh"
            script_path.write_text("#!/bin/bash\necho 'success'\n")
            script_path.chmod(0o755)

            print(f"[VERBOSE] Created script at: {script_path}")

            result = run_executable(str(script_path))
            print(f"[VERBOSE] Result: {result.stdout.strip()}")

            self.assertTrue(result.success)
            self.assertIn("success", result.stdout)

    def test_windows_forward_slash_path(self):
        """Test that forward slashes work on Windows.

        Windows accepts both backslashes and forward slashes.
        """
        if not self.is_windows:
            self.skipTest("Windows-specific test")

        print("[VERBOSE] Testing forward slash path on Windows")

        # Convert a Windows path to use forward slashes
        result = run_executable("where", ["cmd.exe"])
        cmd_path = result.stdout.strip().split('\n')[0]
        cmd_path_forward = cmd_path.replace('\\', '/')

        print(f"[VERBOSE] Original path: {cmd_path}")
        print(f"[VERBOSE] Forward slash path: {cmd_path_forward}")

        # Should still work with forward slashes
        result = run_executable(cmd_path_forward, ["/c", "echo", "test"])
        self.assertTrue(result.success)

    def test_cross_platform_path_object(self):
        """Test that Path objects work correctly on all platforms.

        Ensures pathlib.Path objects are handled properly regardless of platform.
        """
        print(f"[VERBOSE] Testing Path object on {sys.platform}")

        # Create a temporary executable using Path
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test_script.sh"
            script_path.write_text("#!/bin/bash\necho 'path_object_test'\n")
            script_path.chmod(0o755)

            print(f"[VERBOSE] Script path type: {type(script_path)}")
            print(f"[VERBOSE] Script path: {script_path}")

            # Pass Path object directly
            result = run_executable(script_path)

            print(f"[VERBOSE] Result: {result.stdout.strip()}")
            self.assertTrue(result.success)
            self.assertIn("path_object_test", result.stdout)


if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)
