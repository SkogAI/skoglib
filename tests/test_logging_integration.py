"""
Test suite for full logging integration across skoglib modules.

Tests end-to-end logging scenarios and integration between modules.
"""

import logging
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

from skoglib import (
    run_executable,
    configure_logging,
    get_logger,
    ExecutableNotFoundError,
    ExecutionError,
)


class TestLoggingIntegration(TestCase):
    """Test end-to-end logging integration scenarios."""

    def setUp(self):
        """Set up integration test environment."""
        # Configure logging with detailed format for testing
        configure_logging(level=logging.DEBUG, format_style="detailed", force=True)

        # Add mock handler to capture all log messages
        self.mock_handler = MagicMock()
        self.mock_handler.level = logging.DEBUG  # Set proper level attribute

        # Add to root skoglib logger to catch all messages
        root_logger = get_logger("root")
        root_logger.addHandler(self.mock_handler)

    def tearDown(self):
        """Clean up after test."""
        root_logger = get_logger("root")
        if self.mock_handler in root_logger.handlers:
            root_logger.removeHandler(self.mock_handler)

    def test_successful_execution_logging(self):
        """Test logging for successful executable execution."""
        try:
            # Use a simple command that should exist on most systems
            _result = run_executable("echo", ["test message"])

            # Should have logged debug messages about execution
            self.mock_handler.handle.assert_called()

            # Check that we got appropriate log messages
            log_messages = [
                call.args[0].getMessage()
                for call in self.mock_handler.handle.call_args_list
            ]

            # Should have execution start message
            execution_msgs = [msg for msg in log_messages if "Executing:" in msg]
            self.assertTrue(
                len(execution_msgs) > 0, f"No execution messages in: {log_messages}"
            )

            # Should have completion message
            completion_msgs = [
                msg
                for msg in log_messages
                if "completed in" in msg and "exit code" in msg
            ]
            self.assertTrue(
                len(completion_msgs) > 0, f"No completion messages in: {log_messages}"
            )

        except (ExecutableNotFoundError, OSError):
            # Skip if echo is not available (shouldn't happen on most systems)
            self.skipTest("echo command not available")

    def test_executable_not_found_logging(self):
        """Test logging when executable is not found."""
        with self.assertRaises(ExecutableNotFoundError):
            run_executable("definitely-not-a-real-command-12345")

        # Should have logged the error
        self.mock_handler.handle.assert_called()

        # Check for error log message
        error_messages = [
            call.args[0].getMessage()
            for call in self.mock_handler.handle.call_args_list
            if call.args[0].levelno == logging.ERROR
        ]

        self.assertTrue(len(error_messages) > 0)
        error_msg = error_messages[0]
        self.assertIn("definitely-not-a-real-command-12345", error_msg)
        self.assertIn("not found", error_msg)

    def test_execution_failure_logging(self):
        """Test logging when execution fails."""
        try:
            with self.assertRaises(ExecutionError):
                # Use false command which should exist but always exits with code 1
                run_executable("false")

            # Should have logged the error
            error_messages = [
                call.args[0].getMessage()
                for call in self.mock_handler.handle.call_args_list
                if call.args[0].levelno == logging.ERROR
            ]

            self.assertTrue(len(error_messages) > 0)
            error_msg = error_messages[0]
            self.assertIn("false", error_msg)
            self.assertIn("failed", error_msg)

        except (ExecutableNotFoundError, OSError):
            # Skip if false command is not available
            self.skipTest("false command not available")

    def test_performance_logging_integration(self):
        """Test that performance logging works in real execution."""
        try:
            # Run a quick command
            run_executable("echo", ["performance test"])

            # Should have performance timing log
            debug_messages = [
                call.args[0].getMessage()
                for call in self.mock_handler.handle.call_args_list
                if call.args[0].levelno == logging.DEBUG
            ]

            # Look for performance log messages
            perf_messages = [
                msg for msg in debug_messages if "execute_echo completed" in msg
            ]
            self.assertTrue(
                len(perf_messages) > 0, f"No performance messages in: {debug_messages}"
            )

        except (ExecutableNotFoundError, OSError):
            self.skipTest("echo command not available")

    def test_logging_configuration_from_public_api(self):
        """Test that logging can be configured through the public API."""
        # Test that configure_logging is available from main import
        from skoglib import configure_logging, get_logger

        # Test configuration
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration_test.log"

            configure_logging(
                level="INFO", format_style="simple", output=log_file, force=True
            )

            # Test that logging works
            logger = get_logger("integration_test")
            logger.info("Integration test message")

            # Check that file was created
            self.assertTrue(log_file.exists())

            # Check file contents
            with open(log_file, "r") as f:
                content = f.read()
                self.assertIn("Integration test message", content)
                self.assertIn("[INFO]", content)

    def test_environment_configuration_integration(self):
        """Test environment-based configuration integration."""
        import os
        from skoglib import configure_from_env

        # Set environment variables
        old_level = os.environ.get("SKOGLIB_LOG_LEVEL")
        old_format = os.environ.get("SKOGLIB_LOG_FORMAT")

        try:
            os.environ["SKOGLIB_LOG_LEVEL"] = "DEBUG"
            os.environ["SKOGLIB_LOG_FORMAT"] = "detailed"

            configure_from_env()

            # Test that configuration worked
            root_logger = get_logger("root")
            self.assertEqual(root_logger.level, logging.DEBUG)

            # Check formatter is detailed
            if root_logger.handlers:
                formatter = root_logger.handlers[0].formatter
                self.assertTrue(hasattr(formatter, "detailed"))
                self.assertTrue(formatter.detailed)

        finally:
            # Clean up environment
            if old_level is not None:
                os.environ["SKOGLIB_LOG_LEVEL"] = old_level
            elif "SKOGLIB_LOG_LEVEL" in os.environ:
                del os.environ["SKOGLIB_LOG_LEVEL"]

            if old_format is not None:
                os.environ["SKOGLIB_LOG_FORMAT"] = old_format
            elif "SKOGLIB_LOG_FORMAT" in os.environ:
                del os.environ["SKOGLIB_LOG_FORMAT"]

    def test_logger_namespace_consistency(self):
        """Test that all loggers use consistent namespace."""
        from skoglib.logging_config import LOGGER_PREFIX

        # Get loggers from different modules
        executable_logger = get_logger("executable")
        exceptions_logger = get_logger("exceptions")
        performance_logger = get_logger("performance")

        # All should have the skoglib prefix
        self.assertTrue(executable_logger.name.startswith(LOGGER_PREFIX))
        self.assertTrue(exceptions_logger.name.startswith(LOGGER_PREFIX))
        self.assertTrue(performance_logger.name.startswith(LOGGER_PREFIX))

        # Test specific names
        self.assertEqual(executable_logger.name, f"{LOGGER_PREFIX}.executable")
        self.assertEqual(exceptions_logger.name, f"{LOGGER_PREFIX}.exceptions")
        self.assertEqual(performance_logger.name, f"{LOGGER_PREFIX}.performance")

    def test_log_level_hierarchy(self):
        """Test that log level hierarchy works correctly."""
        # Configure with WARNING level
        configure_logging(level=logging.WARNING, force=True)

        logger = get_logger("test")

        # Clear previous calls
        self.mock_handler.reset_mock()

        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Should only have WARNING and ERROR
        logged_levels = [
            call.args[0].levelno for call in self.mock_handler.handle.call_args_list
        ]

        self.assertNotIn(logging.DEBUG, logged_levels)
        self.assertNotIn(logging.INFO, logged_levels)
        self.assertIn(logging.WARNING, logged_levels)
        self.assertIn(logging.ERROR, logged_levels)

    def test_logging_doesnt_break_functionality(self):
        """Test that logging doesn't interfere with core functionality."""
        try:
            # Test basic functionality still works with logging enabled
            result = run_executable("echo", ["functionality test"])

            # Core functionality should work
            self.assertEqual(result.exit_code, 0)
            self.assertIn("functionality test", result.stdout)
            self.assertTrue(result.success)

            # And logging should have occurred
            self.mock_handler.handle.assert_called()

        except (ExecutableNotFoundError, OSError):
            self.skipTest("echo command not available")


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
