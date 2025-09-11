---
framework: pytest
test_command: uv run pytest
created: 2025-09-10T15:01:56Z
---

# Testing Configuration

## Framework
- Type: Pytest
- Version: 8.4.2
- Config File: pyproject.toml
- Package Manager: UV

## Test Structure
- Test Directory: tests/
- Test Files: 5 files found
- Total Test Cases: 62 tests
- Naming Pattern: test_*.py

## Commands
- Run All Tests: `uv run pytest tests/ -v`
- Run Specific Test: `uv run pytest tests/{test_file} -v`
- Run with Coverage: `uv run pytest tests/ --cov=src/skoglib --cov-report=term-missing`
- Run with Debugging: `uv run pytest tests/ -v --tb=long -s`

## Environment
- Python Version: >=3.13
- Required ENV vars: PYTHONPATH set to project root
- Package Management: UV with pyproject.toml
- Dev Dependencies: pytest, pytest-cov, mypy, ruff, bandit, coverage

## Test Files
- test_exception_logging.py: Exception logging integration tests
- test_import_performance.py: Performance and import timing tests
- test_logging_config.py: Core logging configuration tests
- test_logging_integration.py: End-to-end logging integration tests

## Test Runner Agent Configuration
- Use verbose output for debugging
- Run tests sequentially (no parallel)
- Capture full stack traces with --tb=long
- No mocking - use real implementations
- Wait for each test to complete

## Pytest Configuration
- Root directory: /home/skogix/dev/skoglib/
- Configuration in pyproject.toml [tool.pytest.ini_options]
- Test discovery: automatic via test_*.py pattern
- Coverage tracking available via pytest-cov