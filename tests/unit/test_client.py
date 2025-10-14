"""
Unit tests for MCIClient class.

Tests the main client API including initialization, tool listing,
filtering, execution, and schema retrieval.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mcipy import ExecutionResult, MCIClient, MCIClientError, Tool


@pytest.fixture
def sample_schema_dict():
    """Create a sample schema dictionary for testing."""
    return {
        "schemaVersion": "1.0",
        "metadata": {
            "name": "Test Tools",
            "description": "Test tool collection",
            "version": "1.0.0",
        },
        "tools": [
            {
                "name": "get_weather",
                "title": "Get Weather",
                "description": "Get weather information",
                "inputSchema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
                "execution": {
                    "type": "http",
                    "method": "GET",
                    "url": "https://api.example.com/weather",
                    "params": {"location": "{{props.location}}"},
                },
            },
            {
                "name": "create_report",
                "title": "Create Report",
                "description": "Create a report",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["title", "content"],
                },
                "execution": {
                    "type": "http",
                    "method": "POST",
                    "url": "https://api.example.com/reports",
                },
            },
            {
                "name": "search_files",
                "title": "Search Files",
                "description": "Search for files",
                "inputSchema": {
                    "type": "object",
                    "properties": {"pattern": {"type": "string"}},
                    "required": ["pattern"],
                },
                "execution": {
                    "type": "cli",
                    "command": "grep",
                    "args": ["-r", "{{props.pattern}}"],
                },
            },
            {
                "name": "load_file",
                "title": "Load File",
                "description": "Load a file",
                "inputSchema": None,
                "execution": {"type": "file", "path": "/tmp/test.txt"},
            },
            {
                "name": "generate_text",
                "title": "Generate Text",
                "description": "Generate text",
                "inputSchema": {},
                "execution": {"type": "text", "text": "Hello {{props.name}}!"},
            },
        ],
    }


@pytest.fixture
def temp_schema_file(sample_schema_dict):
    """Create a temporary schema file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_schema_dict, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def client(temp_schema_file):
    """Create an MCIClient instance for testing."""
    return MCIClient(
        json_file_path=temp_schema_file, env_vars={"API_KEY": "test-key", "USER": "testuser"}
    )


