"""
Test suite for exception logging integration in skoglib.

Tests that exceptions are properly logged when raised.
"""

import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from skoglib.exceptions import (
    SkogAIError, 
    ExecutableNotFoundError,
    ExecutionError,
    ConfigurationError
)
from skoglib.logging_config import get_logger, configure_logging


class TestExceptionLogging(TestCase):
    """Test logging integration with exceptions."""
    
    def setUp(self):
        """Set up test logging environment."""
        # Configure logging to capture all messages
        configure_logging(level=logging.DEBUG, force=True)
        
        # Add mock handler to capture log messages
        self.mock_handler = MagicMock()
        self.mock_handler.level = logging.DEBUG  # Set proper level attribute
        
        # Get the exceptions logger and add our mock handler
        self.exceptions_logger = get_logger("exceptions")
        self.exceptions_logger.addHandler(self.mock_handler)
        
    def tearDown(self):
        """Clean up after test."""
        # Remove our mock handler
        if self.mock_handler in self.exceptions_logger.handlers:
            self.exceptions_logger.removeHandler(self.mock_handler)
    
    def test_skogai_error_logs_by_default(self):
        """Test that SkogAIError logs errors by default."""
        message = "Test error message"
        
        try:
            raise SkogAIError(message)
        except SkogAIError:
            pass
            
        # Should have logged the error
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertEqual(call_args.levelno, logging.ERROR)
        self.assertEqual(call_args.getMessage(), message)
    
    def test_skogai_error_logs_with_context(self):
        """Test that SkogAIError logs context information."""
        message = "Test error with context"
        context = {"key": "value", "number": 42}
        
        try:
            raise SkogAIError(message, context=context)
        except SkogAIError:
            pass
            
        # Should have logged the error with context
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertEqual(call_args.levelno, logging.ERROR)
        logged_message = call_args.getMessage()
        self.assertIn(message, logged_message)
        self.assertIn("Context:", logged_message)
        self.assertIn("key", logged_message)
        self.assertIn("value", logged_message)
        self.assertIn("42", logged_message)
    
    def test_skogai_error_can_disable_logging(self):
        """Test that logging can be disabled for SkogAIError."""
        message = "Test error without logging"
        
        try:
            raise SkogAIError(message, log_error=False)
        except SkogAIError:
            pass
            
        # Should not have logged anything
        self.mock_handler.handle.assert_not_called()
    
    def test_executable_not_found_error_logs(self):
        """Test that ExecutableNotFoundError logs appropriately."""
        executable = "nonexistent-command"
        search_paths = ["/usr/bin", "/bin"]
        
        try:
            raise ExecutableNotFoundError(executable, search_paths)
        except ExecutableNotFoundError:
            pass
            
        # Should have logged the error
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertEqual(call_args.levelno, logging.ERROR)
        logged_message = call_args.getMessage()
        self.assertIn(executable, logged_message)
        self.assertIn("not found", logged_message)
    
    def test_execution_error_logs(self):
        """Test that ExecutionError logs execution details."""
        executable = "failed-command"
        exit_code = 1
        stdout = "Some output"
        stderr = "Error output"
        execution_time = 1.23
        
        try:
            raise ExecutionError(
                executable=executable,
                exit_code=exit_code,
                command_args=["--arg", "value"],
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time
            )
        except ExecutionError:
            pass
            
        # Should have logged the error
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertEqual(call_args.levelno, logging.ERROR)
        logged_message = call_args.getMessage()
        self.assertIn(executable, logged_message)
        self.assertIn(str(exit_code), logged_message)
        self.assertIn("failed", logged_message)
    
    def test_configuration_error_logs(self):
        """Test that ConfigurationError logs configuration details."""
        message = "Invalid configuration"
        config_key = "timeout"
        config_value = -5
        valid_values = ["positive numbers"]
        
        try:
            raise ConfigurationError(
                message=message,
                config_key=config_key,
                config_value=config_value,
                valid_values=valid_values
            )
        except ConfigurationError:
            pass
            
        # Should have logged the error
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertEqual(call_args.levelno, logging.ERROR)
        logged_message = call_args.getMessage()
        self.assertIn(message, logged_message)
    
    def test_exception_string_representation(self):
        """Test that exception string representation includes context."""
        message = "Test error"
        context = {"executable": "test-cmd", "exit_code": 1}
        
        error = SkogAIError(message, context=context, log_error=False)
        error_str = str(error)
        
        self.assertIn(message, error_str)
        self.assertIn("context:", error_str)
        self.assertIn("executable=test-cmd", error_str)
        self.assertIn("exit_code=1", error_str)
    
    def test_exception_without_context_simple_string(self):
        """Test that exceptions without context have simple string representation."""
        message = "Simple error"
        
        error = SkogAIError(message, log_error=False)
        error_str = str(error)
        
        self.assertEqual(error_str, message)
        self.assertNotIn("context:", error_str)
    
    def test_logging_preserves_exception_hierarchy(self):
        """Test that logging doesn't interfere with exception hierarchy."""
        # Test that ExecutableNotFoundError is still a SkogAIError
        try:
            raise ExecutableNotFoundError("test")
        except SkogAIError:
            # Should catch as SkogAIError
            caught_as_base = True
        except:
            caught_as_base = False
        
        self.assertTrue(caught_as_base)
        
        # Test that specific exception type is preserved
        try:
            raise ExecutableNotFoundError("test")
        except ExecutableNotFoundError:
            # Should catch as specific type
            caught_as_specific = True
        except:
            caught_as_specific = False
        
        self.assertTrue(caught_as_specific)
    
    def test_exception_properties_preserved(self):
        """Test that exception properties are preserved after logging."""
        executable = "test-cmd"
        search_paths = ["/usr/bin", "/bin"]
        
        error = ExecutableNotFoundError(executable, search_paths)
        
        # Properties should be preserved
        self.assertEqual(error.executable, executable)
        self.assertEqual(error.search_paths, search_paths)
        
        # Context should include the executable
        self.assertIn("executable", error.context)
        self.assertEqual(error.context["executable"], executable)


class TestLoggingPerformance(TestCase):
    """Test that logging doesn't significantly impact performance."""
    
    def test_exception_creation_performance(self):
        """Test that exception creation with logging is reasonably fast."""
        import time
        
        # Time exception creation without logging
        start_time = time.time()
        for i in range(100):
            try:
                raise SkogAIError(f"Test error {i}", log_error=False)
            except SkogAIError:
                pass
        no_logging_time = time.time() - start_time
        
        # Time exception creation with logging (but at a level that won't actually log)
        configure_logging(level=logging.CRITICAL, force=True)  # Higher than ERROR
        
        start_time = time.time()
        for i in range(100):
            try:
                raise SkogAIError(f"Test error {i}", log_error=True)
            except SkogAIError:
                pass
        with_logging_time = time.time() - start_time
        
        # Logging overhead should be minimal when not actually logging
        # Allow up to 50% overhead for the logging check
        self.assertLess(with_logging_time, no_logging_time * 1.5,
                       f"Logging overhead too high: {with_logging_time:.3f}s vs {no_logging_time:.3f}s")


if __name__ == "__main__":
    # Run tests with verbose output
    import unittest
    unittest.main(verbosity=2)