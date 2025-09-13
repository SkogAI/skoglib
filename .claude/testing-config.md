---
framework: pytest
test_command: pytest
created: 2025-09-12T22:53:10Z
updated: 2025-09-12T22:53:10Z
---

# Testing Configuration

## Framework
- Type: pytest
- Version: 8.4.2
- Config File: pyproject.toml

## Test Structure
- Test Directory: tests/
- Test Files: 7 files found
- Naming Pattern: test_*.py

## Commands
- Run All Tests: `pytest -v --tb=short`
- Run Specific Test: `pytest -v {test_file}`
- Run with Coverage: `pytest --cov=src/skoglib --cov-report=term-missing`
- Run with Debugging: `pytest -v -s --tb=long`

## Environment
- Required ENV vars: None specified
- Python Path: Automatically handled by pytest
- Virtual Environment: .venv (active)

## Test Runner Agent Configuration
- Use verbose output for debugging
- Run tests sequentially (no parallel)
- Capture full stack traces
- No mocking - use real implementations
- Wait for each test to complete

## Project Details
- Project: skoglib v0.1.0
- Python Version: >=3.13
- Build System: uv_build
- Dependencies: dotenv>=0.9.9
- Dev Dependencies: pytest, mypy, ruff, bandit, coverage, pytest-cov

## Test Files
- test_import_performance.py - Performance benchmarking
- test_logging_integration.py - Logging system tests  
- test_exception_logging.py - Exception handling tests
- test_logging_config.py - Configuration tests
- test_config.py - Configuration management tests
- test_utils.py - Utility functions tests
- __init__.py - Test package initialization