"""
Tests for validating mode in MCIClient.

Tests that MCIClient with validating=True can validate schemas containing
MCP servers and toolsets without requiring env_vars or performing network/file
operations.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mcipy import MCIClient, MCIClientError
from mcipy.parser import SchemaParser, SchemaParserError


class TestValidatingModeBasic:
    """Tests for basic validating mode functionality."""

    def test_validating_mode_basic_schema(self, tmp_path):
        """Test that validating mode works with a basic schema."""
        schema_data = {
            "schemaVersion": "1.0",
            "metadata": {"name": "Test Tools"},
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "execution": {"type": "text", "text": "Hello {{env.NAME}}"},
                }
            ],
        }

        # Write schema to file
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should work without env_vars in validating mode
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Should be able to list tools
        tools = client.list_tools()
        assert len(tools) == 1
        assert tools[0] == "test_tool"

    def test_validating_mode_execution_raises_error(self, tmp_path):
        """Test that execution raises error in validating mode."""
        schema_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "test_tool",
                    "execution": {"type": "text", "text": "Hello World"},
                }
            ],
        }

        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Attempting to execute should raise error
        with pytest.raises(MCIClientError) as exc_info:
            client.execute("test_tool")

        assert "validating mode" in str(exc_info.value).lower()
        assert "Cannot execute tools" in str(exc_info.value)

    def test_validating_mode_with_unresolved_templates(self, tmp_path):
        """Test that validating mode works with unresolved template placeholders."""
        schema_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "api_call",
                    "execution": {
                        "type": "http",
                        "method": "GET",
                        "url": "https://api.example.com/{{env.ENDPOINT}}",
                        "headers": {"Authorization": "Bearer {{env.API_KEY}}"},
                    },
                }
            ],
        }

        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should work without env_vars in validating mode
        # (templates not resolved, just validated)
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Should be able to list tools
        tools = client.list_tools()
        assert len(tools) == 1
        assert tools[0] == "api_call"


class TestValidatingModeToolsets:
    """Tests for validating mode with toolsets."""

    def test_validating_mode_with_toolsets(self, tmp_path):
        """Test that validating mode validates toolset file existence."""
        # Create a toolset file
        lib_dir = tmp_path / "mci"
        lib_dir.mkdir()

        toolset_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "toolset_tool",
                    "execution": {"type": "text", "text": "Toolset tool"},
                }
            ],
        }

        toolset_file = lib_dir / "test_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_data))

        # Main schema referencing the toolset
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["test_toolset"],
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should validate successfully (checks file exists but doesn't load)
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Tools should be empty in validating mode (toolsets not loaded)
        tools = client.list_tools()
        assert len(tools) == 0

    def test_validating_mode_with_missing_toolset(self, tmp_path):
        """Test that validating mode raises error for missing toolset."""
        # Create library directory but no toolset file
        lib_dir = tmp_path / "mci"
        lib_dir.mkdir()

        # Main schema referencing non-existent toolset
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["missing_toolset"],
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should raise error for missing toolset even in validating mode
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)

        assert "Toolset not found" in str(exc_info.value)
        assert "missing_toolset" in str(exc_info.value)

    def test_validating_mode_with_toolset_filters(self, tmp_path):
        """Test that validating mode works with toolset filters."""
        # Create a toolset file
        lib_dir = tmp_path / "mci"
        lib_dir.mkdir()

        toolset_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "tool1",
                    "tags": ["read"],
                    "execution": {"type": "text", "text": "Tool 1"},
                },
                {
                    "name": "tool2",
                    "tags": ["write"],
                    "execution": {"type": "text", "text": "Tool 2"},
                },
            ],
        }

        toolset_file = lib_dir / "filtered_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_data))

        # Main schema with filter
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": [{"name": "filtered_toolset", "filter": "tags", "filterValue": "read"}],
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should validate successfully
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Tools should be empty in validating mode
        tools = client.list_tools()
        assert len(tools) == 0


class TestValidatingModeMCPServers:
    """Tests for validating mode with MCP servers."""

    def test_validating_mode_with_stdio_mcp_server(self, tmp_path):
        """Test that validating mode validates MCP server structure without fetching."""
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "test_server": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-test"],
                    "env": {"API_KEY": "{{env.API_KEY}}"},
                    "config": {"expDays": 7},
                }
            },
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should validate successfully without env_vars or network calls
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Tools should be empty in validating mode (MCP not fetched)
        tools = client.list_tools()
        assert len(tools) == 0

    def test_validating_mode_with_http_mcp_server(self, tmp_path):
        """Test that validating mode validates HTTP MCP server structure."""
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "http_server": {
                    "type": "http",
                    "url": "https://mcp.example.com/{{env.SERVER_ID}}",
                    "headers": {"Authorization": "Bearer {{env.TOKEN}}"},
                    "config": {"expDays": 30, "filter": "tags", "filterValue": "safe"},
                }
            },
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should validate successfully without env_vars or network calls
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Tools should be empty in validating mode
        tools = client.list_tools()
        assert len(tools) == 0

    def test_validating_mode_with_invalid_mcp_server(self, tmp_path):
        """Test that validating mode catches invalid MCP server configs."""
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "invalid_server": {
                    "command": "",  # Empty command should fail validation
                    "args": [],
                }
            },
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should raise error for invalid config even in validating mode
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)

        assert "missing required 'command' field" in str(exc_info.value)


class TestValidatingModeMixed:
    """Tests for validating mode with mixed tools, toolsets, and MCP servers."""

    def test_validating_mode_with_all_sources(self, tmp_path):
        """Test validating mode with tools, toolsets, and MCP servers together."""
        # Create a toolset
        lib_dir = tmp_path / "mci"
        lib_dir.mkdir()

        toolset_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "toolset_tool",
                    "execution": {"type": "text", "text": "From toolset"},
                }
            ],
        }

        toolset_file = lib_dir / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_data))

        # Main schema with all three sources
        schema_data = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "tools": [
                {
                    "name": "direct_tool",
                    "execution": {"type": "text", "text": "Hello {{env.USER}}"},
                }
            ],
            "toolsets": ["my_toolset"],
            "mcp_servers": {
                "test_mcp": {
                    "command": "npx",
                    "args": ["-y", "test-server"],
                    "env": {"KEY": "{{env.SECRET}}"},
                }
            },
        }

        schema_file = tmp_path / "main_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should validate successfully without env_vars
        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # In validating mode:
        # - Direct tools are loaded (they're in the schema)
        # - Toolsets are NOT loaded (just validated for existence)
        # - MCP servers are NOT fetched (just validated for structure)
        tools = client.list_tools()
        assert len(tools) == 1  # Only direct_tool
        assert tools[0] == "direct_tool"

    def test_validating_mode_schema_validation_still_works(self, tmp_path):
        """Test that schema validation errors are still caught in validating mode."""
        # Invalid schema (missing schemaVersion)
        schema_data = {
            "tools": [
                {
                    "name": "test_tool",
                    "execution": {"type": "text", "text": "Hello"},
                }
            ]
        }

        schema_file = tmp_path / "invalid_schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should still raise validation error
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)

        assert "schemaVersion" in str(exc_info.value)


class TestValidatingModeToolsetFile:
    """Tests for validating mode with toolset files as the main schema."""

    def test_validating_mode_with_toolset_file(self, tmp_path):
        """Test that validating mode works when validating a toolset file directly."""
        toolset_data = {
            "schemaVersion": "1.0",
            "metadata": {"name": "Test Toolset"},
            "tools": [
                {
                    "name": "tool1",
                    "execution": {"type": "text", "text": "Tool 1 with {{env.VAR}}"},
                },
                {
                    "name": "tool2",
                    "execution": {
                        "type": "http",
                        "method": "POST",
                        "url": "https://api.example.com/{{env.ENDPOINT}}",
                    },
                },
            ],
        }

        toolset_file = tmp_path / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_data))

        # Should validate toolset file successfully without env_vars
        client = MCIClient(schema_file_path=str(toolset_file), validating=True)

        # Tools should be loaded (they're directly in the file)
        tools = client.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_validating_mode_prevents_toolset_execution(self, tmp_path):
        """Test that toolset files in validating mode prevent execution."""
        toolset_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "simple_tool",
                    "execution": {"type": "text", "text": "Simple text"},
                }
            ],
        }

        toolset_file = tmp_path / "simple_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_data))

        client = MCIClient(schema_file_path=str(toolset_file), validating=True)

        # Execution should fail even for simple tools
        with pytest.raises(MCIClientError) as exc_info:
            client.execute("simple_tool")

        assert "validating mode" in str(exc_info.value).lower()


class TestValidatingModeSchemaParser:
    """Tests for SchemaParser validating mode."""

    def test_schema_parser_validating_mode(self, tmp_path):
        """Test SchemaParser.parse_file with validating mode."""
        schema_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "test",
                    "execution": {"type": "text", "text": "{{env.VALUE}}"},
                }
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema_data))

        # Should parse successfully in validating mode
        schema = SchemaParser.parse_file(str(schema_file), validating=True)

        assert schema.schemaVersion == "1.0"
        assert len(schema.tools) == 1
        assert schema.tools[0].name == "test"

    def test_schema_parser_parse_dict_validating_mode(self):
        """Test SchemaParser.parse_dict with validating mode."""
        schema_data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "test",
                    "execution": {
                        "type": "http",
                        "method": "GET",
                        "url": "https://api.example.com/{{env.KEY}}",
                    },
                }
            ],
        }

        # Should parse successfully
        schema = SchemaParser.parse_dict(schema_data, validating=True)

        assert schema.schemaVersion == "1.0"
        assert len(schema.tools) == 1
