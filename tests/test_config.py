"""
Test suite for skoglib.config module.

Tests configuration management, environment variable loading, executable discovery,
path resolution, thread safety, and validation.
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


from skoglib.config import (
    SkogAIConfig,
    get_config,
    reset_config,
    load_config_from_env,
    find_executable,
    validate_executable,
    resolve_path,
    merge_configs,
)
from skoglib.exceptions import ConfigurationError


class TestSkogAIConfig(TestCase):
    """Test the SkogAIConfig dataclass."""

    def test_default_initialization(self):
        """Test configuration with default values."""
        config = SkogAIConfig()

        # Check default values
        self.assertEqual(config.default_timeout, 30)
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.executable_search_paths, [])
        self.assertEqual(config.env_prefix, "SKOGAI")

    def test_custom_initialization(self):
        """Test configuration with custom values."""
        config = SkogAIConfig(
            default_timeout=60,
            log_level="DEBUG",
            executable_search_paths=["/usr/local/bin", "/opt/bin"],
            env_prefix="CUSTOM",
        )

        self.assertEqual(config.default_timeout, 60)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.executable_search_paths, ["/usr/local/bin", "/opt/bin"])
        self.assertEqual(config.env_prefix, "CUSTOM")

    def test_validation_invalid_timeout(self):
        """Test validation with invalid timeout values."""
        with self.assertRaises(ConfigurationError) as cm:
            SkogAIConfig(default_timeout=-1)

        error = cm.exception
        self.assertIn("default_timeout must be a positive integer", error.message)
        self.assertEqual(error.config_key, "default_timeout")
        self.assertEqual(error.config_value, -1)

        with self.assertRaises(ConfigurationError):
            SkogAIConfig(default_timeout=0)

        with self.assertRaises(ConfigurationError):
            SkogAIConfig(default_timeout="invalid")

    def test_validation_invalid_log_level(self):
        """Test validation with invalid log level values."""
        with self.assertRaises(ConfigurationError) as cm:
            SkogAIConfig(log_level="INVALID")

        error = cm.exception
        self.assertIn("log_level must be one of:", error.message)
        self.assertEqual(error.config_key, "log_level")
        self.assertEqual(error.config_value, "INVALID")
        self.assertIn("DEBUG", error.valid_values)
        self.assertIn("INFO", error.valid_values)
        self.assertIn("WARNING", error.valid_values)
        self.assertIn("ERROR", error.valid_values)
        self.assertIn("CRITICAL", error.valid_values)

    def test_validation_invalid_search_paths(self):
        """Test validation with invalid search paths."""
        with self.assertRaises(ConfigurationError) as cm:
            SkogAIConfig(executable_search_paths=[123, "valid/path"])

        error = cm.exception
        self.assertIn("All executable_search_paths must be strings", error.message)
        self.assertEqual(error.config_key, "executable_search_paths")
        self.assertEqual(error.config_value, 123)

    def test_validation_nonexistent_search_path_warning(self):
        """Test that nonexistent search paths generate warnings but don't fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_path = os.path.join(temp_dir, "nonexistent")

            # Should not raise an exception, just log a warning
            config = SkogAIConfig(executable_search_paths=[nonexistent_path])
            self.assertEqual(config.executable_search_paths, [nonexistent_path])

    def test_validation_file_as_search_path(self):
        """Test that files (not directories) as search paths cause validation error."""
        with tempfile.NamedTemporaryFile() as temp_file:
            with self.assertRaises(ConfigurationError) as cm:
                SkogAIConfig(executable_search_paths=[temp_file.name])

            error = cm.exception
            self.assertIn("Search path must be a directory:", error.message)
            self.assertEqual(error.config_key, "executable_search_paths")
            self.assertEqual(error.config_value, temp_file.name)


