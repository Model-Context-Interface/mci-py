# MCI Python Adapter Implementation Plan

## Overview

This plan outlines the step-by-step implementation of the Model Context Interface (MCI) v1 Python adapter based on PRD.md requirements. The implementation follows DRY, KISS, and modern software engineering principles with a focus on modularity, testability, and maintainability.

---

## Stage 1: Core Infrastructure and Data Models ✔️

### 1.1 Execution Type Enum

**File**: `src/mcipy/enums.py`

Define execution types as an enum:

- `HTTP` - HTTP request execution
- `CLI` - Command-line execution
- `FILE` - File reading execution
- `TEXT` - Text template execution

### 1.2 Data Models

**File**: `src/mcipy/models.py`

Define Pydantic models for:

- `MCISchema` - Top-level schema with `schemaVersion`, `metadata`, `tools[]`
- `Metadata` - Optional metadata fields (`name`, `description`, `version`, `license`, `authors[]`)
- `Tool` - Individual tool definition with `name`, `title`, `description`, `inputSchema`, `execution`
- `ExecutionConfig` - Base execution configuration
- `HTTPExecutionConfig` - HTTP-specific fields (method, url, auth, headers, body, timeout_ms, retries)
- `CLIExecutionConfig` - CLI-specific fields (command, args, flags, cwd, timeout_ms)
- `FileExecutionConfig` - File-specific fields (path, enableTemplating)
- `TextExecutionConfig` - Text-specific fields (text)
- `AuthConfig` - Authentication configurations (apiKey, bearer, basic, oauth2)
- `ExecutionResult` - Result format with `isError` and `content`/`error`

**Purpose**: Provide strong typing, validation, and schema enforcement.

---

## Stage 2: Templating Engine ✔️

### 2.1 Template Processor

**File**: `src/mcipy/templating.py`

Implement a decoupled templating engine with:

**Class**: `TemplateEngine`

- `render_basic(template: str, context: dict) -> str` - Basic placeholder substitution (`{{props.x}}`, `{{env.Y}}`)
- `render_advanced(template: str, context: dict) -> str` - Advanced templating with loops and control blocks
- `_resolve_placeholder(path: str, context: dict) -> Any` - Resolve dot-notation paths (e.g., `props.location`)
- `_parse_for_loop(content: str, context: dict) -> str` - Parse `@for` -> `@endfor`
- `_parse_foreach_loop(content: str, context: dict) -> str` - Parse `@foreach` -> `@endforeach`
- `_parse_control_blocks(content: str, context: dict) -> str` - Parse `@if` -> `@elseif` -> `@else` -> `@endif`

**Context Structure**:

```python
{
    "props": {...},  # Properties from execute() call
    "env": {...},    # Environment variables
    "input": {...}   # Alias for props (for backward compatibility)
}
```

---

## Stage 3: Execution Handlers

### 3.1 Base Executor Class ✔️

**File**: `src/mcipy/executors/base.py`

**Class**: `BaseExecutor` (Abstract)

- `execute(config: ExecutionConfig, context: dict) -> ExecutionResult` - Abstract method
- `_build_context(props: dict, env_vars: dict) -> dict` - Build template context
- `_handle_timeout(timeout_ms: int) -> int` - Convert timeout to seconds, apply defaults
- `_format_error(error: Exception) -> ExecutionResult` - Standardize error responses

### 3.2 HTTP Executor ✔️

**File**: `src/mcipy/executors/http_executor.py`

**Class**: `HTTPExecutor(BaseExecutor)`

- `execute(config: HTTPExecutionConfig, context: dict) -> ExecutionResult`
- `_apply_authentication(auth: AuthConfig, request_kwargs: dict) -> None` - Apply auth to request
- `_handle_api_key_auth(auth: AuthConfig, request_kwargs: dict) -> None`
- `_handle_bearer_auth(auth: AuthConfig, request_kwargs: dict) -> None`
- `_handle_basic_auth(auth: AuthConfig, request_kwargs: dict) -> None`
- `_handle_oauth2_auth(auth: AuthConfig, request_kwargs: dict) -> None` - Fetch token and apply
- `_build_body(body_config: dict, context: dict) -> tuple` - Build request body (json/form/raw)
- `_apply_retry_logic(func, retries: dict) -> Any` - Implement retry with backoff

**Dependencies**: `requests` library

### 3.3 CLI Executor ✔️

**File**: `src/mcipy/executors/cli_executor.py`

**Class**: `CLIExecutor(BaseExecutor)`

- `execute(config: CLIExecutionConfig, context: dict) -> ExecutionResult`
- `_build_command_args(config: CLIExecutionConfig, context: dict) -> list` - Build full command with args and flags
- `_apply_flags(flags: dict, context: dict) -> list` - Convert flags based on type (boolean/value)
- `_run_subprocess(command: list, cwd: str, timeout: int) -> tuple` - Execute subprocess

**Platform Consideration**: Handle Windows/Linux/macOS path and command differences.

### 3.4 File Executor ✔️

