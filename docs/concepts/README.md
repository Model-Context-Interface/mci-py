# MCI Concepts

This directory contains conceptual guides that explain core MCI principles and features. These guides are adapter-agnostic and focus on understanding MCI itself, not specific implementation details.

## Available Guides

### [Structure](structure.md)
Learn about MCI project organization, including:
- Entry files in the project root
- Toolsets directory organization
- MCP server caching
- Basic templating with default values

**Start here** to understand how to organize your MCI projects.

### [Tools](tools.md)
Understand the four tool execution types:
- **HTTP**: API requests and workflow integration (n8n, Zapier, Make)
- **CLI**: Running scripts (.py, .js, .php) and command-line tools
- **File**: The best way to manage prompts with advanced templating
- **Text**: Simple text generation

Learn when to use each type and see practical examples.

### [Toolsets](toolsets.md)
Master tool organization and sharing:
- Creating reusable tool collections
- Loading and resolving toolsets
- Schema-level filtering
- Sharing toolsets across projects and teams

Perfect for understanding how to organize and distribute tools.

### [MCP Servers](mcp_servers.md)
Learn about MCP integration benefits:
- Automatic caching for 20x faster tool discovery
- Filtering MCP tools
- Splitting and combining tools from different servers
- Performance optimization

Discover why MCI's MCP integration is better than direct MCP connections.

### [Templates](templates.md)
Master MCI's standard templating system:
- Variable substitution (`{{props.field}}`, `{{env.VAR}}`)
- Default values (`{{env.VAR|default}}`)
- Conditionals (`@if`, `@else`, `@endif`)
- Loops (`@for`, `@foreach`)

These features work consistently across all MCI adapters (Python, JavaScript, Go, etc.).

## Reading Order

**For Beginners:**
1. [Structure](structure.md) - Understand project organization
2. [Tools](tools.md) - Learn about execution types
3. [Templates](templates.md) - Master templating basics

**For Tool Organization:**
1. [Tools](tools.md) - Individual tool definitions
2. [Toolsets](toolsets.md) - Organizing tools into collections
3. [Structure](structure.md) - Overall project layout

**For MCP Integration:**
1. [MCP Servers](mcp_servers.md) - Integration and caching
2. [Toolsets](toolsets.md) - Managing MCP toolsets
3. [Structure](structure.md) - MCP cache location

**For Advanced Templating:**
1. [Templates](templates.md) - Complete templating reference
2. [Tools](tools.md) - Using templates in file execution
3. [Structure](structure.md) - Templating in entry files

## Note on Examples

All examples in these guides use:
- **JSON** for MCI schema files
- **XML** for template file examples (where applicable)
- **Plain text** for other templates

**No adapter-specific code** (Python, JavaScript, etc.) is included in these concept guides. For adapter-specific usage, see:

*Currently, only the Python adapter is available; documentation for other adapters will be added as they are released.*
- [Basic Usage Guide](../basic_usage.md) - Python adapter examples
- [API Reference](../api_reference.md) - Python API documentation

## Additional Resources

- [Quickstart Guide](../quickstart.md) - Get started in 5 minutes
- [Basic Usage Guide](../basic_usage.md) - Detailed Python usage
- [Schema Reference](../schema_reference.md) - Complete schema documentation
- [API Reference](../api_reference.md) - Python API documentation
- [MCP Integration Guide](../mcp_integration.md) - MCP server setup

## Contributing

These concept guides are meant to be clear, practical, and universally applicable across all MCI adapters. If you find areas that could be improved or clarified, please open an issue or submit a pull request.
