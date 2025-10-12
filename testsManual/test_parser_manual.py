#!/usr/bin/env python3
"""
Manual test for SchemaParser.

This test demonstrates the SchemaParser's ability to:
- Load and parse the example.mci.json file
- Validate schema structure and version
- Parse all execution types (HTTP, CLI, File, Text)
- Display parsed schema details in a human-readable format

Run with: uv run python testsManual/test_parser_manual.py
"""

from pathlib import Path

from mcipy.enums import ExecutionType
from mcipy.models import (
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    TextExecutionConfig,
)
from mcipy.parser import SchemaParser, SchemaParserError


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_parse_example_mci_json():
    """Test parsing the example.mci.json file."""
    print_section("PARSING example.mci.json")

    # Get the path to example.mci.json
    repo_root = Path(__file__).parent.parent
    schema_file = repo_root / "example.mci.json"

    if not schema_file.exists():
        print(f"❌ Error: example.mci.json not found at {schema_file}")
        return False

    print(f"\n📁 Loading schema file: {schema_file}")

    try:
        # Parse the file
        schema = SchemaParser.parse_file(str(schema_file))
        print("✅ Schema loaded successfully!")

        # Display schema version
        print(f"\n📋 Schema Version: {schema.schemaVersion}")

        # Display metadata
        if schema.metadata:
            print("\n📝 Metadata:")
            print(f"   Name:        {schema.metadata.name}")
            print(f"   Description: {schema.metadata.description}")
            print(f"   Version:     {schema.metadata.version}")
            print(f"   License:     {schema.metadata.license}")
            if schema.metadata.authors:
                print(f"   Authors:     {', '.join(schema.metadata.authors)}")

        # Display tools
        print(f"\n🔧 Tools ({len(schema.tools)} total):")
        print()

        for idx, tool in enumerate(schema.tools, 1):
            print(f"   {idx}. {tool.name}")
            if tool.title:
                print(f"      Title:       {tool.title}")
            if tool.description:
                print(f"      Description: {tool.description}")

            # Display execution type
            exec_config = tool.execution
            print(f"      Type:        {exec_config.type.value}")

            # Display type-specific details
            if isinstance(exec_config, HTTPExecutionConfig):
                print(f"      Method:      {exec_config.method}")
                print(f"      URL:         {exec_config.url}")
                if exec_config.auth:
                    print(f"      Auth:        {exec_config.auth.type}")
                if exec_config.timeout_ms:
                    print(f"      Timeout:     {exec_config.timeout_ms}ms")

            elif isinstance(exec_config, CLIExecutionConfig):
                print(f"      Command:     {exec_config.command}")
                if exec_config.args:
                    print(f"      Args:        {exec_config.args}")
                if exec_config.cwd:
                    print(f"      Working Dir: {exec_config.cwd}")

            elif isinstance(exec_config, FileExecutionConfig):
                print(f"      Path:        {exec_config.path}")
                print(f"      Templating:  {exec_config.enableTemplating}")

            elif isinstance(exec_config, TextExecutionConfig):
                text_preview = (
                    exec_config.text[:50] + "..."
                    if len(exec_config.text) > 50
                    else exec_config.text
                )
                print(f"      Text:        {text_preview}")

            # Display input schema if present
            if tool.inputSchema:
                required = tool.inputSchema.get("required", [])
                props = tool.inputSchema.get("properties", {})
                print(f"      Input:       {len(props)} parameter(s)")
                if required:
                    print(f"      Required:    {', '.join(required)}")

            print()

        return True

    except SchemaParserError as e:
        print(f"❌ Schema parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_parse_invalid_schemas():
    """Test parsing invalid schemas to demonstrate error handling."""
    print_section("TESTING ERROR HANDLING")

    # Test 1: Invalid schema version
    print("\n1. Testing invalid schema version:")
    try:
        SchemaParser.parse_dict(
            {"schemaVersion": "2.0", "tools": []}
        )
        print("   ❌ Should have raised an error!")
    except SchemaParserError as e:
        print(f"   ✅ Caught expected error: {e}")

    # Test 2: Missing required fields
    print("\n2. Testing missing required fields:")
    try:
        SchemaParser.parse_dict({"tools": []})
        print("   ❌ Should have raised an error!")
    except SchemaParserError as e:
        print(f"   ✅ Caught expected error: {e}")

    # Test 3: Invalid execution type
    print("\n3. Testing invalid execution type:")
    try:
        SchemaParser.parse_dict(
            {
                "schemaVersion": "1.0",
                "tools": [{"name": "bad_tool", "execution": {"type": "invalid"}}],
            }
        )
        print("   ❌ Should have raised an error!")
    except SchemaParserError as e:
        print(f"   ✅ Caught expected error: {e}")

    # Test 4: Missing execution config fields
    print("\n4. Testing missing execution config fields:")
    try:
        SchemaParser.parse_dict(
            {
                "schemaVersion": "1.0",
                "tools": [{"name": "bad_tool", "execution": {"type": "http"}}],
            }
        )
        print("   ❌ Should have raised an error!")
    except SchemaParserError as e:
        print(f"   ✅ Caught expected error: {e}")


def test_parse_all_execution_types():
    """Test parsing a schema with all execution types."""
    print_section("TESTING ALL EXECUTION TYPES")

    schema_data = {
        "schemaVersion": "1.0",
        "tools": [
            {
                "name": "http_tool",
                "execution": {
                    "type": "http",
                    "url": "https://api.example.com",
                    "method": "POST",
                },
            },
            {
                "name": "cli_tool",
                "execution": {"type": "cli", "command": "echo", "args": ["hello"]},
            },
            {
                "name": "file_tool",
                "execution": {
                    "type": "file",
                    "path": "/tmp/test.txt",
                    "enableTemplating": True,
                },
            },
            {
                "name": "text_tool",
                "execution": {"type": "text", "text": "Hello {{props.name}}!"},
            },
        ],
    }

    try:
        schema = SchemaParser.parse_dict(schema_data)
        print("\n✅ All execution types parsed successfully!")
        print(f"\n   Parsed {len(schema.tools)} tools:")

        for tool in schema.tools:
            exec_type = tool.execution.type.value
            print(f"   - {tool.name}: {exec_type}")

        # Verify each type
        assert isinstance(schema.tools[0].execution, HTTPExecutionConfig)
        assert isinstance(schema.tools[1].execution, CLIExecutionConfig)
        assert isinstance(schema.tools[2].execution, FileExecutionConfig)
        assert isinstance(schema.tools[3].execution, TextExecutionConfig)

        print("\n   ✅ All execution configs have correct types!")

    except SchemaParserError as e:
        print(f"❌ Error parsing schema: {e}")


def main():
    """Run all manual tests."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "MCI SCHEMA PARSER MANUAL TEST" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        # Test 1: Parse example.mci.json
        success = test_parse_example_mci_json()

        # Test 2: Parse all execution types
        test_parse_all_execution_types()

        # Test 3: Test error handling
        test_parse_invalid_schemas()

        print("\n" + "=" * 70)
        if success:
            print("  ✓ All manual tests completed successfully!")
        else:
            print("  ⚠ Some tests had issues (see above)")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ Error during manual testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
