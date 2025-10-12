"""Unit tests for SchemaParser."""

import json

import pytest

from mcipy.enums import ExecutionType
from mcipy.models import (
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    MCISchema,
    TextExecutionConfig,
)
from mcipy.parser import SchemaParser, SchemaParserError


class TestSchemaParserParseFile:
    """Tests for SchemaParser.parse_file method."""

    def test_parse_file_valid_schema(self, tmp_path):
        """Test parsing a valid schema file."""
        schema_data = {
            "schemaVersion": "1.0",
            "metadata": {"name": "Test Tools", "version": "1.0.0"},
            "tools": [
                {
                    "name": "test_tool",
                    "execution": {"type": "text", "text": "Hello World"},
                }
            ],
        }

        # Write schema to temporary file
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Parse the file
        schema = SchemaParser.parse_file(str(schema_file))

        assert isinstance(schema, MCISchema)
        assert schema.schemaVersion == "1.0"
        assert schema.metadata is not None
        assert schema.metadata.name == "Test Tools"
        assert len(schema.tools) == 1
        assert schema.tools[0].name == "test_tool"

    def test_parse_file_not_found(self):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(SchemaParserError, match="Schema file not found"):
            SchemaParser.parse_file("/nonexistent/file.json")

    def test_parse_file_is_directory(self, tmp_path):
        """Test parsing when path is a directory."""
        with pytest.raises(SchemaParserError, match="Path is not a file"):
            SchemaParser.parse_file(str(tmp_path))

    def test_parse_file_invalid_json(self, tmp_path):
        """Test parsing a file with invalid JSON."""
        schema_file = tmp_path / "invalid.json"
        schema_file.write_text("{ invalid json }")

        with pytest.raises(SchemaParserError, match="Invalid JSON"):
            SchemaParser.parse_file(str(schema_file))

    def test_parse_file_empty_file(self, tmp_path):
        """Test parsing an empty file."""
        schema_file = tmp_path / "empty.json"
        schema_file.write_text("")

        with pytest.raises(SchemaParserError, match="Invalid JSON"):
            SchemaParser.parse_file(str(schema_file))


class TestSchemaParserParseDict:
    """Tests for SchemaParser.parse_dict method."""

    def test_parse_dict_valid_minimal(self):
        """Test parsing a valid minimal schema."""
        data = {
            "schemaVersion": "1.0",
            "tools": [{"name": "tool1", "execution": {"type": "text", "text": "Hello"}}],
        }

        schema = SchemaParser.parse_dict(data)

        assert isinstance(schema, MCISchema)
        assert schema.schemaVersion == "1.0"
        assert schema.metadata is None
        assert len(schema.tools) == 1

    def test_parse_dict_valid_full(self):
        """Test parsing a valid schema with all fields."""
        data = {
            "schemaVersion": "1.0",
            "metadata": {
                "name": "Test Context",
                "description": "A test context",
                "version": "1.0.0",
                "license": "MIT",
                "authors": ["Alice", "Bob"],
            },
            "tools": [
                {
                    "name": "http_tool",
                    "title": "HTTP Tool",
                    "description": "An HTTP tool",
                    "execution": {"type": "http", "url": "https://api.example.com"},
                },
                {
                    "name": "cli_tool",
                    "execution": {"type": "cli", "command": "ls"},
                },
            ],
        }

        schema = SchemaParser.parse_dict(data)

        assert schema.schemaVersion == "1.0"
        assert schema.metadata is not None
        assert schema.metadata.name == "Test Context"
        assert len(schema.tools) == 2
        assert schema.tools[0].name == "http_tool"
        assert schema.tools[1].name == "cli_tool"

    def test_parse_dict_not_dict(self):
        """Test parsing when input is not a dictionary."""
        with pytest.raises(SchemaParserError, match="Expected dictionary, got"):
            SchemaParser.parse_dict("not a dict")  # pyright: ignore[reportArgumentType]

        with pytest.raises(SchemaParserError, match="Expected dictionary, got"):
            SchemaParser.parse_dict([])  # pyright: ignore[reportArgumentType]

    def test_parse_dict_missing_schema_version(self):
        """Test parsing a dictionary without schemaVersion."""
        data = {"tools": []}

        with pytest.raises(SchemaParserError, match="Missing required field 'schemaVersion'"):
            SchemaParser.parse_dict(data)

    def test_parse_dict_missing_tools(self):
        """Test parsing a dictionary without tools."""
        data = {"schemaVersion": "1.0"}

        with pytest.raises(SchemaParserError, match="Missing required field 'tools'"):
            SchemaParser.parse_dict(data)

    def test_parse_dict_tools_not_list(self):
        """Test parsing when tools is not a list."""
        data = {"schemaVersion": "1.0", "tools": "not a list"}

        with pytest.raises(SchemaParserError, match="Field 'tools' must be a list"):
            SchemaParser.parse_dict(data)

    def test_parse_dict_empty_tools(self):
        """Test parsing with empty tools list."""
        data = {"schemaVersion": "1.0", "tools": []}

        schema = SchemaParser.parse_dict(data)

        assert len(schema.tools) == 0


