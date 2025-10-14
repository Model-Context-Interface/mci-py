"""
Unit tests for ToolManager class.

Tests the tool retrieval, filtering, and execution functionality of the ToolManager.
"""

import pytest

from mcipy import (
    CLIExecutionConfig,
    ExecutionResult,
    FileExecutionConfig,
    HTTPExecutionConfig,
    MCISchema,
    SchemaParser,
    TextExecutionConfig,
    Tool,
    ToolManager,
    ToolManagerError,
)


@pytest.fixture
def sample_schema():
    """Create a sample MCISchema for testing."""
    tools = [
        Tool(
            name="get_weather",
            title="Get Weather",
            description="Get weather information",
            inputSchema={
                "type": "object",
                "properties": {"location": {"type": "string", "description": "City name"}},
                "required": ["location"],
            },
            execution=HTTPExecutionConfig(
                url="https://api.example.com/weather",
                params={"location": "{{props.location}}"},
            ),
        ),
        Tool(
            name="create_report",
            title="Create Report",
            description="Create a report",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["title", "content"],
            },
            execution=HTTPExecutionConfig(
                method="POST",
                url="https://api.example.com/reports",
            ),
        ),
        Tool(
            name="list_files",
            title="List Files",
            description="List files in directory",
            inputSchema={
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": ["directory"],
            },
            execution=CLIExecutionConfig(command="ls", args=["-la"]),
        ),
        Tool(
            name="read_config",
            title="Read Config",
            description="Read configuration file",
            inputSchema=None,  # No input schema
            execution=FileExecutionConfig(path="/tmp/config.txt"),
        ),
        Tool(
            name="generate_message",
            title="Generate Message",
            description="Generate a message",
            inputSchema={},  # Empty input schema
            execution=TextExecutionConfig(text="Hello {{props.name}}!"),
        ),
    ]

    return MCISchema(schemaVersion="1.0", tools=tools)


@pytest.fixture
def tool_manager(sample_schema):
    """Create a ToolManager instance for testing."""
    return ToolManager(sample_schema)


class TestToolManagerInit:
    """Tests for ToolManager initialization."""

    def test_init_with_schema(self, sample_schema):
        """Test initialization with valid schema."""
        manager = ToolManager(sample_schema)
        assert manager.schema == sample_schema
        # Verify all tools are accessible
        assert len(manager.list_tools()) == 5
        assert manager.get_tool("get_weather") is not None
        assert manager.get_tool("create_report") is not None

    def test_init_creates_tool_map(self, sample_schema):
        """Test that initialization creates a tool mapping.

        Note: This test accesses the private _tool_map to verify internal structure.
        This is acceptable for testing implementation details that affect performance.
        """
        manager = ToolManager(sample_schema)
        assert isinstance(manager._tool_map, dict)
        assert all(isinstance(k, str) for k in manager._tool_map.keys())
        assert all(isinstance(v, Tool) for v in manager._tool_map.values())


class TestGetTool:
    """Tests for get_tool method."""

    def test_get_existing_tool(self, tool_manager):
        """Test retrieving an existing tool by name."""
        tool = tool_manager.get_tool("get_weather")
        assert tool is not None
        assert tool.name == "get_weather"
        assert tool.title == "Get Weather"

    def test_get_nonexistent_tool(self, tool_manager):
        """Test retrieving a non-existent tool returns None."""
        tool = tool_manager.get_tool("nonexistent_tool")
        assert tool is None

    def test_get_tool_case_sensitive(self, tool_manager):
        """Test that tool retrieval is case-sensitive."""
        tool = tool_manager.get_tool("GET_WEATHER")
        assert tool is None

        tool = tool_manager.get_tool("get_weather")
        assert tool is not None

    def test_get_tool_returns_correct_instance(self, tool_manager):
        """Test that get_tool returns the exact tool instance."""
        tool1 = tool_manager.get_tool("create_report")
        tool2 = tool_manager.get_tool("create_report")
        assert tool1 is tool2  # Same instance


class TestListTools:
    """Tests for list_tools method."""

    def test_list_all_tools(self, tool_manager):
        """Test listing all tools."""
        tools = tool_manager.list_tools()
        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        assert "get_weather" in tool_names
        assert "create_report" in tool_names
        assert "list_files" in tool_names
        assert "read_config" in tool_names
        assert "generate_message" in tool_names

    def test_list_tools_returns_original_list(self, tool_manager):
        """Test that list_tools returns the schema's tool list."""
        tools = tool_manager.list_tools()
        assert tools is tool_manager.schema.tools

    def test_list_tools_empty_schema(self):
        """Test listing tools from an empty schema."""
        empty_schema = MCISchema(schemaVersion="1.0", tools=[])
        manager = ToolManager(empty_schema)
        tools = manager.list_tools()
        assert tools == []


