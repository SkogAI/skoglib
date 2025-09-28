"""
Test suite for skoglib.logging_config module.

Tests logging configuration, performance logging, formatters, and integration.
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock


from skoglib.logging_config import (
    configure_logging,
    configure_from_env,
    get_logger,
    get_performance_logger,
    SkogLibFormatter,
    PerformanceLogger,
    DEFAULT_LOG_LEVEL,
    LOGGER_PREFIX
)


class TestSkogLibFormatter(TestCase):
    """Test the custom SkogLib formatter."""
    
    def test_simple_format(self):
        """Test simple format output."""
        formatter = SkogLibFormatter(detailed=False)
        
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.created = time.time()
        
        formatted = formatter.format(record)
        
        # Should contain timestamp, level, name, and message
        self.assertIn("[INFO]", formatted)
        self.assertIn("test:", formatted)
        self.assertIn("Test message", formatted)
        # Should NOT contain line numbers or function names in simple format
        self.assertNotIn("lineno", formatted)
        self.assertNotIn("funcName", formatted)
    
    def test_detailed_format_when_debug(self):
        """Test that DEBUG level automatically uses detailed format."""
        formatter = SkogLibFormatter(detailed=False)
        
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="test.py", lineno=42,
            msg="Debug message", args=(), exc_info=None, func="test_func"
        )
        record.created = time.time()
        
        formatted = formatter.format(record)
        
        # Should contain detailed information for DEBUG level
        self.assertIn("[DEBUG]", formatted)
        self.assertIn("test:42", formatted)
        self.assertIn("test_func", formatted)
        self.assertIn("Debug message", formatted)
    
    def test_detailed_format_when_requested(self):
        """Test explicit detailed format request."""
        formatter = SkogLibFormatter(detailed=True)
        
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=42,
            msg="Info message", args=(), exc_info=None, func="test_func"
        )
        record.created = time.time()
        
        formatted = formatter.format(record)
        
        # Should contain detailed information when explicitly requested
        self.assertIn("[INFO]", formatted)
        self.assertIn("test:42", formatted) 
        self.assertIn("test_func", formatted)
        self.assertIn("Info message", formatted)


class TestGetLogger(TestCase):
    """Test the get_logger function."""
    
    def test_get_logger_with_prefix(self):
        """Test that get_logger adds skoglib prefix."""
        logger = get_logger("test")
        self.assertEqual(logger.name, f"{LOGGER_PREFIX}.test")
    
    def test_get_logger_already_prefixed(self):
        """Test that get_logger doesn't double-prefix."""
        logger = get_logger(f"{LOGGER_PREFIX}.test")
        self.assertEqual(logger.name, f"{LOGGER_PREFIX}.test")
    
    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test")
        self.assertIsInstance(logger, logging.Logger)


class TestPerformanceLogger(TestCase):
    """Test the PerformanceLogger context manager."""
    
    def setUp(self):
        """Set up test logger."""
        self.test_logger = get_logger("test_performance")
        self.test_logger.setLevel(logging.DEBUG)
        
        # Add a mock handler to capture log messages
        self.mock_handler = MagicMock()
        self.mock_handler.level = logging.DEBUG  # Set proper level attribute
        self.test_logger.addHandler(self.mock_handler)
    
    def tearDown(self):
        """Clean up test logger."""
        self.test_logger.handlers.clear()
    
    def test_performance_logger_logs_when_debug_enabled(self):
        """Test that performance logger works when DEBUG is enabled."""
        perf_logger = PerformanceLogger(self.test_logger, "test_operation", 0.0)
        
        with perf_logger:
            # Simulate some work
            time.sleep(0.01)
        
        # Should have logged the timing
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertEqual(call_args.levelno, logging.DEBUG)
        self.assertIn("test_operation completed", call_args.getMessage())
    
    def test_performance_logger_skips_when_debug_disabled(self):
        """Test that performance logger skips when DEBUG is disabled."""
        self.test_logger.setLevel(logging.INFO)
        perf_logger = PerformanceLogger(self.test_logger, "test_operation", 0.0)
        
        with perf_logger:
            time.sleep(0.01)
        
        # Should not have logged anything
        self.mock_handler.handle.assert_not_called()
    
    def test_performance_logger_threshold(self):
        """Test that performance logger respects threshold."""
        perf_logger = PerformanceLogger(self.test_logger, "fast_operation", 100.0)  # 100ms threshold
        
        with perf_logger:
            # Sleep for less than threshold
            time.sleep(0.001)  # 1ms
        
        # Should not have logged due to threshold
        self.mock_handler.handle.assert_not_called()


