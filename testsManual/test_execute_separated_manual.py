#!/usr/bin/env python3
"""
Manual test for executeSeparated method.

This script demonstrates how to use the new executeSeparated method
to execute Tool models directly without registering them in the schema.

Run with: uv run python testsManual/test_execute_separated_manual.py
"""

from mcipy import MCIClient
from mcipy.models import (
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    TextExecutionConfig,
    Tool,
)


def test_text_execution():
    """Test executeSeparated with text execution."""
    print("=" * 70)
    print("Test 1: Text Execution with Template Substitution")
    print("=" * 70)

    # Create a minimal client
    client = MCIClient(schema_file_path="example.mci.json")

    # Create a dynamic tool
    tool = Tool(
        name="dynamic_greeting",
        description="Generate a personalized greeting",
        execution=TextExecutionConfig(
            type="text",
            text="Hello {{props.name}}! Welcome to {{env.LOCATION}}. Your role is {{props.role}}.",
        ),
    )

    # Execute the tool
    result = client.executeSeparated(
        tool=tool,
        properties={"name": "Alice", "role": "Developer"},
        env_vars={"LOCATION": "San Francisco"},
    )

    # Display result
    print(f"Success: {not result.result.isError}")
    print(f"Output: {result.result.content[0].text}")
    print()


def test_cli_execution():
    """Test executeSeparated with CLI execution."""
    print("=" * 70)
    print("Test 2: CLI Execution")
    print("=" * 70)

    client = MCIClient(schema_file_path="example.mci.json")

    # Create a tool that uses echo command
    tool = Tool(
        name="echo_tool",
        description="Echo a message using system command",
        execution=CLIExecutionConfig(
            type="cli", command="echo", args=["Message: {{props.text}}"]
        ),
    )

    result = client.executeSeparated(
        tool=tool, properties={"text": "Hello from CLI!"}
    )

    print(f"Success: {not result.result.isError}")
    print(f"Output: {result.result.content[0].text.strip()}")
    print()


def test_with_input_schema():
    """Test executeSeparated with input schema validation."""
    print("=" * 70)
    print("Test 3: Input Schema Validation and Default Values")
    print("=" * 70)

    client = MCIClient(schema_file_path="example.mci.json")

    # Tool with input schema
    tool = Tool(
        name="formatted_message",
        description="Create a formatted message",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "greeting": {"type": "string", "default": "Hi"},
                "suffix": {"type": "string", "default": "Have a great day!"},
            },
            "required": ["name"],
        },
        execution=TextExecutionConfig(
            type="text",
            text="{{props.greeting}} {{props.name}}! {{props.suffix}}",
        ),
    )

    # Test with only required properties (should use defaults)
    print("Testing with defaults:")
    result1 = client.executeSeparated(tool=tool, properties={"name": "Bob"})
    print(f"  Output: {result1.result.content[0].text}")

    # Test with custom values
    print("Testing with custom values:")
    result2 = client.executeSeparated(
        tool=tool,
        properties={
            "name": "Charlie",
            "greeting": "Greetings",
            "suffix": "See you soon!",
        },
    )
    print(f"  Output: {result2.result.content[0].text}")
    print()


def test_tool_registry_isolation():
    """Test that executeSeparated doesn't affect the tool registry."""
    print("=" * 70)
    print("Test 4: Tool Registry Isolation")
    print("=" * 70)

    client = MCIClient(schema_file_path="example.mci.json")

    # Get initial tool list
    initial_tools = client.list_tools()
    print(f"Initial tools in registry: {len(initial_tools)}")
    print(f"  {', '.join(initial_tools[:3])}...")

    # Execute a dynamic tool
    dynamic_tool = Tool(
        name="temporary_tool",
        description="This tool won't be registered",
        execution=TextExecutionConfig(type="text", text="Temporary output"),
    )

    result = client.executeSeparated(tool=dynamic_tool)
    print(f"\nExecuted dynamic tool: {dynamic_tool.name}")
    print(f"  Output: {result.result.content[0].text}")

    # Verify tool list hasn't changed
    final_tools = client.list_tools()
    print(f"\nFinal tools in registry: {len(final_tools)}")
    print(f"  Registry unchanged: {initial_tools == final_tools}")
    print(
        f"  Dynamic tool in registry: {'temporary_tool' in final_tools}"
    )
    print()


def test_environment_variable_override():
    """Test environment variable override with executeSeparated."""
    print("=" * 70)
    print("Test 5: Environment Variable Override")
    print("=" * 70)

    # Client with default env vars
    client = MCIClient(
        schema_file_path="example.mci.json",
        env_vars={"API_KEY": "client-default-key", "ENVIRONMENT": "production"},
    )

    tool = Tool(
        name="api_info",
        execution=TextExecutionConfig(
            type="text",
            text="API Key: {{env.API_KEY}} | Environment: {{env.ENVIRONMENT}}",
        ),
    )

    # Use client's env vars
    print("Using client's environment variables:")
    result1 = client.executeSeparated(tool=tool, env_vars=None)
    print(f"  {result1.result.content[0].text}")

    # Override with custom env vars
    print("\nUsing custom environment variables:")
    result2 = client.executeSeparated(
        tool=tool,
        env_vars={"API_KEY": "test-key-123", "ENVIRONMENT": "testing"},
    )
    print(f"  {result2.result.content[0].text}")

    # Verify client's env vars are unchanged
    print("\nVerifying client's env vars unchanged:")
    result3 = client.executeSeparated(tool=tool, env_vars=None)
    print(f"  {result3.result.content[0].text}")
    print()


def test_error_handling():
    """Test error handling in executeSeparated."""
    print("=" * 70)
    print("Test 6: Error Handling")
    print("=" * 70)

    client = MCIClient(schema_file_path="example.mci.json")

    # Tool with required properties
    tool = Tool(
        name="required_props_tool",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        execution=TextExecutionConfig(type="text", text="Hello {{props.name}}"),
    )

    # Try to execute without required property
    print("Testing missing required property:")
    try:
        client.executeSeparated(tool=tool, properties={})
        print("  ❌ Should have raised an error!")
    except Exception as e:
        print(f"  ✓ Correctly raised error: {type(e).__name__}")
        print(f"    Message: {str(e)}")

    # Test with validating mode
    print("\nTesting validating mode:")
    validating_client = MCIClient(
        schema_file_path="example.mci.json", validating=True
    )
    try:
        validating_client.executeSeparated(tool=tool)
        print("  ❌ Should have raised an error!")
    except Exception as e:
        print(f"  ✓ Correctly raised error: {type(e).__name__}")
        print(f"    Message: {str(e)}")
    print()


def main():
    """Run all manual tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Manual Tests for executeSeparated Method".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    try:
        test_text_execution()
        test_cli_execution()
        test_with_input_schema()
        test_tool_registry_isolation()
        test_environment_variable_override()
        test_error_handling()

        print("=" * 70)
        print("✅ All manual tests completed successfully!")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
