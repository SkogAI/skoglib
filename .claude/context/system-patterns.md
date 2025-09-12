---
created: 2025-09-11T14:31:20Z
last_updated: 2025-09-11T14:31:20Z
version: 1.0
author: Claude Code PM System
---

# System Patterns

## Architectural Style

### Package Architecture
- **Modular Design**: Clear separation between core functionality, utilities, and CLI
- **Layered Structure**: Core business logic separated from presentation/interface layers
- **Minimal Dependencies**: Zero runtime dependencies for maximum compatibility and reliability
- **Single Responsibility**: Each module has a clear, focused purpose

### Code Organization Patterns
- **src/ Layout**: Modern Python packaging with source code isolated in `src/`
- **Package Entry Points**: Multiple access patterns via `__main__.py` and script entry points
- **Import Management**: Clean public API through `__init__.py` with controlled exports

## Design Patterns

### Configuration Management
- **Declarative Config**: pyproject.toml as single source of truth
- **Tool Configuration**: All development tools configured in pyproject.toml
- **Environment Isolation**: direnv + UV for reproducible development environments

### Error Handling Philosophy
From CLAUDE.md project instructions:
- **Fail Fast**: Critical configuration errors stop execution immediately
- **Log and Continue**: Optional features degrade gracefully
- **Graceful Degradation**: External service failures don't break core functionality
- **User-Friendly Messages**: Error messages are clear and actionable through resilience layer

### Testing Strategy
From CLAUDE.md project instructions:
- **Real Integration**: No mock services, test against real implementations
- **Verbose Testing**: Tests provide detailed output for debugging
- **Sequential Testing**: Complete one test fully before moving to next
- **Test Structure Validation**: Verify test correctness before assuming code issues

## Development Patterns

### Code Quality Gates
- **Static Analysis Pipeline**: mypy → ruff → bandit → pytest
- **Type-First Development**: Full type annotations required
- **Security-First**: Bandit security scanning on all code
- **Coverage-Driven**: Test coverage measurement and reporting

### Modern Python Practices
- **Type Hints**: Full mypy static typing throughout codebase
- **Modern Tooling**: UV for dependency management, Ruff for linting/formatting
- **Python 3.13+**: Leveraging latest Python features and performance
- **Pure Python**: No compiled extensions, maximum compatibility

## Anti-Patterns to Avoid

### From CLAUDE.md Absolute Rules
- **NO PARTIAL IMPLEMENTATION**: Complete features before moving on
- **NO SIMPLIFICATION**: No placeholder implementations or TODOs
- **NO CODE DUPLICATION**: Reuse existing functions and constants
- **NO DEAD CODE**: Remove unused code immediately
- **NO CHEATER TESTS**: Tests must be accurate and reveal real flaws
- **NO INCONSISTENT NAMING**: Follow established naming patterns
- **NO OVER-ENGINEERING**: Simple functions over complex abstractions
- **NO MIXED CONCERNS**: Proper separation of responsibilities
- **NO RESOURCE LEAKS**: Proper cleanup of resources

## Data Flow Patterns

### Input Validation
- **Type Safety**: mypy ensures type correctness at build time
- **Runtime Validation**: Explicit validation where needed
- **Error Propagation**: Clear error messages bubble up appropriately

### State Management
- **Immutable Patterns**: Prefer immutable data structures
- **Stateless Functions**: Functions with no side effects where possible
- **Clear Ownership**: Explicit ownership of mutable state

## Integration Patterns

### External Services
- **Resilience Layer**: Graceful handling of external service failures
- **Timeout Management**: Appropriate timeouts for all external calls
- **Retry Patterns**: Exponential backoff for transient failures

### CLI Patterns
- **Entry Point**: `__main__.py` provides clean CLI entry point
- **Script Integration**: pyproject.toml scripts section for installation
- **Command Structure**: Clear, intuitive command structure

## Performance Patterns

### Build Performance
- **UV Benefits**: Leverage UV's speed for dependency management
- **Incremental Analysis**: Tools support incremental checking
- **Parallel Processing**: Where applicable, leverage parallelism

### Runtime Performance
- **Zero Dependencies**: No runtime dependency overhead
- **Lazy Loading**: Import modules only when needed
- **Memory Efficiency**: Conscious memory usage patterns

## Security Patterns

### Input Sanitization
- **Validation at Boundaries**: All external input validated
- **Type Safety**: Static typing prevents many injection attacks
- **Secure Defaults**: All defaults are secure

### Dependency Management
- **Minimal Surface**: Zero runtime dependencies reduces attack surface
- **Lock File Security**: UV lock with hashes ensures dependency integrity
- **Regular Updates**: Keep development dependencies current

## Monitoring and Observability

### Development Observability
- **Verbose Testing**: Tests provide debugging information
- **Type Coverage**: Track type annotation coverage
- **Code Coverage**: Measure and maintain test coverage
- **Security Scanning**: Regular vulnerability scanning

### Error Tracking
- **Clear Error Messages**: Errors include context and suggestions
- **Error Categorization**: Different error types handled appropriately
- **Debug Information**: Sufficient context for troubleshooting

## Future Evolution Patterns

### Extensibility
- **Plugin Architecture**: Ready for plugin system if needed
- **API Stability**: Public API designed for backward compatibility
- **Feature Flags**: Ability to toggle features during development

### Scalability Preparation
- **Async Ready**: Structure supports async patterns if needed
- **Modular Growth**: Easy to extract modules as separate packages
- **Configuration Flexibility**: Easy to extend configuration options