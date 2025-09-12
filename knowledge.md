# SkogAI Python Library

## Project Overview

This is the official Python library for SkogAI, providing developers with easy access to SkogAI's machine learning services for forest management and analysis.

## Key Conventions

- Use `uv` as the package manager for dependency management
- Follow Python PEP 8 style guidelines
- Implement comprehensive tests for all functions
- No mock services - use real implementations for testing
- Verbose test output for debugging purposes

## Development Workflow

- Use sub-agents for context optimization (file-analyzer, code-analyzer, test-runner)
- Fail fast for critical configuration errors
- Graceful degradation for optional features
- Always run tests after code changes

## Project Structure

- `src/skoglib/` - Main library code
- `scripts/` - Development and utility scripts
- `.claude/` - Claude AI configuration and context
- Tests should be comprehensive and reveal potential flaws

## Error Handling Philosophy

- Critical errors: fail fast
- Optional features: log and continue
- External services: graceful degradation
- User-facing: friendly error messages
