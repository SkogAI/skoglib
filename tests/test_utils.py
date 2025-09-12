"""
Tests for skoglib.utils module.

Comprehensive tests for performance timing utilities, path handling,
and general utility functions.
"""

import time
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

from skoglib.utils import (
    time_execution,
    format_duration,
    timing_decorator,
    safe_dict_get,
    ensure_directory,
    bytes_to_human_readable
)


class TestTimeExecution:
    """Test the time_execution function."""
    
    def test_successful_execution(self):
        """Test timing a successful function execution."""
        def test_func():
            time.sleep(0.01)  # 10ms
            return "success"
        
        result, duration = time_execution(test_func)
        
        assert result == "success"
        assert duration >= 0.01  # Should be at least 10ms
        assert duration < 0.1    # Should be well under 100ms
    
    def test_function_with_exception(self):
        """Test timing a function that raises an exception."""
        def failing_func():
            time.sleep(0.005)  # 5ms
            raise ValueError("test error")
        
        with pytest.raises(ValueError, match="test error"):
            time_execution(failing_func)
    
    def test_zero_duration_function(self):
        """Test timing a very fast function."""
        def fast_func():
            return 42
        
        result, duration = time_execution(fast_func)
        
        assert result == 42
        assert duration >= 0  # Duration should never be negative
        assert duration < 0.01  # Should be very fast
    
    def test_lambda_function(self):
        """Test timing a lambda function."""
        result, duration = time_execution(lambda: [i**2 for i in range(100)])
        
        assert len(result) == 100
        assert result[0] == 0
        assert result[9] == 81
        assert duration >= 0


