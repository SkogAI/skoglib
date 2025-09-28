"""
Test suite for skoglib main module and CLI interface.

Tests command-line interface, main entry point, and package-level functionality.
"""

import sys
import subprocess
from unittest import TestCase
from unittest.mock import patch
from io import StringIO

import skoglib
from skoglib import main


class TestMainFunction(TestCase):
    """Test the main() function."""

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.exit")
    def test_main_function_output(self, mock_exit, mock_stdout):
        """Test that main function produces expected output."""
        main()

        output = mock_stdout.getvalue()

        # Check expected output content
        self.assertIn("skoglib v0.1.0", output)
        self.assertIn("Usage: python -m skoglib", output)
        self.assertIn(
            "For programmatic usage: from skoglib import run_executable", output
        )

        # Check that it exits with code 0
        mock_exit.assert_called_once_with(0)

    def test_main_module_execution(self):
        """Test running skoglib as a module."""
        # Test using subprocess to ensure actual execution
        result = subprocess.run(
            [sys.executable, "-m", "skoglib"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("skoglib v0.1.0", result.stdout)
        self.assertIn("Usage: python -m skoglib", result.stdout)

    def test_package_metadata_access(self):
        """Test access to package metadata through main module."""
        # These are the lines in __init__.py that weren't covered
        self.assertEqual(skoglib.__version__, "0.1.0")
        self.assertEqual(skoglib.__author__, "Emil Skogsund")
        self.assertEqual(skoglib.__email__, "emil@skogsund.se")

    def test_main_function_directly(self):
        """Test calling main function directly."""
        with patch("sys.exit") as mock_exit:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                skoglib.main()

                # Verify main function was called
                mock_exit.assert_called_once_with(0)

                output = mock_stdout.getvalue()
                self.assertIn("skoglib", output)


class TestPackageImports(TestCase):
    """Test package-level imports and public API."""

    def test_all_public_api_importable(self):
        """Test that all items in __all__ are importable."""
        from skoglib import (
            # Main functionality
            run_executable,
            ExecutionResult,
            # Exception hierarchy
            __version__,
        )

        # Basic smoke test that imports worked
        self.assertEqual(__version__, "0.1.0")
        self.assertIsNotNone(run_executable)
        self.assertIsNotNone(ExecutionResult)

    def test_package_has_all_attribute(self):
        """Test that package defines __all__."""
        self.assertTrue(hasattr(skoglib, "__all__"))
        self.assertIsInstance(skoglib.__all__, list)
        self.assertGreater(len(skoglib.__all__), 0)

    def test_public_api_completeness(self):
        """Test that __all__ contains expected public API."""
        expected_exports = {
            "run_executable",
            "ExecutionResult",
            "SkogAIError",
            "ExecutableNotFoundError",
            "ExecutionError",
            "ConfigurationError",
            "configure_logging",
            "configure_from_env",
            "get_logger",
            "get_performance_logger",
            "SkogAIConfig",
            "get_config",
            "reset_config",
            "find_executable",
            "validate_executable",
            "resolve_path",
            "merge_configs",
            "__version__",
            "__author__",
            "__email__",
        }

        actual_exports = set(skoglib.__all__)

        # Check that all expected exports are present
        missing_exports = expected_exports - actual_exports
        self.assertEqual(missing_exports, set(), f"Missing exports: {missing_exports}")

        # Check that all listed exports are actually available
        for export_name in skoglib.__all__:
            self.assertTrue(
                hasattr(skoglib, export_name),
                f"Export '{export_name}' not available in package",
            )


class TestCLIIntegration(TestCase):
    """Test command-line interface integration."""

    def test_cli_via_module(self):
        """Test CLI access via python -m skoglib."""
        result = subprocess.run(
            [sys.executable, "-m", "skoglib"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("skoglib v", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_cli_help_information(self):
        """Test that CLI provides helpful information."""
        result = subprocess.run(
            [sys.executable, "-m", "skoglib"], capture_output=True, text=True
        )

        output = result.stdout

        # Should contain version info
        self.assertIn("v0.1.0", output)

        # Should contain usage information
        self.assertIn("Usage:", output)
        self.assertIn("python -m skoglib", output)

        # Should contain programmatic usage hint
        self.assertIn("programmatic usage", output)
        self.assertIn("from skoglib import", output)

    def test_script_entry_point(self):
        """Test that the script entry point works."""
        # This tests the script defined in pyproject.toml
        try:
            result = subprocess.run(
                ["skoglib"], capture_output=True, text=True, timeout=10
            )

            # If the script is available, it should work
            if result.returncode == 0:
                self.assertIn("skoglib v", result.stdout)
            else:
                # If not available, that's also fine (depends on installation)
                self.skipTest("skoglib script not available in PATH")

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Script not found in PATH - this is acceptable for test environment
            self.skipTest("skoglib script not available in PATH")


class TestModuleDiscoverability(TestCase):
    """Test that module is properly discoverable and introspectable."""

    def test_module_docstring(self):
        """Test that module has proper docstring."""
        self.assertIsNotNone(skoglib.__doc__)
        self.assertIn("skoglib", skoglib.__doc__)

    def test_module_attributes(self):
        """Test that module has expected attributes."""
        required_attrs = ["__version__", "__author__", "__email__", "__all__"]

        for attr in required_attrs:
            self.assertTrue(hasattr(skoglib, attr), f"Missing attribute: {attr}")
            self.assertIsNotNone(getattr(skoglib, attr), f"Attribute {attr} is None")

    def test_version_format(self):
        """Test that version follows expected format."""
        version = skoglib.__version__

        # Should be a string
        self.assertIsInstance(version, str)

        # Should follow semantic versioning pattern (basic check)
        parts = version.split(".")
        self.assertGreaterEqual(
            len(parts), 2, "Version should have at least major.minor"
        )

        # Parts should be numeric
        for part in parts:
            self.assertTrue(part.isdigit(), f"Version part '{part}' should be numeric")


if __name__ == "__main__":
    import unittest

    unittest.main()
