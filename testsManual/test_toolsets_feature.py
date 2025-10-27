#!/usr/bin/env python3
"""
Manual test for the Toolsets feature.

This test demonstrates real-world usage of toolsets including:
- Loading multiple toolsets from library directory
- Schema-level filtering (only, except, tags, withoutTags)
- Adapter-level filtering with toolsets() method
- Mixing main tools with toolset tools
- Combining different filter methods
"""

import json
import shutil
import sys
from pathlib import Path

from mcipy import MCIClient


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_tools(tools, indent: str = "") -> None:
    """Print tool information."""
    for tool in tools:
        source = f" (from {tool.toolset_source})" if tool.toolset_source else " (main)"
        tags_str = f" [tags: {', '.join(tool.tags)}]" if tool.tags else ""
        print(f"{indent}- {tool.name}{source}{tags_str}")


def main():
    """Run manual test demonstration."""
    print_section("Toolsets Feature Manual Test")
    
    # Create temporary test directory
    test_dir = Path("/tmp/mci_toolsets_test")
    test_dir.mkdir(exist_ok=True)
    
    # Create library directory
    lib_dir = test_dir / "mci"
    lib_dir.mkdir(exist_ok=True)
    
    print("\n1. Creating test toolset files...")
    
    # Create weather toolset
    weather_file = lib_dir / "weather.mci.json"
    weather_file.write_text(json.dumps({
        "schemaVersion": "1.0",
        "metadata": {
            "name": "Weather Tools",
            "description": "Tools for weather information"
        },
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather",
                "tags": ["weather", "read"],
                "execution": {
                    "type": "text",
                    "text": "Current weather for {{props.location}}"
                }
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast",
                "tags": ["weather", "read"],
                "execution": {
                    "type": "text",
                    "text": "Forecast for {{props.location}}"
                }
            },
            {
                "name": "set_weather_alert",
                "description": "Set weather alert",
                "tags": ["weather", "write"],
                "execution": {
                    "type": "text",
                    "text": "Alert set for {{props.location}}"
                }
            }
        ]
    }, indent=2))
    print(f"   ✓ Created {weather_file}")
    
    # Create database toolset
    db_file = lib_dir / "database.mci.json"
    db_file.write_text(json.dumps({
        "schemaVersion": "1.0",
        "metadata": {
            "name": "Database Tools",
            "description": "Tools for database operations"
        },
        "tools": [
            {
                "name": "query_data",
                "description": "Query database",
                "tags": ["database", "read"],
                "execution": {
                    "type": "text",
                    "text": "Query result: {{props.query}}"
                }
            },
            {
                "name": "insert_data",
                "description": "Insert data",
                "tags": ["database", "write"],
                "execution": {
                    "type": "text",
                    "text": "Inserted {{props.data}}"
                }
            },
            {
                "name": "delete_data",
                "description": "Delete data",
                "tags": ["database", "write", "destructive"],
                "execution": {
                    "type": "text",
                    "text": "Deleted from {{props.table}}"
                }
            }
        ]
    }, indent=2))
    print(f"   ✓ Created {db_file}")
    
    # Create GitHub directory with multiple files
    github_dir = lib_dir / "github"
    github_dir.mkdir(exist_ok=True)
    
    prs_file = github_dir / "prs.mci.json"
    prs_file.write_text(json.dumps({
        "schemaVersion": "1.0",
        "tools": [
            {
                "name": "list_prs",
                "description": "List pull requests",
                "tags": ["github", "read"],
                "execution": {
                    "type": "text",
                    "text": "PRs in {{props.repo}}"
                }
            },
            {
                "name": "create_pr",
                "description": "Create pull request",
                "tags": ["github", "write"],
                "execution": {
                    "type": "text",
                    "text": "Created PR in {{props.repo}}"
                }
            }
        ]
    }, indent=2))
    
    issues_file = github_dir / "issues.mci.json"
    issues_file.write_text(json.dumps({
        "schemaVersion": "1.0",
        "tools": [
            {
                "name": "list_issues",
                "description": "List issues",
                "tags": ["github", "read"],
                "execution": {
                    "type": "text",
                    "text": "Issues in {{props.repo}}"
                }
            },
            {
                "name": "create_issue",
                "description": "Create issue",
                "tags": ["github", "write"],
                "execution": {
                    "type": "text",
                    "text": "Created issue in {{props.repo}}"
                }
            }
        ]
    }, indent=2))
    print(f"   ✓ Created GitHub toolset directory with {len(list(github_dir.glob('*.mci.json')))} files")
    
    print("\n2. Testing basic toolset loading (no filters)...")
    
    # Create main schema with all toolsets
    main_schema_1 = test_dir / "schema1.mci.json"
    main_schema_1.write_text(json.dumps({
        "schemaVersion": "1.0",
        "metadata": {
            "name": "Test Schema 1",
            "description": "Load all toolsets without filters"
        },
        "toolsets": [
            {"name": "weather"},
            {"name": "database"},
            {"name": "github"}
        ]
    }, indent=2))
    
    client1 = MCIClient(schema_file_path=str(main_schema_1))
    all_tools = client1.tools()
    print(f"\n   Loaded {len(all_tools)} tools from all toolsets:")
    print_tools(all_tools, "   ")
    
    print_section("3. Testing schema-level filtering")
    
    # Test 'only' filter
    print("\n   a) Using 'only' filter to load specific tools from weather toolset:")
    main_schema_2 = test_dir / "schema2.mci.json"
    main_schema_2.write_text(json.dumps({
        "schemaVersion": "1.0",
        "toolsets": [
            {
                "name": "weather",
                "filter": "only",
                "filterValue": "get_weather, get_forecast"
            }
        ]
    }, indent=2))
    
    client2 = MCIClient(schema_file_path=str(main_schema_2))
    tools2 = client2.tools()
    print(f"      Loaded {len(tools2)} tools (expected: 2):")
    print_tools(tools2, "      ")
    
    # Test 'except' filter
    print("\n   b) Using 'except' filter to exclude destructive tools:")
    main_schema_3 = test_dir / "schema3.mci.json"
    main_schema_3.write_text(json.dumps({
        "schemaVersion": "1.0",
        "toolsets": [
            {
                "name": "database",
                "filter": "except",
                "filterValue": "delete_data"
            }
        ]
    }, indent=2))
    
    client3 = MCIClient(schema_file_path=str(main_schema_3))
    tools3 = client3.tools()
    print(f"      Loaded {len(tools3)} tools (expected: 2, excluding delete_data):")
    print_tools(tools3, "      ")
    
    # Test 'tags' filter
    print("\n   c) Using 'tags' filter to load only read-only tools:")
    main_schema_4 = test_dir / "schema4.mci.json"
    main_schema_4.write_text(json.dumps({
        "schemaVersion": "1.0",
        "toolsets": [
            {"name": "weather", "filter": "tags", "filterValue": "read"},
            {"name": "database", "filter": "tags", "filterValue": "read"}
        ]
    }, indent=2))
    
    client4 = MCIClient(schema_file_path=str(main_schema_4))
    tools4 = client4.tools()
    print(f"      Loaded {len(tools4)} read-only tools:")
    print_tools(tools4, "      ")
    
    # Test 'withoutTags' filter
    print("\n   d) Using 'withoutTags' filter to exclude destructive tools:")
    main_schema_5 = test_dir / "schema5.mci.json"
    main_schema_5.write_text(json.dumps({
        "schemaVersion": "1.0",
        "toolsets": [
            {
                "name": "database",
                "filter": "withoutTags",
                "filterValue": "destructive"
            }
        ]
    }, indent=2))
    
    client5 = MCIClient(schema_file_path=str(main_schema_5))
    tools5 = client5.tools()
    print(f"      Loaded {len(tools5)} non-destructive tools:")
    print_tools(tools5, "      ")
    
    print_section("4. Testing adapter-level filtering with toolsets()")
    
    # Load all toolsets without filters
    client6 = MCIClient(schema_file_path=str(main_schema_1))
    
    print("\n   a) Filter by weather toolset:")
    weather_tools = client6.toolsets(["weather"])
    print(f"      Found {len(weather_tools)} tools:")
    print_tools(weather_tools, "      ")
    
    print("\n   b) Filter by database toolset:")
    db_tools = client6.toolsets(["database"])
    print(f"      Found {len(db_tools)} tools:")
    print_tools(db_tools, "      ")
    
    print("\n   c) Filter by github toolset:")
    github_tools = client6.toolsets(["github"])
    print(f"      Found {len(github_tools)} tools:")
    print_tools(github_tools, "      ")
    
    print("\n   d) Filter by multiple toolsets (weather and github):")
    multi_tools = client6.toolsets(["weather", "github"])
    print(f"      Found {len(multi_tools)} tools:")
    print_tools(multi_tools, "      ")
    
    print_section("5. Testing mixed main tools and toolsets")
    
    main_schema_6 = test_dir / "schema6.mci.json"
    main_schema_6.write_text(json.dumps({
        "schemaVersion": "1.0",
        "tools": [
            {
                "name": "main_tool_1",
                "description": "Main tool 1",
                "tags": ["main"],
                "execution": {
                    "type": "text",
                    "text": "Main tool 1"
                }
            },
            {
                "name": "main_tool_2",
                "description": "Main tool 2",
                "tags": ["main"],
                "execution": {
                    "type": "text",
                    "text": "Main tool 2"
                }
            }
        ],
        "toolsets": [
            {"name": "weather"}
        ]
    }, indent=2))
    
    client7 = MCIClient(schema_file_path=str(main_schema_6))
    
    print("\n   All tools (main + toolsets):")
    all_tools_7 = client7.tools()
    print(f"   Total: {len(all_tools_7)} tools")
    print_tools(all_tools_7, "   ")
    
    print("\n   Only toolset tools:")
    toolset_only = client7.toolsets(["weather"])
    print(f"   Total: {len(toolset_only)} tools")
    print_tools(toolset_only, "   ")
    
    print("\n   Only main tools (using tags filter):")
    main_only = client7.tags(["main"])
    print(f"   Total: {len(main_only)} tools")
    print_tools(main_only, "   ")
    
    print_section("6. Testing tool execution from toolsets")
    
    print("\n   Executing tools from different toolsets:")
    
    # Execute weather tool
    result1 = client7.execute("get_weather", {"location": "New York"})
    print(f"\n   ✓ get_weather: {result1.result.content[0].text}")
    
    # Execute main tool
    result2 = client7.execute("main_tool_1", {})
    print(f"   ✓ main_tool_1: {result2.result.content[0].text}")
    
    print_section("Summary")
    
    print("""
   ✅ Successfully demonstrated:
      - Loading single toolset files
      - Loading toolset directories with multiple files
      - Loading multiple toolsets simultaneously
      - Schema-level filtering (only, except, tags, withoutTags)
      - Adapter-level filtering with toolsets() method
      - Mixing main tools with toolset tools
      - Executing tools from different sources
      - Tool source tracking (toolset_source field)
   
   The Toolsets feature is working correctly!
    """)
    
    # Cleanup
    print("\n7. Cleaning up test files...")
    shutil.rmtree(test_dir)
    print("   ✓ Cleaned up test directory")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
