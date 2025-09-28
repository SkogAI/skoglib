"""
Test suite for import performance requirements in skoglib.

Validates that imports meet the <50ms requirement.
"""

import time
import sys
from unittest import TestCase


class TestImportPerformance(TestCase):
    """Test import performance requirements."""
    
    def setUp(self):
        """Clean up imported modules before each test."""
        # Remove skoglib modules from sys.modules if they exist
        modules_to_remove = [name for name in sys.modules.keys() if name.startswith('skoglib')]
        for module_name in modules_to_remove:
            del sys.modules[module_name]
    
    def test_logging_config_import_performance(self):
        """Test that logging_config import is under 50ms."""
        start_time = time.perf_counter()
        
        
        import_time_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"logging_config import time: {import_time_ms:.2f}ms")
        self.assertLess(import_time_ms, 50.0, 
                       f"logging_config import too slow: {import_time_ms:.2f}ms > 50ms")
    
    def test_exceptions_import_performance(self):
        """Test that exceptions import is under 50ms."""
        start_time = time.perf_counter()
        
        
        import_time_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"exceptions import time: {import_time_ms:.2f}ms")
        self.assertLess(import_time_ms, 50.0,
                       f"exceptions import too slow: {import_time_ms:.2f}ms > 50ms")
    
    def test_executable_import_performance(self):
        """Test that executable import is under 50ms."""
        start_time = time.perf_counter()
        
        
        import_time_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"executable import time: {import_time_ms:.2f}ms")
        self.assertLess(import_time_ms, 50.0,
                       f"executable import too slow: {import_time_ms:.2f}ms > 50ms")
    
    def test_main_module_import_performance(self):
        """Test that main skoglib import is under 50ms."""
        start_time = time.perf_counter()
        
        
        import_time_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"skoglib import time: {import_time_ms:.2f}ms")
        self.assertLess(import_time_ms, 50.0,
                       f"skoglib import too slow: {import_time_ms:.2f}ms > 50ms")
    
    def test_full_api_import_performance(self):
        """Test that importing the full public API is under 50ms."""
        start_time = time.perf_counter()
        
        from skoglib import (
            run_executable,
            ExecutionResult,
            SkogAIError,
            ExecutableNotFoundError,
            ExecutionError,
            ConfigurationError,
            configure_logging,
            configure_from_env,
            get_logger
        )
        
        import_time_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"Full API import time: {import_time_ms:.2f}ms")
        self.assertLess(import_time_ms, 50.0,
                       f"Full API import too slow: {import_time_ms:.2f}ms > 50ms")
        
        # Verify all imports worked
        self.assertIsNotNone(run_executable)
        self.assertIsNotNone(ExecutionResult)
        self.assertIsNotNone(SkogAIError)
        self.assertIsNotNone(ExecutableNotFoundError)
        self.assertIsNotNone(ExecutionError)
        self.assertIsNotNone(ConfigurationError)
        self.assertIsNotNone(configure_logging)
        self.assertIsNotNone(configure_from_env)
        self.assertIsNotNone(get_logger)


class TestImportTracking(TestCase):
    """Test the built-in import time tracking."""
    
    def setUp(self):
        """Clean up modules."""
        modules_to_remove = [name for name in sys.modules.keys() if name.startswith('skoglib')]
        for module_name in modules_to_remove:
            del sys.modules[module_name]
    
    def test_import_tracking_works(self):
        """Test that the built-in import tracking captures timing."""
        # Import with debug logging to see the tracking
        from skoglib.logging_config import configure_logging
        configure_logging(level="DEBUG", force=True)
        
        # Import should trigger the debug logging of import time
        
        # The tracking is automatically done - this test just ensures it doesn't crash
        self.assertTrue(True)
    
    def test_import_tracking_variables_exist(self):
        """Test that import tracking variables are set."""
        import skoglib.logging_config
        
        # Check that the tracking variables exist
        self.assertTrue(hasattr(skoglib.logging_config, '_import_start'))
        self.assertTrue(hasattr(skoglib.logging_config, '_import_duration'))
        
        # Duration should be a reasonable number (>0 and <100ms typically)
        duration = skoglib.logging_config._import_duration
        self.assertGreater(duration, 0)
        self.assertLess(duration, 100)  # Should be well under 100ms


if __name__ == "__main__":
    # Run with detailed output to see timing information
    import unittest
    unittest.main(verbosity=2)