**File**: `src/mcipy/executors/file_executor.py`

**Class**: `FileExecutor(BaseExecutor)`

- `execute(config: FileExecutionConfig, context: dict) -> ExecutionResult`
- `_resolve_path(path: str, context: dict) -> str` - Resolve templated path
- `_read_file(path: str) -> str` - Read file content
- `_parse_content(content: str, context: dict, parse_placeholders: bool) -> str` - Apply templating if enabled

### 3.5 Text Executor ✔️

**File**: `src/mcipy/executors/text_executor.py`

**Class**: `TextExecutor(BaseExecutor)`

- `execute(config: TextExecutionConfig, context: dict) -> ExecutionResult`
- Simple implementation that applies templating to text string

### 3.6 Executor Factory ✔️

**File**: `src/mcipy/executors/__init__.py`

**Class**: `ExecutorFactory`

- `get_executor(execution_type: ExecutionType) -> BaseExecutor` - Return appropriate executor instance

**Purpose**: Centralize executor instantiation based on execution type.

---

## Stage 4: JSON Parser and Tool Manager

### 4.1 Schema Parser ✔️

**File**: `src/mcipy/parser.py`

**Class**: `SchemaParser`

- `parse_file(file_path: str) -> MCISchema` - Load and validate JSON file
- `parse_dict(data: dict) -> MCISchema` - Parse dictionary into schema
- `_validate_schema_version(version: str) -> None` - Validate schema version compatibility
- `_validate_tools(tools: list) -> None` - Validate tool definitions
- `_build_execution_config(execution: dict) -> ExecutionConfig` - Build appropriate execution config based on type

**Dependencies**: Pydantic for validation

### 4.2 Tool Manager ✔️

**File**: `src/mcipy/tool_manager.py`

**Class**: `ToolManager`

- `__init__(schema: MCISchema)`
- `get_tool(name: str) -> Tool | None` - Retrieve tool by name
- `list_tools() -> list[Tool]` - List all available tools
- `filter_tools(only: list[str] | None, without: list[str] | None) -> list[Tool]` - Filter tools by inclusion/exclusion

---

## Stage 5: Main Adapter API

### 5.1 MCI Client

**File**: `src/mcipy/client.py`

**Class**: `MCIClient`

**Initialization**:

- `__init__(json_file_path: str, env_vars: dict | None = None)`
- Load JSON via `SchemaParser`
- Store environment variables
- Initialize `ToolManager`
- Cache executors via `ExecutorFactory`

**Methods**:

- `tools() -> list[Tool]` - Get all available tools
- `only(tool_names: list[str]) -> list[Tool]` - Filter to include only specified tools
- `without(tool_names: list[str]) -> list[Tool]` - Filter to exclude specified tools
- `execute(tool_name: str, properties: dict) -> ExecutionResult` - Execute a tool
- `list_tools() -> list[str]` - List available tool names
- `get_tool_schema(tool_name: str) -> dict` - Return tool's input schema

**Execute Flow**:

1. Validate tool exists
2. Build context from properties and env_vars
3. Get appropriate executor from factory
4. Apply templating to execution config
5. Execute via executor
6. Return structured result (with meta data field)

**Error Handling**:

- Tool not found → `ExecutionResult(isError=True, error="Tool not found")`
- Invalid properties → `ExecutionResult(isError=True, error="Invalid input")`
- Execution error → `ExecutionResult(isError=True, error=<error message>)`

**Example**:

```python
from mcipy import MCIClient

# Initialize adapter with JSON file and environment variables
client = MCIClient(
    json_file_path="example.mci.json",
    env_vars={"API_KEY": "your-secret-key", "USERNAME": "user"}
)

# List all available tools
all_tools = client.list_tools()
print(f"Available tools: {all_tools}")

# List all available tools
weather_tools = client.list_tools(
  only=["get_weather", "get_forecast"]
)
print(f"Only weather tools: {all_tools}")

# Filter to include only specific tools
weather_tools = client.only(["get_weather", "get_forecast"])

# Filter to exclude specific tools
restricted_tools = client.without(["delete_data", "admin_tools"])

# Execute a tool with properties
result = client.execute(
    tool_name="get_weather",
    properties={"location": "New York", "unit": "celsius"}
)

# Handle result
if result.isError:
    print(f"Error: {result.error}")
else:
    for content in result.content:
        if content.type == "text":
            print(content.text)
```

---

## Stage 6: Testing Infrastructure

### 6.1 Unit Tests

**Directory**: `tests/unit/`

Test files:

- `test_enums.py` - Test execution type enum
- `test_models.py` - Test Pydantic models and validation
- `test_templating.py` - Test basic and advanced templating
- `test_http_executor.py` - Test HTTP executor with mocked requests
- `test_cli_executor.py` - Test CLI executor with mocked subprocess
- `test_file_executor.py` - Test file executor with temp files
- `test_text_executor.py` - Test text executor
- `test_parser.py` - Test JSON schema parsing
- `test_tool_manager.py` - Test tool filtering and retrieval
- `test_adapter.py` - Test main adapter API

