---
created: 2025-09-11T14:31:20Z
last_updated: 2025-09-11T14:31:20Z
version: 1.0
author: Claude Code PM System
---

# Project Structure

## Directory Organization

```
epic-skogai-python-library/
├── .claude/                    # Claude Code configuration
│   ├── context/               # Project context documentation
│   └── rules/                 # Claude-specific rules and guidelines
├── .github/                   # GitHub configuration
│   └── workflows/             # CI/CD workflows
├── .venv/                     # Python virtual environment
├── scripts/                   # Build and utility scripts
├── src/                       # Source code
│   └── skoglib/              # Main package
│       ├── __init__.py       # Package initialization
│       └── __main__.py       # Main entry point
├── .envrc                     # Environment configuration (direnv)
├── .gitignore                # Git ignore rules
├── .python-version           # Python version specification
├── CLAUDE.md                 # Claude Code project instructions
├── pyproject.toml            # Python project configuration
├── README.md                 # Project documentation
└── uv.lock                   # UV dependency lock file
```

## File Organization Patterns

### Source Code Structure
- **Main package**: `src/skoglib/` - Core library implementation
- **Entry point**: `__main__.py` - CLI and main functionality
- **Package init**: `__init__.py` - Package exports and version

### Configuration Files
- **Project config**: `pyproject.toml` - Dependencies, build system, tools
- **Environment**: `.envrc` - Development environment setup
- **Python version**: `.python-version` - Exact Python version (3.13)
- **Lock file**: `uv.lock` - Pinned dependency versions

### Development Infrastructure
- **GitHub Actions**: `.github/workflows/` - CI/CD automation
- **Scripts**: `scripts/` - Build and development utilities
- **Claude Config**: `.claude/` - AI assistant configuration

## Naming Conventions

### Python Code
- **Package names**: lowercase, underscores (skoglib)
- **Module names**: lowercase, underscores
- **Class names**: PascalCase
- **Function names**: snake_case
- **Constants**: UPPER_SNAKE_CASE

### File Naming
- **Python files**: snake_case.py
- **Configuration**: kebab-case or standard names
- **Documentation**: kebab-case.md

## Module Organization

### Core Package Structure
```
src/skoglib/
├── __init__.py              # Public API exports
├── __main__.py              # CLI entry point
├── core/                    # Core functionality (planned)
├── utils/                   # Utility functions (planned)
└── tests/                   # Unit tests (planned)
```

### Import Hierarchy
- Public API exposed through `__init__.py`
- Internal modules import from core
- No circular dependencies
- Clear separation of concerns

## Development Patterns

### Testing Structure
- Tests will be placed in `src/skoglib/tests/`
- Test files prefixed with `test_`
- Mirror source structure in test organization

### Build Artifacts
- Built packages in `dist/` (generated)
- Coverage reports in `htmlcov/` (generated)
- Cache directories in `.pytest_cache/`, `.mypy_cache/`

## File Types and Extensions

### Source Code
- `.py` - Python source files
- `.pyi` - Type stub files (if needed)

### Configuration
- `.toml` - Configuration files (pyproject.toml)
- `.md` - Documentation (Markdown)
- `.yml/.yaml` - Workflows and configs

### Development
- `.lock` - Lock files for dependencies
- `.envrc` - Environment configuration
- `.python-version` - Version specification

## Key Directories

### Source (`src/`)
- Contains all package source code
- Enables editable installs
- Separates source from project root

### Scripts (`scripts/`)
- Build automation
- Development utilities
- Deployment scripts

### Configuration (`.claude/`)
- Claude Code specific configuration
- Context documentation
- AI assistant rules and guidelines