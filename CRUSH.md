# CRUSH.md - skoglib Development Guide

## Build/Test/Lint Commands
```bash
# Setup (required first step - takes 30 seconds)
pip install uv && uv sync --dev

# Testing
uv run pytest                                    # All tests (~1.6s)
uv run pytest tests/test_specific.py -v         # Single test file  
uv run pytest --cov=src/skoglib                 # With coverage
uv run pytest -k "test_name" -v                 # Single test by name

# Code Quality (run before commits)
uv run ruff check                                # Lint (~0.04s)
uv run ruff check --fix                         # Auto-fix linting
uv run mypy src/                                 # Type check (~1.6s)
uv run bandit -r src/                           # Security scan (~0.4s)

# Run application
uv run python -m skoglib
uv run skoglib
```

## Code Style Guidelines
- **Python 3.13+** with type hints (use `Optional`, `List`, `Dict` from typing)
- **Module docstrings**: Triple quotes describing purpose and main exports
- **Function docstrings**: Brief description of purpose and behavior
- **Imports**: Group stdlib, third-party, local with blank lines between
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use custom exception hierarchy (SkogAIError base)
- **Dataclasses**: Use for structured data with type annotations
- **Logging**: Use `get_logger(__name__)` from logging_config module
- **Testing**: Pytest with class-based organization, no mocks, verbose output