class TestFilterTools:
    """Tests for filter_tools method."""

    def test_filter_with_only_list(self, tool_manager):
        """Test filtering with only inclusion list."""
        filtered = tool_manager.filter_tools(only=["get_weather", "create_report"])
        assert len(filtered) == 2
        tool_names = [tool.name for tool in filtered]
        assert "get_weather" in tool_names
        assert "create_report" in tool_names
        assert "list_files" not in tool_names

    def test_filter_with_without_list(self, tool_manager):
        """Test filtering with only exclusion list."""
        filtered = tool_manager.filter_tools(without=["list_files", "read_config"])
        assert len(filtered) == 3
        tool_names = [tool.name for tool in filtered]
        assert "get_weather" in tool_names
        assert "create_report" in tool_names
        assert "generate_message" in tool_names
        assert "list_files" not in tool_names
        assert "read_config" not in tool_names

    def test_filter_with_both_only_and_without(self, tool_manager):
        """Test filtering with both inclusion and exclusion lists."""
        # Only takes precedence: include get_weather and create_report, but exclude create_report
        filtered = tool_manager.filter_tools(
            only=["get_weather", "create_report"], without=["create_report"]
        )
        assert len(filtered) == 1
        assert filtered[0].name == "get_weather"

    def test_filter_with_none_parameters(self, tool_manager):
        """Test filtering with None parameters returns all tools."""
        filtered = tool_manager.filter_tools(only=None, without=None)
        assert len(filtered) == 5

    def test_filter_with_only_none(self, tool_manager):
        """Test filtering with only=None returns all except without."""
        filtered = tool_manager.filter_tools(only=None, without=["list_files"])
        assert len(filtered) == 4
        tool_names = [tool.name for tool in filtered]
        assert "list_files" not in tool_names

    def test_filter_with_without_none(self, tool_manager):
        """Test filtering with without=None returns only the 'only' list."""
        filtered = tool_manager.filter_tools(only=["get_weather"], without=None)
        assert len(filtered) == 1
        assert filtered[0].name == "get_weather"

    def test_filter_with_nonexistent_tool_in_only(self, tool_manager):
        """Test filtering with non-existent tool in only list."""
        filtered = tool_manager.filter_tools(only=["nonexistent", "get_weather"])
        assert len(filtered) == 1
        assert filtered[0].name == "get_weather"

    def test_filter_with_nonexistent_tool_in_without(self, tool_manager):
        """Test filtering with non-existent tool in without list."""
        filtered = tool_manager.filter_tools(without=["nonexistent"])
        assert len(filtered) == 5  # All tools should be present

    def test_filter_empty_only_list(self, tool_manager):
        """Test filtering with empty only list returns no tools."""
        filtered = tool_manager.filter_tools(only=[])
        assert len(filtered) == 0

    def test_filter_empty_without_list(self, tool_manager):
        """Test filtering with empty without list returns all tools."""
        filtered = tool_manager.filter_tools(without=[])
        assert len(filtered) == 5


