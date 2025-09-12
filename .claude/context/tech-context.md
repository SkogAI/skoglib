---
created: 2025-09-11T14:31:20Z
last_updated: 2025-09-11T14:31:20Z
version: 1.0
author: Claude Code PM System
---

# Technical Context

## Language & Runtime

### Python
- **Version**: Python >=3.13
- **Package Manager**: UV (modern Python package manager)
- **Build System**: UV Build (>=0.8.15,<0.9.0)
- **Virtual Environment**: UV-managed venv in `.venv/`

### Version Management
- **Python Version File**: `.python-version` (specifies exact version)
- **Lock File**: `uv.lock` (pinned dependencies with hashes)
- **Environment**: direnv with `.envrc` for local development

## Dependencies

### Runtime Dependencies
- **Count**: 0 (minimal runtime footprint)
- **Philosophy**: Keep runtime dependencies minimal

### Development Dependencies
- **mypy** (>=1.17.1) - Static type checking
- **pytest** (>=8.4.2) - Testing framework
- **ruff** (>=0.12.12) - Fast Python linter and formatter
- **bandit** (>=1.8.6) - Security linter for Python
- **coverage** (>=7.3.2) - Code coverage measurement
- **pytest-cov** (>=4.1.0) - Coverage plugin for pytest

## Development Tools

### Code Quality
- **Linting**: Ruff (replaces flake8, isort, black)
- **Type Checking**: mypy with strict configuration
- **Security**: Bandit for security vulnerability scanning
- **Formatting**: Ruff formatter (replaces black)

### Testing
- **Framework**: pytest for all testing
- **Coverage**: Coverage.py with pytest-cov integration
- **Test Discovery**: Automatic test discovery in `src/skoglib/tests/`

### Build & Package
- **Build Backend**: UV Build (modern, fast Python build system)
- **Package Format**: Standard Python wheel and sdist
- **Distribution**: Ready for PyPI publication

## Development Environment

### Local Setup
- **Environment Manager**: direnv with `.envrc`
- **Package Manager**: UV for dependency management
- **Virtual Environment**: Automatic UV venv management

### IDE Configuration
- **Type Hints**: Full mypy static typing
- **Import Organization**: Ruff import sorting
- **Code Style**: Ruff formatting rules

## CI/CD Pipeline

### GitHub Actions
- **Code Review**: Claude Code Review workflow
- **PR Assistant**: Claude PR Assistant workflow
- **Integration**: Automated workflows for code quality

### Quality Gates
- Type checking with mypy
- Linting with ruff
- Security scanning with bandit
- Test coverage reporting
- Automated code review

## Architecture Decisions

### Modern Python Stack
- **UV Over pip**: Faster, more reliable dependency management
- **Ruff Over Multiple Tools**: Single tool for linting/formatting
- **pytest**: Industry standard testing framework
- **mypy**: Static type checking for reliability

### Package Structure
- **src/ Layout**: Modern Python packaging best practice
- **Entry Point**: CLI via `__main__.py` and scripts section
- **Minimal Runtime**: Zero runtime dependencies for maximum compatibility

## Performance Considerations

### Build Performance
- **UV**: Extremely fast dependency resolution and installation
- **Ruff**: Rust-based tools for maximum performance
- **Incremental**: Tools support incremental checking

### Runtime Performance
- **Zero Dependencies**: No runtime overhead from dependencies
- **Python 3.13**: Latest Python performance improvements
- **Type Hints**: Enable potential optimization paths

## Security

### Development Security
- **Bandit**: Automated security vulnerability scanning
- **Dependency Scanning**: UV lock file with integrity hashes
- **Code Review**: Automated Claude Code Review workflow

### Runtime Security
- **Minimal Attack Surface**: Zero runtime dependencies
- **Type Safety**: mypy static analysis prevents many bugs
- **Secure Defaults**: Following Python security best practices

## Compatibility

### Python Versions
- **Minimum**: Python 3.13+
- **Target**: Latest stable Python
- **Future**: Ready for Python 3.14+ features

### Platform Support
- **Cross-platform**: Works on Linux, macOS, Windows
- **Architecture**: Pure Python, no native dependencies
- **Container**: Ready for containerization

## Monitoring & Observability

### Code Quality Metrics
- **Coverage**: pytest-cov integration
- **Type Coverage**: mypy coverage reporting
- **Complexity**: Ruff complexity analysis
- **Security**: Bandit vulnerability reports

### Build Metrics
- **Build Time**: UV fast builds
- **Package Size**: Minimal footprint tracking
- **Dependency Count**: Zero runtime dependencies