class TestFormatDuration:
    """Test the format_duration function."""
    
    def test_negative_duration(self):
        """Test formatting negative duration."""
        assert format_duration(-1.5) == "0.00s"
        assert format_duration(-0.001) == "0.00s"
    
    def test_microseconds(self):
        """Test formatting microsecond durations."""
        assert format_duration(0.0001) == "100μs"
        assert format_duration(0.0005) == "500μs"
        assert format_duration(0.0009) == "900μs"
    
    def test_milliseconds(self):
        """Test formatting millisecond durations."""
        assert format_duration(0.001) == "1.00ms"
        assert format_duration(0.001234) == "1.23ms"
        assert format_duration(0.5) == "500.00ms"
        assert format_duration(0.999) == "999.00ms"
    
    def test_seconds(self):
        """Test formatting second durations."""
        assert format_duration(1.0) == "1.00s"
        assert format_duration(1.234) == "1.23s"
        assert format_duration(30.5) == "30.50s"
        assert format_duration(59.99) == "59.99s"
    
    def test_minutes_and_seconds(self):
        """Test formatting minute durations."""
        assert format_duration(60) == "1m 0.00s"
        assert format_duration(61.5) == "1m 1.50s"
        assert format_duration(125.75) == "2m 5.75s"
        assert format_duration(3599.9) == "59m 59.90s"
    
    def test_hours_minutes_seconds(self):
        """Test formatting hour durations."""
        assert format_duration(3600) == "1h 0m 0.00s"
        assert format_duration(3661.25) == "1h 1m 1.25s"
        assert format_duration(7323.5) == "2h 2m 3.50s"
        assert format_duration(86400) == "24h 0m 0.00s"
    
    def test_zero_duration(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "0.00s"
        assert format_duration(0.0) == "0.00s"


class TestTimingDecorator:
    """Test the timing_decorator function."""
    
    def test_decorator_preserves_function_behavior(self):
        """Test that decorator preserves original function behavior."""
        @timing_decorator
        def add_numbers(a: int, b: int) -> int:
            return a + b
        
        result = add_numbers(5, 3)
        assert result == 8
        assert add_numbers.__name__ == "add_numbers"
    
    def test_decorator_with_exception(self):
        """Test decorator behavior when decorated function raises exception."""
        @timing_decorator
        def failing_function():
            raise RuntimeError("decorated failure")
        
        with pytest.raises(RuntimeError, match="decorated failure"):
            failing_function()
    
    def test_decorator_with_args_and_kwargs(self):
        """Test decorator with functions that use args and kwargs."""
        @timing_decorator
        def flexible_func(*args, **kwargs):
            return {"args": args, "kwargs": kwargs}
        
        result = flexible_func(1, 2, key="value", other=True)
        
        expected = {"args": (1, 2), "kwargs": {"key": "value", "other": True}}
        assert result == expected
    
    @patch('skoglib.utils.logger')
    def test_decorator_logging_success(self, mock_logger):
        """Test that decorator logs successful execution."""
        @timing_decorator
        def test_function():
            return "success"
        
        result = test_function()
        
        assert result == "success"
        mock_logger.debug.assert_called()
        
        # Check that the debug call contains expected information
        call_args = mock_logger.debug.call_args
        assert "test_function" in call_args[0][0]
        assert "completed" in call_args[0][0]
    
    @patch('skoglib.utils.logger')
    def test_decorator_logging_failure(self, mock_logger):
        """Test that decorator logs failed execution."""
        @timing_decorator
        def failing_function():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        mock_logger.error.assert_called()
        
        # Check that the error call contains expected information
        call_args = mock_logger.error.call_args
        assert "failing_function" in call_args[0][0]
        assert "failed" in call_args[0][0]


class TestSafeDictGet:
    """Test the safe_dict_get function."""
    
    def test_key_exists(self):
        """Test getting an existing key."""
        data = {"key": "value", "number": 42}
        
        assert safe_dict_get(data, "key") == "value"
        assert safe_dict_get(data, "number") == 42
    
    def test_key_missing_with_default(self):
        """Test getting a missing key with default value."""
        data = {"existing": "value"}
        
        assert safe_dict_get(data, "missing", "default") == "default"
        assert safe_dict_get(data, "missing", None) is None
        assert safe_dict_get(data, "missing", 0) == 0
    
    def test_key_missing_no_default(self):
        """Test getting a missing key without explicit default."""
        data = {"existing": "value"}
        
        assert safe_dict_get(data, "missing") is None
    
    def test_type_validation_success(self):
        """Test successful type validation."""
        data = {"string": "hello", "integer": 42, "boolean": True}
        
        assert safe_dict_get(data, "string", expected_type=str) == "hello"
        assert safe_dict_get(data, "integer", expected_type=int) == 42
        assert safe_dict_get(data, "boolean", expected_type=bool) is True
    
    def test_type_validation_failure(self):
        """Test failed type validation."""
        data = {"string_number": "42", "int_as_string": 42}
        
        with pytest.raises(TypeError, match="Expected int .* got str"):
            safe_dict_get(data, "string_number", expected_type=int)
        
        with pytest.raises(TypeError, match="Expected str .* got int"):
            safe_dict_get(data, "int_as_string", expected_type=str)
    
    def test_type_validation_with_none_value(self):
        """Test type validation when value is None."""
        data = {"null_value": None}
        
        # None values should not trigger type validation
        assert safe_dict_get(data, "null_value", expected_type=str) is None
        assert safe_dict_get(data, "missing", None, expected_type=int) is None
    
    def test_type_validation_with_default(self):
        """Test type validation with default values."""
        data = {}
        
        # Default values should also be type-checked if expected_type is provided
        assert safe_dict_get(data, "missing", "default", expected_type=str) == "default"
        
        with pytest.raises(TypeError):
            safe_dict_get(data, "missing", "wrong_type", expected_type=int)


class TestEnsureDirectory:
    """Test the ensure_directory function."""
    
    def test_create_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_directory"
            
            result = ensure_directory(new_dir)
            
            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()
    
    def test_create_nested_directories(self):
        """Test creating nested directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
            
            result = ensure_directory(nested_dir)
            
            assert result == nested_dir
            assert nested_dir.exists()
            assert nested_dir.is_dir()
            
            # Verify all parent directories were created
            assert (Path(temp_dir) / "level1").exists()
            assert (Path(temp_dir) / "level1" / "level2").exists()
    
    def test_existing_directory(self):
        """Test with an already existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir)
            
            result = ensure_directory(existing_dir)
            
            assert result == existing_dir
            assert existing_dir.exists()
            assert existing_dir.is_dir()
    
    def test_string_path_input(self):
        """Test with string path input instead of Path object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir_str = str(Path(temp_dir) / "string_input")
            
            result = ensure_directory(new_dir_str)
            
            assert isinstance(result, Path)
            assert result.exists()
            assert result.is_dir()
    
    def test_permission_error(self):
        """Test handling of permission errors."""
        # Try to create a directory in a location that should cause permission error
        # This test might be platform-specific
        with pytest.raises(OSError):
            ensure_directory("/root/should_fail_permission")


class TestBytesToHumanReadable:
    """Test the bytes_to_human_readable function."""
    
    def test_bytes(self):
        """Test formatting byte values."""
        assert bytes_to_human_readable(0) == "0 B"
        assert bytes_to_human_readable(1) == "1 B"
        assert bytes_to_human_readable(512) == "512 B"
        assert bytes_to_human_readable(1023) == "1023 B"
    
    def test_kilobytes(self):
        """Test formatting kilobyte values."""
        assert bytes_to_human_readable(1024) == "1.00 KB"
        assert bytes_to_human_readable(1536) == "1.50 KB"
        assert bytes_to_human_readable(2048) == "2.00 KB"
        assert bytes_to_human_readable(1048575) == "1024.00 KB"
    
    def test_megabytes(self):
        """Test formatting megabyte values."""
        assert bytes_to_human_readable(1048576) == "1.00 MB"
        assert bytes_to_human_readable(1572864) == "1.50 MB"
        assert bytes_to_human_readable(10485760) == "10.00 MB"
        assert bytes_to_human_readable(1073741823) == "1024.00 MB"
    
    def test_gigabytes(self):
        """Test formatting gigabyte values."""
        assert bytes_to_human_readable(1073741824) == "1.00 GB"
        assert bytes_to_human_readable(1610612736) == "1.50 GB"
        assert bytes_to_human_readable(10737418240) == "10.00 GB"
    
    def test_larger_units(self):
        """Test formatting terabyte and petabyte values."""
        tb = 1024**4
        pb = 1024**5
        
        assert bytes_to_human_readable(tb) == "1.00 TB"
        assert bytes_to_human_readable(int(1.5 * tb)) == "1.50 TB"
        assert bytes_to_human_readable(pb) == "1.00 PB"
    
    def test_negative_bytes(self):
        """Test handling negative byte values."""
        assert bytes_to_human_readable(-1) == "0 B"
        assert bytes_to_human_readable(-1024) == "0 B"
    
    def test_large_values(self):
        """Test very large byte values."""
        very_large = 1024**5 * 100  # 100 PB
        result = bytes_to_human_readable(very_large)
        assert result.endswith(" PB")
        assert "100.00" in result


class TestIntegration:
    """Integration tests combining multiple utilities."""
    
    def test_timing_with_format_duration(self):
        """Test combining time_execution with format_duration."""
        def test_operation():
            time.sleep(0.01)
            return "completed"
        
        result, duration = time_execution(test_operation)
        formatted = format_duration(duration)
        
        assert result == "completed"
        assert "ms" in formatted or "s" in formatted
        assert duration >= 0.01
    
    def test_directory_creation_with_timing(self):
        """Test timing directory creation operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            def create_deep_dirs():
                deep_path = Path(temp_dir) / "a" / "b" / "c" / "d" / "e"
                return ensure_directory(deep_path)
            
            result, duration = time_execution(create_deep_dirs)
            
            assert result.exists()
            assert result.is_dir()
            assert duration > 0
    
    @timing_decorator
    def example_function_with_decorator(self, data: Dict[str, Any]) -> str:
        """Example function to test decorator integration."""
        value = safe_dict_get(data, "key", "default")
        time.sleep(0.001)  # Small delay to measure
        return f"processed: {value}"
    
    def test_decorator_with_safe_dict_get(self):
        """Test timing decorator with safe_dict_get."""
        test_data = {"key": "test_value"}
        
        result = self.example_function_with_decorator(test_data)
        
        assert result == "processed: test_value"
        
        # Test with missing key
        empty_data = {}
        result = self.example_function_with_decorator(empty_data)
        
        assert result == "processed: default"