class TestExecute:
    """Tests for execute method."""

    def test_execute_tool_not_found(self, tool_manager):
        """Test executing a non-existent tool raises error."""
        with pytest.raises(ToolManagerError, match="Tool not found: nonexistent"):
            tool_manager.execute("nonexistent", {})

    def test_execute_with_missing_required_properties(self, tool_manager):
        """Test executing tool with missing required properties raises error."""
        with pytest.raises(ToolManagerError, match="requires properties.*Missing: location"):
            tool_manager.execute("get_weather", {})

    def test_execute_with_partial_required_properties(self, tool_manager):
        """Test executing tool with partial required properties raises error."""
        with pytest.raises(ToolManagerError, match="requires properties.*Missing: content"):
            tool_manager.execute("create_report", {"title": "My Report"})

    def test_execute_tool_with_no_input_schema(self, tool_manager):
        """Test executing tool with no input schema (should not raise)."""
        # Mock the file to avoid actual file read
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        # Update the tool's path to use the temp file
        tool = tool_manager.get_tool("read_config")
        tool.execution.path = temp_path

        # Should not raise error even with no properties
        result = tool_manager.execute("read_config")
        assert isinstance(result, ExecutionResult)

        # Cleanup
        import os

        os.unlink(temp_path)

    def test_execute_tool_with_empty_input_schema(self, tool_manager):
        """Test executing tool with empty input schema dict."""
        # Should not raise error
        result = tool_manager.execute("generate_message", {"name": "Alice"})
        assert isinstance(result, ExecutionResult)

    def test_execute_tool_with_valid_properties(self, tool_manager):
        """Test executing text tool with valid properties."""
        result = tool_manager.execute("generate_message", {"name": "Bob"})
        assert isinstance(result, ExecutionResult)
        assert result.isError is False
        assert result.content is not None
        assert "Hello Bob!" in result.content

    def test_execute_with_none_properties(self, tool_manager):
        """Test executing with None properties defaults to empty dict."""
        # Should not raise when properties is None and tool has no required properties
        result = tool_manager.execute("generate_message", None)
        assert isinstance(result, ExecutionResult)

    def test_execute_with_env_vars(self, tool_manager):
        """Test executing with environment variables."""
        result = tool_manager.execute(
            "generate_message",
            properties={"name": "Charlie"},
            env_vars={"CURRENT_DATE": "2024-01-01"},
        )
        assert isinstance(result, ExecutionResult)
        assert result.isError is False

    def test_execute_builds_correct_context(self, tool_manager, monkeypatch):
        """Test that execute builds the correct context."""
        captured_context = {}

        def mock_execute(_self, _config, context):
            captured_context.update(context)
            return ExecutionResult(isError=False, content="mocked")

        # Patch the TextExecutor execute method
        from mcipy.executors.text_executor import TextExecutor

        monkeypatch.setattr(TextExecutor, "execute", mock_execute)

        props = {"name": "Diana"}
        env_vars = {"API_KEY": "secret"}
        tool_manager.execute("generate_message", props, env_vars)

        assert "props" in captured_context
        assert "env" in captured_context
        assert "input" in captured_context
        assert captured_context["props"] == props
        assert captured_context["env"] == env_vars
        assert captured_context["input"] is captured_context["props"]


class TestValidateInputProperties:
    """Tests for _validate_input_properties private method."""

    def test_validate_with_all_required_properties(self, tool_manager):
        """Test validation passes with all required properties."""
        tool = tool_manager.get_tool("get_weather")
        # Should not raise
        tool_manager._validate_input_properties(tool, {"location": "New York"})

    def test_validate_with_extra_properties(self, tool_manager):
        """Test validation passes with extra properties."""
        tool = tool_manager.get_tool("get_weather")
        # Should not raise
        tool_manager._validate_input_properties(tool, {"location": "New York", "units": "metric"})

    def test_validate_with_no_input_schema(self, tool_manager):
        """Test validation passes when tool has no input schema."""
        tool = tool_manager.get_tool("read_config")
        # Should not raise
        tool_manager._validate_input_properties(tool, {})
        tool_manager._validate_input_properties(tool, {"any": "property"})

    def test_validate_with_empty_input_schema(self, tool_manager):
        """Test validation passes when tool has empty input schema."""
        tool = tool_manager.get_tool("generate_message")
        # Should not raise
        tool_manager._validate_input_properties(tool, {})
        tool_manager._validate_input_properties(tool, {"name": "Test"})

    def test_validate_missing_single_required_property(self, tool_manager):
        """Test validation fails with missing required property."""
        tool = tool_manager.get_tool("get_weather")
        with pytest.raises(ToolManagerError, match="requires properties.*Missing: location"):
            tool_manager._validate_input_properties(tool, {})

    def test_validate_missing_multiple_required_properties(self, tool_manager):
        """Test validation fails with multiple missing required properties."""
        tool = tool_manager.get_tool("create_report")
        with pytest.raises(ToolManagerError, match="requires properties.*Missing"):
            tool_manager._validate_input_properties(tool, {})


class TestEdgeCases:
    """Tests for edge cases and integration scenarios."""

    def test_execute_case_sensitive_tool_name(self, tool_manager):
        """Test that execute is case-sensitive for tool names."""
        with pytest.raises(ToolManagerError, match="Tool not found"):
            tool_manager.execute("GET_WEATHER", {"location": "NYC"})

    def test_multiple_managers_same_schema(self, sample_schema):
        """Test creating multiple managers from same schema."""
        manager1 = ToolManager(sample_schema)
        manager2 = ToolManager(sample_schema)

        assert manager1.schema is manager2.schema
        # Verify both managers have access to the same tools
        tools1 = {tool.name for tool in manager1.list_tools()}
        tools2 = {tool.name for tool in manager2.list_tools()}
        assert tools1 == tools2

    def test_with_real_schema_file(self):
        """Test ToolManager with schema loaded from file."""
        schema = SchemaParser.parse_file("example.mci.json")
        manager = ToolManager(schema)

        tools = manager.list_tools()
        assert len(tools) > 0

        # Test get_tool
        weather_tool = manager.get_tool("get_weather")
        assert weather_tool is not None

        # Test filter
        filtered = manager.filter_tools(only=["get_weather"])
        assert len(filtered) == 1
