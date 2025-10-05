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

## Development Workflow

### Testing Commands
```bash
# Run all tests
make test

# Run specific test file with output
uv run pytest -s tests/test_file.py

# Run tests with coverage
uv run pytest --cov
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
