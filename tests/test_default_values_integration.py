"""
Integration tests for default value support and optional property handling.

These tests demonstrate the real-world usage of the default value feature
where tools can define default values for optional properties, and those
defaults are used when properties are not provided.
"""

import pytest

from mcipy import Annotations, MCISchema, TextExecutionConfig, Tool, ToolManager


class TestDefaultValuesIntegration:
    """Integration tests for default values feature."""

    @pytest.fixture
    def schema_with_search_tool(self):
        """Create a schema with a search tool similar to the issue description."""
        tools = [
            Tool(
                name="search_files",
                annotations=Annotations(title="Search Files", readOnlyHint=True),
                description="Search for text in files with optional parameters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern",
                        },
                        "directory": {
                            "type": "string",
                            "description": "Directory to search in",
                        },
                        "include_images": {
                            "type": "boolean",
                            "description": "Include image files in search",
                            "default": False,
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Use case-sensitive search",
                            "default": True,
                        },
                        "max_results": {
                            "type": "number",
                            "description": "Maximum number of results",
                            "default": 100,
                        },
                        "file_extensions": {
                            "type": "string",
                            "description": "Optional comma-separated list of file extensions",
                        },
                    },
                    "required": ["pattern", "directory"],
                },
                execution=TextExecutionConfig(
                    text="Searching for '{{props.pattern}}' in {{props.directory}}\n"
                    "Include images: {{props.include_images}}\n"
                    "Case sensitive: {{props.case_sensitive}}\n"
                    "Max results: {{props.max_results}}"
                ),
            )
        ]
        return MCISchema(schemaVersion="1.0", tools=tools)

    def test_required_properties_only_uses_defaults(self, schema_with_search_tool):
        """Test that providing only required properties uses defaults for optional ones."""
        manager = ToolManager(schema_with_search_tool)

        # Execute with only required properties
        result = manager.execute(
            "search_files",
            properties={
                "pattern": "TODO",
                "directory": "/home/user/projects",
            },
        )

        # Should succeed
        assert result.result.isError is False
        content = result.result.content[0].text

        # Verify defaults are used
        assert "Searching for 'TODO' in /home/user/projects" in content
        assert "Include images: False" in content
        assert "Case sensitive: True" in content
        assert "Max results: 100" in content

    def test_override_some_defaults(self, schema_with_search_tool):
        """Test that some defaults can be overridden while others are used."""
        manager = ToolManager(schema_with_search_tool)

        # Execute with some optional properties overridden
        result = manager.execute(
            "search_files",
            properties={
                "pattern": "FIXME",
                "directory": "/tmp",
                "include_images": True,
                "max_results": 50,
            },
        )

        assert result.result.isError is False
        content = result.result.content[0].text

        # Verify provided values and defaults
        assert "Searching for 'FIXME' in /tmp" in content
        assert "Include images: True" in content  # Overridden
        assert "Case sensitive: True" in content  # Default
        assert "Max results: 50" in content  # Overridden

    def test_optional_property_without_default_does_not_cause_error(
        self, schema_with_search_tool
    ):
        """Test that optional properties without defaults don't cause template errors."""
        manager = ToolManager(schema_with_search_tool)

        # Execute without providing file_extensions (optional, no default)
        # This should not cause a template error even though file_extensions is not in the template
        result = manager.execute(
            "search_files",
            properties={
                "pattern": "ERROR",
                "directory": "/var/log",
            },
        )

        # Should succeed without attempting to resolve file_extensions
        assert result.result.isError is False

    def test_all_properties_provided(self, schema_with_search_tool):
        """Test that all properties can be provided, overriding all defaults."""
        manager = ToolManager(schema_with_search_tool)

        # Execute with all properties
        result = manager.execute(
            "search_files",
            properties={
                "pattern": "WARNING",
                "directory": "/var/log",
                "include_images": False,
                "case_sensitive": False,
                "max_results": 10,
                "file_extensions": ".log,.txt",
            },
        )

        assert result.result.isError is False
        content = result.result.content[0].text

        # Verify all provided values
        assert "Searching for 'WARNING' in /var/log" in content
        assert "Include images: False" in content
        assert "Case sensitive: False" in content
        assert "Max results: 10" in content

    def test_boolean_default_false(self, schema_with_search_tool):
        """Test that boolean default value of False works correctly."""
        manager = ToolManager(schema_with_search_tool)

        result = manager.execute(
            "search_files",
            properties={
                "pattern": "test",
                "directory": "/tmp",
            },
        )

        assert result.result.isError is False
        content = result.result.content[0].text
        # include_images has default=False
        assert "Include images: False" in content

    def test_number_default(self, schema_with_search_tool):
        """Test that number default value works correctly."""
        manager = ToolManager(schema_with_search_tool)

        result = manager.execute(
            "search_files",
            properties={
                "pattern": "test",
                "directory": "/tmp",
            },
        )

        assert result.result.isError is False
        content = result.result.content[0].text
        # max_results has default=100
        assert "Max results: 100" in content

    def test_string_default_when_used(self):
        """Test string default values."""
        tool = Tool(
            name="format_text",
            annotations=Annotations(title="Format Text"),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "format": {"type": "string", "default": "plain"},
                },
                "required": ["text"],
            },
            execution=TextExecutionConfig(
                text="Text: {{props.text}}, Format: {{props.format}}"
            ),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        result = manager.execute("format_text", properties={"text": "Hello"})

        assert result.result.isError is False
        content = result.result.content[0].text
        assert "Text: Hello, Format: plain" in content


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing behavior."""

    def test_no_input_schema_still_works(self):
        """Test that tools without input schema still work."""
        tool = Tool(
            name="simple_tool",
            annotations=Annotations(title="Simple Tool"),
            inputSchema=None,
            execution=TextExecutionConfig(text="Simple output"),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        result = manager.execute("simple_tool", properties={"any_prop": "value"})
        assert result.result.isError is False

    def test_empty_input_schema_still_works(self):
        """Test that tools with empty input schema still work."""
        tool = Tool(
            name="empty_schema_tool",
            annotations=Annotations(title="Empty Schema Tool"),
            inputSchema={},
            execution=TextExecutionConfig(text="Output: {{props.custom}}"),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        result = manager.execute("empty_schema_tool", properties={"custom": "value"})
        assert result.result.isError is False

    def test_required_validation_still_works(self):
        """Test that required property validation still works."""
        from mcipy import ToolManagerError

        tool = Tool(
            name="required_tool",
            annotations=Annotations(title="Required Tool"),
            inputSchema={
                "type": "object",
                "properties": {"required_prop": {"type": "string"}},
                "required": ["required_prop"],
            },
            execution=TextExecutionConfig(text="Output"),
        )
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        manager = ToolManager(schema)

        # Should raise error when required property is missing
        with pytest.raises(ToolManagerError) as exc_info:
            manager.execute("required_tool", properties={})

        assert "requires properties" in str(exc_info.value)
        assert "required_prop" in str(exc_info.value)