class TestConfigureLogging(TestCase):
    """Test the configure_logging function."""
    
    def setUp(self):
        """Set up clean logging state for each test."""
        # Clear all handlers from skoglib loggers
        root_logger = get_logger("root")
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)
    
    def tearDown(self):
        """Clean up after each test."""
        root_logger = get_logger("root")
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)
    
    def test_configure_logging_defaults(self):
        """Test configure_logging with default parameters."""
        configure_logging()
        
        root_logger = get_logger("root")
        
        # Should have one handler (console)
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)
        self.assertEqual(root_logger.level, DEFAULT_LOG_LEVEL)
    
    def test_configure_logging_custom_level(self):
        """Test configure_logging with custom log level."""
        configure_logging(level=logging.DEBUG)
        
        root_logger = get_logger("root")
        self.assertEqual(root_logger.level, logging.DEBUG)
        self.assertEqual(root_logger.handlers[0].level, logging.DEBUG)
    
    def test_configure_logging_string_level(self):
        """Test configure_logging with string log level."""
        configure_logging(level="DEBUG")
        
        root_logger = get_logger("root")
        self.assertEqual(root_logger.level, logging.DEBUG)
    
    def test_configure_logging_no_console(self):
        """Test configure_logging with console disabled."""
        configure_logging(console=False)
        
        root_logger = get_logger("root")
        # Should have no handlers when console is disabled and no file output
        self.assertEqual(len(root_logger.handlers), 0)
    
    def test_configure_logging_with_file(self):
        """Test configure_logging with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            configure_logging(output=log_file)
            
            root_logger = get_logger("root")
            # Should have console + file handlers
            self.assertEqual(len(root_logger.handlers), 2)
            
            # Check that one handler is a RotatingFileHandler
            handler_types = [type(h).__name__ for h in root_logger.handlers]
            self.assertIn("RotatingFileHandler", handler_types)
            self.assertIn("StreamHandler", handler_types)
    
    def test_configure_logging_detailed_format(self):
        """Test configure_logging with detailed format."""
        configure_logging(format_style="detailed")
        
        root_logger = get_logger("root")
        formatter = root_logger.handlers[0].formatter
        self.assertIsInstance(formatter, SkogLibFormatter)
        self.assertTrue(formatter.detailed)
    
    def test_configure_logging_only_once(self):
        """Test that configure_logging only configures once by default."""
        configure_logging(level=logging.DEBUG)
        initial_handler_count = len(get_logger("root").handlers)
        
        # Second call should not add more handlers
        configure_logging(level=logging.INFO)
        self.assertEqual(len(get_logger("root").handlers), initial_handler_count)
        
        # Level should remain DEBUG (first configuration)
        self.assertEqual(get_logger("root").level, logging.DEBUG)
    
    def test_configure_logging_force_reconfigure(self):
        """Test force reconfiguration."""
        configure_logging(level=logging.DEBUG)
        
        # Force reconfiguration with different level
        configure_logging(level=logging.INFO, force=True)
        
        root_logger = get_logger("root")
        self.assertEqual(root_logger.level, logging.INFO)


class TestConfigureFromEnv(TestCase):
    """Test environment-based logging configuration."""
    
    def setUp(self):
        """Clean up environment variables."""
        env_vars = [
            "SKOGLIB_LOG_LEVEL", 
            "SKOGLIB_LOG_FORMAT",
            "SKOGLIB_LOG_FILE", 
            "SKOGLIB_LOG_CONSOLE"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Clear logging configuration
        root_logger = get_logger("root")
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)
    
    def tearDown(self):
        """Clean up after test."""
        env_vars = [
            "SKOGLIB_LOG_LEVEL",
            "SKOGLIB_LOG_FORMAT", 
            "SKOGLIB_LOG_FILE",
            "SKOGLIB_LOG_CONSOLE"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_configure_from_env_defaults(self):
        """Test configure_from_env with no environment variables."""
        configure_from_env()
        
        root_logger = get_logger("root")
        self.assertEqual(root_logger.level, logging.WARNING)
        self.assertEqual(len(root_logger.handlers), 1)
    
    def test_configure_from_env_custom_level(self):
        """Test configure_from_env with custom log level."""
        os.environ["SKOGLIB_LOG_LEVEL"] = "DEBUG"
        
        configure_from_env()
        
        root_logger = get_logger("root")
        self.assertEqual(root_logger.level, logging.DEBUG)
    
    def test_configure_from_env_detailed_format(self):
        """Test configure_from_env with detailed format."""
        os.environ["SKOGLIB_LOG_FORMAT"] = "detailed"
        
        configure_from_env()
        
        root_logger = get_logger("root")
        formatter = root_logger.handlers[0].formatter
        self.assertTrue(formatter.detailed)
    
    def test_configure_from_env_no_console(self):
        """Test configure_from_env with console disabled."""
        os.environ["SKOGLIB_LOG_CONSOLE"] = "false"
        
        configure_from_env()
        
        root_logger = get_logger("root")
        # Should have no handlers when console disabled and no file
        self.assertEqual(len(root_logger.handlers), 0)
    
    def test_configure_from_env_invalid_format(self):
        """Test configure_from_env with invalid format falls back to simple."""
        os.environ["SKOGLIB_LOG_FORMAT"] = "invalid"
        
        configure_from_env()
        
        root_logger = get_logger("root")
        formatter = root_logger.handlers[0].formatter
        self.assertFalse(formatter.detailed)
    
    def test_configure_from_env_with_file(self):
        """Test configure_from_env with log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            os.environ["SKOGLIB_LOG_FILE"] = str(log_file)
            
            configure_from_env()
            
            root_logger = get_logger("root")
            # Should have console + file handlers
            self.assertEqual(len(root_logger.handlers), 2)


