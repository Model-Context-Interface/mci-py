# MCI Python Adapter - Quickstart Guide

Welcome to the MCI Python Adapter! This guide will help you get started quickly with installing, configuring, and using the MCI (Model Context Interface) adapter to define and execute tools in your Python applications.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Tool Definitions](#tool-definitions)
- [Execution Types](#execution-types)
  - [Text Execution](#text-execution)
  - [File Execution](#file-execution)
  - [CLI Execution](#cli-execution)
  - [HTTP Execution](#http-execution)
- [Advanced Features](#advanced-features)
- [Next Steps](#next-steps)

## Installation

### Prerequisites

- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`

### Option 1: Using uv (Recommended)

First, install `uv` if you haven't already:

```bash
# macOS or Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew on macOS
brew install uv
```

Then install the MCI Python adapter:

```bash
# Install from PyPI
uv pip install mci-py

# Or install with uv add (if using uv project)
uv add mci-py
```

### Option 2: Using pip

```bash
pip install mci-py
```

### Verify Installation

```python
import mcipy
print("MCI Python Adapter installed successfully!")
```

## Basic Usage

### 1. Import the Client

```python
from mcipy import MCIClient
```

### 2. Create a Tool Schema File

Create a file named `my-tools.mci.json` with your tool definitions:

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "My Tools",
    "description": "A collection of useful tools",
    "version": "1.0.0"
  },
  "tools": [
    {
      "name": "greet_user",
      "title": "User Greeting",
      "description": "Generate a personalized greeting message",
      "inputSchema": {
        "type": "object",
        "properties": {
          "username": {
            "type": "string",
            "description": "The user's name"
          }
        },
        "required": ["username"]
      },
      "execution": {
        "type": "text",
        "text": "Hello, {{props.username}}! Welcome to MCI."
      }
    }
  ]
}
```

### 3. Initialize the Client

```python
from mcipy import MCIClient

# Initialize with your schema file
client = MCIClient(
    json_file_path="my-tools.mci.json",
    env_vars={
        "API_KEY": "your-secret-key",
        "USERNAME": "demo_user"
    }
)
```

### 4. List Available Tools

```python
# Get all tool names
tool_names = client.list_tools()
print(f"Available tools: {tool_names}")

# Get full tool objects
tools = client.tools()
for tool in tools:
    print(f"- {tool.name}: {tool.title}")
```

### 5. Execute a Tool

```python
# Execute the tool with properties
result = client.execute(
    tool_name="greet_user",
    properties={"username": "Alice"}
)

# Check the result
if result.isError:
    print(f"Error: {result.error}")
else:
    print(f"Success: {result.content}")
```

### 6. Filter Tools

```python
# Include only specific tools
weather_tools = client.only(["get_weather", "get_forecast"])

# Exclude specific tools
safe_tools = client.without(["delete_data", "admin_tools"])
```

### 7. Get Tool Schema

```python
# Retrieve input schema for a tool
schema = client.get_tool_schema("greet_user")
print(f"Required properties: {schema.get('required', [])}")
print(f"Properties: {list(schema.get('properties', {}).keys())}")
```

## Tool Definitions

All tools in MCI follow a standard JSON schema structure. Here's the complete anatomy of a tool definition:

```json
{
  "name": "tool_identifier",
  "title": "Human-Readable Tool Name",
  "description": "What this tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Description of parameter 1"
      },
      "param2": {
        "type": "number",
        "description": "Description of parameter 2"
      }
    },
    "required": ["param1"]
  },
  "execution": {
    "type": "http|cli|file|text",
    ...
  }
}
```

### Template Placeholders

MCI supports powerful templating with placeholders:

- `{{props.propertyName}}` - Access input properties
- `{{env.VARIABLE_NAME}}` - Access environment variables
- `{{input.fieldName}}` - Alias for `{{props.fieldName}}`

## Execution Types

MCI supports four execution types: **Text**, **File**, **CLI**, and **HTTP**. Each type is designed for different use cases.

### Text Execution

Return static or templated text directly. Perfect for simple messages, templates, or computed strings.

**Schema Example:**

```json
{
  "name": "generate_welcome",
  "title": "Welcome Message Generator",
  "description": "Generate a welcome message with current date",
  "inputSchema": {
    "type": "object",
    "properties": {
      "username": {
        "type": "string",
        "description": "User's name"
      }
    },
    "required": ["username"]
  },
  "execution": {
    "type": "text",
    "text": "Welcome {{props.username}}! Today is {{env.CURRENT_DATE}}."
  }
}
```

**Python Usage:**

```python
from datetime import datetime

client = MCIClient(
    json_file_path="tools.mci.json",
    env_vars={"CURRENT_DATE": datetime.now().strftime("%Y-%m-%d")}
)

result = client.execute(
    tool_name="generate_welcome",
    properties={"username": "Alice"}
)
print(result.content)  # "Welcome Alice! Today is 2024-01-15."
```

### File Execution

Read and return file contents with optional template substitution. Useful for loading configuration files, templates, or documentation.

**Schema Example:**

```json
{
  "name": "load_config",
  "title": "Load Configuration File",
  "description": "Load a configuration file with template substitution",
  "inputSchema": {
    "type": "object",
    "properties": {
      "config_name": {
        "type": "string",
        "description": "Name of the configuration"
      }
    },
    "required": ["config_name"]
  },
  "execution": {
    "type": "file",
    "path": "./configs/{{props.config_name}}.conf",
    "enableTemplating": true
  }
}
```

**File Content (configs/database.conf):**

```
host={{env.DB_HOST}}
port={{env.DB_PORT}}
user={{env.DB_USER}}
database={{props.database_name}}
```

**Python Usage:**

```python
client = MCIClient(
    json_file_path="tools.mci.json",
    env_vars={
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "admin"
    }
)

result = client.execute(
    tool_name="load_config",
    properties={
        "config_name": "database",
        "database_name": "production_db"
    }
)
print(result.content)
# Output:
# host=localhost
# port=5432
# user=admin
# database=production_db
```

### CLI Execution

Execute command-line programs and capture their output. Great for running system commands, scripts, or CLI tools.

**Schema Example:**

```json
{
  "name": "search_files",
  "title": "Search Files with Grep",
  "description": "Search for text patterns in files",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "Search pattern"
      },
      "directory": {
        "type": "string",
        "description": "Directory to search"
      },
      "ignore_case": {
        "type": "boolean",
        "description": "Ignore case when searching"
      }
    },
    "required": ["pattern", "directory"]
  },
  "execution": {
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
}
```

**Python Usage:**

```python
client = MCIClient(json_file_path="tools.mci.json")

result = client.execute(
    tool_name="search_files",
    properties={
        "pattern": "TODO",
        "directory": "./src",
        "ignore_case": True
    }
)

if result.isError:
    print(f"Error: {result.error}")
else:
    print(result.content)  # Output from grep command
```

**CLI Configuration Options:**

- `command`: The command to execute (e.g., "grep", "python", "node")
- `args`: Fixed arguments passed to the command
- `flags`: Dynamic flags based on input properties
  - `type: "boolean"`: Include flag only if property is true
  - `type: "value"`: Include flag with property value (e.g., `--file value`)
- `cwd`: Working directory for command execution
- `timeout_ms`: Maximum execution time in milliseconds

### HTTP Execution

Make HTTP requests to APIs with full support for authentication, headers, query parameters, and request bodies.

#### Basic GET Request

**Schema Example:**

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
        "description": "City name"
      }
    },
    "required": ["location"]
  },
  "execution": {
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
}
```

#### POST Request with JSON Body

**Schema Example:**

```json
{
  "name": "create_report",
  "title": "Create Report",
  "description": "Create a new report via API",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string"
      },
      "content": {
        "type": "string"
      }
    },
    "required": ["title", "content"]
  },
  "execution": {
    "type": "http",
    "method": "POST",
    "url": "https://api.example.com/reports",
    "headers": {
      "Content-Type": "application/json"
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
}
```

#### Authentication Options

**API Key Authentication (Header):**

```json
{
  "execution": {
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
}
```

**API Key Authentication (Query Parameter):**

```json
{
  "execution": {
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
}
```

**Bearer Token Authentication:**

```json
{
  "execution": {
    "type": "http",
    "method": "POST",
    "url": "https://api.example.com/data",
    "auth": {
      "type": "bearer",
      "token": "{{env.BEARER_TOKEN}}"
    }
  }
}
```

**Basic Authentication:**

```json
{
  "execution": {
    "type": "http",
    "method": "GET",
    "url": "https://api.example.com/data",
    "auth": {
      "type": "basic",
      "username": "{{env.USERNAME}}",
      "password": "{{env.PASSWORD}}"
    }
  }
}
```

**OAuth2 Client Credentials:**

```json
{
  "execution": {
    "type": "http",
    "method": "GET",
    "url": "https://api.example.com/data",
    "auth": {
      "type": "oauth2",
      "flow": "clientCredentials",
      "tokenUrl": "https://auth.example.com/token",
      "clientId": "{{env.CLIENT_ID}}",
      "clientSecret": "{{env.CLIENT_SECRET}}",
      "scopes": ["read:data"]
    }
  }
}
```

#### Request Body Types

**JSON Body:**

```json
{
  "body": {
    "type": "json",
    "content": {
      "key": "{{props.value}}"
    }
  }
}
```

**Form Body:**

```json
{
  "body": {
    "type": "form",
    "content": {
      "field1": "{{props.value1}}",
      "field2": "{{props.value2}}"
    }
  }
}
```

**Raw Body:**

```json
{
  "body": {
    "type": "raw",
    "content": "custom={{props.data}}&format=xml"
  }
}
```

#### Python Usage Example:

```python
from datetime import datetime

client = MCIClient(
    json_file_path="api-tools.mci.json",
    env_vars={
        "API_KEY": "your-secret-key",
        "BEARER_TOKEN": "your-bearer-token",
        "CURRENT_TIMESTAMP": datetime.now().isoformat()
    }
)

# Execute GET request
weather_result = client.execute(
    tool_name="get_weather",
    properties={"location": "New York"}
)

if not weather_result.isError:
    print(f"Weather data: {weather_result.content}")

# Execute POST request
report_result = client.execute(
    tool_name="create_report",
    properties={
        "title": "Q1 Sales Report",
        "content": "Sales increased by 15%"
    }
)

if not report_result.isError:
    print(f"Report created: {report_result.content}")
```

## Advanced Features

### Error Handling

Always check the `isError` property of execution results:

```python
result = client.execute(tool_name="my_tool", properties={...})

if result.isError:
    print(f"Error occurred: {result.error}")
    # Handle error case
else:
    print(f"Success: {result.content}")
    # Process successful result
```

### Multiple Clients

You can create multiple client instances for different schema files:

```python
# Client for API tools
api_client = MCIClient(
    json_file_path="api-tools.mci.json",
    env_vars={"API_KEY": "key1"}
)

# Client for CLI tools
cli_client = MCIClient(
    json_file_path="cli-tools.mci.json",
    env_vars={"WORKSPACE": "/home/user"}
)
```

### Environment Variables

Environment variables are the recommended way to handle secrets and configuration:

```python
import os

client = MCIClient(
    json_file_path="tools.mci.json",
    env_vars={
        "API_KEY": os.getenv("MY_API_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "ENVIRONMENT": "production"
    }
)
```

### Complete Example

Here's a complete example putting it all together:

```python
#!/usr/bin/env python3
"""
Complete MCI example with multiple execution types.
"""

from datetime import datetime
from mcipy import MCIClient

def main():
    # Initialize client with environment variables
    client = MCIClient(
        json_file_path="./tools.mci.json",
        env_vars={
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "API_KEY": "demo-api-key-123",
            "USERNAME": "demo_user"
        }
    )
    
    # List all available tools
    print("Available tools:")
    for tool_name in client.list_tools():
        print(f"  - {tool_name}")
    
    # Execute text tool
    print("\n1. Executing text tool...")
    result = client.execute(
        tool_name="generate_welcome",
        properties={"username": "Alice"}
    )
    if not result.isError:
        print(f"   Output: {result.content}")
    
    # Execute file tool
    print("\n2. Executing file tool...")
    result = client.execute(
        tool_name="load_config",
        properties={"config_name": "database"}
    )
    if not result.isError:
        print(f"   Config loaded: {len(result.content)} bytes")
    
    # Execute CLI tool
    print("\n3. Executing CLI tool...")
    result = client.execute(
        tool_name="search_files",
        properties={
            "pattern": "TODO",
            "directory": ".",
            "ignore_case": True
        }
    )
    if not result.isError:
        print(f"   Found matches: {len(result.content.splitlines())} lines")
    
    # Filter tools
    print("\n4. Filtering tools...")
    text_tools = client.only(["generate_welcome"])
    print(f"   Filtered to {len(text_tools)} tools")
    
    print("\n✓ Example completed successfully!")

if __name__ == "__main__":
    main()
```

## Next Steps

Now that you've learned the basics, explore these resources:

- **[API Reference](api_reference.md)** - Detailed documentation of all classes and methods
- **[Schema Reference](schema_reference.md)** - Complete JSON schema documentation
- **[Examples Directory](../examples/)** - More real-world examples
- **[GitHub Repository](https://github.com/Model-Context-Interface/mci-py)** - Source code and issue tracker

### Common Use Cases

- **API Integration**: Use HTTP execution to integrate with REST APIs
- **DevOps Automation**: Use CLI execution for system administration tasks
- **Configuration Management**: Use File execution to load and template config files
- **Reporting**: Use Text execution to generate formatted reports
- **Data Processing**: Combine multiple execution types for complex workflows

### Tips and Best Practices

1. **Always use environment variables for secrets** - Never hardcode API keys or passwords in schema files
2. **Set appropriate timeouts** - Prevent tools from hanging indefinitely
3. **Check `isError` before using results** - Proper error handling prevents runtime issues
4. **Use descriptive tool names** - Make your tools easy to discover and understand
5. **Document input schemas clearly** - Help users understand what each tool requires
6. **Test with minimal examples first** - Start simple and add complexity gradually

### Getting Help

If you encounter issues or have questions:

- Check the [GitHub Issues](https://github.com/Model-Context-Interface/mci-py/issues)
- Review the [PRD.md](../PRD.md) for design decisions
- Examine the [example.py](../example.py) for working code

Happy building with MCI! 🚀
