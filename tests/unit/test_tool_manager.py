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
    from mcipy import Annotations

    tools = [
        Tool(
            name="get_weather",
            annotations=Annotations(title="Get Weather"),
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
            annotations=Annotations(title="Create Report"),
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
            annotations=Annotations(title="List Files"),
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
            annotations=Annotations(title="Read Config"),
            description="Read configuration file",
            inputSchema=None,  # No input schema
            execution=FileExecutionConfig(path="/tmp/config.txt"),
        ),
        Tool(
            name="generate_message",
            annotations=Annotations(title="Generate Message"),
            description="Generate a message",
            inputSchema={},  # Empty input schema
            execution=TextExecutionConfig(text="Hello {{props.name}}!"),
        ),
    ]

    return MCISchema(schemaVersion="1.0", tools=tools)


@pytest.fixture
def schema_with_disabled_tools():
    """Create a sample MCISchema with some disabled tools for testing."""
    from mcipy import Annotations

    tools = [
        Tool(
            name="enabled_tool_1",
            annotations=Annotations(title="Enabled Tool 1"),
            description="First enabled tool",
            execution=HTTPExecutionConfig(url="https://api.example.com/tool1"),
        ),
        Tool(
            name="disabled_tool_1",
            disabled=True,
            annotations=Annotations(title="Disabled Tool 1"),
            description="First disabled tool",
            execution=HTTPExecutionConfig(url="https://api.example.com/disabled1"),
        ),
        Tool(
            name="enabled_tool_2",
            annotations=Annotations(title="Enabled Tool 2"),
            description="Second enabled tool",
            execution=HTTPExecutionConfig(url="https://api.example.com/tool2"),
        ),
        Tool(
            name="disabled_tool_2",
            disabled=True,
            annotations=Annotations(title="Disabled Tool 2"),
            description="Second disabled tool",
            execution=CLIExecutionConfig(command="disabled_cmd"),
        ),
        Tool(
            name="enabled_tool_3",
            annotations=Annotations(title="Enabled Tool 3"),
            description="Third enabled tool",
            execution=TextExecutionConfig(text="Enabled text"),
        ),
    ]

    return MCISchema(schemaVersion="1.0", tools=tools)


@pytest.fixture
def tool_manager(sample_schema):
    """Create a ToolManager instance for testing."""
    return ToolManager(sample_schema)


@pytest.fixture
def tool_manager_with_disabled(schema_with_disabled_tools):
    """Create a ToolManager instance with disabled tools for testing."""
    return ToolManager(schema_with_disabled_tools)


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
        assert tool.annotations is not None
        assert tool.annotations.title == "Get Weather"

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
        """Test that list_tools returns enabled tools from the schema."""
        tools = tool_manager.list_tools()
        # Should return the same list if no tools are disabled
        assert len(tools) == len(tool_manager.schema.tools)

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
        assert result.result.isError is False
        assert len(result.result.content) >= 1
        assert "Hello Bob!" in result.result.content[0].text

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
        assert result.result.isError is False

    def test_execute_builds_correct_context(self, tool_manager, monkeypatch):
        """Test that execute builds the correct context."""
        captured_context = {}

        def mock_execute(_self, _config, context):
            from mcipy import ExecutionResultContent, TextContent

            captured_context.update(context)
            return ExecutionResult(
                result=ExecutionResultContent(
                    isError=False,
                    content=[TextContent(text="mocked")],
                )
            )

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


