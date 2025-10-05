# Copilot Instructions for mci-py

## Project Context

- **Check `PRD.md`** for overall project context, goals, and requirements
- **Check `development.md`** for testing and linting commands
- **Check `installation.md`** for setup and installation instructions

## Code Documentation Standards

### File-Level Comments

Write explanation comments at the start of each file that describe:
- The purpose of the file
- What functionality it provides
- How it fits into the overall project

Example:
```python
"""
mcipy.py - Main entry point for the MCI Python adapter

This module provides the core functionality for loading and executing
MCI tool definitions from JSON schema files.
"""
```

### Function/Class Documentation

Write explanation comments for each function, class, and method that explain:
- What the function/class does
- Why it exists (not just what it does)
- Any important implementation details or gotchas
- Parameters and return values (if not obvious from type hints)

Example:
```python
def execute_tool(tool_def: dict, properties: dict) -> dict:
    """
    Execute an MCI tool definition with the provided properties.
    
    Handles templating of environment variables and property values,
    then dispatches to the appropriate executor (HTTP, CLI, or file).
    Returns a structured result with error handling.
    """
    # Implementation
```

## Testing Strategy

### Coverage Goal

**Target: 90%+ test coverage** across all modules

### Test Types

#### 1. Unit Tests

Test every function involved in processing:
- **JSON Schema Validation**: Test schema loading, validation, and error handling
- **Templating Engine**: Test placeholder replacement for `{{env.VAR}}`, `{{props.name}}`, `{{input.field}}`
- **Execution Dispatchers**: Test each executor (HTTP, CLI, file) in isolation
- **Authentication Handlers**: Test API key, OAuth2, basic auth parsing and application
- **Error Handling**: Test error detection, formatting, and propagation
- **Utility Functions**: Test all helper functions for parsing, formatting, and validation

Example unit test structure:
```python
def test_template_replacement():
    """Test that environment variables are correctly replaced in templates."""
    template = "Hello {{env.USER}}"
    env = {"USER": "TestUser"}
    result = replace_template(template, env=env)
    assert result == "Hello TestUser"

def test_template_missing_variable():
    """Test error handling when template variable is missing."""
    template = "Hello {{env.MISSING}}"
    with pytest.raises(TemplateError):
        replace_template(template, env={})
```

#### 2. Feature Tests

Test full features end-to-end:
- **Tool Loading**: Load JSON context file and parse all tools
- **HTTP Execution**: Make real HTTP requests to test endpoints (use mocking where appropriate)
- **CLI Execution**: Execute command-line tools and capture output
- **File Reading**: Read and parse files with template replacement
- **Authentication Flows**: Test complete auth flows (API key, OAuth2, basic auth)
- **Error Scenarios**: Test network failures, timeouts, invalid inputs

Example feature test:
```python
def test_execute_http_tool_with_api_key():
    """Test executing an HTTP tool with API key authentication."""
    tool_def = {
        "name": "get_weather",
        "execution": {
            "type": "http",
            "method": "GET",
            "url": "https://api.example.com/weather",
            "auth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "value": "{{env.API_KEY}}"
            }
        }
    }
    env = {"API_KEY": "test-key-123"}
    result = execute_tool(tool_def, env=env, props={})
    assert result["success"] is True
```

#### 3. Manual Tests

Create manual test files for large features that should be run individually via terminal with clear output.

**Location**: `tests/manual/`

**Requirements**:
- Each test file should be standalone and executable
- Provide clear, human-readable output showing what is being tested
- Include setup instructions in comments at the top of each file
- Show both success and failure cases

**Manual Test Examples**:

##### `tests/manual/test_parsing_tools.py`
```python
#!/usr/bin/env python3
"""
Manual test for parsing MCI tool definitions.

Setup:
1. Ensure you have a sample JSON context file at ./mci-example.json
2. Run: uv run python tests/manual/test_parsing_tools.py

This test will:
- Load the JSON context file
- Parse all tool definitions
- Display parsed tools with their properties
- Show any validation errors
"""

def main():
    print("=" * 60)
    print("Manual Test: Parsing MCI Tool Definitions")
    print("=" * 60)
    
    # Test implementation with clear output
    print("\n1. Loading JSON context file...")
    # ... implementation
    
    print("\n2. Parsing tool definitions...")
    # ... implementation
    
    print("\n✓ Test completed successfully")

if __name__ == "__main__":
    main()
```

