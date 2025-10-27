#!/usr/bin/env python3
"""
Example demonstrating the Toolsets feature.

This example shows how to:
- Load toolsets from a library directory
- Apply schema-level filters to toolsets
- Use adapter-level filtering with toolsets() method
- Mix main schema tools with toolset tools
- Filter by tags and names across all tools
"""

from mcipy import MCIClient


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70 + "\n")


def print_tools(tools, prefix=""):
    """Print tool names with their sources."""
    for tool in tools:
        source = f" (from {tool.toolset_source})" if tool.toolset_source else " (main)"
        tags = f" [{', '.join(tool.tags)}]" if tool.tags else ""
        print(f"{prefix}{tool.name}{source}{tags}")


def main():
    """Run toolsets example."""
    
    # Initialize client with toolsets
    print_section("Initializing MCI Client with Toolsets")
    
    client = MCIClient(
        schema_file_path="examples/toolsets_example.mci.json",
        env_vars={
            "APP_VERSION": "1.0.0",
            "ENVIRONMENT": "development",
            "DEBUG_MODE": "true"
        }
    )
    
    print("✓ Client initialized with main schema and toolsets")
    
    # List all tools
    print_section("1. All Available Tools")
    all_tools = client.tools()
    print(f"Total: {len(all_tools)} tools\n")
    print_tools(all_tools, "  ")
    
    # Filter by toolset
    print_section("2. Filter by Toolset")
    
    print("Weather toolset tools:")
    weather_tools = client.toolsets(["weather"])
    print_tools(weather_tools, "  ")
    
    print("\nDatabase toolset tools:")
    db_tools = client.toolsets(["database"])
    print_tools(db_tools, "  ")
    
    print("\nGitHub toolset tools:")
    github_tools = client.toolsets(["github"])
    print_tools(github_tools, "  ")
    
    # Combine multiple toolsets
    print_section("3. Multiple Toolsets")
    
    api_tools = client.toolsets(["weather", "database"])
    print(f"Weather + Database tools: {len(api_tools)}")
    print_tools(api_tools, "  ")
    
    # Filter by tags
    print_section("4. Filter by Tags")
    
    read_tools = client.tags(["read"])
    print(f"Read-only tools: {len(read_tools)}")
    print_tools(read_tools, "  ")
    
    write_tools = client.tags(["write"])
    print(f"\nWrite tools: {len(write_tools)}")
    print_tools(write_tools, "  ")
    
    # Filter by tool names
    print_section("5. Filter by Tool Names")
    
    specific_tools = client.only(["app_status", "get_weather", "query_data"])
    print(f"Specific tools: {len(specific_tools)}")
    print_tools(specific_tools, "  ")
    
    # Exclude tools
    print_section("6. Exclude Specific Tools")
    
    safe_tools = client.without(["delete_data"])
    print(f"Tools without delete_data: {len(safe_tools)}")
    print_tools(safe_tools, "  ")
    
    # Execute tools from different sources
    print_section("7. Execute Tools from Different Sources")
    
    # Execute main schema tool
    print("Executing main schema tool (app_status):")
    result1 = client.execute("app_status")
    print(f"  → {result1.result.content[0].text}")
    
    # Execute toolset tool
    print("\nExecuting toolset tool (get_weather):")
    result2 = client.execute("get_weather", {"location": "San Francisco"})
    print(f"  → {result2.result.content[0].text}")
    
    # Execute another toolset tool
    print("\nExecuting toolset tool (query_data):")
    result3 = client.execute("query_data", {"query": "SELECT * FROM users"})
    print(f"  → {result3.result.content[0].text}")
    
    # Summary
    print_section("Summary")
    
    print("""
The Toolsets feature allows you to:
  ✓ Organize tools into reusable libraries
  ✓ Apply schema-level filters when loading toolsets
  ✓ Filter tools by their source toolset at runtime
  ✓ Mix main schema tools with toolset tools
  ✓ Use all existing filtering methods (tags, only, without, etc.)
  
See the documentation for more details:
  - Schema Reference: docs/schema_reference.md
  - API Reference: docs/api_reference.md
  - Quickstart Guide: docs/quickstart.md
    """)


if __name__ == "__main__":
    main()
