# skoglib

Minimal Python library for SkogAI tool execution and automation.

## Installation

```bash
pip install skoglib
```

## Quick Start

```python
from skoglib import run_executable

# Execute a command and get structured results
result = run_executable("echo", ["Hello, World!"])
print(f"Output: {result.stdout}")
print(f"Exit code: {result.return_code}")
```

## Features

- **Batteries included but minimal** approach to running external executables
- Proper error handling with structured exception hierarchy
- Output capture and logging integration
- Performance monitoring and debugging support
- Python 3.8+ compatibility

## Development

### CI/CD Pipeline

This project uses a comprehensive CI/CD pipeline with multiple quality gates:

#### Continuous Integration
- **Multi-platform testing**: Linux, macOS, Windows
- **Python version matrix**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Quality checks**: Ruff linting, MyPy type checking
- **Performance benchmarks**: Import time < 50ms, execution overhead monitoring
- **Code coverage**: Automated coverage reporting with Codecov

#### Security Pipeline
- **SAST**: Static application security testing with Bandit
- **Dependency scanning**: Vulnerability detection with pip-audit
- **Supply chain security**: Package integrity verification
- **Secrets detection**: TruffleHog for credential leak prevention
- **Automated updates**: Dependabot for security patches

#### Release Pipeline
- **Automated publishing**: PyPI publishing with OIDC trusted publishing
- **Package verification**: Wheel and source distribution validation
- **Release validation**: Post-publish functionality testing

### Development Workflow

```bash
# Setup development environment
pip install uv
uv sync --dev

# Run quality checks
uv run ruff check .          # Linting
uv run ruff format --check . # Format checking
uv run mypy src/            # Type checking
uv run bandit -r src/       # Security scanning

# Run tests
uv run pytest              # All tests
uv run pytest --cov=src/skoglib --cov-report=term-missing  # With coverage

# Build package
uv build
```

### Performance Requirements

The library maintains strict performance standards:
- **Import time**: < 50ms
- **Execution overhead**: Minimal subprocess overhead
- **Memory usage**: Lightweight footprint

## License

MIT License - see LICENSE file for details.
