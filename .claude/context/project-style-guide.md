---
created: 2025-09-11T14:31:20Z
last_updated: 2025-09-11T14:31:20Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide

## Code Style Standards

### Python Code Formatting
- **Formatter**: Ruff (configured in pyproject.toml)
- **Line Length**: 88 characters (Black compatible)
- **Quote Style**: Double quotes preferred, single quotes for nested strings
- **Import Organization**: Ruff import sorting with isort compatibility
- **Indentation**: 4 spaces, no tabs

### Naming Conventions

#### Variables and Functions
```python
# snake_case for variables and functions
user_name = "john_doe"
def calculate_total_price(items: list) -> float:
    return sum(item.price for item in items)

# Private methods and variables prefixed with underscore
def _internal_helper(data: dict) -> str:
    return data.get("key", "")

_private_constant = "internal_value"
```

#### Classes and Types
```python
# PascalCase for classes
class UserManager:
    def __init__(self, database: Database) -> None:
        self.database = database

# PascalCase for type aliases and protocols
UserDict = dict[str, Any]

class DatabaseProtocol(Protocol):
    def query(self, sql: str) -> list[dict]:
        ...
```

#### Constants and Enums
```python
# UPPER_SNAKE_CASE for module-level constants
DEFAULT_TIMEOUT = 30.0
API_BASE_URL = "https://api.skogai.com"

# PascalCase for Enums, UPPER_SNAKE_CASE for values
class StatusCode(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PENDING = "PENDING"
```

#### Files and Modules
- **Python files**: snake_case.py
- **Packages**: snake_case (single word preferred)
- **Test files**: test_*.py or *_test.py
- **Configuration**: pyproject.toml, .envrc, etc.

### Type Annotations

#### Function Signatures
```python
# Complete type annotations required
def process_data(
    input_data: list[dict[str, Any]], 
    config: ConfigDict | None = None
) -> ProcessResult:
    """Process input data with optional configuration."""
    ...

# Use modern type syntax (Python 3.9+)
def get_users() -> list[User]:  # Not List[User]
    return []

def update_mapping(data: dict[str, int]) -> None:  # Not Dict[str, int]
    ...
```

#### Class Type Hints
```python
class DataProcessor:
    def __init__(
        self, 
        config: ProcessorConfig,
        logger: Logger | None = None
    ) -> None:
        self.config = config
        self.logger = logger or default_logger
        self._cache: dict[str, ProcessResult] = {}

    def process(self, data: InputData) -> ProcessResult:
        ...
```

#### Union Types and Optionals
```python
# Use | for unions (Python 3.10+)
def parse_value(raw: str | int | None) -> ParsedValue | None:
    ...

# Generic types
from collections.abc import Callable, Iterator

def apply_transform(
    data: Iterator[T], 
    transform: Callable[[T], U]
) -> Iterator[U]:
    ...
```

## Documentation Standards

### Docstring Format
```python
def calculate_metrics(
    data: list[DataPoint], 
    weights: dict[str, float] | None = None
) -> MetricResult:
    """Calculate weighted metrics from data points.
    
    Processes a list of data points and applies optional weights
    to calculate aggregated metrics. Missing weights default to 1.0.
    
    Args:
        data: List of data points to process
        weights: Optional weights for each metric type
        
    Returns:
        MetricResult containing calculated metrics and metadata
        
    Raises:
        ValueError: If data is empty or contains invalid points
        KeyError: If required metric type is missing from weights
        
    Example:
        >>> data = [DataPoint(value=10, type="revenue")]
        >>> weights = {"revenue": 0.8}
        >>> result = calculate_metrics(data, weights)
        >>> result.total
        8.0
    """
    ...
```

### Class Documentation
```python
class APIClient:
    """HTTP client for SkogAI API interactions.
    
    Provides a high-level interface for making authenticated requests
    to SkogAI services with automatic retry logic and error handling.
    
    Attributes:
        base_url: API base URL for all requests
        timeout: Default timeout for HTTP requests in seconds
        max_retries: Maximum number of retry attempts for failed requests
        
    Example:
        >>> client = APIClient("https://api.skogai.com", timeout=30.0)
        >>> response = await client.get("/users/123")
        >>> user = response.json()
    """
    
    def __init__(
        self, 
        base_url: str, 
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> None:
        """Initialize API client.
        
        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        ...
```

### Module Documentation
```python
"""Utility functions for data processing and validation.

This module provides common utilities for processing and validating
data structures used throughout the SkogAI ecosystem.

Classes:
    DataValidator: Validates data against schemas
    DataProcessor: Processes and transforms data
    
Functions:
    validate_schema: Validates data against JSON schema
    transform_data: Applies transformations to data structures
    
Constants:
    DEFAULT_SCHEMA: Default validation schema
    SUPPORTED_FORMATS: List of supported data formats
    
Example:
    >>> from skoglib.utils.data import validate_schema, DEFAULT_SCHEMA
    >>> result = validate_schema(data, DEFAULT_SCHEMA)
    >>> if result.valid:
    ...     print("Data is valid")
"""
```