class TestDisabledToolFiltering:
    """Tests for disabled tool filtering in ToolManager."""

    def test_list_tools_excludes_disabled(self, tool_manager_with_disabled):
        """Test that list_tools excludes disabled tools."""
        tools = tool_manager_with_disabled.list_tools()
        tool_names = [tool.name for tool in tools]

        # Should only include enabled tools
        assert len(tools) == 3
        assert "enabled_tool_1" in tool_names
        assert "enabled_tool_2" in tool_names
        assert "enabled_tool_3" in tool_names

        # Should not include disabled tools
        assert "disabled_tool_1" not in tool_names
        assert "disabled_tool_2" not in tool_names

    def test_get_tool_returns_none_for_disabled(self, tool_manager_with_disabled):
        """Test that get_tool returns None for disabled tools."""
        # Enabled tools should be retrievable
        enabled_tool = tool_manager_with_disabled.get_tool("enabled_tool_1")
        assert enabled_tool is not None
        assert enabled_tool.name == "enabled_tool_1"

        # Disabled tools should return None
        disabled_tool = tool_manager_with_disabled.get_tool("disabled_tool_1")
        assert disabled_tool is None

        disabled_tool_2 = tool_manager_with_disabled.get_tool("disabled_tool_2")
        assert disabled_tool_2 is None

    def test_filter_tools_excludes_disabled_with_only(self, tool_manager_with_disabled):
        """Test that filter_tools with 'only' excludes disabled tools."""
        # Request both enabled and disabled tools
        tools = tool_manager_with_disabled.filter_tools(
            only=["enabled_tool_1", "disabled_tool_1", "enabled_tool_2"]
        )
        tool_names = [tool.name for tool in tools]

        # Should only return enabled tools from the list
        assert len(tools) == 2
        assert "enabled_tool_1" in tool_names
        assert "enabled_tool_2" in tool_names
        assert "disabled_tool_1" not in tool_names

    def test_filter_tools_excludes_disabled_with_without(self, tool_manager_with_disabled):
        """Test that filter_tools with 'without' excludes disabled tools."""
        # Exclude one enabled tool
        tools = tool_manager_with_disabled.filter_tools(without=["enabled_tool_1"])
        tool_names = [tool.name for tool in tools]

        # Should return other enabled tools but not disabled ones
        assert len(tools) == 2
        assert "enabled_tool_2" in tool_names
        assert "enabled_tool_3" in tool_names
        assert "enabled_tool_1" not in tool_names
        assert "disabled_tool_1" not in tool_names
        assert "disabled_tool_2" not in tool_names

    def test_filter_tools_excludes_disabled_no_filters(self, tool_manager_with_disabled):
        """Test that filter_tools without filters excludes disabled tools."""
        tools = tool_manager_with_disabled.filter_tools()
        tool_names = [tool.name for tool in tools]

        # Should return all enabled tools
        assert len(tools) == 3
        assert "enabled_tool_1" in tool_names
        assert "enabled_tool_2" in tool_names
        assert "enabled_tool_3" in tool_names
        assert "disabled_tool_1" not in tool_names
        assert "disabled_tool_2" not in tool_names

    def test_execute_disabled_tool_raises_error(self, tool_manager_with_disabled):
        """Test that executing a disabled tool raises an error."""
        # Executing an enabled tool should work (we'll test it doesn't raise here)
        # Note: This will fail during execution due to network, but should pass validation

        # Executing a disabled tool should raise ToolManagerError
        with pytest.raises(ToolManagerError, match="Tool not found: disabled_tool_1"):
            tool_manager_with_disabled.execute(
                tool_name="disabled_tool_1",
                properties={},
                env_vars={},
            )

    def test_tool_map_excludes_disabled_tools(self, tool_manager_with_disabled):
        """Test that the internal tool map excludes disabled tools.

        Note: This test accesses private _tool_map to verify implementation.
        """
        # Should only contain enabled tools
        assert len(tool_manager_with_disabled._tool_map) == 3
        assert "enabled_tool_1" in tool_manager_with_disabled._tool_map
        assert "enabled_tool_2" in tool_manager_with_disabled._tool_map
        assert "enabled_tool_3" in tool_manager_with_disabled._tool_map
        assert "disabled_tool_1" not in tool_manager_with_disabled._tool_map
        assert "disabled_tool_2" not in tool_manager_with_disabled._tool_map

    def test_disabled_false_behaves_as_enabled(self):
        """Test that disabled=False behaves the same as not setting disabled."""

        tools = [
            Tool(
                name="tool_default",
                execution=HTTPExecutionConfig(url="https://api.example.com"),
            ),
            Tool(
                name="tool_explicit_false",
                disabled=False,
                execution=HTTPExecutionConfig(url="https://api.example.com"),
            ),
        ]
        schema = MCISchema(schemaVersion="1.0", tools=tools)
        manager = ToolManager(schema)

        # Both tools should be available
        assert len(manager.list_tools()) == 2
        assert manager.get_tool("tool_default") is not None
        assert manager.get_tool("tool_explicit_false") is not None


