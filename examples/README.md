# MCI Python Adapter - Examples

This directory contains comprehensive example files demonstrating the MCI Python Adapter functionality. Each example file showcases different execution types and features.

## Example Files

### 1. `http_example.json`
Demonstrates HTTP execution with various authentication methods:
- **get_weather**: HTTP GET request with query parameters
- **create_report**: HTTP POST with Bearer token authentication and JSON body
- **github_api**: HTTP GET with API key authentication and retry configuration
- **update_user**: HTTP PUT with Basic authentication

**Features demonstrated:**
- Multiple HTTP methods (GET, POST, PUT)
- Authentication types (Bearer, API Key, Basic)
- Request headers and query parameters
- JSON request bodies
- Timeout and retry configuration
- Template placeholders in URLs, headers, and body

### 2. `cli_example.json`
Demonstrates command-line execution:
- **search_files**: Search text using grep with optional case-insensitive flag
- **list_files**: List files with ls command and optional show-hidden flag
- **count_lines**: Count lines in a file using wc
- **find_files**: Find files by name pattern using find command

**Features demonstrated:**
- Command execution with arguments
- Boolean and value flags
- Working directory specification
- Timeout configuration
- Template placeholders in commands and arguments

### 3. `file_example.json`
Demonstrates file reading with and without templating:
- **load_template**: Read file with placeholder substitution enabled
- **read_report**: Read file with dynamic path templating
- **load_config**: Read raw file without template processing
- **read_email_template**: Read template with multiple placeholders

**Features demonstrated:**
- File reading with template substitution
- Dynamic file paths using placeholders
- Enabling/disabling template processing
- Reading configuration files

### 4. `text_example.json`
Demonstrates text template execution:
- **generate_message**: Simple text with placeholders
- **generate_welcome**: Welcome message with multiple placeholders
- **status_message**: Status message with timestamp
- **generate_report_summary**: Multi-line formatted text with placeholders

**Features demonstrated:**
- Text template with placeholder substitution
- Environment variable placeholders
- Property placeholders
- Multi-line text templates

### 5. `mixed_example.json`
Comprehensive example combining all execution types:
- 2 HTTP tools (GET and POST)
- 2 CLI tools (grep and ls)
- 2 File tools (with and without templating)
- 2 Text tools (simple messages)

**Features demonstrated:**
- All four execution types in one schema
- Demonstrates how different tool types can coexist
- Useful for testing filtering and tool selection

## Usage Script

### `example_usage.py`
Executable Python script demonstrating how to:
- Load MCI schema files
- Initialize MCIClient with environment variables
- List available tools
- Execute tools of each type
- Filter tools by name
- Retrieve tool schemas
- Handle execution results

**Run the script:**
```bash
# From repository root
python examples/example_usage.py
# or
uv run python examples/example_usage.py
```

## Running Individual Examples

You can load and use any example file with the MCIClient:

```python
from mcipy import MCIClient

# Load HTTP examples
client = MCIClient(
    json_file_path="examples/http_example.json",
    env_vars={"BEARER_TOKEN": "your-token"}
)

# List tools
print(client.list_tools())

# Execute a tool (Note: HTTP examples use fake endpoints)
result = client.execute(
    tool_name="get_weather",
    properties={"location": "Seattle"}
)
```

## Validation

All example files have been validated to:
- Be valid JSON
- Pass MCI schema validation
- Load correctly with MCIClient
- Execute without errors (for applicable tools)

## Template Placeholders

Examples use two types of placeholders:

1. **Environment variables**: `{{env.VARIABLE_NAME}}`
   - Example: `{{env.API_KEY}}`, `{{env.CURRENT_DATE}}`

2. **Input properties**: `{{props.property_name}}`
   - Example: `{{props.username}}`, `{{props.location}}`

## Notes

- HTTP examples use `api.example.com` which won't resolve - they're for demonstration purposes
- CLI examples use standard Unix commands (grep, ls, wc, find) that should work on most systems
- File examples reference paths that may not exist - create test files as needed
- Text examples work immediately as they don't require external resources

## See Also

- [API Reference](../docs/api_reference.md) - Complete API documentation
- [Quickstart Guide](../docs/quickstart.md) - Getting started guide
- [Schema Reference](../docs/schema_reference.md) - MCI schema documentation