## Error Handling Patterns

### Exception Hierarchy
```python
class SkogLibError(Exception):
    """Base exception for all skoglib errors."""
    
class ConfigurationError(SkogLibError):
    """Raised when configuration is invalid or missing."""
    
class ValidationError(SkogLibError):
    """Raised when data validation fails."""
    
class APIError(SkogLibError):
    """Raised when API operations fail."""
    
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
```

### Error Handling Strategy
```python
def process_user_data(data: dict[str, Any]) -> ProcessResult:
    """Process user data with comprehensive error handling."""
    try:
        # Validate input
        validated_data = validate_user_data(data)
    except ValidationError as e:
        logger.error(f"Data validation failed: {e}")
        raise  # Re-raise validation errors
    
    try:
        # Process data
        result = transform_data(validated_data)
    except ProcessingError as e:
        logger.error(f"Data processing failed: {e}")
        # Return error result instead of raising
        return ProcessResult(success=False, error=str(e))
    except Exception as e:
        # Unexpected errors get logged and re-raised
        logger.exception(f"Unexpected error processing data: {e}")
        raise ProcessingError(f"Unexpected error: {e}") from e
    
    return ProcessResult(success=True, data=result)
```

## Testing Patterns

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

from skoglib.utils import DataProcessor
from skoglib.exceptions import ValidationError


class TestDataProcessor:
    """Test suite for DataProcessor class."""
    
    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.processor = DataProcessor(config=test_config)
        self.sample_data = [
            {"id": 1, "value": "test1"},
            {"id": 2, "value": "test2"},
        ]
    
    def test_process_valid_data_returns_success(self) -> None:
        """Test that processing valid data returns success result."""
        # Given
        expected_result = ProcessResult(success=True, count=2)
        
        # When
        result = self.processor.process(self.sample_data)
        
        # Then
        assert result.success is True
        assert result.count == 2
        assert result.errors == []
    
    def test_process_invalid_data_raises_validation_error(self) -> None:
        """Test that processing invalid data raises ValidationError."""
        # Given
        invalid_data = [{"invalid": "data"}]
        
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            self.processor.process(invalid_data)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    @patch('skoglib.utils.external_service_call')
    def test_process_with_external_service_failure(
        self, 
        mock_service: Mock
    ) -> None:
        """Test graceful handling of external service failures."""
        # Given
        mock_service.side_effect = ConnectionError("Service unavailable")
        
        # When
        result = self.processor.process(self.sample_data)
        
        # Then
        assert result.success is False
        assert "service unavailable" in result.error.lower()
```

### Test Organization
- **File naming**: test_*.py or *_test.py
- **Class naming**: TestClassName for each class being tested
- **Method naming**: test_method_name_condition_expected_result
- **Fixtures**: Use pytest fixtures for common test data
- **Mocking**: Mock external dependencies, not internal logic

## Configuration Patterns

### Settings Management
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'skoglib'),
            username=os.getenv('DB_USER', 'user'),
            password=os.getenv('DB_PASSWORD', ''),
        )

@dataclass
class AppConfig:
    debug: bool = False
    log_level: str = "INFO"
    database: DatabaseConfig | None = None
    
    @classmethod
    def load_from_file(cls, path: Path) -> 'AppConfig':
        """Load configuration from YAML or JSON file."""
        ...
```

## Import Organization

### Import Order
```python
# 1. Standard library imports
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. Third-party imports (none for skoglib)

# 3. Local imports
from skoglib.core import BaseProcessor
from skoglib.exceptions import ValidationError
from skoglib.utils.helpers import format_message

# 4. Conditional imports
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib
```

### Import Style
```python
# Prefer specific imports over wildcard
from skoglib.utils import validate_data, transform_data  # Good
from skoglib.utils import *  # Bad

# Use type-only imports for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from skoglib.types import ComplexType

# Alias imports for clarity
from skoglib.external.long_module_name import SomeClass as ExternalClass
```

## Performance Guidelines

### Lazy Imports
```python
def expensive_operation(data: Any) -> ProcessResult:
    """Import expensive modules only when needed."""
    import pandas as pd  # Only import if function is called
    
    df = pd.DataFrame(data)
    return ProcessResult(data=df.to_dict())
```

### Memory Management
```python
def process_large_dataset(file_path: Path) -> Iterator[ProcessResult]:
    """Process large datasets using generators to minimize memory usage."""
    with file_path.open() as file:
        for line in file:
            data = json.loads(line)
            yield process_single_item(data)  # Yield instead of accumulating
```

### Caching Patterns
```python
from functools import lru_cache
from typing import Final

# Use lru_cache for expensive pure functions
@lru_cache(maxsize=128)
def expensive_calculation(input_value: str) -> float:
    """Cache expensive calculations."""
    ...

# Use module-level constants for static data
VALIDATION_PATTERNS: Final[dict[str, str]] = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone": r"^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$",
}
```