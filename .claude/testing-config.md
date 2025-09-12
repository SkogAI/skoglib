---
framework: pytest
test_command: pytest
created: 2025-09-11T15:48:55Z
---

# Testing Configuration

## Framework
- Type: pytest
- Version: 8.4.2
- Config File: pyproject.toml

## Test Structure
- Test Directory: tests
- Test Files: 5 files found
- Naming Pattern: test_*.py

## Commands
- Run All Tests: `pytest -v --tb=short`
- Run Specific Test: `pytest -v {test_file}`
- Run with Coverage: `pytest --cov=skoglib --cov-report=term-missing`

## Environment
- Python Version: >=3.13
- Virtual Environment: .venv
- Required Dependencies: pytest>=8.4.2, pytest-cov>=4.1.0

## Test Runner Agent Configuration
- Use verbose output for debugging
- Run tests sequentially (no parallel)
- Capture full stack traces
- No mocking - use real implementations
- Wait for each test to complete

## Test Files
- test_import_performance.py - Performance benchmarking
- test_logging_integration.py - Logging system tests
- test_exception_logging.py - Exception handling tests
- test_logging_config.py - Configuration tests
- __init__.py - Test package initialization