class TestGetPerformanceLogger(TestCase):
    """Test the get_performance_logger function."""
    
    def test_get_performance_logger(self):
        """Test that get_performance_logger returns a PerformanceLogger."""
        perf_logger = get_performance_logger("test_operation")
        
        self.assertIsInstance(perf_logger, PerformanceLogger)
        self.assertEqual(perf_logger.operation, "test_operation")
        self.assertEqual(perf_logger.logger.name, f"{LOGGER_PREFIX}.performance")


class TestLoggingIntegration(TestCase):
    """Test logging integration scenarios."""
    
    def setUp(self):
        """Set up integration test environment."""
        # Configure logging to capture all messages
        configure_logging(level=logging.DEBUG, force=True)
        
        # Add mock handler to capture messages
        self.mock_handler = MagicMock()
        self.mock_handler.level = logging.DEBUG  # Set proper level attribute
        root_logger = get_logger("root")
        root_logger.addHandler(self.mock_handler)
        
    def tearDown(self):
        """Clean up after integration test."""
        root_logger = get_logger("root")
        root_logger.handlers = [h for h in root_logger.handlers if not isinstance(h, MagicMock)]
    
    def test_module_loggers_work(self):
        """Test that module-specific loggers work correctly."""
        executable_logger = get_logger("executable")
        exceptions_logger = get_logger("exceptions")
        
        # Ensure loggers propagate to root
        executable_logger.propagate = True
        exceptions_logger.propagate = True
        
        # Clear any previous calls
        self.mock_handler.reset_mock()
        
        executable_logger.info("Test executable log")
        exceptions_logger.error("Test exception log")
        
        # Both should have been logged
        self.assertEqual(self.mock_handler.handle.call_count, 2)
    
    def test_performance_logging_integration(self):
        """Test that performance logging integrates properly."""
        # Clear any previous calls
        self.mock_handler.reset_mock()
        
        with get_performance_logger("integration_test"):
            time.sleep(0.001)  # Small delay to ensure timing
        
        # Should have logged the performance timing
        self.mock_handler.handle.assert_called()
        call_args = self.mock_handler.handle.call_args[0][0]
        self.assertIn("integration_test completed", call_args.getMessage())


if __name__ == "__main__":
    # Run tests with verbose output
    import unittest
    unittest.main(verbosity=2)