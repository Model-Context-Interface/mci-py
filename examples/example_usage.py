#!/usr/bin/env python3
"""
Example usage script demonstrating the MCI Python Adapter.

This script shows how to load and execute tools from the example MCI files,
demonstrating all four execution types: HTTP, CLI, File, and Text.

Usage:
    python examples/example_usage.py
    # or
    uv run python examples/example_usage.py
"""

from datetime import datetime
from pathlib import Path

from mcipy import MCIClient


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def demo_http_examples():
    """Demonstrate HTTP execution examples."""
    print_section("HTTP Execution Examples")

    # Initialize client with HTTP examples
    client = MCIClient(
        json_file_path="examples/http_example.json",
        env_vars={
            "BEARER_TOKEN": "demo-bearer-token-xyz",
            "GITHUB_TOKEN": "demo-github-token-abc",
            "USERNAME": "demo_user",
            "PASSWORD": "demo_password",
            "CURRENT_TIMESTAMP": datetime.now().isoformat(),
        },
    )

    print("Available HTTP tools:")
    for tool_name in client.list_tools():
        print(f"  - {tool_name}")
    print()

    # Note: These are example API calls that would fail in production
    # They're here to demonstrate the structure and usage
    print("Example: Get weather tool (would make HTTP GET request)")
    print("  Tool: get_weather")
    print("  Would call: https://api.example.com/weather?location=Seattle&units=metric")
    print()

    print("Example: Create report tool (would make HTTP POST request)")
    print("  Tool: create_report")
    print("  Would call: https://api.example.com/reports")
    print("  With Bearer authentication and JSON body")
    print()