### 6.2 Integration Tests

**Directory**: `tests/integration/`

Test files:

- `test_http_integration.py` - Real HTTP calls (or mock server)
- `test_cli_integration.py` - Real CLI commands
- `test_file_integration.py` - Real file operations
- `test_end_to_end.py` - Full workflow tests with example JSON

### 6.3 Security Tests

**Directory**: `tests/security/`

Test files:

- `test_env_vars.py` - Ensure secrets only from env vars
- `test_injection.py` - Test against command injection
- `test_path_traversal.py` - Test file path security

---

## Stage 7: Documentation and Examples

### 7.1 API Documentation

**File**: `docs/api_reference.md`

Document:

- `MCIAdapter` class and methods
- Configuration models
- Execution result format
- Error handling

### 7.2 Quickstart Guide

**File**: `docs/quickstart.md`

Include:

- Installation instructions
- Basic usage example
- Tool definition example
- Execution examples for each type

### 7.3 Schema Reference

**File**: `docs/schema_reference.md`

Document:

- Complete JSON schema structure
- All execution types and their parameters
- Authentication options
- Templating syntax

### 7.4 Examples

**Directory**: `examples/`

Provide:

- `http_example.json` - HTTP execution examples
- `cli_example.json` - CLI execution examples
- `file_example.json` - File execution examples
- `text_example.json` - Text execution examples
- `mixed_example.json` - Combined examples
- `example_usage.py` - Python usage examples

---

## Stage 8: Package Configuration and Build

### 8.1 Dependencies

**File**: `pyproject.toml`

Add required dependencies:

- `pydantic>=2.0` - Data validation
- `requests>=2.31` - HTTP requests
- Development dependencies already configured

### 8.2 Package Metadata

Update `pyproject.toml`:

- Version: `1.0.0`
- Description and keywords
- Entry points if needed

### 8.3 Type Hints and Linting

- Ensure all code has proper type hints
- Run `basedpyright` for type checking
- Run `ruff` for linting and formatting
- Ensure `codespell` passes

---

## Implementation Principles

### DRY (Don't Repeat Yourself)

- Shared templating logic in single `TemplateEngine` class
- Base executor class for common functionality
- Executor factory for instantiation
- Shared context building and error formatting

### KISS (Keep It Simple, Stupid)

- Each executor handles only its execution type
- Clear separation between parsing, templating, and execution
- Simple, focused methods with single responsibilities
- Minimal dependencies (only `pydantic` and `requests`)

### Additional Best Practices

- **Type Safety**: Pydantic models for all data structures
- **Error Handling**: Consistent error format across all executors
- **Testability**: Decoupled components, easy to mock
- **Extensibility**: Easy to add new execution types via base class
- **Security**: Environment-only secrets, no credential exposure
- **Platform Agnostic**: Handle OS differences in CLI executor
- **Performance**: Lazy loading, caching where appropriate

---

## File Structure

```
src/mcipy/
├── __init__.py              # Package exports
├── adapter.py               # Main MCIAdapter class
├── enums.py                 # ExecutionType enum
├── models.py                # Pydantic models
├── parser.py                # SchemaParser class
├── tool_manager.py          # ToolManager class
├── templating.py            # TemplateEngine class
└── executors/
    ├── __init__.py          # ExecutorFactory
    ├── base.py              # BaseExecutor
    ├── http_executor.py     # HTTPExecutor
    ├── cli_executor.py      # CLIExecutor
    ├── file_executor.py     # FileExecutor
    └── text_executor.py     # TextExecutor

tests/
├── unit/
│   ├── test_enums.py
│   ├── test_models.py
│   ├── test_templating.py
│   ├── test_http_executor.py
│   ├── test_cli_executor.py
│   ├── test_file_executor.py
│   ├── test_text_executor.py
│   ├── test_parser.py
│   ├── test_tool_manager.py
│   └── test_adapter.py
├── integration/
│   ├── test_http_integration.py
│   ├── test_cli_integration.py
│   ├── test_file_integration.py
│   └── test_end_to_end.py
└── security/
    ├── test_env_vars.py
    ├── test_injection.py
    └── test_path_traversal.py

docs/
├── api_reference.md
├── quickstart.md
└── schema_reference.md

examples/
├── http_example.json
├── cli_example.json
├── file_example.json
├── text_example.json
├── mixed_example.json
└── example_usage.py
```

---

## Execution Order

1. **Stage 1**: Establish type system and data models (foundation)
2. **Stage 2**: Implement templating (needed by all executors)
3. **Stage 3**: Build executors (core functionality)
4. **Stage 4**: Create parser and tool manager (JSON handling)
5. **Stage 5**: Implement main adapter API (public interface)
6. **Stage 6**: Write comprehensive tests (quality assurance)
7. **Stage 7**: Create documentation (user enablement)
8. **Stage 8**: Finalize package (distribution ready)

Each stage builds upon previous stages, ensuring dependencies are met before implementation.