class TestSchemaParserValidateSchemaVersion:
    """Tests for SchemaParser._validate_schema_version method."""

    def test_validate_version_valid(self):
        """Test validating a valid schema version."""
        # Should not raise an exception
        SchemaParser._validate_schema_version("1.0")

    def test_validate_version_invalid(self):
        """Test validating an invalid schema version."""
        with pytest.raises(SchemaParserError, match="Unsupported schema version '2.0'"):
            SchemaParser._validate_schema_version("2.0")

    def test_validate_version_not_string(self):
        """Test validating when version is not a string."""
        with pytest.raises(SchemaParserError, match="Schema version must be a string"):
            SchemaParser._validate_schema_version(1.0)  # pyright: ignore[reportArgumentType]

        with pytest.raises(SchemaParserError, match="Schema version must be a string"):
            SchemaParser._validate_schema_version(None)  # pyright: ignore[reportArgumentType]


class TestSchemaParserValidateTools:
    """Tests for SchemaParser._validate_tools method."""

    def test_validate_tools_valid_single(self):
        """Test validating a single valid tool."""
        tools = [{"name": "tool1", "execution": {"type": "text", "text": "Hello"}}]

        # Should not raise an exception
        SchemaParser._validate_tools(tools)

    def test_validate_tools_valid_multiple(self):
        """Test validating multiple valid tools."""
        tools = [
            {"name": "tool1", "execution": {"type": "text", "text": "Hello"}},
            {"name": "tool2", "execution": {"type": "cli", "command": "ls"}},
            {"name": "tool3", "execution": {"type": "file", "path": "/file.txt"}},
            {
                "name": "tool4",
                "execution": {"type": "http", "url": "https://api.example.com"},
            },
        ]

        # Should not raise an exception
        SchemaParser._validate_tools(tools)

    def test_validate_tools_not_dict(self):
        """Test validating when a tool is not a dictionary."""
        tools = ["not a dict"]

        with pytest.raises(SchemaParserError, match="Tool at index 0 must be a dictionary"):
            SchemaParser._validate_tools(tools)

    def test_validate_tools_missing_name(self):
        """Test validating when a tool is missing name."""
        tools = [{"execution": {"type": "text", "text": "Hello"}}]

        with pytest.raises(
            SchemaParserError, match="Tool at index 0 missing required field 'name'"
        ):
            SchemaParser._validate_tools(tools)

    def test_validate_tools_missing_execution(self):
        """Test validating when a tool is missing execution."""
        tools = [{"name": "tool1"}]

        with pytest.raises(
            SchemaParserError,
            match="Tool at index 0 \\('tool1'\\) missing required field 'execution'",
        ):
            SchemaParser._validate_tools(tools)

    def test_validate_tools_execution_not_dict(self):
        """Test validating when execution is not a dictionary."""
        tools = [{"name": "tool1", "execution": "not a dict"}]

        with pytest.raises(SchemaParserError, match="Tool 'tool1' execution must be a dictionary"):
            SchemaParser._validate_tools(tools)

    def test_validate_tools_invalid_execution_type(self):
        """Test validating when execution type is invalid."""
        tools = [{"name": "tool1", "execution": {"type": "invalid"}}]

        with pytest.raises(SchemaParserError, match="Tool 'tool1' has invalid execution config"):
            SchemaParser._validate_tools(tools)


