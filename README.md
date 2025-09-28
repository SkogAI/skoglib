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

## License

MIT License - see LICENSE file for details.
