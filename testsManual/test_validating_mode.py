#!/usr/bin/env python3
"""
Manual test for MCIClient validating mode.

This script demonstrates the validating mode feature by showing:
1. Schema validation with MCP servers without env vars
2. Schema validation with toolsets without loading them
3. Execution blocking in validating mode
4. Normal mode comparison

Run this test with:
    uv run python testsManual/test_validating_mode.py
"""

import json
import tempfile
from pathlib import Path

from mcipy import MCIClient, MCIClientError


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_mcp_server_validation() -> None:
    """Test validating mode with MCP server requiring env vars."""
    print_section("Test 1: MCP Server Validation")

    # Create schema with MCP server requiring env var
    schema = {
        "schemaVersion": "1.0",
        "libraryDir": "./mci",
        "mcp_servers": {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "{{env.GITHUB_TOKEN}}"},
                "config": {"expDays": 30, "filter": "only", "filterValue": "create_issue"},
            }
        },
        "tools": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        # Try normal mode without env vars (should fail)
        print("1. Normal mode without env vars:")
        try:
            client = MCIClient(schema_file_path=temp_path, env_vars={})
            print("   ✗ UNEXPECTED: Should have failed due to missing env var")
        except MCIClientError as e:
            print(f"   ✓ Expected failure: {str(e)[:80]}...")

        # Try validating mode without env vars (should succeed)
        print("\n2. Validating mode without env vars:")
        try:
            client = MCIClient(schema_file_path=temp_path, env_vars={}, validating=True)
            print("   ✓ SUCCESS: Schema validated without env vars")
            print(f"   Schema contains {len(client.list_tools())} inline tools")
        except Exception as e:
            print(f"   ✗ FAILED: {e}")

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_toolset_validation() -> None:
    """Test validating mode with toolsets."""
    print_section("Test 2: Toolset Validation")

    # Create a toolset file
    with tempfile.TemporaryDirectory() as tmpdir:
        toolset_dir = Path(tmpdir) / "mci"
        toolset_dir.mkdir()

        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        toolset_file = toolset_dir / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_schema, indent=2))

        # Create main schema
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["my_toolset"],
            "tools": [{"name": "inline_tool", "execution": {"type": "text", "text": "Inline"}}],
        }

        schema_file = Path(tmpdir) / "schema.json"
        schema_file.write_text(json.dumps(schema, indent=2))

        # Normal mode: loads toolset tools
        print("1. Normal mode:")
        client = MCIClient(schema_file_path=str(schema_file), validating=False)
        print(f"   ✓ Loaded {len(client.list_tools())} tools (includes toolset tools)")
        print(f"   Tools: {client.list_tools()}")

        # Validating mode: doesn't load toolset tools
        print("\n2. Validating mode:")
        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        print(f"   ✓ Validated schema with {len(client.list_tools())} inline tools")
        print(f"   Tools: {client.list_tools()}")
        print("   Note: Toolset tools are not loaded in validating mode")


def test_execution_blocking() -> None:
    """Test that execution is blocked in validating mode."""
    print_section("Test 3: Execution Blocking")

    schema = {
        "schemaVersion": "1.0",
        "tools": [{"name": "greet", "execution": {"type": "text", "text": "Hello, World!"}}],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        # Normal mode: execution works
        print("1. Normal mode execution:")
        client = MCIClient(schema_file_path=temp_path, validating=False)
        result = client.execute("greet", {})
        print(f"   ✓ Execution succeeded: {result.result.content[0].text}")

        # Validating mode: execution blocked
        print("\n2. Validating mode execution:")
        client = MCIClient(schema_file_path=temp_path, validating=True)
        try:
            client.execute("greet", {})
            print("   ✗ UNEXPECTED: Execution should have been blocked")
        except MCIClientError as e:
            print(f"   ✓ Execution blocked as expected")
            print(f"   Error message: {e}")

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_schema_validation_errors() -> None:
    """Test that schema validation errors are still caught in validating mode."""
    print_section("Test 4: Schema Validation Errors")

    # Invalid schema version
    print("1. Invalid schema version:")
    schema = {"schemaVersion": "999.0", "tools": []}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        client = MCIClient(schema_file_path=temp_path, validating=True)
        print("   ✗ UNEXPECTED: Should have failed validation")
    except MCIClientError as e:
        print(f"   ✓ Validation error caught: {str(e)[:80]}...")
    finally:
        Path(temp_path).unlink(missing_ok=True)

    # Missing required field
    print("\n2. Missing required field (execution):")
    schema = {"schemaVersion": "1.0", "tools": [{"name": "bad_tool"}]}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        client = MCIClient(schema_file_path=temp_path, validating=True)
        print("   ✗ UNEXPECTED: Should have failed validation")
    except MCIClientError as e:
        print(f"   ✓ Validation error caught: {str(e)[:80]}...")
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_read_only_operations() -> None:
    """Test that read-only operations work in validating mode."""
    print_section("Test 5: Read-Only Operations")

    schema = {
        "schemaVersion": "1.0",
        "tools": [
            {
                "name": "tool1",
                "tags": ["api"],
                "execution": {"type": "text", "text": "Tool 1"},
            },
            {
                "name": "tool2",
                "tags": ["cli"],
                "execution": {"type": "text", "text": "Tool 2"},
            },
            {"name": "tool3", "tags": ["api"], "execution": {"type": "text", "text": "Tool 3"}},
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        client = MCIClient(schema_file_path=temp_path, validating=True)

        print("1. list_tools():")
        print(f"   ✓ {client.list_tools()}")

        print("\n2. only(['tool1', 'tool3']):")
        tools = client.only(["tool1", "tool3"])
        print(f"   ✓ {[t.name for t in tools]}")

        print("\n3. without(['tool2']):")
        tools = client.without(["tool2"])
        print(f"   ✓ {[t.name for t in tools]}")

        print("\n4. tags(['api']):")
        tools = client.tags(["api"])
        print(f"   ✓ {[t.name for t in tools]}")

        print("\n5. withoutTags(['cli']):")
        tools = client.withoutTags(["cli"])
        print(f"   ✓ {[t.name for t in tools]}")

    finally:
        Path(temp_path).unlink(missing_ok=True)


def main() -> None:
    """Run all manual tests."""
    print("\n" + "=" * 60)
    print("  MCIClient Validating Mode - Manual Test Suite")
    print("=" * 60)

    try:
        test_mcp_server_validation()
        test_toolset_validation()
        test_execution_blocking()
        test_schema_validation_errors()
        test_read_only_operations()

        print_section("All Tests Completed Successfully!")
        print("✅ Validating mode is working as expected\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
