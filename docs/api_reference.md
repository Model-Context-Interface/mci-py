# MCI Python Adapter - API Reference

This document provides a comprehensive API reference for the Python MCI Adapter (`mcipy`). The API follows OpenAPI-style documentation with detailed method signatures, parameters, response formats, and examples.

## Table of Contents

- [MCIClient Class](#mciclient-class)
  - [Initialization](#initialization)
  - [Methods](#methods)
    - [tools()](#tools)
    - [only()](#only)
    - [without()](#without)
    - [execute()](#execute)
    - [list_tools()](#list_tools)
    - [get_tool_schema()](#get_tool_schema)
- [Data Models](#data-models)
  - [MCISchema](#mcischema)
  - [Tool](#tool)
  - [ExecutionResult](#executionresult)
  - [Metadata](#metadata)
- [Execution Configurations](#execution-configurations)
  - [HTTPExecutionConfig](#httpexecutionconfig)
  - [CLIExecutionConfig](#cliexecutionconfig)
  - [FileExecutionConfig](#fileexecutionconfig)
  - [TextExecutionConfig](#textexecutionconfig)
- [Authentication Models](#authentication-models)
  - [ApiKeyAuth](#apikeyauth)
  - [BearerAuth](#bearerauth)
  - [BasicAuth](#basicauth)
  - [OAuth2Auth](#oauth2auth)
- [Error Handling](#error-handling)

---

## MCIClient Class

The `MCIClient` class is the main entry point for the MCI Python adapter. It provides methods for loading, filtering, and executing MCI tools from a JSON schema file.

### Initialization

#### `MCIClient(json_file_path, env_vars=None)`

Initialize the MCI client with a schema file and optional environment variables.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `json_file_path` | `str` | Yes | Path to the MCI JSON schema file |
| `env_vars` | `dict[str, Any]` | No | Environment variables for template substitution (default: `{}`) |

**Raises:**

- `MCIClientError` - If the schema file cannot be loaded or parsed

**Example:**

```python
from mcipy import MCIClient

# Initialize without environment variables
client = MCIClient(json_file_path="example.mci.json")

# Initialize with environment variables
client = MCIClient(
    json_file_path="example.mci.json",
    env_vars={
        "API_KEY": "your-secret-key",
        "USERNAME": "demo_user",
        "BEARER_TOKEN": "token-123"
    }
)
```

**Success Response:**

Returns an initialized `MCIClient` instance ready to use.

**Error Response:**

```python
# Raises MCIClientError
MCIClientError: Failed to load schema from invalid.json: [Errno 2] No such file or directory: 'invalid.json'
```

---

### Methods

#### `tools()`

Get all available tools from the loaded schema.

**Method Signature:**

```python
def tools(self) -> list[Tool]
```

**Parameters:**

None

**Returns:**

| Type | Description |
|------|-------------|
| `list[Tool]` | List of all Tool objects in the schema |

**Example:**

```python
from mcipy import MCIClient

client = MCIClient(json_file_path="example.mci.json")
all_tools = client.tools()

for tool in all_tools:
    print(f"Tool: {tool.name} - {tool.description}")
```

**Success Response:**

```python
[
    Tool(
        name="get_weather",
        title="Get Weather Information",
        description="Fetch current weather information for a location",
        inputSchema={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or location"}
            },
            "required": ["location"]
        },
        execution=HTTPExecutionConfig(...)
    ),
    Tool(
        name="create_report",
        title="Create Report",
        description="Create a new report using HTTP POST request",
        inputSchema={...},
        execution=HTTPExecutionConfig(...)
    )
]
```

**Error Response:**

No errors - always returns a list (may be empty if no tools defined).

---

#### `only()`

Filter tools to include only specified tools by name.

**Method Signature:**

```python
def only(self, tool_names: list[str]) -> list[Tool]
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_names` | `list[str]` | Yes | List of tool names to include |

**Returns:**

| Type | Description |
|------|-------------|
| `list[Tool]` | Filtered list of Tool objects matching the specified names |

**Example:**

```python
from mcipy import MCIClient

client = MCIClient(json_file_path="example.mci.json")

# Get only weather-related tools
weather_tools = client.only(["get_weather", "get_forecast"])

for tool in weather_tools:
    print(f"Weather tool: {tool.name}")
```

**Success Response:**

```python
[
    Tool(
        name="get_weather",
        title="Get Weather Information",
        description="Fetch current weather information for a location",
        inputSchema={...},
        execution=HTTPExecutionConfig(...)
    ),
    Tool(
        name="get_forecast",
        title="Get Weather Forecast",
        description="Get weather forecast for the next 7 days",
        inputSchema={...},
        execution=HTTPExecutionConfig(...)
    )
]
```

**Error Response:**

No errors - returns empty list if no tools match the specified names.

---

#### `without()`

Filter tools to exclude specified tools by name.

**Method Signature:**

```python
def without(self, tool_names: list[str]) -> list[Tool]
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_names` | `list[str]` | Yes | List of tool names to exclude |

**Returns:**

| Type | Description |
|------|-------------|
| `list[Tool]` | Filtered list of Tool objects excluding the specified names |

**Example:**

```python
from mcipy import MCIClient

client = MCIClient(json_file_path="example.mci.json")

# Get all tools except dangerous ones
safe_tools = client.without(["delete_data", "admin_tools"])

for tool in safe_tools:
    print(f"Safe tool: {tool.name}")
```

**Success Response:**

```python
[
    Tool(
        name="get_weather",
        title="Get Weather Information",
        description="Fetch current weather information for a location",
        inputSchema={...},
        execution=HTTPExecutionConfig(...)
    ),
    Tool(
        name="search_data",
        title="Search Data",
        description="Search for data in the database",
        inputSchema={...},
        execution=HTTPExecutionConfig(...)
    )
    # delete_data and admin_tools are excluded
]
```

**Error Response:**

No errors - returns all tools if specified names don't exist.

---

#### `execute()`

Execute a tool by name with the provided properties.

**Method Signature:**

```python
def execute(self, tool_name: str, properties: dict[str, Any] | None = None) -> ExecutionResult
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_name` | `str` | Yes | Name of the tool to execute |
| `properties` | `dict[str, Any]` | No | Properties/parameters to pass to the tool (default: `{}`) |

**Returns:**

| Type | Description |
|------|-------------|
| `ExecutionResult` | Result object with success/error status and content |

**Raises:**

- `MCIClientError` - If tool not found or execution fails with validation error

**Example:**

```python
from mcipy import MCIClient

client = MCIClient(
    json_file_path="example.mci.json",
    env_vars={"API_KEY": "your-secret-key"}
)

# Execute a tool with properties
result = client.execute(
    tool_name="get_weather",
    properties={"location": "New York"}
)

# Handle result
if result.isError:
    print(f"Error: {result.error}")
else:
    print(f"Success: {result.content}")
    if result.metadata:
        print(f"Metadata: {result.metadata}")
```

**Success Response:**

```python
ExecutionResult(
    isError=False,
    content={
        "location": "New York",
        "temperature": 72,
        "conditions": "Sunny",
        "humidity": 45
    },
    error=None,
    metadata={
        "status_code": 200,
        "execution_time_ms": 150
    }
)
```

**Error Response - Tool Not Found:**

```python
# Raises MCIClientError
MCIClientError: Tool not found: invalid_tool_name
```

**Error Response - Execution Error:**

```python
ExecutionResult(
    isError=True,
    content=None,
    error="HTTP request failed: 404 Not Found",
    metadata={
        "status_code": 404,
        "execution_time_ms": 75
    }
)
```

**Error Response - Network Error:**

```python
ExecutionResult(
    isError=True,
    content=None,
    error="Connection timeout after 5000ms",
    metadata=None
)
```

---

#### `list_tools()`

List available tool names as strings.

**Method Signature:**

```python
def list_tools(self) -> list[str]
```

**Parameters:**

None

**Returns:**

| Type | Description |
|------|-------------|
| `list[str]` | List of tool names (strings) |

**Example:**

```python
from mcipy import MCIClient

client = MCIClient(json_file_path="example.mci.json")
tool_names = client.list_tools()

print(f"Available tools: {tool_names}")
```

**Success Response:**

```python
["get_weather", "create_report", "search_files", "load_file", "generate_text"]
```

**Error Response:**

No errors - returns empty list if no tools defined.

---

#### `get_tool_schema()`

Get a tool's input schema (JSON Schema format).

**Method Signature:**

```python
def get_tool_schema(self, tool_name: str) -> dict[str, Any]
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_name` | `str` | Yes | Name of the tool |

**Returns:**

| Type | Description |
|------|-------------|
| `dict[str, Any]` | Tool's input schema as a dictionary (or empty dict if no schema) |

**Raises:**

- `MCIClientError` - If tool not found

**Example:**

```python
from mcipy import MCIClient

client = MCIClient(json_file_path="example.mci.json")
schema = client.get_tool_schema("get_weather")

print(f"Schema: {schema}")
```

**Success Response:**

```python
{
    "type": "object",
    "properties": {
        "location": {
            "type": "string",
            "description": "City name or location"
        },
        "unit": {
            "type": "string",
            "description": "Temperature unit (celsius or fahrenheit)",
            "enum": ["celsius", "fahrenheit"]
        }
    },
    "required": ["location"]
}
```

**Success Response - No Schema:**

```python
{}  # Empty dict if tool has no input schema
```

**Error Response:**

```python
# Raises MCIClientError
MCIClientError: Tool not found: invalid_tool_name
```

---

## Data Models

### MCISchema

Top-level MCI schema representing the complete MCI context file.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schemaVersion` | `str` | Yes | Schema version (e.g., "1.0") |
| `metadata` | `Metadata` | No | Optional metadata about the tool collection |
| `tools` | `list[Tool]` | Yes | List of tool definitions |

**Example:**

```python
{
    "schemaVersion": "1.0",
    "metadata": {
        "name": "Example MCI Tools",
        "description": "Example tool collection",
        "version": "1.0.0",
        "license": "MIT",
        "authors": ["MCI Team"]
    },
    "tools": [
        {
            "name": "get_weather",
            "title": "Get Weather",
            "description": "Get weather information",
            "inputSchema": {...},
            "execution": {...}
        }
    ]
}
```

---

### Tool

Individual tool definition with name, description, input schema, and execution configuration.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Unique identifier for the tool |
| `title` | `str` | No | Human-readable title |
| `description` | `str` | No | Description of what the tool does |
| `inputSchema` | `dict[str, Any]` | No | JSON Schema defining expected input properties |
| `execution` | `HTTPExecutionConfig` \| `CLIExecutionConfig` \| `FileExecutionConfig` \| `TextExecutionConfig` | Yes | Execution configuration (determines how tool is executed) |

**Example:**

```python
{
    "name": "get_weather",
    "title": "Get Weather Information",
    "description": "Fetch current weather information for a location",
    "inputSchema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or location"
            }
        },
        "required": ["location"]
    },
    "execution": {
        "type": "http",
        "method": "GET",
        "url": "https://api.example.com/weather",
        "params": {
            "location": "{{props.location}}"
        }
    }
}
```

---

### ExecutionResult

Result format returned from tool execution.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isError` | `bool` | Yes | Whether an error occurred during execution |
| `content` | `Any` | No | Result content (None if error) |
| `error` | `str` | No | Error message (None if success) |
| `metadata` | `dict[str, Any]` | No | Additional metadata (e.g., status_code, execution_time_ms) |

**Example - Success:**

```python
ExecutionResult(
    isError=False,
    content={
        "location": "New York",
        "temperature": 72,
        "conditions": "Sunny"
    },
    error=None,
    metadata={
        "status_code": 200,
        "execution_time_ms": 150
    }
)
```

**Example - Error:**

```python
ExecutionResult(
    isError=True,
    content=None,
    error="HTTP request failed: 404 Not Found",
    metadata={
        "status_code": 404,
        "execution_time_ms": 75
    }
)
```

**Example - Text Content:**

```python
ExecutionResult(
    isError=False,
    content="Hello, World!",
    error=None,
    metadata=None
)
```

**Example - File Content:**

```python
ExecutionResult(
    isError=False,
    content="File content with template: user@example.com",
    error=None,
    metadata=None
)
```

---

### Metadata

Optional metadata about the MCI tool collection.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | No | Name of the tool collection |
| `description` | `str` | No | Description of the collection |
| `version` | `str` | No | Version number (e.g., "1.0.0") |
| `license` | `str` | No | License type (e.g., "MIT") |
| `authors` | `list[str]` | No | List of author names |

**Example:**

```python
{
    "name": "Weather Tools",
    "description": "Collection of weather-related tools",
    "version": "1.0.0",
    "license": "MIT",
    "authors": ["Alice Smith", "Bob Jones"]
}
```

---

## Execution Configurations

### HTTPExecutionConfig

Configuration for HTTP-based tool execution.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `ExecutionType` | Yes | `"http"` | Execution type identifier |
| `method` | `str` | No | `"GET"` | HTTP method (GET, POST, PUT, DELETE, etc.) |
| `url` | `str` | Yes | - | URL endpoint for the request |
| `headers` | `dict[str, str]` | No | `None` | HTTP headers |
| `auth` | `AuthConfig` | No | `None` | Authentication configuration |
| `params` | `dict[str, Any]` | No | `None` | Query parameters |
| `body` | `HTTPBodyConfig` | No | `None` | Request body configuration |
| `timeout_ms` | `int` | No | `30000` | Request timeout in milliseconds |
| `retries` | `RetryConfig` | No | `None` | Retry configuration |

**Example - GET Request:**

```python
{
    "type": "http",
    "method": "GET",
    "url": "https://api.example.com/weather",
    "params": {
        "location": "{{props.location}}",
        "units": "metric"
    },
    "headers": {
        "Accept": "application/json"
    },
    "timeout_ms": 5000
}
```

**Example - POST Request with Authentication:**

```python
{
    "type": "http",
    "method": "POST",
    "url": "https://api.example.com/reports",
    "headers": {
        "Content-Type": "application/json"
    },
    "auth": {
        "type": "bearer",
        "token": "{{env.BEARER_TOKEN}}"
    },
    "body": {
        "type": "json",
        "content": {
            "title": "{{props.title}}",
            "content": "{{props.content}}"
        }
    },
    "timeout_ms": 10000,
    "retries": {
        "attempts": 3,
        "backoff_ms": 1000
    }
}
```

---

### CLIExecutionConfig

Configuration for command-line tool execution.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `ExecutionType` | Yes | `"cli"` | Execution type identifier |
| `command` | `str` | Yes | - | Command to execute |
| `args` | `list[str]` | No | `None` | Command arguments |
| `flags` | `dict[str, FlagConfig]` | No | `None` | Command flags configuration |
| `cwd` | `str` | No | `None` | Working directory for command execution |
| `timeout_ms` | `int` | No | `30000` | Execution timeout in milliseconds |

**Example - Simple Command:**

```python
{
    "type": "cli",
    "command": "ls",
    "args": ["-la", "/home/user"],
    "timeout_ms": 5000
}
```

**Example - Command with Flags:**

```python
{
    "type": "cli",
    "command": "grep",
    "args": ["-r", "{{props.pattern}}"],
    "flags": {
        "--color": {
            "from": "props.color",
            "type": "boolean"
        }
    },
    "cwd": "/home/user/projects",
    "timeout_ms": 10000
}
```

---

### FileExecutionConfig

Configuration for file reading and templating.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `ExecutionType` | Yes | `"file"` | Execution type identifier |
| `path` | `str` | Yes | - | Path to the file to read |
| `enableTemplating` | `bool` | No | `True` | Whether to process template placeholders in file content |

**Example - Read File with Templating:**

```python
{
    "type": "file",
    "path": "/home/user/templates/email.txt",
    "enableTemplating": true
}
```

**Example - Read File Without Templating:**

```python
{
    "type": "file",
    "path": "/home/user/data/config.json",
    "enableTemplating": false
}
```

---

### TextExecutionConfig

Configuration for simple text template execution.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `ExecutionType` | Yes | `"text"` | Execution type identifier |
| `text` | `str` | Yes | - | Text template with placeholder support |

**Example:**

```python
{
    "type": "text",
    "text": "Hello {{props.name}}! Your email is {{env.USER_EMAIL}}."
}
```

**Execution Result:**

```python
# With properties={"name": "Alice"} and env_vars={"USER_EMAIL": "alice@example.com"}
ExecutionResult(
    isError=False,
    content="Hello Alice! Your email is alice@example.com.",
    error=None,
    metadata=None
)
```

---

## Authentication Models

### ApiKeyAuth

API Key authentication configuration.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `str` | Yes | `"apiKey"` | Authentication type |
| `in` | `str` | Yes | - | Where to place the key: "header" or "query" |
| `name` | `str` | Yes | - | Name of the header or query parameter |
| `value` | `str` | Yes | - | API key value (supports templates) |

**Example - Header-based:**

```python
{
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Key",
    "value": "{{env.API_KEY}}"
}
```

**Example - Query parameter:**

```python
{
    "type": "apiKey",
    "in": "query",
    "name": "api_key",
    "value": "{{env.API_KEY}}"
}
```

---

### BearerAuth

Bearer token authentication configuration.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `str` | Yes | `"bearer"` | Authentication type |
| `token` | `str` | Yes | - | Bearer token value (supports templates) |

**Example:**

```python
{
    "type": "bearer",
    "token": "{{env.BEARER_TOKEN}}"
}
```

---

### BasicAuth

Basic authentication (username/password) configuration.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `str` | Yes | `"basic"` | Authentication type |
| `username` | `str` | Yes | - | Username (supports templates) |
| `password` | `str` | Yes | - | Password (supports templates) |

**Example:**

```python
{
    "type": "basic",
    "username": "{{env.USERNAME}}",
    "password": "{{env.PASSWORD}}"
}
```

---

### OAuth2Auth

OAuth2 authentication configuration.

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `str` | Yes | `"oauth2"` | Authentication type |
| `flow` | `str` | Yes | - | OAuth2 flow type (e.g., "clientCredentials") |
| `tokenUrl` | `str` | Yes | - | Token endpoint URL |
| `clientId` | `str` | Yes | - | OAuth2 client ID |
| `clientSecret` | `str` | Yes | - | OAuth2 client secret (supports templates) |
| `scopes` | `list[str]` | No | `None` | Optional OAuth2 scopes |

**Example:**

```python
{
    "type": "oauth2",
    "flow": "clientCredentials",
    "tokenUrl": "https://auth.example.com/oauth/token",
    "clientId": "my-client-id",
    "clientSecret": "{{env.OAUTH_CLIENT_SECRET}}",
    "scopes": ["read:data", "write:data"]
}
```

---

## Error Handling

The MCI Python adapter provides consistent error handling across all operations.

### Exception Types

#### MCIClientError

Raised by `MCIClient` methods for client-level errors.

**Common Causes:**

- Schema file not found or invalid
- Tool not found
- Invalid tool execution

**Example:**

```python
from mcipy import MCIClient, MCIClientError

try:
    client = MCIClient(json_file_path="nonexistent.json")
except MCIClientError as e:
    print(f"Client error: {e}")
    # Output: Client error: Failed to load schema from nonexistent.json: [Errno 2] No such file or directory
```

### ExecutionResult Error Format

Execution errors are returned as `ExecutionResult` objects with `isError=True`.

**Error Fields:**

| Field | Description |
|-------|-------------|
| `isError` | Always `True` for errors |
| `content` | Always `None` for errors |
| `error` | Human-readable error message |
| `metadata` | Optional additional error context |

**Example Error Scenarios:**

**HTTP Request Failed:**

```python
result = client.execute("get_weather", {"location": "InvalidCity"})
# ExecutionResult(
#     isError=True,
#     content=None,
#     error="HTTP request failed: 404 Not Found",
#     metadata={"status_code": 404, "execution_time_ms": 75}
# )
```

**Connection Timeout:**

```python
result = client.execute("slow_api", {})
# ExecutionResult(
#     isError=True,
#     content=None,
#     error="Connection timeout after 30000ms",
#     metadata=None
# )
```

**CLI Command Failed:**

```python
result = client.execute("invalid_command", {})
# ExecutionResult(
#     isError=True,
#     content=None,
#     error="Command failed with exit code 127: command not found",
#     metadata={"exit_code": 127}
# )
```

**File Not Found:**

```python
result = client.execute("read_config", {})
# ExecutionResult(
#     isError=True,
#     content=None,
#     error="File not found: /path/to/config.json",
#     metadata=None
# )
```

**Template Variable Missing:**

```python
# If {{env.MISSING_VAR}} is referenced but not provided
result = client.execute("template_tool", {})
# ExecutionResult(
#     isError=True,
#     content=None,
#     error="Template variable not found: env.MISSING_VAR",
#     metadata=None
# )
```

### Error Handling Best Practices

**Check isError Flag:**

```python
result = client.execute("get_weather", {"location": "New York"})

if result.isError:
    print(f"Error occurred: {result.error}")
    if result.metadata:
        print(f"Additional context: {result.metadata}")
else:
    print(f"Success: {result.content}")
```

**Try-Except for Client Errors:**

```python
try:
    client = MCIClient(json_file_path="example.mci.json")
    result = client.execute("get_weather", {"location": "New York"})
    
    if result.isError:
        # Handle execution errors
        print(f"Execution failed: {result.error}")
    else:
        # Process successful result
        print(f"Weather data: {result.content}")
        
except MCIClientError as e:
    # Handle client-level errors (tool not found, invalid schema, etc.)
    print(f"Client error: {e}")
```

**Validate Tools Before Execution:**

```python
client = MCIClient(json_file_path="example.mci.json")

# Check if tool exists
available_tools = client.list_tools()
if "get_weather" in available_tools:
    result = client.execute("get_weather", {"location": "New York"})
else:
    print("Tool 'get_weather' not available")
```

---

## Complete Usage Example

Here's a comprehensive example demonstrating all major features:

```python
from mcipy import MCIClient, MCIClientError

# Initialize client with environment variables
try:
    client = MCIClient(
        json_file_path="example.mci.json",
        env_vars={
            "API_KEY": "your-secret-key",
            "BEARER_TOKEN": "bearer-token-123",
            "USERNAME": "demo_user"
        }
    )
except MCIClientError as e:
    print(f"Failed to initialize client: {e}")
    exit(1)

# List all available tools
print("Available tools:")
for tool_name in client.list_tools():
    print(f"  - {tool_name}")

# Get detailed tool information
all_tools = client.tools()
for tool in all_tools:
    print(f"\nTool: {tool.name}")
    print(f"  Title: {tool.title}")
    print(f"  Description: {tool.description}")

# Filter tools
weather_tools = client.only(["get_weather", "get_forecast"])
print(f"\nWeather tools: {[t.name for t in weather_tools]}")

safe_tools = client.without(["delete_data", "admin_tools"])
print(f"Safe tools: {[t.name for t in safe_tools]}")

# Get tool schema
try:
    schema = client.get_tool_schema("get_weather")
    print(f"\nWeather tool schema: {schema}")
except MCIClientError as e:
    print(f"Error getting schema: {e}")

# Execute a tool
result = client.execute(
    tool_name="get_weather",
    properties={"location": "New York"}
)

if result.isError:
    print(f"\nExecution failed: {result.error}")
    if result.metadata:
        print(f"Error metadata: {result.metadata}")
else:
    print(f"\nExecution successful!")
    print(f"Content: {result.content}")
    if result.metadata:
        print(f"Metadata: {result.metadata}")
```

---

## Template Syntax

MCI supports template placeholders for dynamic value substitution:

- `{{props.fieldName}}` - Access properties passed to execute()
- `{{env.VARIABLE_NAME}}` - Access environment variables
- `{{input.fieldName}}` - **Deprecated** alias for props (use `props` instead)

> **Note:** `{{input.fieldName}}` is supported for backward compatibility but is deprecated. Use `{{props.fieldName}}` in all new code.
**Example:**

```json
{
    "execution": {
        "type": "http",
        "url": "https://api.example.com/users/{{props.userId}}",
        "headers": {
            "Authorization": "Bearer {{env.API_TOKEN}}"
        }
    }
}
```

With execution:

```python
result = client.execute(
    "get_user",
    properties={"userId": "12345"}
)
# Resolves to: https://api.example.com/users/12345
```

---

## Notes

- All methods are synchronous (blocking) - execution waits for completion
- Environment variables should be provided during initialization, not at execution time
- Templates are processed before execution using a simple `{{}}` placeholder substitution system (not full Jinja2 syntax)
- HTTP responses are automatically parsed as JSON when possible
- CLI commands capture both stdout and stderr
- File paths can be relative or absolute
- Timeout values are in milliseconds
- All string fields support template substitution unless explicitly disabled

---

## See Also

- [Quickstart Guide](quickstart.md) - Getting started with MCI
- [Schema Reference](schema_reference.md) - Complete JSON schema documentation
- [Examples](../examples/) - Example tool definitions and usage patterns