class TestEnvironmentVariableLoading(TestCase):
    """Test loading configuration from environment variables."""

    def setUp(self):
        """Clear environment variables before each test."""
        self.original_env = {}
        env_vars = [
            "SKOGAI_DEFAULT_TIMEOUT",
            "SKOGAI_MAX_OUTPUT_SIZE",
            "SKOGAI_LOG_LEVEL",
            "SKOGAI_SEARCH_PATHS",
        ]

        for var in env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]

    def tearDown(self):
        """Restore original environment variables."""
        # Clear test variables
        env_vars = [
            "SKOGAI_DEFAULT_TIMEOUT",
            "SKOGAI_MAX_OUTPUT_SIZE",
            "SKOGAI_LOG_LEVEL",
            "SKOGAI_SEARCH_PATHS",
        ]

        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

        # Restore original values
        for var, value in self.original_env.items():
            os.environ[var] = value

    def test_load_config_defaults(self):
        """Test loading configuration with no environment variables (defaults)."""
        config = load_config_from_env()

        self.assertEqual(config.default_timeout, 30)
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.executable_search_paths, [])

    def test_load_config_timeout(self):
        """Test loading timeout from environment."""
        os.environ["SKOGAI_DEFAULT_TIMEOUT"] = "60"
        config = load_config_from_env()

        self.assertEqual(config.default_timeout, 60)

    def test_load_config_log_level(self):
        """Test loading log level from environment."""
        os.environ["SKOGAI_LOG_LEVEL"] = "debug"  # Should be normalized to uppercase
        config = load_config_from_env()

        self.assertEqual(config.log_level, "DEBUG")

    def test_load_config_search_paths(self):
        """Test loading search paths from environment."""
        os.environ["SKOGAI_SEARCH_PATHS"] = "/usr/local/bin:/opt/bin:/custom/bin"
        config = load_config_from_env()

        expected_paths = ["/usr/local/bin", "/opt/bin", "/custom/bin"]
        self.assertEqual(config.executable_search_paths, expected_paths)

    def test_load_config_search_paths_empty_entries(self):
        """Test loading search paths with empty entries."""
        os.environ["SKOGAI_SEARCH_PATHS"] = "/usr/local/bin::/opt/bin:"
        config = load_config_from_env()

        # Empty entries should be filtered out
        expected_paths = ["/usr/local/bin", "/opt/bin"]
        self.assertEqual(config.executable_search_paths, expected_paths)

    def test_load_config_all_variables(self):
        """Test loading all configuration from environment."""
        os.environ.update(
            {
                "SKOGAI_DEFAULT_TIMEOUT": "120",
                "SKOGAI_LOG_LEVEL": "ERROR",
                "SKOGAI_SEARCH_PATHS": "/custom/bin:/another/path",
            }
        )

        config = load_config_from_env()

        self.assertEqual(config.default_timeout, 120)
        self.assertEqual(config.log_level, "ERROR")
        self.assertEqual(
            config.executable_search_paths, ["/custom/bin", "/another/path"]
        )

    def test_load_config_invalid_timeout(self):
        """Test loading invalid timeout from environment."""
        os.environ["SKOGAI_DEFAULT_TIMEOUT"] = "invalid"

        with self.assertRaises(ConfigurationError) as cm:
            load_config_from_env()

        error = cm.exception
        self.assertIn("Invalid value for SKOGAI_DEFAULT_TIMEOUT", error.message)
        self.assertEqual(error.config_key, "default_timeout")
        self.assertEqual(error.config_value, "invalid")


class TestGlobalConfiguration(TestCase):
    """Test global configuration management."""

    def setUp(self):
        """Reset configuration before each test."""
        reset_config()

    def tearDown(self):
        """Reset configuration after each test."""
        reset_config()

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()

        # Should be the same object
        self.assertIs(config1, config2)

    def test_reset_config(self):
        """Test that reset_config clears the cached instance."""
        config1 = get_config()
        reset_config()
        config2 = get_config()

        # Should be different objects after reset
        self.assertIsNot(config1, config2)

    @patch.dict(os.environ, {"SKOGAI_DEFAULT_TIMEOUT": "90"})
    def test_get_config_loads_from_environment(self):
        """Test that get_config loads configuration from environment."""
        config = get_config()
        self.assertEqual(config.default_timeout, 90)


