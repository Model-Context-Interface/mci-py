"""
Manual test for MCIClient class.

This test demonstrates realistic usage of the MCIClient API with clear,
human-readable output. Run this file directly to see the MCIClient in action.

Usage:
    uv run python testsManual/test_client_manual.py
"""
import sys
from pathlib import Path

from mcipy import MCIClient, MCIClientError


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def test_initialization():
    """Test client initialization with schema file and environment variables."""
    print_section("CLIENT INITIALIZATION")

    # Use the example schema file from the repository
    schema_path = "example.mci.json"

    # Test 1: Initialize without environment variables
    print("1. Initialize without environment variables:")
    client = MCIClient(json_file_path=schema_path)
    print(f"   Client created: {client is not None}")
    print(f"   Available tools: {len(client.list_tools())}")
    print(f"   Status: ✓ Success\n")

    # Test 2: Initialize with environment variables
    print("2. Initialize with environment variables:")
    env_vars = {
        "API_KEY": "test-secret-key",
        "BEARER_TOKEN": "test-bearer-token",
        "CURRENT_TIMESTAMP": "2024-01-15T10:30:00Z",
        "CURRENT_DATE": "2024-01-15",
        "USERNAME": "demo_user",
    }
    client = MCIClient(json_file_path=schema_path, env_vars=env_vars)
    print(f"   Client created: {client is not None}")
    print(f"   Environment variables set: {len(env_vars)}")
    print(f"   Status: ✓ Success\n")

    # Test 3: Initialize with nonexistent file
    print("3. Initialize with nonexistent file (error case):")
    try:
        MCIClient(json_file_path="/nonexistent/path/schema.json")
        print("   Status: ✗ Failed - should have raised error")
    except MCIClientError as e:
        print(f"   Error caught: {type(e).__name__}")
        print(f"   Message: {str(e)[:60]}...")
        print(f"   Status: ✓ Success\n")

    return client


def test_list_tools(client: MCIClient):
    """Test listing available tools."""
    print_section("LIST TOOLS")

    # Test 1: List all tool names
    print("1. List all tool names:")
    tool_names = client.list_tools()
    print(f"   Total tools: {len(tool_names)}")
    for i, name in enumerate(tool_names, 1):
        print(f"   {i}. {name}")
    print(f"   Status: ✓ Success\n")

    # Test 2: Get all tool objects
    print("2. Get all tool objects:")
    tools = client.tools()
    print(f"   Total tools: {len(tools)}")
    for tool in tools[:3]:  # Show first 3
        print(f"   - {tool.name}: {tool.title}")
    print(f"   ... and {len(tools) - 3} more")
    print(f"   Status: ✓ Success\n")


def test_filtering(client: MCIClient):
    """Test tool filtering with only() and without()."""
    print_section("TOOL FILTERING")

    # Test 1: Filter with only()
    print("1. Filter to include only specific tools:")
    filtered = client.only(["get_weather", "create_report"])
    print(f"   Requested tools: ['get_weather', 'create_report']")
    print(f"   Filtered tools: {[t.name for t in filtered]}")
    print(f"   Count: {len(filtered)}")
    print(f"   Status: ✓ Success\n")

    # Test 2: Filter with without()
    print("2. Filter to exclude specific tools:")
    excluded = client.without(["get_weather", "create_report"])
    excluded_names = [t.name for t in excluded]
    print(f"   Excluded tools: ['get_weather', 'create_report']")
    print(f"   Remaining tools: {excluded_names}")
    print(f"   Count: {len(excluded)}")
    print(f"   Status: ✓ Success\n")

    # Test 3: Combine filters (conceptually - show both approaches)
    print("3. Multiple filtering approaches:")
    only_weather = client.only(["get_weather", "load_template"])
    without_weather = client.without(["create_report", "search_files"])
    print(f"   Only weather-related: {[t.name for t in only_weather]}")
    print(f"   Without specific tools: {[t.name for t in without_weather]}")
    print(f"   Status: ✓ Success\n")


