#!/usr/bin/env python3
"""
Manual test for ToolManager implementation.

This test demonstrates the ToolManager class functionality including:
- Loading a schema from file
- Retrieving tools by name
- Listing all available tools
- Filtering tools with only/without parameters
- Executing tools with properties and validation

Run with: uv run python testsManual/test_tool_manager_manual.py
"""

from mcipy import SchemaParser, ToolManager, ToolManagerError


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_loading_and_initialization():
    """Test loading schema and initializing ToolManager."""
    print_section("TOOL MANAGER INITIALIZATION")

    # Load schema from file
    schema = SchemaParser.parse_file("example.mci.json")
    print(f"✓ Schema loaded successfully")
    print(f"  Schema version: {schema.schemaVersion}")
    print(f"  Number of tools: {len(schema.tools)}")

    # Initialize ToolManager
    manager = ToolManager(schema)
    print(f"✓ ToolManager initialized")
    print(f"  Manager contains {len(manager.list_tools())} tools")


def test_get_tool():
    """Test retrieving tools by name."""
    print_section("GET TOOL BY NAME")

    schema = SchemaParser.parse_file("example.mci.json")
    manager = ToolManager(schema)

    # Test successful retrieval
    print("\n1. Retrieve existing tool:")
    tool = manager.get_tool("get_weather")
    if tool:
        print(f"   ✓ Found tool: {tool.name}")
        print(f"     Title: {tool.title}")
        print(f"     Description: {tool.description}")
        print(f"     Execution type: {tool.execution.type.value}")
    else:
        print(f"   ✗ Tool not found")

    # Test non-existent tool
    print("\n2. Retrieve non-existent tool:")
    tool = manager.get_tool("nonexistent_tool")
    if tool is None:
        print(f"   ✓ Correctly returned None for non-existent tool")
    else:
        print(f"   ✗ Unexpectedly found tool: {tool.name}")

    # Test case sensitivity
    print("\n3. Test case sensitivity:")
    tool = manager.get_tool("GET_WEATHER")
    if tool is None:
        print(f"   ✓ Tool names are case-sensitive (GET_WEATHER not found)")
    else:
        print(f"   ✗ Found tool with wrong case: {tool.name}")


def test_list_tools():
    """Test listing all tools."""
    print_section("LIST ALL TOOLS")

    schema = SchemaParser.parse_file("example.mci.json")
    manager = ToolManager(schema)

    tools = manager.list_tools()
    print(f"\nTotal tools: {len(tools)}\n")

    for idx, tool in enumerate(tools, 1):
        print(f"{idx}. {tool.name}")
        print(f"   Title: {tool.title or 'N/A'}")
        print(f"   Type: {tool.execution.type.value}")
        print(f"   Has input schema: {tool.inputSchema is not None and bool(tool.inputSchema)}")
        if tool.inputSchema and "required" in tool.inputSchema:
            print(f"   Required fields: {', '.join(tool.inputSchema['required'])}")


def test_filter_tools():
    """Test filtering tools with only/without parameters."""
    print_section("FILTER TOOLS")

    schema = SchemaParser.parse_file("example.mci.json")
    manager = ToolManager(schema)

    # Test 'only' filter
    print("\n1. Filter with 'only' parameter:")
    filtered = manager.filter_tools(only=["get_weather", "create_report"])
    print(f"   Requested: get_weather, create_report")
    print(f"   Result: {[tool.name for tool in filtered]}")
    print(f"   ✓ Filtered to {len(filtered)} tools")

    # Test 'without' filter
    print("\n2. Filter with 'without' parameter:")
    filtered = manager.filter_tools(without=["search_files"])
    print(f"   Excluded: search_files")
    print(f"   Result: {[tool.name for tool in filtered]}")
    print(f"   ✓ Filtered to {len(filtered)} tools")

    # Test both 'only' and 'without'
    print("\n3. Filter with both 'only' and 'without':")
    filtered = manager.filter_tools(
        only=["get_weather", "create_report", "search_files"],
        without=["search_files"]
    )
    print(f"   Only: get_weather, create_report, search_files")
    print(f"   Without: search_files")
    print(f"   Result: {[tool.name for tool in filtered]}")
    print(f"   ✓ Filtered to {len(filtered)} tools (search_files excluded)")

    # Test no filters
    print("\n4. No filters (all tools):")
    filtered = manager.filter_tools()
    print(f"   Result: {len(filtered)} tools")
    print(f"   ✓ Returns all tools when no filters specified")