class TestTagFiltering:
    """Tests for tag-based filtering in ToolManager."""

    @pytest.fixture
    def schema_with_tags(self):
        """Create a sample MCISchema with tools that have tags."""
        from mcipy import Annotations

        tools = [
            Tool(
                name="api_tool_1",
                annotations=Annotations(title="API Tool 1"),
                description="First API tool",
                execution=HTTPExecutionConfig(url="https://api.example.com/tool1"),
                tags=["api", "external", "data"],
            ),
            Tool(
                name="api_tool_2",
                annotations=Annotations(title="API Tool 2"),
                description="Second API tool",
                execution=HTTPExecutionConfig(url="https://api.example.com/tool2"),
                tags=["api", "internal"],
            ),
            Tool(
                name="cli_tool_1",
                annotations=Annotations(title="CLI Tool 1"),
                description="First CLI tool",
                execution=CLIExecutionConfig(command="ls"),
                tags=["cli", "filesystem"],
            ),
            Tool(
                name="data_tool",
                annotations=Annotations(title="Data Tool"),
                description="Data processing tool",
                execution=HTTPExecutionConfig(url="https://api.example.com/data"),
                tags=["data", "processing", "internal"],
            ),
            Tool(
                name="no_tags_tool",
                annotations=Annotations(title="No Tags Tool"),
                description="Tool without tags",
                execution=TextExecutionConfig(text="Hello"),
                tags=[],
            ),
        ]

        return MCISchema(schemaVersion="1.0", tools=tools)

    def test_tags_filter_single_tag(self, schema_with_tags):
        """Test filtering by a single tag."""
        manager = ToolManager(schema_with_tags)
        tools = manager.tags(["api"])
        tool_names = [tool.name for tool in tools]

        assert len(tools) == 2
        assert "api_tool_1" in tool_names
        assert "api_tool_2" in tool_names

    def test_tags_filter_multiple_tags_or_logic(self, schema_with_tags):
        """Test filtering by multiple tags (OR logic)."""
        manager = ToolManager(schema_with_tags)
        tools = manager.tags(["api", "cli"])
        tool_names = [tool.name for tool in tools]

        # Should return tools with 'api' OR 'cli' tags
        assert len(tools) == 3
        assert "api_tool_1" in tool_names
        assert "api_tool_2" in tool_names
        assert "cli_tool_1" in tool_names

    def test_tags_filter_no_matches(self, schema_with_tags):
        """Test filtering with tags that don't match any tools."""
        manager = ToolManager(schema_with_tags)
        tools = manager.tags(["nonexistent"])

        assert len(tools) == 0

    def test_tags_filter_empty_list(self, schema_with_tags):
        """Test filtering with empty tag list."""
        manager = ToolManager(schema_with_tags)
        tools = manager.tags([])

        # Empty tag list should return no tools
        assert len(tools) == 0

    def test_tags_filter_case_sensitive(self, schema_with_tags):
        """Test that tag filtering is case-sensitive."""
        manager = ToolManager(schema_with_tags)
        tools_lower = manager.tags(["api"])
        tools_upper = manager.tags(["API"])

        # Should find 'api' but not 'API'
        assert len(tools_lower) == 2
        assert len(tools_upper) == 0

    def test_tags_filter_excludes_tools_without_tags(self, schema_with_tags):
        """Test that filtering excludes tools without tags."""
        manager = ToolManager(schema_with_tags)
        tools = manager.tags(["data"])
        tool_names = [tool.name for tool in tools]

        assert len(tools) == 2
        assert "api_tool_1" in tool_names
        assert "data_tool" in tool_names
        assert "no_tags_tool" not in tool_names

    def test_without_tags_single_tag(self, schema_with_tags):
        """Test excluding tools with a single tag."""
        manager = ToolManager(schema_with_tags)
        tools = manager.withoutTags(["api"])
        tool_names = [tool.name for tool in tools]

        # Should exclude api_tool_1 and api_tool_2
        assert len(tools) == 3
        assert "cli_tool_1" in tool_names
        assert "data_tool" in tool_names
        assert "no_tags_tool" in tool_names
        assert "api_tool_1" not in tool_names
        assert "api_tool_2" not in tool_names

    def test_without_tags_multiple_tags_or_logic(self, schema_with_tags):
        """Test excluding tools with multiple tags (OR logic)."""
        manager = ToolManager(schema_with_tags)
        tools = manager.withoutTags(["api", "cli"])
        tool_names = [tool.name for tool in tools]

        # Should exclude tools with 'api' OR 'cli' tags
        assert len(tools) == 2
        assert "data_tool" in tool_names
        assert "no_tags_tool" in tool_names

    def test_without_tags_no_matches(self, schema_with_tags):
        """Test excluding with tags that don't match any tools."""
        manager = ToolManager(schema_with_tags)
        tools = manager.withoutTags(["nonexistent"])

        # Should return all tools
        assert len(tools) == 5

    def test_without_tags_empty_list(self, schema_with_tags):
        """Test excluding with empty tag list."""
        manager = ToolManager(schema_with_tags)
        tools = manager.withoutTags([])

        # Empty tag list should return all tools
        assert len(tools) == 5

    def test_without_tags_case_sensitive(self, schema_with_tags):
        """Test that withoutTags filtering is case-sensitive."""
        manager = ToolManager(schema_with_tags)
        tools_lower = manager.withoutTags(["api"])
        tools_upper = manager.withoutTags(["API"])

        # Should exclude 'api' but not 'API'
        assert len(tools_lower) == 3
        assert len(tools_upper) == 5  # No tools excluded

    def test_without_tags_includes_tools_without_tags(self, schema_with_tags):
        """Test that withoutTags includes tools without tags."""
        manager = ToolManager(schema_with_tags)
        tools = manager.withoutTags(["api", "cli", "data"])
        tool_names = [tool.name for tool in tools]

        assert len(tools) == 1
        assert "no_tags_tool" in tool_names

    def test_tags_filter_with_disabled_tools(self):
        """Test that tag filtering excludes disabled tools."""
        from mcipy import Annotations

        tools = [
            Tool(
                name="enabled_api_tool",
                annotations=Annotations(title="Enabled API Tool"),
                execution=HTTPExecutionConfig(url="https://api.example.com"),
                tags=["api"],
            ),
            Tool(
                name="disabled_api_tool",
                disabled=True,
                annotations=Annotations(title="Disabled API Tool"),
                execution=HTTPExecutionConfig(url="https://api.example.com"),
                tags=["api"],
            ),
        ]
        schema = MCISchema(schemaVersion="1.0", tools=tools)
        manager = ToolManager(schema)

        filtered = manager.tags(["api"])
        tool_names = [tool.name for tool in filtered]

        # Should only include enabled tools
        assert len(filtered) == 1
        assert "enabled_api_tool" in tool_names
        assert "disabled_api_tool" not in tool_names

    def test_without_tags_filter_with_disabled_tools(self):
        """Test that withoutTags filtering excludes disabled tools."""
        from mcipy import Annotations

        tools = [
            Tool(
                name="enabled_no_api",
                annotations=Annotations(title="Enabled No API"),
                execution=HTTPExecutionConfig(url="https://api.example.com"),
                tags=["data"],
            ),
            Tool(
                name="disabled_no_api",
                disabled=True,
                annotations=Annotations(title="Disabled No API"),
                execution=HTTPExecutionConfig(url="https://api.example.com"),
                tags=["data"],
            ),
        ]
        schema = MCISchema(schemaVersion="1.0", tools=tools)
        manager = ToolManager(schema)

        filtered = manager.withoutTags(["api"])
        tool_names = [tool.name for tool in filtered]

        # Should only include enabled tools
        assert len(filtered) == 1
        assert "enabled_no_api" in tool_names
        assert "disabled_no_api" not in tool_names