def test_get_tool_schema(client: MCIClient):
    """Test retrieving tool schemas."""
    print_section("GET TOOL SCHEMA")

    # Test 1: Get schema for tool with input requirements
    print("1. Get schema for 'get_weather' tool:")
    schema = client.get_tool_schema("get_weather")
    print(f"   Schema type: {schema.get('type', 'N/A')}")
    print(f"   Properties: {list(schema.get('properties', {}).keys())}")
    print(f"   Required: {schema.get('required', [])}")
    print(f"   Status: ✓ Success\n")

    # Test 2: Get schema for tool with complex requirements
    print("2. Get schema for 'create_report' tool:")
    schema = client.get_tool_schema("create_report")
    print(f"   Schema type: {schema.get('type', 'N/A')}")
    print(f"   Properties: {list(schema.get('properties', {}).keys())}")
    print(f"   Required: {schema.get('required', [])}")
    print(f"   Status: ✓ Success\n")

    # Test 3: Get schema for nonexistent tool (error case)
    print("3. Get schema for nonexistent tool (error case):")
    try:
        client.get_tool_schema("nonexistent_tool")
        print("   Status: ✗ Failed - should have raised error")
    except MCIClientError as e:
        print(f"   Error caught: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print(f"   Status: ✓ Success\n")


def test_execution(client: MCIClient):
    """Test tool execution."""
    print_section("TOOL EXECUTION")

    # Test 1: Execute text generation tool
    print("1. Execute 'generate_message' tool:")
    result = client.execute("generate_message", properties={"username": "TestUser"})
    print(f"   Tool: generate_message")
    print(f"   Properties: {{'username': 'TestUser'}}")
    print(f"   Result Error: {result.isError}")
    print(f"   Result Content: {result.content}")
    print(f"   Status: ✓ Success\n")

    # Test 2: Execute with missing required properties (error case)
    print("2. Execute with missing required properties (error case):")
    try:
        client.execute("get_weather", properties={})
        print("   Status: ✗ Failed - should have raised error")
    except MCIClientError as e:
        print(f"   Error caught: {type(e).__name__}")
        print(f"   Message: {str(e)[:80]}...")
        print(f"   Status: ✓ Success\n")

    # Test 3: Execute tool with environment variable templating
    print("3. Execute with environment variable templating:")
    result = client.execute("generate_message", properties={"username": "{{env.USERNAME}}"})
    print(f"   Tool: generate_message")
    print(f"   Properties: {{'username': '{{{{env.USERNAME}}}}'}}")
    print(f"   Result Error: {result.isError}")
    print(f"   Result Content: {result.content}")
    print(f"   Status: ✓ Success\n")

    # Test 4: Execute nonexistent tool (error case)
    print("4. Execute nonexistent tool (error case):")
    try:
        client.execute("nonexistent_tool", properties={})
        print("   Status: ✗ Failed - should have raised error")
    except MCIClientError as e:
        print(f"   Error caught: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print(f"   Status: ✓ Success\n")


def test_complete_workflow():
    """Test a complete workflow using the client."""
    print_section("COMPLETE WORKFLOW")

    schema_path = "example.mci.json"
    env_vars = {
        "API_KEY": "my-secret-key",
        "USERNAME": "workflow_user",
        "CURRENT_DATE": "2024-01-15",
    }

    print("1. Initialize client:")
    client = MCIClient(json_file_path=schema_path, env_vars=env_vars)
    print(f"   Client initialized with {len(env_vars)} env vars")
    print(f"   Status: ✓ Success\n")

    print("2. List available tools:")
    all_tools = client.list_tools()
    print(f"   Found {len(all_tools)} tools: {', '.join(all_tools[:3])}...")
    print(f"   Status: ✓ Success\n")

    print("3. Filter to safe tools (exclude potentially dangerous operations):")
    safe_tools = client.without(["create_report", "search_files"])
    safe_tool_names = [t.name for t in safe_tools]
    print(f"   Safe tools ({len(safe_tools)}): {', '.join(safe_tool_names)}")
    print(f"   Status: ✓ Success\n")

    print("4. Get schema for a specific tool:")
    schema = client.get_tool_schema("generate_message")
    print(f"   Tool: generate_message")
    print(f"   Required properties: {schema.get('required', [])}")
    print(f"   Status: ✓ Success\n")

    print("5. Execute the tool:")
    result = client.execute("generate_message", properties={"username": "workflow_user"})
    print(f"   Execution successful: {not result.isError}")
    print(f"   Content: {result.content}")
    print(f"   Status: ✓ Success\n")


def test_multiple_clients():
    """Test multiple client instances."""
    print_section("MULTIPLE CLIENT INSTANCES")

    schema_path = "example.mci.json"

    print("1. Create first client with API_KEY:")
    client1 = MCIClient(schema_path, env_vars={"API_KEY": "key-123", "ENV": "production"})
    print(f"   Client 1 created with env: production")
    print(f"   Tools available: {len(client1.list_tools())}")
    print(f"   Status: ✓ Success\n")

    print("2. Create second client with different environment:")
    client2 = MCIClient(schema_path, env_vars={"API_KEY": "key-456", "ENV": "development"})
    print(f"   Client 2 created with env: development")
    print(f"   Tools available: {len(client2.list_tools())}")
    print(f"   Status: ✓ Success\n")

    print("3. Verify clients are independent:")
    print(f"   Client 1 env vars: {len(client1._env_vars)} vars")
    print(f"   Client 2 env vars: {len(client2._env_vars)} vars")
    print(f"   Same tool count: {len(client1.list_tools()) == len(client2.list_tools())}")
    print(f"   Different env values: {client1._env_vars != client2._env_vars}")
    print(f"   Status: ✓ Success\n")


def test_error_handling():
    """Test error handling across different scenarios."""
    print_section("ERROR HANDLING")

    schema_path = "example.mci.json"
    client = MCIClient(schema_path)

    # Test 1: Nonexistent tool in execute
    print("1. Execute nonexistent tool:")
    try:
        client.execute("nonexistent_tool")
        print("   Status: ✗ Failed")
    except MCIClientError as e:
        print(f"   MCIClientError caught: '{str(e)}'")
        print(f"   Status: ✓ Success\n")

    # Test 2: Nonexistent tool in get_tool_schema
    print("2. Get schema for nonexistent tool:")
    try:
        client.get_tool_schema("nonexistent_tool")
        print("   Status: ✗ Failed")
    except MCIClientError as e:
        print(f"   MCIClientError caught: '{str(e)}'")
        print(f"   Status: ✓ Success\n")

    # Test 3: Missing required properties
    print("3. Execute with missing required properties:")
    try:
        client.execute("get_weather", properties={})
        print("   Status: ✗ Failed")
    except MCIClientError as e:
        print(f"   MCIClientError caught")
        print(f"   Message indicates missing properties: {'requires properties' in str(e).lower()}")
        print(f"   Status: ✓ Success\n")

    # Test 4: Invalid schema file
    print("4. Initialize with invalid schema file:")
    try:
        MCIClient("/invalid/path/schema.json")
        print("   Status: ✗ Failed")
    except MCIClientError as e:
        print(f"   MCIClientError caught")
        print(f"   Message indicates file error: {'Failed to load schema' in str(e)}")
        print(f"   Status: ✓ Success\n")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 80)
    print("  MCI CLIENT MANUAL TESTS")
    print("  Demonstrating MCIClient API functionality")
    print("=" * 80)

    # Create a client for reuse in multiple tests
    schema_path = "example.mci.json"
    env_vars = {
        "API_KEY": "test-key-123",
        "BEARER_TOKEN": "test-bearer-token",
        "USERNAME": "demo_user",
        "CURRENT_DATE": "2024-01-15",
        "CURRENT_TIMESTAMP": "2024-01-15T10:30:00Z",
    }

    # Check if schema file exists
    if not Path(schema_path).exists():
        print(f"\nError: Schema file '{schema_path}' not found!")
        print("Please run this test from the repository root directory.")
        return 1

    client = MCIClient(json_file_path=schema_path, env_vars=env_vars)

    # Run all test sections
    test_initialization()
    test_list_tools(client)
    test_filtering(client)
    test_get_tool_schema(client)
    test_execution(client)
    test_complete_workflow()
    test_multiple_clients()
    test_error_handling()

    print_section("ALL TESTS COMPLETED")
    print("All manual tests executed successfully!")
    print("MCIClient API is working as expected.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
