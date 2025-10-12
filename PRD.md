# Product Requirements Document (PRD)

# Model Context Interface (MCI) v1

## Overview

MCI is an open-source, platform-agnostic system for defining and executing AI agent tools through a standardized JSON schema. It allows synchronous execution of tools via adapters in multiple programming languages, initially focusing on Python (with the goal of expanding to PHP, Go, and Node.js). MCI aims to offer a secure, lightweight alternative to MCP, eliminating dependency on third-party code and providing fine-grained control over tool sets.

- **Version:** v1.0.0 (initial public release)
- **Owner / PM:** Revaz Ghambarashvili (aka MaestroError)
- **Drivers:** Lightweight alternative to MCP, sync-first, schema-defined context, language-agnostic via adapters
- **Primary Outcomes:** Enable agents to call tools described in a static JSON file; execute synchronously via adapter; reduce supply-chain risk; reduce token cost by scoping minimal toolsets.

---

## Goals **(v1)**

- JSON **schema v1** that defines Tools with properties and Execution.
- **HTTP** and **CLI** execution types with robust parameter templating.
- **Python adapter** that loads the JSON, validates, executes synchronously, returns structured results.
- Minimal, clear **docs** (Quickstart, Schema Reference, Examples).
- Security posture: **env-only secrets**

## Primary Use Cases

1. Wrap an HTTP API.
2. Wrap a CLI utility.
3. Minimal toolset per agent.
4. Portable definitions.

### Usage Example

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

## Functional Requirements

### FR-1: JSON Tool Definition Schema

### JSON Schema v1

- Formal JSON Schema (Draft 2020‑12) for an **MCI context**.
- Platform agnostic — works identically on Linux, macOS, and Windows.
- Top‑level keys:
  - `schemaVersion` (string, SemVer; e.g., "1.0")
  - `metadata` (object; optional: `name`, `description`, `version`, `license`, `authors[]`)
  - `tools[]`: Array of Objects including tool definition (check example below)

Each tool is defined as:

```json
{
  "name": "get_weather",
  "title": "Weather Information Provider",
  "description": "Get current weather information for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or zip code"
      }
    },
    "required": ["location"]
  },
  "execution": {}
}
```

### FR-2: Execution Types

Initial release supports:

- **HTTP requests**
- **CLI commands**
- **File execution**
- **Text execution**

### FR‑3: HTTP Execution (Detailed)

- Keys:
  - `type`: "http"
  - `auth` (optional)
  - `method`: GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS
  - `url`: templatable string
  - `headers`: object with templating
  - `query`: key-value pairs
  - `body`: `{ "json": {...} }` | `{ "form": {...} }` | `{ "raw": "string" }`
  - `timeout_ms`: integer
  - `retries` (optional): `{ "attempts": 1, "backoff_ms": 500 }`

### HTTP Request Execution Schema Example (JSON body, API Key Auth)

```json
{
  "execution": {
    "type": "http",
    "method": "POST",
    "url": "https://api.example.com/weather",
    "headers": {
      "Accept": "application/json"
    },
    "auth": {
		  "type": "apiKey",
		  "in": "header",
		  "name": "X-API-Key",
		  "value": "{{env.API_KEY}}"
		}
    "body": {
      "type": "json",
      "content": {
        "location": "{{input.location}}"
      }
    }
  }
}
```

`auth.in` can be also a “query”

### HTTP Request Execution Schema Example (Form body, Bearer Token)

```json
{
  "execution": {
    "type": "http",
    "method": "POST",
    "url": "https://api.example.com/weather",
    "auth": {
      "type": "bearer",
      "token": "{{env.BERERTOA_KEN}}"
    },
    "body": {
      "type": "form",
      "content": {
        "location": "{{input.location}}",
        "unit": "celsius"
      }
    }
  }
}
```

### HTTP Request Execution Schema Example (Raw body, Basic Auth)

```json
{
  "execution": {
    "type": "http",
    "method": "POST",
    "url": "https://api.example.com/weather",
    "auth": {
      "type": "basic",
      "username": "{{env.USERNAME}}",
      "password": "{{env.PASSWORD}}"
    },
    "body": {
      "type": "raw",
      "content": "location={{input.location}}&unit=celsius"
    }
  }
}
```

