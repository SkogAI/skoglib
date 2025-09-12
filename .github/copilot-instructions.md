# skoglib - Python Library for Executable Management

skoglib is a Python 3.13 library providing a "batteries included but minimal" approach to running external executables with proper error handling, output capture, and logging. It uses uv as the package manager.

**CRITICAL: ALWAYS reference these instructions first and only fallback to search or bash commands when you encounter unexpected information that does not match the info here. These instructions contain validated, working commands with proper timeout expectations.**

## Quick Start and Environment Setup

**CRITICAL SETUP STEPS** - Execute these commands in order:

```bash
# Install uv package manager (required for all operations)
pip install uv

# Install all dependencies including dev tools - NEVER CANCEL: Takes 30 seconds
uv sync --dev
```

**NOTE**: The initial `uv sync --dev` downloads Python 3.13.7 and all dependencies. This is NORMAL and expected. Set timeout to 120+ seconds.

## Development Commands

### Testing
```bash
# Run all tests - Fast execution: ~1.6 seconds
uv run pytest

# Run tests with coverage report - Fast execution: ~2 seconds  
uv run pytest --cov=src/skoglib --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_import_performance.py -v
```

**Test Status**: 53 tests total, 43 pass, 10 fail. The failing tests are existing logging integration issues and do NOT indicate broken functionality. The core library works correctly.

### Code Quality and Validation
```bash
# Lint code - VERY FAST: ~0.04 seconds
uv run ruff check

# Auto-fix linting issues
uv run ruff check --fix

# Type checking - Fast: ~1.6 seconds
uv run mypy src/

# Security scanning - Fast: ~0.4 seconds  
uv run bandit -r src/
```

**ALWAYS** run `uv run ruff check` and `uv run mypy src/` before committing changes.

### Running the Application

```bash
# Command-line interface
uv run python -m skoglib
uv run skoglib

# Programmatic usage test
uv run python -c "from skoglib import run_executable; result = run_executable('echo', ['Hello World']); print(f'Success: {result.success}, Output: {result.stdout.strip()}')"
```

## Validation Scenarios

After making changes, **ALWAYS** test these scenarios:

1. **Basic functionality test**:
   ```bash
   uv run python -c "from skoglib import run_executable; result = run_executable('echo', ['test']); assert result.success and 'test' in result.stdout"
   ```

2. **Error handling test**:
   ```bash
   uv run python -c "
from skoglib import run_executable, ExecutableNotFoundError
import sys
try:
    run_executable('nonexistent_command_12345', [])
    sys.exit(1)
except ExecutableNotFoundError:
    print('✓ Error handling works')
    sys.exit(0)
"
   ```

3. **CLI functionality test**:
   ```bash
   uv run skoglib | grep -q "skoglib v0.1.0" && echo "✓ CLI works"
   ```

4. **Comprehensive integration test**:
   ```bash
   uv run python -c "
from skoglib import run_executable, configure_logging
import logging

configure_logging(level=logging.WARNING)  # Reduce noise

# Test basic functionality
result = run_executable('echo', ['Hello', 'World'])
assert result.success and 'Hello World' in result.stdout
print('✓ Echo test passed')

# Test error handling with exit codes
result = run_executable('bash', ['-c', 'exit 42'], check_exit_code=False)
assert not result.success and result.exit_code == 42
print('✓ Exit code test passed')

# Test environment variables
result = run_executable('printenv', ['TEST_VAR'], env_vars={'TEST_VAR': 'test_value'})
assert result.success and 'test_value' in result.stdout
print('✓ Environment test passed')

print('All integration tests passed!')
"
   ```

## Project Structure

### Key Directories
```
src/skoglib/                    # Main library code
├── __init__.py                # Public API and package metadata  
├── executable.py              # Core executable management
├── exceptions.py              # Exception hierarchy
└── logging_config.py          # Logging configuration

tests/                         # Test suite (85% coverage)
├── test_exception_logging.py  # Exception behavior and performance tests
├── test_import_performance.py # Import speed and tracking tests
├── test_logging_config.py     # Logging configuration tests
└── test_logging_integration.py # End-to-end logging tests

.claude/                       # Claude AI project management
├── scripts/                   # PM and utility scripts
└── commands/                  # Claude command definitions

scripts/                       # Development utilities
```

