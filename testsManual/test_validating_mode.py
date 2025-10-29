#!/usr/bin/env python3
"""
Manual test for validating mode functionality.

This script demonstrates the validating mode feature, showing how it can
validate schemas without requiring environment variables or performing
network/file operations.
"""

import json
import tempfile
from pathlib import Path

from mcipy import MCIClient


def test_basic_validating_mode():
    """Test basic validating mode with unresolved templates."""
    print("=" * 70)
    print("Test 1: Basic Validating Mode with Unresolved Templates")
    print("=" * 70)

    schema = {
        "schemaVersion": "1.0",
        "metadata": {"name": "Test Schema", "description": "Schema with env var placeholders"},
        "tools": [
            {
                "name": "api_call",
                "description": "Make an API call with authentication",
                "execution": {
                    "type": "http",
                    "method": "GET",
                    "url": "https://api.example.com/{{env.ENDPOINT}}",
                    "headers": {"Authorization": "Bearer {{env.API_KEY}}"},
                },
            },
            {
                "name": "greet_user",
                "description": "Greet a user by name",
                "execution": {"type": "text", "text": "Hello, {{env.USERNAME}}!"},
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "schema.json"
        schema_path.write_text(json.dumps(schema, indent=2))

        print(f"\nSchema file: {schema_path}")
        print("\nSchema content:")
        print(json.dumps(schema, indent=2))

        print("\n--- Without validating mode (loads successfully, templates resolved on execution) ---")
        try:
            client = MCIClient(schema_file_path=str(schema_path))
            print("✓ Schema loaded successfully (templates not resolved until execution)")
            
            # Templates would fail during execution, not during loading
            print("  Note: Templates in execution configs are only resolved during tool execution")

        except Exception as e:
            print(f"✗ Unexpected error during load: {type(e).__name__}: {e}")

        print("\n--- With validating mode (should succeed) ---")
        try:
            client = MCIClient(schema_file_path=str(schema_path), validating=True)
            print("✓ Schema loaded successfully in validating mode!")

            tools = client.list_tools()
            print(f"✓ Found {len(tools)} tools: {tools}")

            # Try to get tool schema
            schema_info = client.get_tool_schema("api_call")
            print(f"✓ Retrieved tool schema for 'api_call': {schema_info}")

        except Exception as e:
            print(f"✗ Unexpected error: {type(e).__name__}: {e}")

        print("\n--- Attempting execution in validating mode (should fail) ---")
        try:
            result = client.execute("greet_user", properties={"name": "Alice"})
            print(f"✗ Execution should have failed but got: {result}")
        except Exception as e:
            print(f"✓ Expected failure: {type(e).__name__}: {e}")


def test_validating_mode_with_toolsets():
    """Test validating mode with toolsets."""
    print("\n" + "=" * 70)
    print("Test 2: Validating Mode with Toolsets")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create toolset
        lib_dir = tmpdir_path / "mci"
        lib_dir.mkdir()

        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "toolset_tool",
                    "description": "A tool from a toolset",
                    "execution": {"type": "text", "text": "From toolset: {{env.MESSAGE}}"},
                }
            ],
        }

        toolset_path = lib_dir / "my_toolset.mci.json"
        toolset_path.write_text(json.dumps(toolset_schema, indent=2))

        # Main schema
        main_schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["my_toolset"],
        }

        schema_path = tmpdir_path / "main.json"
        schema_path.write_text(json.dumps(main_schema, indent=2))

        print(f"\nMain schema file: {schema_path}")
        print(f"Toolset file: {toolset_path}")

        print("\n--- With validating mode ---")
        try:
            client = MCIClient(schema_file_path=str(schema_path), validating=True)
            print("✓ Schema with toolset loaded successfully in validating mode!")

            tools = client.list_tools()
            print(
                f"✓ Found {len(tools)} tools (toolsets not loaded in validating mode): {tools}"
            )

        except Exception as e:
            print(f"✗ Unexpected error: {type(e).__name__}: {e}")


def test_validating_mode_with_mcp_servers():
    """Test validating mode with MCP servers."""
    print("\n" + "=" * 70)
    print("Test 3: Validating Mode with MCP Servers")
    print("=" * 70)

    schema = {
        "schemaVersion": "1.0",
        "libraryDir": "./mci",
        "mcp_servers": {
            "test_server": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-test"],
                "env": {"API_KEY": "{{env.SECRET_KEY}}", "ENDPOINT": "{{env.API_ENDPOINT}}"},
                "config": {"expDays": 7, "filter": "tags", "filterValue": "safe"},
            }
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "schema.json"
        schema_path.write_text(json.dumps(schema, indent=2))

        print(f"\nSchema file: {schema_path}")
        print("\nSchema content:")
        print(json.dumps(schema, indent=2))

        print("\n--- With validating mode ---")
        try:
            client = MCIClient(schema_file_path=str(schema_path), validating=True)
            print("✓ Schema with MCP server loaded successfully in validating mode!")
            print("  (MCP server structure validated but not fetched)")

            tools = client.list_tools()
            print(f"✓ Found {len(tools)} tools (MCP not fetched in validating mode): {tools}")

        except Exception as e:
            print(f"✗ Unexpected error: {type(e).__name__}: {e}")


def test_mixed_schema():
    """Test validating mode with all three sources."""
    print("\n" + "=" * 70)
    print("Test 4: Validating Mode with Mixed Sources")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create toolset
        lib_dir = tmpdir_path / "mci"
        lib_dir.mkdir()

        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "toolset_tool", "execution": {"type": "text", "text": "From toolset"}}
            ],
        }

        toolset_path = lib_dir / "toolset.mci.json"
        toolset_path.write_text(json.dumps(toolset_schema, indent=2))

        # Main schema with all sources
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "tools": [
                {
                    "name": "direct_tool",
                    "execution": {"type": "text", "text": "Hello {{env.USER}}"},
                }
            ],
            "toolsets": ["toolset"],
            "mcp_servers": {
                "test_mcp": {"command": "npx", "args": ["-y", "test"], "env": {"K": "{{env.V}}"}}
            },
        }

        schema_path = tmpdir_path / "schema.json"
        schema_path.write_text(json.dumps(schema, indent=2))

        print(f"\nSchema file: {schema_path}")

        print("\n--- With validating mode ---")
        try:
            client = MCIClient(schema_file_path=str(schema_path), validating=True)
            print("✓ Mixed schema loaded successfully in validating mode!")

            tools = client.list_tools()
            print(f"✓ Found {len(tools)} tools: {tools}")
            print("  (Only direct tools loaded; toolsets and MCP servers validated but not loaded)")

        except Exception as e:
            print(f"✗ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Manual Test: Validating Mode Feature")
    print("=" * 70)

    try:
        test_basic_validating_mode()
        test_validating_mode_with_toolsets()
        test_validating_mode_with_mcp_servers()
        test_mixed_schema()

        print("\n" + "=" * 70)
        print("✓ All manual tests completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