##### `tests/manual/test_terminal_execution.py`
```python
#!/usr/bin/env python3
"""
Manual test for executing terminal commands.

Setup:
1. Ensure you have the MCI adapter installed
2. Run: uv run python tests/manual/test_terminal_execution.py

This test will:
- Execute various CLI commands (ls, echo, grep, etc.)
- Test with different flags and arguments
- Test error handling for invalid commands
- Show command output in real-time
"""

def main():
    print("=" * 60)
    print("Manual Test: Terminal Command Execution")
    print("=" * 60)
    
    # Test implementation with clear output
    print("\n1. Testing basic command execution (echo)...")
    # ... implementation
    
    print("\n2. Testing command with flags (ls -la)...")
    # ... implementation
    
    print("\n3. Testing error handling (invalid command)...")
    # ... implementation
    
    print("\n✓ All terminal execution tests completed")

if __name__ == "__main__":
    main()
```

##### `tests/manual/test_http_requests.py`
```python
#!/usr/bin/env python3
"""
Manual test for HTTP request execution.

Setup:
1. Set environment variables for API keys if testing authenticated endpoints
2. Run: uv run python tests/manual/test_http_requests.py

This test will:
- Make HTTP requests to test endpoints
- Test different HTTP methods (GET, POST, PUT, DELETE)
- Test authentication (API key, OAuth2, basic auth)
- Test error handling (timeouts, 404s, 500s)
- Display request/response details
"""

def main():
    print("=" * 60)
    print("Manual Test: HTTP Request Execution")
    print("=" * 60)
    
    # Test implementation with clear output
    print("\n1. Testing GET request...")
    # ... implementation
    
    print("\n2. Testing POST with JSON body...")
    # ... implementation
    
    print("\n3. Testing API key authentication...")
    # ... implementation
    
    print("\n✓ All HTTP request tests completed")

if __name__ == "__main__":
    main()
```

##### `tests/manual/test_file_operations.py`
```python
#!/usr/bin/env python3
"""
Manual test for file reading and template replacement.

Setup:
1. Ensure test files exist in tests/fixtures/
2. Run: uv run python tests/manual/test_file_operations.py

This test will:
- Read files with and without template placeholders
- Test template replacement with env vars and properties
- Test error handling for missing files
- Display file contents before and after processing
"""

def main():
    print("=" * 60)
    print("Manual Test: File Operations")
    print("=" * 60)
    
    # Test implementation with clear output
    print("\n1. Reading plain text file...")
    # ... implementation
    
    print("\n2. Reading file with template placeholders...")
    # ... implementation
    
    print("\n3. Testing error handling for missing file...")
    # ... implementation
    
    print("\n✓ All file operation tests completed")

if __name__ == "__main__":
    main()
```

### Test Organization

```
tests/
├── test_placeholder.py          # Placeholder (remove once real tests exist)
├── test_schema.py              # Unit tests for JSON schema validation
├── test_templating.py          # Unit tests for template engine
├── test_http_executor.py       # Unit tests for HTTP execution
├── test_cli_executor.py        # Unit tests for CLI execution
├── test_file_executor.py       # Unit tests for file execution
├── test_auth.py                # Unit tests for authentication
├── test_integration.py         # Integration tests combining multiple components
└── manual/
    ├── test_parsing_tools.py        # Manual test for tool parsing
    ├── test_terminal_execution.py   # Manual test for CLI execution
    ├── test_http_requests.py        # Manual test for HTTP requests
    └── test_file_operations.py      # Manual test for file operations
```

### Running Tests

```bash
# Run all automated tests
make test

# Run specific test file with output
uv run pytest -s tests/test_schema.py

# Run tests with coverage report
uv run pytest --cov --cov-report=html --cov-report=term

# Run a manual test
uv run python tests/manual/test_parsing_tools.py
```

## Development Workflow

### Testing Commands
```bash
# Run all tests
make test

# Run specific test file with output
uv run pytest -s tests/test_file.py

# Run tests with coverage
uv run pytest --cov

# Run manual tests individually
uv run python tests/manual/test_parsing_tools.py
uv run python tests/manual/test_terminal_execution.py
```

### Linting Commands
```bash
# Run all linters and formatters
make lint

# Run individual linters
uv run ruff check --fix src/
uv run ruff format src/
uv run basedpyright --stats src/
```

### Installation
```bash
# Install all dependencies
make install

# Run sync, lint, and test in one command
make
```

## Code Style Guidelines

- Use modern Python 3.11+ features and type annotations
- Follow the guidelines in `.cursor/rules/python.mdc`
- Keep comments concise and explanatory (explain WHY, not WHAT)
- Avoid obvious or redundant comments
- Use `uv` for all Python operations, not `pip` or `python` directly
