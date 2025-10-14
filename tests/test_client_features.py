"""
Feature tests for MCIClient class.

End-to-end tests demonstrating realistic usage scenarios of the MCIClient API.
"""

from pathlib import Path

import pytest

from mcipy import MCIClient, MCIClientError


class TestMCIClientFeatures:
    """Feature tests for MCIClient with realistic usage scenarios."""

    def test_complete_workflow_with_example_schema(self):
        """Test complete workflow using the example schema file."""
        # Use the example schema from the repository
        schema_path = "example.mci.json"

        # Skip if schema file doesn't exist
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found - test must run from repo root")

        # Initialize client with environment variables
        env_vars = {
            "API_KEY": "test-api-key",
            "BEARER_TOKEN": "test-bearer-token",
            "CURRENT_TIMESTAMP": "2024-01-15T10:30:00Z",
            "CURRENT_DATE": "2024-01-15",
        }
        client = MCIClient(json_file_path=schema_path, env_vars=env_vars)

        # Verify client initialization
        assert client is not None

        # List all tools
        tool_names = client.list_tools()
        assert len(tool_names) > 0
        assert "get_weather" in tool_names
        assert "create_report" in tool_names
        assert "search_files" in tool_names
        assert "load_template" in tool_names
        assert "generate_message" in tool_names

        # Get all tool objects
        all_tools = client.tools()
        assert len(all_tools) == len(tool_names)

        # Filter to include only specific tools
        weather_tools = client.only(["get_weather", "load_template"])
        assert len(weather_tools) == 2
        weather_names = [t.name for t in weather_tools]
        assert "get_weather" in weather_names
        assert "load_template" in weather_names

        # Filter to exclude specific tools
        safe_tools = client.without(["create_report", "search_files"])
        safe_names = [t.name for t in safe_tools]
        assert "create_report" not in safe_names
        assert "search_files" not in safe_names

        # Get schema for a specific tool
        weather_schema = client.get_tool_schema("get_weather")
        assert "properties" in weather_schema
        assert "location" in weather_schema["properties"]
        assert "required" in weather_schema
        assert "location" in weather_schema["required"]

        # Execute a text generation tool (doesn't require network/filesystem)
        result = client.execute("generate_message", properties={"username": "TestUser"})
        assert result is not None
        assert result.isError is False
        assert result.content is not None
        assert isinstance(result.content, str)
        assert "TestUser" in result.content

    def test_client_with_multiple_env_var_scenarios(self):
        """Test client behavior with different environment variable scenarios."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        # Test 1: Client with no env vars
        client1 = MCIClient(json_file_path=schema_path)
        assert len(client1.list_tools()) > 0

        # Test 2: Client with env vars
        client2 = MCIClient(json_file_path=schema_path, env_vars={"KEY": "value"})
        assert len(client2.list_tools()) > 0

        # Test 3: Multiple clients are independent
        assert len(client1.list_tools()) == len(client2.list_tools())

    def test_filtering_combinations(self):
        """Test various filtering combinations."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        client = MCIClient(json_file_path=schema_path)

        # Test empty filter lists
        assert len(client.only([])) == 0
        assert len(client.without([])) == len(client.list_tools())

        # Test filtering with nonexistent tools
        result = client.only(["nonexistent_tool"])
        assert len(result) == 0

        result = client.without(["nonexistent_tool"])
        assert len(result) == len(client.list_tools())

        # Test filtering all tools
        all_names = client.list_tools()
        result = client.without(all_names)
        assert len(result) == 0

    def test_execute_with_property_validation(self):
        """Test execution with property validation."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        client = MCIClient(json_file_path=schema_path)

        # Test executing with required properties missing
        with pytest.raises(MCIClientError) as exc_info:
            client.execute("get_weather", properties={})
        assert "requires properties" in str(exc_info.value).lower()
        assert "location" in str(exc_info.value).lower()

        # Test executing with all required properties
        # Note: This will fail at HTTP level (no real API), but validation passes
        # We're just testing the client API here, not actual HTTP execution
        result = client.execute("generate_message", properties={"username": "ValidUser"})
        assert result is not None

    def test_get_tool_schema_for_all_tools(self):
        """Test getting schema for all tools in the example file."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        client = MCIClient(json_file_path=schema_path)

        # Get schema for each tool
        for tool_name in client.list_tools():
            schema = client.get_tool_schema(tool_name)
            assert isinstance(schema, dict)
            # Schema can be empty dict or have properties

    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        # Test 1: Nonexistent schema file
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(json_file_path="/nonexistent/path/schema.json")
        assert "Failed to load schema" in str(exc_info.value)

        # Test 2: Valid client, but nonexistent tool
        client = MCIClient(json_file_path=schema_path)

        with pytest.raises(MCIClientError) as exc_info:
            client.execute("nonexistent_tool")
        assert "Tool not found" in str(exc_info.value)

        with pytest.raises(MCIClientError) as exc_info:
            client.get_tool_schema("nonexistent_tool")
        assert "Tool not found" in str(exc_info.value)

    def test_text_tool_execution_variations(self):
        """Test various text tool execution scenarios."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        client = MCIClient(
            json_file_path=schema_path,
            env_vars={"CURRENT_DATE": "2024-01-15", "USERNAME": "EnvUser"},
        )

        # Execute with simple properties
        result1 = client.execute("generate_message", properties={"username": "User1"})
        assert result1.isError is False
        assert isinstance(result1.content, str)
        assert "User1" in result1.content

        # Execute with different properties
        result2 = client.execute("generate_message", properties={"username": "User2"})
        assert result2.isError is False
        assert isinstance(result2.content, str)
        assert "User2" in result2.content

        # Results should be different
        assert result1.content != result2.content

    def test_client_state_after_operations(self):
        """Test that client state remains consistent after operations."""
        schema_path = "example.mci.json"
        if not Path(schema_path).exists():
            pytest.skip("example.mci.json not found")

        client = MCIClient(json_file_path=schema_path, env_vars={"KEY": "value"})

        # Initial state
        initial_tools = client.list_tools()

        # Perform various operations
        client.tools()
        client.only(["get_weather"])
        client.without(["create_report"])
        client.get_tool_schema("get_weather")
        client.execute("generate_message", properties={"username": "Test"})

        # Verify state hasn't changed
        assert client.list_tools() == initial_tools
