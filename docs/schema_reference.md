# MCI Schema Reference

This document provides a complete reference for the Model Context Interface (MCI) JSON schema v1. It describes all fields, types, execution configurations, authentication options, and templating syntax supported by the MCI Python adapter.

## Table of Contents

- [Overview](#overview)
- [Top-Level Schema Structure](#top-level-schema-structure)
- [Metadata](#metadata)
- [Tool Definition](#tool-definition)
- [Execution Types](#execution-types)
  - [HTTP Execution](#http-execution)
  - [CLI Execution](#cli-execution)
  - [File Execution](#file-execution)
  - [Text Execution](#text-execution)
- [Authentication](#authentication)
  - [API Key Authentication](#api-key-authentication)
  - [Bearer Token Authentication](#bearer-token-authentication)
  - [Basic Authentication](#basic-authentication)
  - [OAuth2 Authentication](#oauth2-authentication)
- [Templating Syntax](#templating-syntax)
  - [Basic Placeholders](#basic-placeholders)
  - [For Loops](#for-loops)
  - [Foreach Loops](#foreach-loops)
  - [Conditional Blocks](#conditional-blocks)
- [Execution Result Format](#execution-result-format)

---

## Overview

MCI (Model Context Interface) uses a JSON schema to define tools that AI agents can execute. Each tool specifies:

- What it does (metadata and description)
- What inputs it accepts (JSON Schema)
- How to execute it (execution configuration)

The schema is designed to be platform-agnostic, secure (secrets via environment variables), and supports multiple execution types.

**Schema Version**: `1.0`

---

## Top-Level Schema Structure

The root MCI context file has three main fields:

| Field           | Type   | Required     | Description                                    |
| --------------- | ------ | ------------ | ---------------------------------------------- |
| `schemaVersion` | string | **Required** | MCI schema version (e.g., `"1.0"`)             |
| `metadata`      | object | Optional     | Descriptive metadata about the tool collection |
| `tools`         | array  | **Required** | Array of tool definitions                      |

### Example

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "My API Tools",
    "description": "Tools for interacting with my API",
    "version": "1.0.0",
    "license": "MIT",
    "authors": ["John Doe"]
  },
  "tools": []
}
```

---

## Metadata

Optional metadata about the tool collection.

| Field         | Type   | Required | Description                                        |
| ------------- | ------ | -------- | -------------------------------------------------- |
| `name`        | string | Optional | Name of the tool collection                        |
| `description` | string | Optional | Description of the tool collection                 |
| `version`     | string | Optional | Version of the tool collection (e.g., SemVer)      |
| `license`     | string | Optional | License identifier (e.g., `"MIT"`, `"Apache-2.0"`) |
| `authors`     | array  | Optional | Array of author names                              |

### Example

```json
{
  "name": "Weather API Tools",
  "description": "Tools for fetching weather information",
  "version": "1.2.0",
  "license": "MIT",
  "authors": ["Weather Team", "API Team"]
}
```

---

## Tool Definition

Each tool in the `tools` array represents a single executable operation.

| Field         | Type   | Required     | Description                                                       |
| ------------- | ------ | ------------ | ----------------------------------------------------------------- |
| `name`        | string | **Required** | Unique identifier for the tool                                    |
| `title`       | string | Optional     | Human-readable title                                              |
| `description` | string | Optional     | Description of what the tool does                                 |
| `inputSchema` | object | Optional     | JSON Schema describing expected inputs                            |
| `execution`   | object | **Required** | Execution configuration (see [Execution Types](#execution-types)) |

### Example

```json
{
  "name": "get_weather",
  "title": "Get Weather Information",
  "description": "Fetch current weather for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or zip code"
      },
      "units": {
        "type": "string",
        "enum": ["metric", "imperial"],
        "default": "metric"
      }
    },
    "required": ["location"]
  },
  "execution": {
    "type": "http",
    "method": "GET",
    "url": "https://api.weather.com/v1/current",
    "params": {
      "location": "{{props.location}}",
      "units": "{{props.units}}"
    }
  }
}
```

---

## Execution Types

MCI supports four execution types: `http`, `cli`, `file`, and `text`. The `type` field in the `execution` object determines which executor is used.

### HTTP Execution

Execute HTTP requests to external APIs.

**Type**: `"http"`

#### Fields

| Field        | Type    | Required     | Default | Description                                                             |
| ------------ | ------- | ------------ | ------- | ----------------------------------------------------------------------- |
| `type`       | string  | **Required** | -       | Must be `"http"`                                                        |
| `method`     | string  | Optional     | `"GET"` | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS` |
| `url`        | string  | **Required** | -       | Target URL (supports templating)                                        |
| `headers`    | object  | Optional     | -       | HTTP headers as key-value pairs (supports templating)                   |
| `auth`       | object  | Optional     | -       | Authentication configuration (see [Authentication](#authentication))    |
| `params`     | object  | Optional     | -       | Query parameters as key-value pairs (supports templating)               |
| `body`       | object  | Optional     | -       | Request body configuration                                              |
| `timeout_ms` | integer | Optional     | `30000` | Request timeout in milliseconds (must be ≥ 0)                           |
| `retries`    | object  | Optional     | -       | Retry configuration                                                     |

#### Body Configuration

The `body` field defines the request body:

| Field     | Type          | Required     | Description                                         |
| --------- | ------------- | ------------ | --------------------------------------------------- |
| `type`    | string        | **Required** | Body type: `"json"`, `"form"`, or `"raw"`           |
| `content` | object/string | **Required** | Body content (object for json/form, string for raw) |

#### Retry Configuration

The `retries` field configures retry behavior:

| Field        | Type    | Required | Default | Description                                 |
| ------------ | ------- | -------- | ------- | ------------------------------------------- |
| `attempts`   | integer | Optional | `1`     | Number of retry attempts (must be ≥ 1)      |
| `backoff_ms` | integer | Optional | `500`   | Backoff delay in milliseconds (must be ≥ 0) |

#### Examples

**GET Request with Query Parameters**

```json
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

**POST Request with JSON Body**

```json
{
  "type": "http",
  "method": "POST",
  "url": "https://api.example.com/reports",
  "headers": {
    "Content-Type": "application/json",
    "Accept": "application/json"
  },
  "body": {
    "type": "json",
    "content": {
      "title": "{{props.title}}",
      "content": "{{props.content}}",
      "timestamp": "{{env.CURRENT_TIMESTAMP}}"
    }
  },
  "timeout_ms": 10000
}
```

**POST Request with Form Data**

```json
{
  "type": "http",
  "method": "POST",
  "url": "https://api.example.com/upload",
  "body": {
    "type": "form",
    "content": {
      "filename": "{{props.filename}}",
      "category": "documents"
    }
  }
}
```

**Request with Retry Logic**

```json
{
  "type": "http",
  "method": "GET",
  "url": "https://api.example.com/data",
  "retries": {
    "attempts": 3,
    "backoff_ms": 1000
  }
}
```

---

### CLI Execution

Execute command-line tools and scripts.

**Type**: `"cli"`

#### Fields

| Field        | Type    | Required     | Default | Description                                     |
| ------------ | ------- | ------------ | ------- | ----------------------------------------------- |
| `type`       | string  | **Required** | -       | Must be `"cli"`                                 |
| `command`    | string  | **Required** | -       | Command to execute                              |
| `args`       | array   | Optional     | -       | Fixed positional arguments                      |
| `flags`      | object  | Optional     | -       | Dynamic flags mapped from properties            |
| `cwd`        | string  | Optional     | -       | Working directory (supports templating)         |
| `timeout_ms` | integer | Optional     | `30000` | Execution timeout in milliseconds (must be ≥ 0) |

#### Flag Configuration

Each flag in the `flags` object has:

| Field  | Type   | Required     | Description                                 |
| ------ | ------ | ------------ | ------------------------------------------- |
| `from` | string | **Required** | Property path (e.g., `"props.ignore_case"`) |
| `type` | string | **Required** | Flag type: `"boolean"` or `"value"`         |

- **`boolean`**: Flag is included only if the property is truthy (e.g., `-i`)
- **`value`**: Flag is included with the property value (e.g., `--file=myfile.txt`)

#### Examples

**Basic CLI Command**

```json
{
  "type": "cli",
  "command": "grep",
  "args": ["-r", "-n"],
  "flags": {
    "-i": {
      "from": "props.ignore_case",
      "type": "boolean"
    }
  },
  "cwd": "{{props.directory}}",
  "timeout_ms": 8000
}
```

**CLI with Value Flags**

```json
{
  "type": "cli",
  "command": "convert",
  "args": ["input.png"],
  "flags": {
    "--resize": {
      "from": "props.size",
      "type": "value"
    },
    "--quality": {
      "from": "props.quality",
      "type": "value"
    }
  },
  "cwd": "/tmp"
}
```

---

### File Execution

Read and parse file contents with optional templating.

**Type**: `"file"`

#### Fields

| Field              | Type    | Required     | Default | Description                                  |
| ------------------ | ------- | ------------ | ------- | -------------------------------------------- |
| `type`             | string  | **Required** | -       | Must be `"file"`                             |
| `path`             | string  | **Required** | -       | File path (supports templating)              |
| `enableTemplating` | boolean | Optional     | `true`  | Whether to process templates in file content |

When `enableTemplating` is `true`, the file contents are processed with the full templating engine (basic placeholders, loops, and conditionals).

#### Examples

**Load Template File**

```json
{
  "type": "file",
  "path": "./templates/report-{{props.report_id}}.txt",
  "enableTemplating": true
}
```

**Load Raw File**

```json
{
  "type": "file",
  "path": "/etc/config/settings.json",
  "enableTemplating": false
}
```

---

### Text Execution

Return templated text directly.

**Type**: `"text"`

#### Fields

| Field  | Type   | Required     | Description                         |
| ------ | ------ | ------------ | ----------------------------------- |
| `type` | string | **Required** | Must be `"text"`                    |
| `text` | string | **Required** | Text template (supports templating) |

The text is processed with the full templating engine (basic placeholders, loops, and conditionals).

#### Examples

**Simple Message**

```json
{
  "type": "text",
  "text": "Hello {{props.username}}! This message was generated on {{env.CURRENT_DATE}}."
}
```

**Report with Conditionals**

```json
{
  "type": "text",
  "text": "Report for {{props.username}}\n@if(props.premium)Premium features enabled@else Standard features available @endif"
}
```

---

## Authentication

HTTP execution supports four authentication types: API Key, Bearer Token, Basic Auth, and OAuth2.

### API Key Authentication

Pass an API key in headers or query parameters.

**Type**: `"apiKey"`

#### Fields

| Field   | Type   | Required     | Description                                                      |
| ------- | ------ | ------------ | ---------------------------------------------------------------- |
| `type`  | string | **Required** | Must be `"apiKey"`                                               |
| `in`    | string | **Required** | Where to send the key: `"header"` or `"query"`                   |
| `name`  | string | **Required** | Header/query parameter name                                      |
| `value` | string | **Required** | API key value (supports templating, typically `{{env.API_KEY}}`) |

#### Examples

**API Key in Header**

```json
{
  "type": "http",
  "method": "GET",
  "url": "https://api.example.com/data",
  "auth": {
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Key",
    "value": "{{env.API_KEY}}"
  }
}
```

**API Key in Query Parameter**

```json
{
  "type": "http",
  "method": "GET",
  "url": "https://api.example.com/data",
  "auth": {
    "type": "apiKey",
    "in": "query",
    "name": "api_key",
    "value": "{{env.API_KEY}}"
  }
}
```

---

### Bearer Token Authentication

Pass a bearer token in the `Authorization` header.

**Type**: `"bearer"`

#### Fields

| Field   | Type   | Required     | Description                                                          |
| ------- | ------ | ------------ | -------------------------------------------------------------------- |
| `type`  | string | **Required** | Must be `"bearer"`                                                   |
| `token` | string | **Required** | Bearer token (supports templating, typically `{{env.BEARER_TOKEN}}`) |

#### Example

```json
{
  "type": "http",
  "method": "POST",
  "url": "https://api.example.com/reports",
  "auth": {
    "type": "bearer",
    "token": "{{env.BEARER_TOKEN}}"
  },
  "body": {
    "type": "json",
    "content": {
      "title": "{{props.title}}"
    }
  }
}
```

---

### Basic Authentication

Use HTTP Basic Authentication with username and password.

**Type**: `"basic"`

#### Fields

| Field      | Type   | Required     | Description                                                  |
| ---------- | ------ | ------------ | ------------------------------------------------------------ |
| `type`     | string | **Required** | Must be `"basic"`                                            |
| `username` | string | **Required** | Username (supports templating, typically `{{env.USERNAME}}`) |
| `password` | string | **Required** | Password (supports templating, typically `{{env.PASSWORD}}`) |

#### Example

```json
{
  "type": "http",
  "method": "GET",
  "url": "https://api.example.com/private-data",
  "auth": {
    "type": "basic",
    "username": "{{env.USERNAME}}",
    "password": "{{env.PASSWORD}}"
  }
}
```

---

### OAuth2 Authentication

Authenticate using OAuth2 client credentials flow.

**Type**: `"oauth2"`

#### Fields

| Field          | Type   | Required     | Description                                    |
| -------------- | ------ | ------------ | ---------------------------------------------- |
| `type`         | string | **Required** | Must be `"oauth2"`                             |
| `flow`         | string | **Required** | OAuth2 flow type (e.g., `"clientCredentials"`) |
| `tokenUrl`     | string | **Required** | Token endpoint URL                             |
| `clientId`     | string | **Required** | OAuth2 client ID (supports templating)         |
| `clientSecret` | string | **Required** | OAuth2 client secret (supports templating)     |
| `scopes`       | array  | Optional     | Array of scope strings                         |

#### Example

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
    "scopes": ["read:weather", "read:forecast"]
  }
}
```

---

## Templating Syntax

The MCI templating engine supports placeholder substitution, loops, and conditional blocks. Templating is available in:

- Execution configurations (URLs, headers, params, body, etc.)
- File contents (when `enableTemplating: true`)
- Text execution

### Context Structure

The templating engine has access to three contexts:

- **`props`**: Properties passed to `execute()` method
- **`env`**: Environment variables passed to the adapter
- **`input`**: Alias for `props` (for backward compatibility)

### Basic Placeholders

Replace placeholders with values from the context.

**Syntax**: `{{path.to.value}}`

#### Examples

```
{{props.location}}
{{env.API_KEY}}
{{input.username}}
{{props.user.name}}
{{env.DATABASE_URL}}
```

**In JSON**:

```json
{
  "url": "https://api.example.com/users/{{props.user_id}}",
  "headers": {
    "Authorization": "Bearer {{env.ACCESS_TOKEN}}",
    "X-Request-ID": "{{props.request_id}}"
  }
}
```

---

### For Loops

Iterate a fixed number of times using a range.

**Syntax**: `@for(variable in range(start, end))...@endfor`

- `variable`: Loop variable name
- `start`: Starting value (inclusive)
- `end`: Ending value (exclusive)

#### Example

**Template**:

```
@for(i in range(0, 3))
Item {{i}}
@endfor
```

**Output**:

```
Item 0
Item 1
Item 2
```

---

### Foreach Loops

Iterate over arrays or objects from the context.

**Syntax**: `@foreach(variable in path.to.collection)...@endforeach`

- `variable`: Loop variable name
- `path.to.collection`: Path to an array or object in the context

#### Array Example

**Context**:

```json
{
  "props": {
    "items": ["Apple", "Banana", "Cherry"]
  }
}
```

**Template**:

```
@foreach(item in props.items)
- {{item}}
@endforeach
```

**Output**:

```
- Apple
- Banana
- Cherry
```

#### Object Example

**Context**:

```json
{
  "props": {
    "users": [
      { "name": "Alice", "age": 30 },
      { "name": "Bob", "age": 25 }
    ]
  }
}
```

**Template**:

```
@foreach(user in props.users)
Name: {{user.name}}, Age: {{user.age}}
@endforeach
```

**Output**:

```
Name: Alice, Age: 30
Name: Bob, Age: 25
```

---

### Conditional Blocks

Execute code conditionally based on values in the context.

**Syntax**:

```
@if(condition)
...
@elseif(condition)
...
@else
...
@endif
```

#### Supported Conditions

- **Truthy check**: `@if(path.to.value)`
- **Equality**: `@if(path.to.value == "expected")`
- **Inequality**: `@if(path.to.value != "unexpected")`
- **Greater than**: `@if(path.to.value > 10)`
- **Less than**: `@if(path.to.value < 100)`

#### Examples

**Simple Conditional**:

```
@if(props.premium)
You have premium access!
@else
Upgrade to premium for more features.
@endif
```

**Multiple Conditions**:

```
@if(props.status == "active")
Status: Active
@elseif(props.status == "pending")
Status: Pending approval
@else
Status: Inactive
@endif
```

**Numeric Comparison**:

```
@if(props.age > 18)
Adult content available
@else
Restricted content
@endif
```

---

## Execution Result Format

All tool executions return a consistent result format.

| Field      | Type    | Description                                               |
| ---------- | ------- | --------------------------------------------------------- |
| `isError`  | boolean | Whether an error occurred during execution                |
| `content`  | any     | Result content (if successful)                            |
| `error`    | string  | Error message (if `isError: true`)                        |
| `metadata` | object  | Optional metadata (e.g., HTTP status code, CLI exit code) |

### Successful Result

```json
{
  "isError": false,
  "content": [
    {
      "type": "text",
      "text": "Current weather in New York:\nTemperature: 72°F\nConditions: Partly cloudy"
    }
  ],
  "metadata": {
    "status_code": 200,
    "response_time_ms": 245
  }
}
```

### Error Result

```json
{
  "isError": true,
  "error": "HTTP request failed: 404 Not Found",
  "metadata": {
    "status_code": 404
  }
}
```

---

## Complete Example

Here's a complete MCI context file demonstrating all features:

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "Example API Tools",
    "description": "Comprehensive example of MCI features",
    "version": "1.0.0",
    "license": "MIT",
    "authors": ["MCI Team"]
  },
  "tools": [
    {
      "name": "get_weather",
      "title": "Get Weather",
      "description": "Fetch weather with API key auth",
      "inputSchema": {
        "type": "object",
        "properties": {
          "location": { "type": "string" }
        },
        "required": ["location"]
      },
      "execution": {
        "type": "http",
        "method": "GET",
        "url": "https://api.weather.com/v1/current",
        "auth": {
          "type": "apiKey",
          "in": "header",
          "name": "X-API-Key",
          "value": "{{env.WEATHER_API_KEY}}"
        },
        "params": {
          "location": "{{props.location}}"
        }
      }
    },
    {
      "name": "search_logs",
      "title": "Search Logs",
      "description": "Search log files with grep",
      "inputSchema": {
        "type": "object",
        "properties": {
          "pattern": { "type": "string" },
          "directory": { "type": "string" }
        },
        "required": ["pattern", "directory"]
      },
      "execution": {
        "type": "cli",
        "command": "grep",
        "args": ["-r", "{{props.pattern}}"],
        "cwd": "{{props.directory}}"
      }
    },
    {
      "name": "load_report",
      "title": "Load Report",
      "description": "Load report template",
      "execution": {
        "type": "file",
        "path": "./templates/report.txt",
        "enableTemplating": true
      }
    },
    {
      "name": "generate_greeting",
      "title": "Generate Greeting",
      "description": "Generate personalized greeting",
      "inputSchema": {
        "type": "object",
        "properties": {
          "name": { "type": "string" }
        },
        "required": ["name"]
      },
      "execution": {
        "type": "text",
        "text": "Hello {{props.name}}! Welcome to MCI."
      }
    }
  ]
}
```

---

## See Also

- [API Reference](api_reference.md) - Python adapter API documentation
- [Quickstart Guide](quickstart.md) - Getting started with MCI
- [PRD.md](../PRD.md) - Product requirements and specifications
- [PLAN.md](../PLAN.md) - Implementation plan and architecture