class TestSchemaParserBuildExecutionConfig:
    """Tests for SchemaParser._build_execution_config method."""

    def test_build_http_config(self):
        """Test building HTTP execution config."""
        execution = {"type": "http", "url": "https://api.example.com", "method": "GET"}

        config = SchemaParser._build_execution_config(execution)

        assert isinstance(config, HTTPExecutionConfig)
        assert config.type == ExecutionType.HTTP
        assert config.url == "https://api.example.com"
        assert config.method == "GET"

    def test_build_cli_config(self):
        """Test building CLI execution config."""
        execution = {"type": "cli", "command": "ls", "args": ["-la"]}

        config = SchemaParser._build_execution_config(execution)

        assert isinstance(config, CLIExecutionConfig)
        assert config.type == ExecutionType.CLI
        assert config.command == "ls"
        assert config.args == ["-la"]

    def test_build_file_config(self):
        """Test building File execution config."""
        execution = {"type": "file", "path": "/path/to/file.txt", "enableTemplating": True}

        config = SchemaParser._build_execution_config(execution)

        assert isinstance(config, FileExecutionConfig)
        assert config.type == ExecutionType.FILE
        assert config.path == "/path/to/file.txt"
        assert config.enableTemplating is True

    def test_build_text_config(self):
        """Test building Text execution config."""
        execution = {"type": "text", "text": "Hello {{props.name}}"}

        config = SchemaParser._build_execution_config(execution)

        assert isinstance(config, TextExecutionConfig)
        assert config.type == ExecutionType.TEXT
        assert config.text == "Hello {{props.name}}"

    def test_build_config_missing_type(self):
        """Test building config when type is missing."""
        execution = {"url": "https://api.example.com"}

        with pytest.raises(
            SchemaParserError, match="Missing required field 'type' in execution config"
        ):
            SchemaParser._build_execution_config(execution)

    def test_build_config_invalid_type_value(self):
        """Test building config with invalid type value."""
        execution = {"type": "invalid_type"}

        with pytest.raises(SchemaParserError, match="Invalid execution type 'invalid_type'"):
            SchemaParser._build_execution_config(execution)

    def test_build_config_type_not_string(self):
        """Test building config when type is not a string."""
        execution = {"type": 123}

        with pytest.raises(SchemaParserError, match="Execution type must be a string"):
            SchemaParser._build_execution_config(execution)

    def test_build_http_config_missing_url(self):
        """Test building HTTP config without required url field."""
        execution = {"type": "http", "method": "GET"}

        with pytest.raises(SchemaParserError, match="Invalid http execution config"):
            SchemaParser._build_execution_config(execution)

    def test_build_cli_config_missing_command(self):
        """Test building CLI config without required command field."""
        execution = {"type": "cli", "args": ["-la"]}

        with pytest.raises(SchemaParserError, match="Invalid cli execution config"):
            SchemaParser._build_execution_config(execution)

    def test_build_file_config_missing_path(self):
        """Test building File config without required path field."""
        execution = {"type": "file", "enableTemplating": True}

        with pytest.raises(SchemaParserError, match="Invalid file execution config"):
            SchemaParser._build_execution_config(execution)

    def test_build_text_config_missing_text(self):
        """Test building Text config without required text field."""
        execution = {"type": "text"}

        with pytest.raises(SchemaParserError, match="Invalid text execution config"):
            SchemaParser._build_execution_config(execution)


class TestSchemaParserIntegration:
    """Integration tests for SchemaParser with complex schemas."""

    def test_parse_complex_schema(self, tmp_path):
        """Test parsing a complex schema with all execution types."""
        schema_data = {
            "schemaVersion": "1.0",
            "metadata": {
                "name": "Complex Tools",
                "description": "A comprehensive tool collection",
                "version": "1.0.0",
                "license": "MIT",
                "authors": ["Developer Team"],
            },
            "tools": [
                {
                    "name": "get_weather",
                    "title": "Get Weather",
                    "description": "Fetch weather data",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                    },
                    "execution": {
                        "type": "http",
                        "url": "https://api.weather.com/v1/current",
                        "method": "GET",
                        "headers": {"Accept": "application/json"},
                        "params": {"location": "{{props.location}}"},
                        "timeout_ms": 5000,
                    },
                },
                {
                    "name": "list_files",
                    "execution": {
                        "type": "cli",
                        "command": "ls",
                        "args": ["-la"],
                        "cwd": "/home",
                        "timeout_ms": 3000,
                    },
                },
                {
                    "name": "read_config",
                    "execution": {
                        "type": "file",
                        "path": "/etc/config.txt",
                        "enableTemplating": True,
                    },
                },
                {
                    "name": "greeting",
                    "execution": {"type": "text", "text": "Hello {{props.name}}!"},
                },
            ],
        }

        # Write and parse
        schema_file = tmp_path / "complex_schema.json"
        schema_file.write_text(json.dumps(schema_data))
        schema = SchemaParser.parse_file(str(schema_file))

        # Verify structure
        assert schema.schemaVersion == "1.0"
        assert schema.metadata is not None
        assert schema.metadata.name == "Complex Tools"
        assert len(schema.tools) == 4

        # Verify HTTP tool
        http_tool = schema.tools[0]
        assert http_tool.name == "get_weather"
        assert http_tool.title == "Get Weather"
        assert isinstance(http_tool.execution, HTTPExecutionConfig)
        assert http_tool.execution.url == "https://api.weather.com/v1/current"

        # Verify CLI tool
        cli_tool = schema.tools[1]
        assert cli_tool.name == "list_files"
        assert isinstance(cli_tool.execution, CLIExecutionConfig)
        assert cli_tool.execution.command == "ls"

        # Verify File tool
        file_tool = schema.tools[2]
        assert file_tool.name == "read_config"
        assert isinstance(file_tool.execution, FileExecutionConfig)
        assert file_tool.execution.path == "/etc/config.txt"

        # Verify Text tool
        text_tool = schema.tools[3]
        assert text_tool.name == "greeting"
        assert isinstance(text_tool.execution, TextExecutionConfig)
        assert text_tool.execution.text == "Hello {{props.name}}!"

    def test_parse_schema_with_pydantic_validation_error(self):
        """Test that Pydantic validation errors are properly wrapped."""
        data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "invalid_tool",
                    "execution": {
                        "type": "http",
                        "url": "https://api.example.com",
                        "timeout_ms": "not_a_number",  # Invalid type
                    },
                }
            ],
        }

        with pytest.raises(
            SchemaParserError, match="Tool 'invalid_tool' has invalid execution config"
        ):
            SchemaParser.parse_dict(data)
