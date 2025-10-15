#!/usr/bin/env python3
"""
Example script demonstrating MCIClient usage.

This script loads the example.mci.json schema and executes the
'load_template' and 'generate_message' tools to show how to use
the MCI Python adapter.

Usage:
    python example.py
    # or
    uv run python example.py
"""

from datetime import datetime

from mcipy import MCIClient


def main():
    """Run the example demonstration."""
    print("=" * 80)
    print("MCI Python Adapter - Example Usage")
    print("=" * 80)
    print()

    # Initialize the client with the example schema
    print("1. Initializing MCIClient with example.mci.json...")
    client = MCIClient(
        json_file_path="./example.mci.json",
        env_vars={
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "API_KEY": "demo-api-key-123",
            "USERNAME": "demo_user",
        },
    )
    print("   ✓ Client initialized successfully")
    print()

    # List available tools
    print("2. Listing available tools...")
    tool_names = client.list_tools()
    print(f"   Found {len(tool_names)} tools:")
    for tool_name in tool_names:
        print(f"   - {tool_name}")
    print()

    # Execute the 'generate_message' tool
    print("3. Executing 'generate_message' tool...")
    print("   Input: username='Alice'")
    result = client.execute(tool_name="generate_message", properties={"username": "Alice"})

    if result.isError:
        print(f"   ✗ Error: {result.error}")
    else:
        print(f"   ✓ Success!")
        print(f"   Output: {result.content}")
    print()

    # Execute the 'load_template' tool
    print("4. Executing 'load_template' tool...")
    print("   Input: username='Bob'")
    print("   Note: This tool reads from ./text.txt with template substitution")
    # Note that new_prop is an array to demonstrate iteration in the template
    # And it is not a part of input schema, showing flexibility
    # That you can pass extra properties not defined in the schema
    # And allows direct passing of inputSchema to LLMs
    result = client.execute(tool_name="load_template", properties={"username": "Bob", "new_prop": [1, 2, 3]})

    if result.isError:
        print(f"   ✗ Error: {result.error}")
    else:
        print(f"   ✓ Success!")
        print(f"   Output: {result.content}")
    print()

    # Show tool filtering
    print("5. Demonstrating tool filtering...")
    print("   Filtering to only 'load_template' and 'generate_message':")
    filtered_tools = client.only(["load_template", "generate_message"])
    print(f"   Found {len(filtered_tools)} tools:")
    for tool in filtered_tools:
        print(f"   - {tool.name}: {tool.title}")
    print()

    # Show schema retrieval
    print("6. Getting tool schema...")
    schema = client.get_tool_schema("generate_message")
    print(f"   Schema for 'generate_message':")
    print(f"   - Required properties: {schema.get('required', [])}")
    print(f"   - Properties: {list(schema.get('properties', {}).keys())}")
    print()

    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