class TestThreadSafety(TestCase):
    """Test thread safety of configuration access."""

    def setUp(self):
        """Reset configuration before each test."""
        reset_config()

    def tearDown(self):
        """Reset configuration after each test."""
        reset_config()

    def test_concurrent_config_access(self):
        """Test that concurrent access to get_config is thread-safe."""
        results = []

        def get_config_worker():
            """Worker function to get configuration."""
            config = get_config()
            results.append(id(config))  # Store object ID

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_config_worker)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All results should have the same object ID (same instance)
        self.assertEqual(
            len(set(results)), 1, "All threads should get the same config instance"
        )
        self.assertEqual(len(results), 10, "All threads should have completed")

    def test_concurrent_config_with_reset(self):
        """Test thread safety when config is reset during access."""
        results = []
        barrier = threading.Barrier(5)

        def config_worker(worker_id):
            """Worker that gets config after barrier."""
            barrier.wait()  # Synchronize all workers
            config = get_config()
            results.append((worker_id, id(config)))

        def reset_worker():
            """Worker that resets config after barrier."""
            barrier.wait()  # Synchronize with config workers
            time.sleep(0.01)  # Small delay to increase chance of race condition
            reset_config()

        threads = []

        # Create config workers
        for i in range(4):
            thread = threading.Thread(target=config_worker, args=(i,))
            threads.append(thread)

        # Create reset worker
        reset_thread = threading.Thread(target=reset_worker)
        threads.append(reset_thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have results from 4 config workers
        self.assertEqual(len(results), 4)

        # Results should be consistent (either all same ID or split between two IDs)
        config_ids = [config_id for worker_id, config_id in results]
        unique_ids = set(config_ids)

        # Should have at most 2 different config instances due to reset timing
        self.assertLessEqual(
            len(unique_ids), 2, "Should have at most 2 different config instances"
        )


class TestExecutableDiscovery(TestCase):
    """Test executable discovery functionality."""

    def test_find_executable_absolute_path(self):
        """Test finding executable with absolute path."""
        # Test with a known executable (e.g., /bin/ls on Unix systems)
        if os.name == "posix":
            ls_path = find_executable("/bin/ls")
            self.assertEqual(ls_path, "/bin/ls")
        else:
            # On Windows, test with a common executable
            cmd_path = find_executable("C:\\Windows\\System32\\cmd.exe")
            if os.path.exists("C:\\Windows\\System32\\cmd.exe"):
                self.assertEqual(cmd_path, "C:\\Windows\\System32\\cmd.exe")

    def test_find_executable_in_path(self):
        """Test finding executable in system PATH."""
        # Find a common executable that should be in PATH
        if os.name == "posix":
            executable_name = "ls"
        else:
            executable_name = "cmd.exe"

        result = find_executable(executable_name)
        if result:  # Only test if executable is found
            self.assertTrue(os.path.isabs(result))
            self.assertTrue(os.path.isfile(result))
            self.assertTrue(os.access(result, os.X_OK))

    def test_find_executable_with_search_paths(self):
        """Test finding executable with custom search paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock executable
            executable_path = Path(temp_dir) / "test_exec"
            executable_path.write_text("#!/bin/bash\\necho test")
            executable_path.chmod(0o755)

            # Find using custom search paths
            result = find_executable("test_exec", search_paths=[temp_dir])

            self.assertEqual(result, str(executable_path))

    def test_find_executable_not_found(self):
        """Test finding non-existent executable."""
        result = find_executable("definitely_does_not_exist_12345")
        self.assertIsNone(result)

    def test_find_executable_consistency(self):
        """Test that find_executable returns consistent results."""
        # Test that the same result is returned for the same input
        result1 = find_executable("definitely_does_not_exist_12345")
        result2 = find_executable("definitely_does_not_exist_12345")

        self.assertEqual(result1, result2)
        self.assertIsNone(result1)
        self.assertIsNone(result2)

    def test_validate_executable_valid(self):
        """Test validating a valid executable."""
        # Test with a known executable
        if os.name == "posix" and os.path.exists("/bin/ls"):
            result = validate_executable("/bin/ls")
            self.assertTrue(result)
        elif os.name == "nt" and os.path.exists("C:\\Windows\\System32\\cmd.exe"):
            result = validate_executable("C:\\Windows\\System32\\cmd.exe")
            self.assertTrue(result)

    def test_validate_executable_invalid(self):
        """Test validating invalid executables."""
        # Non-existent file
        result = validate_executable("/path/that/does/not/exist")
        self.assertFalse(result)

        # Directory instead of file
        result = validate_executable("/tmp" if os.name == "posix" else "C:\\Windows")
        self.assertFalse(result)

    def test_validate_executable_non_executable_file(self):
        """Test validating non-executable file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("not executable")
            temp_path = temp_file.name

        try:
            # Make sure file is not executable
            os.chmod(temp_path, 0o644)
            result = validate_executable(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)


class TestPathResolution(TestCase):
    """Test path resolution functionality."""

    def test_resolve_absolute_path(self):
        """Test resolving absolute paths."""
        if os.name == "posix":
            test_path = "/tmp"
            expected = Path("/tmp")
        else:
            test_path = "C:\\Windows"
            expected = Path("C:\\Windows")

        result = resolve_path(test_path)
        self.assertEqual(result, expected)

    def test_resolve_relative_path_no_base(self):
        """Test resolving relative path without base directory."""
        result = resolve_path("test/path")
        expected = (Path.cwd() / "test" / "path").resolve()
        self.assertEqual(result, expected)

    def test_resolve_relative_path_with_base(self):
        """Test resolving relative path with base directory."""
        if os.name == "posix":
            base_dir = "/tmp"
        else:
            base_dir = "C:\\temp"

        result = resolve_path("test/path", base_dir=base_dir)
        expected = (Path(base_dir) / "test" / "path").resolve()
        self.assertEqual(result, expected)

    def test_resolve_path_object(self):
        """Test resolving Path objects."""
        test_path = Path("test/path")
        result = resolve_path(test_path)
        expected = (Path.cwd() / "test" / "path").resolve()
        self.assertEqual(result, expected)


class TestConfigMerging(TestCase):
    """Test configuration merging functionality."""

    def test_merge_configs_empty(self):
        """Test merging empty configurations."""
        result = merge_configs()
        self.assertEqual(result, {})

    def test_merge_configs_single(self):
        """Test merging single configuration."""
        config = {"timeout": 30, "log_level": "INFO"}
        result = merge_configs(config)
        self.assertEqual(result, config)

    def test_merge_configs_multiple(self):
        """Test merging multiple configurations."""
        config1 = {"timeout": 30, "log_level": "INFO"}
        config2 = {"timeout": 60, "max_size": 1024}
        config3 = {"log_level": "DEBUG", "search_paths": ["/bin"]}

        result = merge_configs(config1, config2, config3)

        expected = {
            "timeout": 60,  # Overridden by config2
            "log_level": "DEBUG",  # Overridden by config3
            "max_size": 1024,  # From config2
            "search_paths": ["/bin"],  # From config3
        }

        self.assertEqual(result, expected)

    def test_merge_configs_with_none(self):
        """Test merging configurations with None values."""
        config1 = {"timeout": 30}
        result = merge_configs(config1, None, {"log_level": "INFO"})

        expected = {"timeout": 30, "log_level": "INFO"}
        self.assertEqual(result, expected)


class TestIntegration(TestCase):
    """Integration tests for configuration system."""

    def setUp(self):
        """Reset configuration before each test."""
        reset_config()

    def tearDown(self):
        """Reset configuration after each test."""
        reset_config()

    @patch.dict(
        os.environ,
        {
            "SKOGAI_DEFAULT_TIMEOUT": "120",
            "SKOGAI_LOG_LEVEL": "DEBUG",
            "SKOGAI_SEARCH_PATHS": "/usr/local/bin:/opt/bin",
        },
    )
    def test_full_configuration_flow(self):
        """Test full configuration flow from environment to usage."""
        # Get configuration (should load from environment)
        config = get_config()

        # Verify environment values were loaded
        self.assertEqual(config.default_timeout, 120)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.executable_search_paths, ["/usr/local/bin", "/opt/bin"])

        # Test that subsequent calls return same instance
        config2 = get_config()
        self.assertIs(config, config2)

        # Test executable discovery with config paths
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock executable in one of the search paths
            # (simulating /usr/local/bin)
            executable_path = Path(temp_dir) / "mock_tool"
            executable_path.write_text("#!/bin/bash\\necho mock")
            executable_path.chmod(0o755)

            # Find executable using config search paths + temp dir
            search_paths = config.executable_search_paths + [temp_dir]
            result = find_executable("mock_tool", search_paths=search_paths)

            if result:  # Only test if found
                self.assertEqual(result, str(executable_path))
                self.assertTrue(validate_executable(result))
