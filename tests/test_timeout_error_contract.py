"""
Test suite to verify TimeoutError properly inherits from ExecutionError.

This test validates that the fix for the TimeoutError inheritance issue
ensures that all ExecutionError attributes are accessible, particularly
the exit_code attribute.
"""

import unittest

from skoglib import TimeoutError, ExecutionError, SkogAIError


class TestTimeoutErrorContract(unittest.TestCase):
    """Test that TimeoutError properly implements the ExecutionError contract."""

    def test_timeout_error_has_exit_code_attribute(self) -> None:
        """Test that TimeoutError has exit_code attribute from ExecutionError."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            command_args=["--arg"],
            log_error=False,
        )

        # Should have exit_code attribute
        self.assertTrue(hasattr(error, "exit_code"))
        self.assertEqual(error.exit_code, -1)

    def test_timeout_error_has_execution_time_attribute(self) -> None:
        """Test that TimeoutError has execution_time attribute from ExecutionError."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            execution_time=25.5,
            log_error=False,
        )

        # Should have execution_time attribute
        self.assertTrue(hasattr(error, "execution_time"))
        self.assertEqual(error.execution_time, 25.5)

    def test_timeout_error_execution_time_defaults_to_timeout(self) -> None:
        """Test that execution_time defaults to timeout if not provided."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            log_error=False,
        )

        # execution_time should default to timeout
        self.assertEqual(error.execution_time, 30.0)

    def test_timeout_error_has_stdout_stderr_attributes(self) -> None:
        """Test that TimeoutError has stdout/stderr attributes from ExecutionError."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            partial_stdout="output",
            partial_stderr="error",
            log_error=False,
        )

        # Should have stdout and stderr attributes from parent
        self.assertTrue(hasattr(error, "stdout"))
        self.assertTrue(hasattr(error, "stderr"))
        self.assertEqual(error.stdout, "output")
        self.assertEqual(error.stderr, "error")

    def test_timeout_error_has_partial_stdout_stderr_aliases(self) -> None:
        """Test that TimeoutError maintains partial_stdout/stderr aliases."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            partial_stdout="output",
            partial_stderr="error",
            log_error=False,
        )

        # Should have partial_stdout/stderr aliases
        self.assertTrue(hasattr(error, "partial_stdout"))
        self.assertTrue(hasattr(error, "partial_stderr"))
        self.assertEqual(error.partial_stdout, "output")
        self.assertEqual(error.partial_stderr, "error")

    def test_timeout_error_can_be_caught_as_execution_error(self) -> None:
        """Test that TimeoutError can be caught as ExecutionError."""
        try:
            raise TimeoutError("test-cmd", timeout=30.0, log_error=False)
        except ExecutionError as e:
            # Should catch as ExecutionError
            self.assertIsInstance(e, TimeoutError)
            self.assertIsInstance(e, ExecutionError)
            # Should have exit_code accessible
            self.assertEqual(e.exit_code, -1)

    def test_timeout_error_exit_code_in_error_handling(self) -> None:
        """Test that exit_code can be accessed in error handling code."""
        try:
            raise TimeoutError("test-cmd", timeout=30.0, log_error=False)
        except ExecutionError as e:
            # Code expecting exit_code from ExecutionError should work
            if e.exit_code == -1:
                # This is a timeout error
                self.assertIsInstance(e, TimeoutError)
            else:
                self.fail("exit_code should be -1 for timeout")

    def test_timeout_error_serialization_includes_all_attributes(self) -> None:
        """Test that TimeoutError serialization includes all required attributes."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            command_args=["--arg"],
            partial_stdout="output",
            partial_stderr="error",
            execution_time=25.5,
            log_error=False,
        )

        error_dict = error.to_dict()

        # Should include all details
        self.assertIn("exit_code", error_dict["details"])
        self.assertIn("execution_time", error_dict["details"])
        self.assertIn("timeout", error_dict["details"])
        self.assertEqual(error_dict["details"]["exit_code"], -1)
        self.assertEqual(error_dict["details"]["execution_time"], 25.5)
        self.assertEqual(error_dict["details"]["timeout"], 30.0)

    def test_timeout_error_maintains_timeout_specific_message(self) -> None:
        """Test that TimeoutError maintains its timeout-specific error message."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            command_args=["--arg"],
            log_error=False,
        )

        # Should have timeout-specific message
        self.assertIn("timed out", error.message.lower())
        self.assertIn("30.0 seconds", str(error))

    def test_timeout_error_has_timeout_specific_suggestions(self) -> None:
        """Test that TimeoutError includes timeout-specific suggestions."""
        error = TimeoutError(
            executable="test-cmd",
            timeout=30.0,
            log_error=False,
        )

        error_dict = error.to_dict()
        suggestions = error_dict["details"]["suggestions"]

        # Should have timeout-specific suggestions
        timeout_suggestion_found = any("timeout" in s.lower() for s in suggestions)
        hanging_suggestion_found = any("hanging" in s.lower() for s in suggestions)

        self.assertTrue(
            timeout_suggestion_found, "Should have timeout-related suggestion"
        )
        self.assertTrue(
            hanging_suggestion_found, "Should have hanging process suggestion"
        )

    def test_timeout_error_inherits_from_skogai_error(self) -> None:
        """Test that TimeoutError is part of the SkogAIError hierarchy."""
        error = TimeoutError("test-cmd", timeout=30.0, log_error=False)

        # Should inherit from SkogAIError
        self.assertIsInstance(error, SkogAIError)
        self.assertIsInstance(error, ExecutionError)
        self.assertIsInstance(error, TimeoutError)


if __name__ == "__main__":
    unittest.main()
