"""
Pytest configuration and shared fixtures for skoglib tests.

Provides common test utilities, fixtures, and configuration.
"""

import os
import tempfile
import pytest
from pathlib import Path

from skoglib import configure_logging


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for test runs."""
    configure_logging(level="WARNING", force=True)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_file():
    """Provide a temporary file that's cleaned up after test."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp_path = tmp.name

    yield Path(tmp_path)

    # Clean up
    if Path(tmp_path).exists():
        Path(tmp_path).unlink()


@pytest.fixture
def sample_text_content():
    """Provide sample text content for testing."""
    return """Line 1: Hello World
Line 2: Testing skoglib
Line 3: Sample data for tests
Line 4: Multiple lines of text
Line 5: End of sample"""


@pytest.fixture
def mock_executable_dir(temp_dir):
    """Create a directory with mock executables for testing."""
    mock_dir = temp_dir / "mock_executables"
    mock_dir.mkdir()

    # Create various mock executables
    mock_executables = {}

    # Mock success executable
    success_script = mock_dir / "mock_success"
    success_script.write_text("""#!/bin/bash
echo "Success: $@"
exit 0
""")
    success_script.chmod(0o755)
    mock_executables["success"] = str(success_script)

    # Mock failure executable
    failure_script = mock_dir / "mock_failure"
    failure_script.write_text("""#!/bin/bash
echo "Error occurred" >&2
exit 1
""")
    failure_script.chmod(0o755)
    mock_executables["failure"] = str(failure_script)

    # Mock slow executable
    slow_script = mock_dir / "mock_slow"
    slow_script.write_text("""#!/bin/bash
echo "Starting..."
sleep 2
echo "Done"
""")
    slow_script.chmod(0o755)
    mock_executables["slow"] = str(slow_script)

    # Mock environment reader
    env_script = mock_dir / "mock_env_reader"
    env_script.write_text("""#!/bin/bash
for var in "$@"; do
    echo "$var=${!var}"
done
""")
    env_script.chmod(0o755)
    mock_executables["env_reader"] = str(env_script)

    # Mock output generator
    output_script = mock_dir / "mock_output"
    output_script.write_text("""#!/bin/bash
echo "STDOUT: $1"
echo "STDERR: $1" >&2
""")
    output_script.chmod(0o755)
    mock_executables["output"] = str(output_script)

    yield mock_executables


@pytest.fixture
def test_data_files(temp_dir):
    """Create test data files for testing."""
    data_dir = temp_dir / "test_data"
    data_dir.mkdir()

    files = {}

    # Simple text file
    simple_file = data_dir / "simple.txt"
    simple_file.write_text("Hello, World!")
    files["simple"] = str(simple_file)

    # Multi-line text file
    multiline_file = data_dir / "multiline.txt"
    multiline_content = """First line
Second line
Third line
Fourth line"""
    multiline_file.write_text(multiline_content)
    files["multiline"] = str(multiline_file)

    # CSV-like data file
    csv_file = data_dir / "data.csv"
    csv_content = """name,age,role
Alice,30,engineer
Bob,25,designer
Charlie,35,manager"""
    csv_file.write_text(csv_content)
    files["csv"] = str(csv_file)

    # Empty file
    empty_file = data_dir / "empty.txt"
    empty_file.write_text("")
    files["empty"] = str(empty_file)

    # Binary-like file (contains non-UTF8 data)
    binary_file = data_dir / "binary.dat"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
    files["binary"] = str(binary_file)

    yield files


@pytest.fixture
def environment_vars():
    """Provide standard environment variables for testing."""
    return {
        "TEST_VAR": "test_value",
        "NUMERIC_VAR": "12345",
        "EMPTY_VAR": "",
        "SPECIAL_CHARS": "Hello $USER & echo 'test'",
    }


@pytest.fixture
def command_arguments():
    """Provide various command argument combinations for testing."""
    return {
        "simple": ["hello"],
        "multiple": ["arg1", "arg2", "arg3"],
        "empty": [],
        "special_chars": ["hello world", "$HOME", "file*.txt"],
        "numeric": ["123", "456.789"],
        "long": [f"argument_{i}" for i in range(20)],
    }


class TestHelper:
    """Helper class for common test operations."""

    @staticmethod
    def create_executable_script(path: Path, content: str, executable: bool = True):
        """Create an executable script at the given path."""
        path.write_text(content)
        if executable:
            path.chmod(0o755)
        return str(path)

    @staticmethod
    def assert_execution_success(result, expected_stdout=None, expected_stderr=None):
        """Assert that an execution result indicates success."""
        assert result.success, f"Execution failed: {result.stderr}"
        assert result.exit_code == 0
        assert result.execution_time > 0

        if expected_stdout is not None:
            assert expected_stdout in result.stdout

        if expected_stderr is not None:
            assert expected_stderr in result.stderr

    @staticmethod
    def assert_execution_failure(result, expected_exit_code=None, expected_stderr=None):
        """Assert that an execution result indicates failure."""
        assert not result.success, "Expected execution to fail"
        assert result.exit_code != 0

        if expected_exit_code is not None:
            assert result.exit_code == expected_exit_code

        if expected_stderr is not None:
            assert expected_stderr in result.stderr


@pytest.fixture
def test_helper():
    """Provide the TestHelper utility class."""
    return TestHelper


# Performance testing markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file names."""
    for item in items:
        # Add markers based on test file names
        if "performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)

        if "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)

        # Mark slow tests based on name patterns
        if any(keyword in item.name for keyword in ["slow", "timeout", "concurrent"]):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def test_session_info():
    """Provide information about the test session."""
    return {
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "platform": os.sys.platform,
        "cwd": str(Path.cwd()),
    }