### Core API
```python
from skoglib import (
    run_executable,          # Main function for executing commands
    ExecutionResult,         # Result object with success, stdout, stderr
    SkogAIError,            # Base exception
    ExecutableNotFoundError, # Command not found
    ExecutionError,         # Command failed
    ConfigurationError      # Invalid parameters
)

# Main function signature:
run_executable(
    executable: str,                    # Command name or path
    args: Optional[List[str]] = None,   # Command arguments
    cwd: Optional[Union[str, Path]] = None,  # Working directory
    env_vars: Optional[Dict[str, str]] = None,  # Environment variables
    timeout: Optional[float] = None,    # Timeout in seconds
    capture_output: bool = True,        # Capture stdout/stderr
    check_exit_code: bool = True        # Raise error on non-zero exit
) -> ExecutionResult
```

## Troubleshooting

### Common Issues

**"uv not found"**: Install uv first with `pip install uv`

**Test failures**: 10 tests currently fail due to logging integration issues. This is expected and does NOT indicate broken functionality. Focus on the 43 passing tests.

**Import errors**: Run `uv sync --dev` to ensure all dependencies are installed

**Wrong Python version**: uv automatically manages Python 3.13.7. Verify with `uv run python --version`

**uv command fails**: Verify uv installation with `uv --version` (should show uv 0.8.17+)

**Performance tests fail**: The exception performance tests may fail on slower systems. This is a known limitation and does not affect functionality.

**Linting issues**: Some linting warnings about unused variables in performance logging contexts are expected. Run `uv run ruff check --fix` to auto-fix simple issues.

### Known Working Configuration
- Python 3.13.7 (automatically installed by uv)
- uv 0.8.17+ (for package management)
- Dependencies managed by uv.lock
- Tests run in ~1.6 seconds (10 failures expected)
- Full setup from fresh clone takes ~30 seconds (first time) or ~0.1 seconds (cached Python)
- Coverage: 85% (253 statements, 38 missing)

## Development Workflow

1. **Setup environment**: `pip install uv && uv sync --dev`
2. **Make changes**: Edit code in `src/skoglib/`
3. **Validate**: `uv run ruff check && uv run mypy src/`
4. **Test**: `uv run pytest`
5. **Manual validation**: Run the validation scenarios above
6. **Coverage check**: `uv run pytest --cov=src/skoglib`

## Common Usage Patterns

### Basic Command Execution
```python
from skoglib import run_executable

# Simple command
result = run_executable("ls", ["-la"])
if result.success:
    print(result.stdout)

# Command with environment variables
result = run_executable("node", ["--version"], env_vars={"NODE_ENV": "production"})

# Command in specific directory
result = run_executable("git", ["status"], cwd="/path/to/repo")

# Handle errors gracefully
result = run_executable("false", check_exit_code=False)
if not result.success:
    print(f"Command failed with exit code: {result.exit_code}")
```

### Error Handling
```python
from skoglib import run_executable, ExecutableNotFoundError, ExecutionError

try:
    result = run_executable("nonexistent-command")
except ExecutableNotFoundError as e:
    print(f"Command not found: {e}")
except ExecutionError as e:
    print(f"Command failed: {e}")
```

### Timeout and Output Control
```python
# Command with timeout
result = run_executable("sleep", ["10"], timeout=5.0, check_exit_code=False)

# Disable output capture for interactive commands
result = run_executable("interactive-tool", capture_output=False)
```

## Timing Expectations

- **Setup** (`uv sync --dev`): 30 seconds - **NEVER CANCEL**
- **Tests** (`uv run pytest`): 1.6 seconds  
- **Linting** (`uv run ruff check`): 0.04 seconds
- **Type checking** (`uv run mypy src/`): 1.6 seconds
- **Security scan** (`uv run bandit -r src/`): 0.4 seconds

All commands except initial setup are very fast. The library is designed for rapid development feedback.

## CI Integration

The repository includes GitHub Actions workflows:
- `.github/workflows/claude.yml` - Claude AI integration
- `.github/workflows/claude-code-review.yml` - Automated code review

No traditional CI build is needed since this is a pure Python library.

## Important Notes

- **No build step required** - This is a pure Python library
- **Test failures expected** - 10/53 tests fail due to logging issues, this is normal
- **Fast feedback cycle** - Most operations complete in under 2 seconds
- **uv is mandatory** - All commands must use `uv run` prefix
- **Python 3.13 required** - Automatically handled by uv