class TestDefaultValuesAndOptionalProperties:
    """Tests for default value support and optional property handling."""

    @pytest.fixture
    def schema_with_defaults(self):
        """Create a schema with tools that have default values and optional properties."""
        from mcipy import Annotations

        tools = [
            Tool(
                name="tool_with_defaults",
                annotations=Annotations(title="Tool With Defaults"),
                description="Tool with default values",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "required_prop": {
                            "type": "string",
                            "description": "Required property",
                        },
                        "optional_with_default": {
                            "type": "boolean",
                            "description": "Optional with default",
                            "default": False,
                        },
                        "optional_no_default": {
                            "type": "string",
                            "description": "Optional without default",
                        },
                        "another_default": {
                            "type": "string",
                            "description": "Another property with default",
                            "default": "default_value",
                        },
                    },
                    "required": ["required_prop"],
                },
                execution=TextExecutionConfig(
                    text="Required: {{props.required_prop}}, "
                    "OptionalWithDefault: {{props.optional_with_default}}, "
                    "AnotherDefault: {{props.another_default}}"
                ),
            ),
            Tool(
                name="tool_all_optional_with_defaults",
                annotations=Annotations(title="All Optional With Defaults"),
                description="Tool where all properties have defaults",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prop1": {"type": "string", "default": "default1"},
                        "prop2": {"type": "number", "default": 42},
                        "prop3": {"type": "boolean", "default": True},
                    },
                    "required": [],
                },
                execution=TextExecutionConfig(
                    text="Prop1: {{props.prop1}}, Prop2: {{props.prop2}}, Prop3: {{props.prop3}}"
                ),
            ),
        ]
        return MCISchema(schemaVersion="1.0", tools=tools)

    def test_default_value_used_when_property_not_provided(self, schema_with_defaults):
        """Test that default values are used when properties are not provided."""
        manager = ToolManager(schema_with_defaults)

        # Execute with only required property
        result = manager.execute(
            "tool_with_defaults", properties={"required_prop": "test_value"}
        )

        assert result.result.isError is False
        content_text = result.result.content[0].text
        # Should use default values for optional_with_default and another_default
        assert "Required: test_value" in content_text
        assert "OptionalWithDefault: False" in content_text
        assert "AnotherDefault: default_value" in content_text

    def test_provided_value_overrides_default(self, schema_with_defaults):
        """Test that provided values override default values."""
        manager = ToolManager(schema_with_defaults)

        # Execute with all properties provided
        result = manager.execute(
            "tool_with_defaults",
            properties={
                "required_prop": "test_value",
                "optional_with_default": True,
                "another_default": "custom_value",
            },
        )

        assert result.result.isError is False
        content_text = result.result.content[0].text
        # Should use provided values, not defaults
        assert "Required: test_value" in content_text
        assert "OptionalWithDefault: True" in content_text
        assert "AnotherDefault: custom_value" in content_text

    def test_optional_property_without_default_is_skipped(self, schema_with_defaults):
        """Test that optional properties without defaults don't cause template errors."""
        manager = ToolManager(schema_with_defaults)

        # Execute with only required property (optional_no_default not provided)
        # This should not raise an error, even though the template doesn't reference it
        result = manager.execute(
            "tool_with_defaults", properties={"required_prop": "test_value"}
        )

        # The execution should succeed
        assert result.result.isError is False

    def test_all_defaults_used_when_no_properties_provided(self, schema_with_defaults):
        """Test that all default values are used when no properties are provided."""
        manager = ToolManager(schema_with_defaults)

        # Execute with no properties at all
        result = manager.execute("tool_all_optional_with_defaults", properties={})

        assert result.result.isError is False
        content_text = result.result.content[0].text
        # Should use all default values
        assert "Prop1: default1" in content_text
        assert "Prop2: 42" in content_text
        assert "Prop3: True" in content_text

    def test_partial_override_of_defaults(self, schema_with_defaults):
        """Test that some properties can override defaults while others use defaults."""
        manager = ToolManager(schema_with_defaults)

        # Execute with only one property overridden
        result = manager.execute(
            "tool_all_optional_with_defaults", properties={"prop1": "custom1"}
        )

        assert result.result.isError is False
        content_text = result.result.content[0].text
        # Should use custom value for prop1, defaults for others
        assert "Prop1: custom1" in content_text
        assert "Prop2: 42" in content_text
        assert "Prop3: True" in content_text

    def test_default_values_with_different_types(self, schema_with_defaults):
        """Test that default values work correctly for different property types."""
        manager = ToolManager(schema_with_defaults)

        result = manager.execute("tool_all_optional_with_defaults", properties={})

        assert result.result.isError is False
        # Verify the resolved properties have the correct types
        # This is an integration test - we just verify execution succeeds

    def test_resolve_properties_with_defaults_method(self, schema_with_defaults):
        """Test the _resolve_properties_with_defaults method directly."""
        manager = ToolManager(schema_with_defaults)
        tool = manager.get_tool("tool_with_defaults")

        # Test with only required property
        resolved = manager._resolve_properties_with_defaults(
            tool, {"required_prop": "test"}
        )

        assert resolved["required_prop"] == "test"
        assert resolved["optional_with_default"] is False
        assert resolved["another_default"] == "default_value"
        # optional_no_default should not be in resolved (skipped)
        assert "optional_no_default" not in resolved

    def test_resolve_properties_all_provided(self, schema_with_defaults):
        """Test property resolution when all properties are provided."""
        manager = ToolManager(schema_with_defaults)
        tool = manager.get_tool("tool_with_defaults")

        # Test with all properties provided
        resolved = manager._resolve_properties_with_defaults(
            tool,
            {
                "required_prop": "test",
                "optional_with_default": True,
                "optional_no_default": "provided",
                "another_default": "custom",
            },
        )

        assert resolved["required_prop"] == "test"
        assert resolved["optional_with_default"] is True
        assert resolved["optional_no_default"] == "provided"
        assert resolved["another_default"] == "custom"

    def test_resolve_properties_no_schema(self):
        """Test property resolution when tool has no input schema."""
        from mcipy import Annotations

        tool = Tool(
            name="no_schema_tool",
            annotations=Annotations(title="No Schema"),
            inputSchema=None,
            execution=TextExecutionConfig(text="Test"),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        resolved = manager._resolve_properties_with_defaults(
            tool, {"custom_prop": "value"}
        )

        # Should return properties as-is when no schema
        assert resolved == {"custom_prop": "value"}

    def test_resolve_properties_empty_schema(self):
        """Test property resolution when tool has empty input schema."""
        from mcipy import Annotations

        tool = Tool(
            name="empty_schema_tool",
            annotations=Annotations(title="Empty Schema"),
            inputSchema={},
            execution=TextExecutionConfig(text="Test"),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        resolved = manager._resolve_properties_with_defaults(
            tool, {"custom_prop": "value"}
        )

        # Should return properties as-is when schema is empty
        assert resolved == {"custom_prop": "value"}

    def test_resolve_properties_schema_without_properties(self):
        """Test property resolution when schema has no properties field."""
        from mcipy import Annotations

        tool = Tool(
            name="no_props_tool",
            annotations=Annotations(title="No Props"),
            inputSchema={"type": "object"},
            execution=TextExecutionConfig(text="Test"),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        resolved = manager._resolve_properties_with_defaults(
            tool, {"custom_prop": "value"}
        )

        # Should return properties as-is when no properties in schema
        assert resolved == {"custom_prop": "value"}