def demo_cli_examples():
    """Demonstrate CLI execution examples."""
    print_section("CLI Execution Examples")

    # Initialize client with CLI examples
    client = MCIClient(json_file_path="examples/cli_example.json")

    print("Available CLI tools:")
    for tool_name in client.list_tools():
        print(f"  - {tool_name}")
    print()

    # Execute count_lines tool (safe to run)
    print("Executing: count_lines on README.md")
    try:
        result = client.execute(tool_name="count_lines", properties={"file_path": "README.md"})

        if not result.isError:
            print("  ✓ Success!")
            print(f"  Output: {result.content.strip()}")
        else:
            print(f"  ✗ Error: {result.error}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    print()

    # Execute list_files tool (safe to run)
    print("Executing: list_files on current directory")
    try:
        result = client.execute(
            tool_name="list_files", properties={"directory": ".", "show_hidden": False}
        )

        if not result.isError:
            print("  ✓ Success!")
            lines = result.content.strip().split("\n")
            print("  Output (first 5 lines):")
            for line in lines[:5]:
                print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... and {len(lines) - 5} more lines")
        else:
            print(f"  ✗ Error: {result.error}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    print()


def demo_file_examples():
    """Demonstrate file execution examples."""
    print_section("File Execution Examples")

    # Initialize client with file examples
    client = MCIClient(
        json_file_path="examples/file_example.json",
        env_vars={"CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"), "USERNAME": "demo_user"},
    )

    print("Available File tools:")
    for tool_name in client.list_tools():
        print(f"  - {tool_name}")
    print()

    # Execute load_template tool (requires text.txt to exist)
    print("Executing: load_template")
    print("  Note: This tool reads ./text.txt with placeholder substitution")
    try:
        result = client.execute(tool_name="load_template", properties={"username": "Alice"})

        if not result.isError:
            print("  ✓ Success!")
            print(f"  Content preview: {result.content[:200]}...")
        else:
            print(f"  ✗ Error: {result.error}")
            print("  (This is expected if text.txt doesn't exist)")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    print()


def demo_text_examples():
    """Demonstrate text execution examples."""
    print_section("Text Execution Examples")

    # Initialize client with text examples
    client = MCIClient(
        json_file_path="examples/text_example.json",
        env_vars={
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "TIMESTAMP": datetime.now().isoformat(),
            "APP_VERSION": "1.0.0",
        },
    )

    print("Available Text tools:")
    for tool_name in client.list_tools():
        print(f"  - {tool_name}")
    print()

    # Execute generate_message tool
    print("Executing: generate_message")
    result = client.execute(tool_name="generate_message", properties={"username": "Bob"})

    if not result.isError:
        print("  ✓ Success!")
        print(f"  Output: {result.content}")
    else:
        print(f"  ✗ Error: {result.error}")
    print()

    # Execute generate_welcome tool
    print("Executing: generate_welcome")
    result = client.execute(
        tool_name="generate_welcome", properties={"username": "Alice", "email": "alice@example.com"}
    )

    if not result.isError:
        print("  ✓ Success!")
        print(f"  Output: {result.content}")
    else:
        print(f"  ✗ Error: {result.error}")
    print()

    # Execute status_message tool
    print("Executing: status_message")
    result = client.execute(tool_name="status_message", properties={"status": "operational"})

    if not result.isError:
        print("  ✓ Success!")
        print(f"  Output: {result.content}")
    else:
        print(f"  ✗ Error: {result.error}")
    print()


def demo_mixed_examples():
    """Demonstrate mixed execution examples (all types)."""
    print_section("Mixed Execution Examples (All Types)")

    # Initialize client with mixed examples
    client = MCIClient(
        json_file_path="examples/mixed_example.json",
        env_vars={
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "BEARER_TOKEN": "demo-bearer-token",
        },
    )

    print("Available tools (all execution types):")
    all_tools = client.tools()
    for tool in all_tools:
        print(f"  - {tool.name} ({tool.execution.type}): {tool.title}")
    print()

    # Demonstrate filtering
    print("Filtering to only text tools:")
    text_tools = client.only(["generate_message", "generate_welcome"])
    print(f"  Found {len(text_tools)} tools:")
    for tool in text_tools:
        print(f"  - {tool.name}")
    print()

    # Execute a text tool from mixed example
    print("Executing: generate_message from mixed example")
    result = client.execute(tool_name="generate_message", properties={"username": "Charlie"})

    if not result.isError:
        print("  ✓ Success!")
        print(f"  Output: {result.content}")
    else:
        print(f"  ✗ Error: {result.error}")
    print()


def demo_tool_inspection():
    """Demonstrate tool inspection capabilities."""
    print_section("Tool Inspection")

    client = MCIClient(json_file_path="examples/text_example.json")

    # Get schema for a specific tool
    print("Getting schema for 'generate_report_summary':")
    schema = client.get_tool_schema("generate_report_summary")
    print(f"  Required properties: {schema.get('required', [])}")
    print("  Properties:")
    for prop_name, prop_details in schema.get("properties", {}).items():
        print(f"    - {prop_name}: {prop_details.get('description', 'No description')}")
    print()

    # Get full tool details
    print("Getting full tool details:")
    tools = client.tools()
    for tool in tools[:2]:  # Show first 2 tools
        print(f"\nTool: {tool.name}")
        print(f"  Title: {tool.title}")
        print(f"  Description: {tool.description}")
        print(f"  Execution Type: {tool.execution.type}")
        if hasattr(tool.execution, "text"):
            print(f"  Template: {tool.execution.text}")
    print()


def main():
    """Run all demonstration examples."""
    print("\n" + "=" * 80)
    print("  MCI Python Adapter - Example Usage Demonstration")
    print("=" * 80)

    # Check if we're in the right directory
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print("\nError: examples/ directory not found.")
        print("Please run this script from the repository root directory.")
        return

    try:
        # Run all demonstrations
        demo_http_examples()
        demo_cli_examples()
        demo_file_examples()
        demo_text_examples()
        demo_mixed_examples()
        demo_tool_inspection()

        print("\n" + "=" * 80)
        print("  All Examples Completed!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