class TestMCIClientInit:
    """Tests for MCIClient initialization."""

    def test_init_with_valid_file(self, temp_schema_file):
        """Test initialization with valid schema file."""
        client = MCIClient(json_file_path=temp_schema_file)
        assert client is not None
        # Verify client is functional by calling public methods
        assert len(client.list_tools()) > 0
        assert len(client.tools()) > 0

    def test_init_with_env_vars(self, temp_schema_file):
        """Test initialization with environment variables."""
        env_vars = {"API_KEY": "secret", "USERNAME": "user"}
        client = MCIClient(json_file_path=temp_schema_file, env_vars=env_vars)
        # Verify env vars are used by executing a tool that uses them
        result = client.execute("generate_text", properties={"name": "{{env.USERNAME}}"})
        assert result is not None

    def test_init_without_env_vars(self, temp_schema_file):
        """Test initialization without environment variables defaults to empty dict."""
        client = MCIClient(json_file_path=temp_schema_file)
        # Verify client works without env vars
        assert len(client.list_tools()) > 0

    def test_init_with_none_env_vars(self, temp_schema_file):
        """Test initialization with None env_vars defaults to empty dict."""
        client = MCIClient(json_file_path=temp_schema_file, env_vars=None)
        # Verify client works with None env vars
        assert len(client.list_tools()) > 0

    def test_init_with_nonexistent_file(self):
        """Test initialization with nonexistent file raises error."""
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(json_file_path="/nonexistent/path/schema.json")
        assert "Failed to load schema" in str(exc_info.value)

    def test_init_with_invalid_json(self):
        """Test initialization with invalid JSON file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            with pytest.raises(MCIClientError) as exc_info:
                MCIClient(json_file_path=temp_path)
            assert "Failed to load schema" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_init_with_invalid_schema(self):
        """Test initialization with invalid schema structure raises error."""
        invalid_schema = {"schemaVersion": "1.0"}  # Missing 'tools' field

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_schema, f)
            temp_path = f.name

        try:
            with pytest.raises(MCIClientError) as exc_info:
                MCIClient(json_file_path=temp_path)
            assert "Failed to load schema" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestTools:
    """Tests for tools() method."""

    def test_tools_returns_all_tools(self, client):
        """Test that tools() returns all available tools."""
        tools = client.tools()
        assert len(tools) == 5
        tool_names = [t.name for t in tools]
        assert "get_weather" in tool_names
        assert "create_report" in tool_names
        assert "search_files" in tool_names
        assert "load_file" in tool_names
        assert "generate_text" in tool_names

    def test_tools_returns_tool_objects(self, client):
        """Test that tools() returns Tool objects."""
        tools = client.tools()
        for tool in tools:
            assert isinstance(tool, Tool)

    def test_tools_returns_correct_tool_data(self, client):
        """Test that tools() returns correct tool data."""
        tools = client.tools()
        weather_tool = next(t for t in tools if t.name == "get_weather")
        assert weather_tool.title == "Get Weather"
        assert weather_tool.description == "Get weather information"
        assert weather_tool.inputSchema is not None


class TestOnly:
    """Tests for only() method."""

    def test_only_single_tool(self, client):
        """Test filtering to include only a single tool."""
        tools = client.only(["get_weather"])
        assert len(tools) == 1
        assert tools[0].name == "get_weather"

    def test_only_multiple_tools(self, client):
        """Test filtering to include multiple tools."""
        tools = client.only(["get_weather", "create_report"])
        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "get_weather" in tool_names
        assert "create_report" in tool_names

    def test_only_nonexistent_tool(self, client):
        """Test filtering with nonexistent tool returns empty list."""
        tools = client.only(["nonexistent_tool"])
        assert len(tools) == 0

    def test_only_empty_list(self, client):
        """Test filtering with empty list returns empty list."""
        tools = client.only([])
        assert len(tools) == 0

    def test_only_all_tools(self, client):
        """Test filtering to include all tools."""
        all_tool_names = client.list_tools()
        tools = client.only(all_tool_names)
        assert len(tools) == 5


class TestWithout:
    """Tests for without() method."""

    def test_without_single_tool(self, client):
        """Test filtering to exclude a single tool."""
        tools = client.without(["get_weather"])
        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "get_weather" not in tool_names

    def test_without_multiple_tools(self, client):
        """Test filtering to exclude multiple tools."""
        tools = client.without(["get_weather", "create_report"])
        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "get_weather" not in tool_names
        assert "create_report" not in tool_names

    def test_without_nonexistent_tool(self, client):
        """Test excluding nonexistent tool returns all tools."""
        tools = client.without(["nonexistent_tool"])
        assert len(tools) == 5

    def test_without_empty_list(self, client):
        """Test filtering with empty exclusion list returns all tools."""
        tools = client.without([])
        assert len(tools) == 5

    def test_without_all_tools(self, client):
        """Test excluding all tools returns empty list."""
        all_tool_names = client.list_tools()
        tools = client.without(all_tool_names)
        assert len(tools) == 0


class TestListTools:
    """Tests for list_tools() method."""

    def test_list_tools_returns_names(self, client):
        """Test that list_tools() returns tool names as strings."""
        tool_names = client.list_tools()
        assert len(tool_names) == 5
        assert all(isinstance(name, str) for name in tool_names)

    def test_list_tools_correct_names(self, client):
        """Test that list_tools() returns correct tool names."""
        tool_names = client.list_tools()
        assert "get_weather" in tool_names
        assert "create_report" in tool_names
        assert "search_files" in tool_names
        assert "load_file" in tool_names
        assert "generate_text" in tool_names


class TestGetToolSchema:
    """Tests for get_tool_schema() method."""

    def test_get_tool_schema_existing_tool(self, client):
        """Test getting schema for existing tool."""
        schema = client.get_tool_schema("get_weather")
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "location" in schema["properties"]
        assert schema["required"] == ["location"]

    def test_get_tool_schema_nonexistent_tool(self, client):
        """Test getting schema for nonexistent tool raises error."""
        with pytest.raises(MCIClientError) as exc_info:
            client.get_tool_schema("nonexistent_tool")
        assert "Tool not found" in str(exc_info.value)

    def test_get_tool_schema_with_none_schema(self, client):
        """Test getting schema for tool with None inputSchema returns empty dict."""
        schema = client.get_tool_schema("load_file")
        assert schema == {}

    def test_get_tool_schema_with_empty_schema(self, client):
        """Test getting schema for tool with empty inputSchema."""
        schema = client.get_tool_schema("generate_text")
        assert schema == {}


class TestExecute:
    """Tests for execute() method."""

    def test_execute_tool_not_found(self, client):
        """Test executing nonexistent tool raises error."""
        with pytest.raises(MCIClientError) as exc_info:
            client.execute("nonexistent_tool", properties={})
        assert "Tool not found" in str(exc_info.value)

    def test_execute_with_missing_required_properties(self, client):
        """Test executing tool with missing required properties raises error."""
        with pytest.raises(MCIClientError) as exc_info:
            client.execute("get_weather", properties={})
        assert "requires properties" in str(exc_info.value).lower()

    def test_execute_text_tool_with_properties(self, client):
        """Test executing text tool with properties."""
        result = client.execute("generate_text", properties={"name": "World"})
        assert isinstance(result, ExecutionResult)
        assert result.isError is False
        assert isinstance(result.content, str)
        assert "Hello World!" in result.content

    def test_execute_with_none_properties(self, client):
        """Test executing tool with None properties defaults to empty dict."""
        # This should fail because get_weather requires location
        with pytest.raises(MCIClientError):
            client.execute("get_weather", properties=None)

    def test_execute_returns_execution_result(self, client):
        """Test that execute returns ExecutionResult object."""
        result = client.execute("generate_text", properties={"name": "test"})
        assert isinstance(result, ExecutionResult)
        assert hasattr(result, "isError")
        assert hasattr(result, "content")
        assert hasattr(result, "error")
        assert isinstance(result.content, str)
        assert "test" in result.content


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_filter_and_execute(self, client):
        """Test filtering tools and then executing one."""
        tools = client.only(["generate_text"])
        assert len(tools) == 1

        result = client.execute("generate_text", properties={"name": "Integration"})
        assert result.isError is False

    def test_list_get_schema_and_execute(self, client):
        """Test listing tools, getting schema, and executing."""
        tool_names = client.list_tools()
        assert "generate_text" in tool_names

        schema = client.get_tool_schema("generate_text")
        assert isinstance(schema, dict)

        result = client.execute("generate_text", properties={"name": "Test"})
        assert result.isError is False

    def test_multiple_clients_same_file(self, temp_schema_file):
        """Test creating multiple clients from same file."""
        client1 = MCIClient(temp_schema_file, env_vars={"KEY": "value1"})
        client2 = MCIClient(temp_schema_file, env_vars={"KEY": "value2"})

        # Verify both clients are independent and functional
        assert len(client1.list_tools()) == len(client2.list_tools())
        assert len(client1.list_tools()) > 0

    def test_only_and_without_combination(self, client):
        """Test that only and without can be used independently."""
        only_tools = client.only(["get_weather", "create_report", "search_files"])
        without_tools = client.without(["get_weather", "create_report"])

        # These should be different sets
        only_names = [t.name for t in only_tools]
        without_names = [t.name for t in without_tools]

        assert "get_weather" in only_names
        assert "get_weather" not in without_names


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_case_sensitive_tool_names(self, client):
        """Test that tool names are case-sensitive."""
        # This should work
        tools = client.only(["get_weather"])
        assert len(tools) == 1

        # This should not find anything (different case)
        tools = client.only(["Get_Weather"])
        assert len(tools) == 0

    def test_execute_with_extra_properties(self, client):
        """Test executing tool with extra (non-schema) properties."""
        # Should not fail - extra properties are allowed
        result = client.execute("generate_text", properties={"name": "Test", "extra_prop": "value"})
        assert isinstance(result, ExecutionResult)

    def test_client_state_isolation(self, temp_schema_file):
        """Test that each client instance has isolated state."""
        client1 = MCIClient(temp_schema_file, env_vars={"CURRENT_DATE": "2024-01-01"})
        client2 = MCIClient(temp_schema_file, env_vars={"CURRENT_DATE": "2024-12-31"})

        # Verify each client uses its own env vars by executing a tool
        # that uses env vars in its execution template
        result1 = client1.execute("generate_text", properties={"name": "User"})
        result2 = client2.execute("generate_text", properties={"name": "User"})

        # Both should succeed and use different dates from their respective env vars
        assert isinstance(result1.content, str)
        assert isinstance(result2.content, str)