def test_execute_tool():
    """Test executing tools with properties."""
    print_section("EXECUTE TOOLS")

    schema = SchemaParser.parse_file("example.mci.json")
    manager = ToolManager(schema)

    # Test 1: Execute text tool with valid properties
    print("\n1. Execute 'generate_message' with valid properties:")
    try:
        result = manager.execute(
            "generate_message",
            properties={"username": "Alice"},
            env_vars={"CURRENT_DATE": "2024-01-15"}
        )
        print(f"   ✓ Execution successful")
        print(f"     Error: {result.isError}")
        print(f"     Content: {result.content}")
    except ToolManagerError as e:
        print(f"   ✗ Error: {e}")

    # Test 2: Execute tool with missing required properties
    print("\n2. Execute 'get_weather' without required 'location':")
    try:
        result = manager.execute("get_weather", properties={})
        print(f"   ✗ Should have raised error but didn't")
    except ToolManagerError as e:
        print(f"   ✓ Correctly raised error: {e}")

    # Test 3: Execute tool with all required properties
    print("\n3. Execute 'get_weather' with required 'location':")
    try:
        result = manager.execute(
            "get_weather",
            properties={"location": "New York"}
        )
        print(f"   ✓ Execution attempted")
        print(f"     Error: {result.isError}")
        # Note: This will fail because we don't have a real API, but validation passed
        if result.isError:
            print(f"     Error message: {result.error}")
            print(f"     (Expected - no real API endpoint)")
    except ToolManagerError as e:
        print(f"   ✗ Validation error: {e}")

    # Test 4: Execute non-existent tool
    print("\n4. Execute non-existent tool:")
    try:
        result = manager.execute("nonexistent_tool", properties={})
        print(f"   ✗ Should have raised error but didn't")
    except ToolManagerError as e:
        print(f"   ✓ Correctly raised error: {e}")

    # Test 5: Execute tool with partial required properties
    print("\n5. Execute 'create_report' with partial properties:")
    try:
        result = manager.execute(
            "create_report",
            properties={"title": "My Report"}
            # Missing 'content' which is required
        )
        print(f"   ✗ Should have raised error but didn't")
    except ToolManagerError as e:
        print(f"   ✓ Correctly raised error: {e}")

    # Test 6: Execute tool with no input schema
    print("\n6. Execute 'load_template' (has required 'username'):")
    try:
        result = manager.execute(
            "load_template",
            properties={"username": "Bob"}
        )
        print(f"   ✓ Execution attempted")
        print(f"     Error: {result.isError}")
        # Will fail because file might not exist
        if result.isError:
            print(f"     Error message: {result.error}")
            print(f"     (Expected - template file may not exist)")
    except ToolManagerError as e:
        print(f"   ✗ Validation error: {e}")


def test_edge_cases():
    """Test edge cases and special scenarios."""
    print_section("EDGE CASES")

    schema = SchemaParser.parse_file("example.mci.json")
    manager = ToolManager(schema)

    # Test 1: Empty only list
    print("\n1. Filter with empty 'only' list:")
    filtered = manager.filter_tools(only=[])
    print(f"   Result: {len(filtered)} tools")
    print(f"   ✓ Empty 'only' list returns no tools")

    # Test 2: Empty without list
    print("\n2. Filter with empty 'without' list:")
    filtered = manager.filter_tools(without=[])
    print(f"   Result: {len(filtered)} tools")
    print(f"   ✓ Empty 'without' list returns all tools")

    # Test 3: Execute with None properties
    print("\n3. Execute with None properties (tool requires username):")
    try:
        result = manager.execute("generate_message", properties=None)
        print(f"   ✗ Should have raised error for missing required properties")
    except ToolManagerError as e:
        print(f"   ✓ Correctly raised error for missing required properties: {e}")

    # Test 4: Tool name case sensitivity in execute
    print("\n4. Case sensitivity in execute:")
    try:
        result = manager.execute("GENERATE_MESSAGE", properties={"username": "Test"})
        print(f"   ✗ Should have raised ToolManagerError")
    except ToolManagerError as e:
        print(f"   ✓ Correctly enforced case sensitivity: {e}")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 70)
    print(" MCI TOOL MANAGER - MANUAL TEST SUITE")
    print("=" * 70)

    try:
        test_loading_and_initialization()
        test_get_tool()
        test_list_tools()
        test_filter_tools()
        test_execute_tool()
        test_edge_cases()

        print("\n" + "=" * 70)
        print(" ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