### HTTP Request Execution Schema Example (OAuth2 Client Credentials)

```json
{
  "type": "http",
  "method": "GET",
  "url": "https://api.example.com/weather",
  "auth": {
    "type": "oauth2",
    "flow": "clientCredentials",
    "tokenUrl": "https://auth.example.com/token",
    "clientId": "{{env.CLIENT_ID}}",
    "clientSecret": "{{env.CLIENT_SECRET}}",
    "scopes": ["read:weather"]
  },
  "params": {
    "location": "{{input.location}}"
  }
}
```

### FR‑4: CLI Execution (Detailed)

- Keys:
  - `type`: "cli"
  - `command`: string
  - `args`: array of fixed arguments
  - `flags`: object mapping flags to property sources
  - `cwd`: templatable string
  - `timeout_ms`: integer

### CLI Command Execution Schema Example

```json
{
  "type": "cli",
  "command": "grep",
  "args": ["-n"],
  "flags": {
    "-i": { "from": "props.ignore_case", "type": "boolean" },
    "--file": { "from": "props.file", "type": "value" }
  },
  "cwd": "{{props.directory}}",
  "timeout_ms": 8000
}
```

### FR-5: File read

- `type`: "file"
- `path`: string
- `enableTemplating`: boolean

### File Execution Schema Example

```json
{
  "execution": {
    "type": "file",
    "path": "./templates/report-{{ properties.report_id }}.txt",
    "enableTemplating": true
  }
}
```

- **Behavior**: Adapter reads the file, replaces placeholders like `{{props.propertyName}}` and `{{env.VAR_NAME}}` and do all other templating.

### FR-6: Text return

- `type`: "text"
- `text`: string

### Text Execution Schema Example

```json
{
  "execution": {
    "type": "text",
    "text": "Report generated for {{input.username}} on {{env.CURRENT_DATE}}"
  }
}
```

- **Behavior**: Adapter directly processes the given string with placeholder substitution.

---

## Output Format

Successful:

```json
{
  "isError": false,
  "content": [
    {
      "type": "text",
      "text": "Current weather in New York:\nTemperature: 72°F\nConditions: Partly cloudy"
    }
  ]
}
```

```json
{
  "isError": true,
  "error": "Error message"
}
```

Note: Include metadata field for infos like http status code, CLI exit code, etc.

---

## Templating

Basic templating should be enabled in parts where we have templating such as execution part, headers and etc.
Loops and Control blocks should be applied in large text parts, like text execution and while parsing a file in file execution flow.

- **Basic**: replaces placeholders like `{{props.propertyName}}` and `{{env.VAR_NAME}}` with values.
- **Loops**: For array and object props or env variables, Adapter should be able to parse `@for` -> `@endfor` and `@foreach` -> `@endforeach`
- **Control Blocks**: Adapter should be able to use control blocks: `@if` -> `@elseif` -> `@else` -> `@endif`

## Non-Functional Requirements

- Platform-agnostic JSON schema.
- Secure execution: Environment variables and secrets are passed via adapter (`{{env.VAR_NAME}}`).
- Properties: Tool properties in templating, including execution JSON part and files parsed should be accessible as `props.propertyName`.
- Adapters handle authentication, input parsing, execution, and result formatting.

### Adapter API

Python package should support reading JSON file, filtering it with `without` and `only` methods. ENV variables should be passed on initialization alongside with JSON file path. Properties should be passed via `execute` method.

## Testing Strategy

- Schema tests, templating tests, HTTP, HTTP Auth tests, CLI execution tests, security, cross‑platform.

---

## Other concerns

- **Execution timeout**: Default 30s, configurable per tool.
- **Error handling**: Always return `isError: true` with `error` content;
- **Schema versioning**: Start at `v1.0.0`, bump minor for backward-compatible, major for breaking changes.
- **Jinja**: Add templating engine choice feature and add "built-in" & "Jinja2" as options
