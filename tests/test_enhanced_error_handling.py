"""
Test the enhanced error handling and recovery features according to Task 6 requirements.

This test file validates the new exception hierarchy, error messages with suggestions,
serialization capabilities, and timestamp functionality.
"""

import time
import unittest
from unittest.mock import patch

from skoglib import (
    SkogAIError,
    ExecutableNotFoundError,
    ExecutionError,
    TimeoutError,
    PermissionError,
    ConfigurationError
)


class TestEnhancedErrorHandling(unittest.TestCase):
    """Test enhanced error handling features from Task 6."""
    
    def test_skogai_error_to_dict_serialization(self):
        """Test that SkogAIError can be serialized to dictionary."""
        message = "Test error message"
        details = {"key": "value", "number": 42}
        
        error = SkogAIError(message, details=details, log_error=False)
        error_dict = error.to_dict()
        
        # Verify required fields
        self.assertEqual(error_dict["error_type"], "SkogAIError")
        self.assertEqual(error_dict["message"], message)
        self.assertEqual(error_dict["details"], details)
        self.assertIsInstance(error_dict["timestamp"], float)
        
        # Verify timestamp is recent
        self.assertGreater(error_dict["timestamp"], time.time() - 1.0)
    
    def test_timeout_error_hierarchy_and_details(self):
        """Test TimeoutError is properly structured with actionable suggestions."""  
        executable = "long-running-command"
        timeout = 30.0
        command_args = ["--verbose", "input.txt"]
        partial_stdout = "Processing..."
        
        error = TimeoutError(
            executable=executable,
            timeout=timeout,
            command_args=command_args,
            partial_stdout=partial_stdout,
            log_error=False
        )
        
        # Test inheritance
        self.assertIsInstance(error, ExecutionError)
        self.assertIsInstance(error, SkogAIError)
        
        # Test message format
        expected_cmd = f"{executable} {' '.join(command_args)}"
        self.assertIn(expected_cmd, str(error))
        self.assertIn(f"{timeout} seconds", str(error))
        
        # Test details include suggestions
        error_dict = error.to_dict()
        self.assertIn("suggestions", error_dict["details"])
        suggestions = error_dict["details"]["suggestions"]
        self.assertIsInstance(suggestions, list)
        self.assertTrue(any("timeout" in s.lower() for s in suggestions))
        self.assertTrue(any("hanging" in s.lower() for s in suggestions))
        
        # Test specific attributes
        self.assertEqual(error.executable, executable)
        self.assertEqual(error.timeout, timeout)
        self.assertEqual(error.command_args, command_args)
        self.assertEqual(error.partial_stdout, partial_stdout)
    
    def test_permission_error_hierarchy_and_suggestions(self):
        """Test PermissionError provides actionable guidance."""
        executable = "/usr/local/bin/restricted-tool"
        file_mode = "644"
        
        error = PermissionError(executable=executable, file_mode=file_mode)
        
        # Test inheritance
        self.assertIsInstance(error, ExecutableNotFoundError) 
        self.assertIsInstance(error, SkogAIError)
        
        # Test message
        self.assertIn("Permission denied", str(error))
        self.assertIn(executable, str(error))
        
        # Test actionable suggestions
        error_dict = error.to_dict()
        suggestions = error_dict["details"]["suggestions"]
        self.assertTrue(any("chmod" in s for s in suggestions))
        self.assertTrue(any("sudo" in s.lower() for s in suggestions))
        self.assertTrue(any("permissions" in s.lower() for s in suggestions))
        
        # Test attributes
        self.assertEqual(error.executable, executable)
        self.assertEqual(error.file_mode, file_mode)
    
    def test_executable_not_found_enhanced_suggestions(self):
        """Test ExecutableNotFoundError includes actionable suggestions."""
        executable = "missing-tool"
        search_paths = ["/usr/bin", "/usr/local/bin", "/opt/bin"]
        
        error = ExecutableNotFoundError(executable, search_paths)
        
        # Test enhanced message
        error_str = str(error)
        self.assertIn("PATH or specified location", error_str)
        self.assertIn("searched:", error_str)
        
        # Test suggestions
        error_dict = error.to_dict()
        suggestions = error_dict["details"]["suggestions"]
        self.assertTrue(any("install" in s.lower() for s in suggestions))
        self.assertTrue(any("path" in s.lower() for s in suggestions))
        self.assertTrue(any("absolute" in s.lower() for s in suggestions))
    
    def test_execution_error_enhanced_suggestions(self):
        """Test ExecutionError provides debugging guidance."""
        executable = "failing-command"
        exit_code = 127
        stderr = "Command not found"
        
        error = ExecutionError(
            executable=executable,
            exit_code=exit_code,
            stderr=stderr,
            log_error=False
        )
        
        # Test suggestions for troubleshooting
        error_dict = error.to_dict()
        suggestions = error_dict["details"]["suggestions"]
        self.assertTrue(any("arguments" in s.lower() for s in suggestions))
        self.assertTrue(any("stderr" in s.lower() for s in suggestions))
        self.assertTrue(any("documentation" in s.lower() for s in suggestions))
    
    def test_configuration_error_enhanced_suggestions(self):
        """Test ConfigurationError provides configuration guidance."""
        message = "Invalid log level"
        config_key = "log_level"
        config_value = "INVALID"
        valid_values = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        error = ConfigurationError(
            message=message,
            config_key=config_key,
            config_value=config_value,
            valid_values=valid_values
        )
        
        # Test suggestions
        error_dict = error.to_dict()
        suggestions = error_dict["details"]["suggestions"]
        self.assertTrue(any("configuration" in s.lower() for s in suggestions))
        self.assertTrue(any("environment" in s.lower() for s in suggestions))
        self.assertTrue(any("documentation" in s.lower() for s in suggestions))
        
        # Test configuration context
        details = error_dict["details"]
        self.assertEqual(details["config_key"], config_key)
        self.assertEqual(details["config_value"], config_value)
        self.assertEqual(details["valid_values"], valid_values)
    
    def test_error_context_preservation(self):
        """Test that error context is preserved through the call stack."""
        def level3():
            raise ExecutableNotFoundError("deep-command", ["/deep/path"])
            
        def level2():
            try:
                level3()
            except ExecutableNotFoundError as e:
                # Re-raise with additional context
                details = e.details.copy()
                details["call_level"] = "level2"
                raise SkogAIError(f"Failed in level2: {e.message}", details=details) from e
                
        def level1():
            try:
                level2()
            except SkogAIError as e:
                details = e.details.copy()
                details["call_level_1"] = "level1"
                raise SkogAIError(f"Failed in level1: {e.message}", details=details) from e
        
        with self.assertRaises(SkogAIError) as context:
            level1()
            
        error = context.exception
        error_dict = error.to_dict()
        
        # Verify context preservation
        self.assertIn("call_level", error_dict["details"])
        self.assertIn("call_level_1", error_dict["details"])
        self.assertIn("executable", error_dict["details"])
        
        # Verify exception chain
        self.assertIsNotNone(error.__cause__)
        self.assertIsInstance(error.__cause__, SkogAIError)
    
    def test_backward_compatibility_with_context_parameter(self):
        """Test that the old 'context' parameter still works."""
        message = "Backward compatibility test"
        context = {"old_style": "context"}
        
        # Should work with context parameter
        error = SkogAIError(message, context=context, log_error=False)
        
        # Should be accessible via both context and details
        self.assertEqual(error.context, context)
        self.assertEqual(error.details, context)
        
        # Should serialize properly
        error_dict = error.to_dict()
        self.assertEqual(error_dict["details"], context)
    
    def test_cannot_specify_both_details_and_context(self):
        """Test that specifying both details and context raises an error."""
        with self.assertRaises(ValueError) as context:
            SkogAIError("test", details={"a": 1}, context={"b": 2})
        
        self.assertIn("Cannot specify both", str(context.exception))


if __name__ == "__main__":
    unittest.main()