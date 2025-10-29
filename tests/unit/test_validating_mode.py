"""
Unit tests for MCIClient validating mode.

Tests that validating mode performs schema validation without loading MCP servers,
toolsets, or resolving templates, and without any side effects.
"""

import json

import pytest

from mcipy import MCIClient, MCIClientError


class TestValidatingModeBasics:
    """Tests for basic validating mode functionality."""

    def test_validating_mode_with_simple_schema(self, tmp_path):
        """Test validating mode with simple schema containing only inline tools."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "test_tool", "execution": {"type": "text", "text": "Hello World"}}
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should load successfully in validating mode
        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        assert client is not None
        assert len(client.list_tools()) == 1

    def test_validating_mode_default_false(self, tmp_path):
        """Test that validating mode defaults to False."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "test_tool", "execution": {"type": "text", "text": "Hello World"}}
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Default should be validating=False
        client = MCIClient(schema_file_path=str(schema_file))
        # Should be able to execute in normal mode
        result = client.execute("test_tool", {})
        assert result.result.isError is False

    def test_validating_mode_explicit_false(self, tmp_path):
        """Test validating mode with explicit validating=False."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "test_tool", "execution": {"type": "text", "text": "Hello World"}}
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Explicit validating=False should work like normal mode
        client = MCIClient(schema_file_path=str(schema_file), validating=False)
        result = client.execute("test_tool", {})
        assert result.result.isError is False


class TestValidatingModeWithMCPServers:
    """Tests for validating mode with MCP servers."""

    def test_mcp_server_without_env_vars_validating_mode(self, tmp_path):
        """Test that MCP server with unresolved env vars works in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "test_server": {
                    "command": "npx",
                    "args": ["-y", "test-server", "{{env.REQUIRED_VAR}}"],
                    "config": {"expDays": 1},
                }
            },
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should work in validating mode without env vars
        client = MCIClient(schema_file_path=str(schema_file), env_vars={}, validating=True)
        assert client is not None

    def test_mcp_server_without_env_vars_normal_mode_fails(self, tmp_path):
        """Test that MCP server with unresolved env vars fails in normal mode."""
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "test_server": {
                    "command": "npx",
                    "args": ["-y", "test-server", "{{env.REQUIRED_VAR}}"],
                    "config": {"expDays": 1},
                }
            },
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should fail in normal mode without env vars
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), env_vars={}, validating=False)
        assert "Failed to resolve placeholder" in str(exc_info.value)

    def test_mcp_server_http_without_env_vars(self, tmp_path):
        """Test HTTP MCP server with unresolved env vars in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "test_http": {
                    "type": "http",
                    "url": "https://api.example.com/mcp",
                    "headers": {"Authorization": "Bearer {{env.API_TOKEN}}"},
                    "config": {"expDays": 1},
                }
            },
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should work in validating mode
        client = MCIClient(schema_file_path=str(schema_file), env_vars={}, validating=True)
        assert client is not None

    def test_multiple_mcp_servers_validating_mode(self, tmp_path):
        """Test multiple MCP servers in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "server1": {
                    "command": "npx",
                    "args": ["-y", "server1", "{{env.VAR1}}"],
                    "config": {"expDays": 1},
                },
                "server2": {
                    "type": "http",
                    "url": "{{env.SERVER2_URL}}",
                    "headers": {},
                    "config": {"expDays": 1},
                },
            },
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should work with all servers in validating mode
        client = MCIClient(schema_file_path=str(schema_file), env_vars={}, validating=True)
        assert client is not None


class TestValidatingModeWithToolsets:
    """Tests for validating mode with toolsets."""

    def test_toolset_validating_mode(self, tmp_path):
        """Test that toolsets are validated but not loaded in validating mode."""
        # Create a toolset file
        toolset_dir = tmp_path / "mci"
        toolset_dir.mkdir()

        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "toolset_tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "toolset_tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        toolset_file = toolset_dir / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_schema))

        # Create main schema
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["my_toolset"],
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should validate but not load tools in validating mode
        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        assert client is not None
        # In validating mode, toolset tools are not loaded
        assert len(client.list_tools()) == 0

    def test_toolset_normal_mode_loads_tools(self, tmp_path):
        """Test that toolsets are loaded in normal mode."""
        # Create a toolset file
        toolset_dir = tmp_path / "mci"
        toolset_dir.mkdir()

        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "toolset_tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "toolset_tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        toolset_file = toolset_dir / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_schema))

        # Create main schema
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["my_toolset"],
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should load tools in normal mode
        client = MCIClient(schema_file_path=str(schema_file), validating=False)
        assert len(client.list_tools()) == 2

    def test_nonexistent_toolset_fails_validating_mode(self, tmp_path):
        """Test that non-existent toolset raises error even in validating mode."""
        toolset_dir = tmp_path / "mci"
        toolset_dir.mkdir()

        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["nonexistent_toolset"],
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should fail in validating mode
        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)
        assert "Toolset not found" in str(exc_info.value)

    def test_toolset_directory_validating_mode(self, tmp_path):
        """Test validating mode with toolset directory."""
        # Create a toolset directory with multiple files
        toolset_dir = tmp_path / "mci" / "my_toolset"
        toolset_dir.mkdir(parents=True)

        toolset1 = {
            "schemaVersion": "1.0",
            "tools": [{"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}}],
        }
        toolset2 = {
            "schemaVersion": "1.0",
            "tools": [{"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}}],
        }

        (toolset_dir / "part1.mci.json").write_text(json.dumps(toolset1))
        (toolset_dir / "part2.mci.json").write_text(json.dumps(toolset2))

        # Create main schema
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": ["my_toolset"],
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should validate successfully
        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        assert client is not None

    def test_toolset_with_filters_validating_mode(self, tmp_path):
        """Test that toolset filters are validated but not applied in validating mode."""
        # Create a toolset file
        toolset_dir = tmp_path / "mci"
        toolset_dir.mkdir()

        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        toolset_file = toolset_dir / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_schema))

        # Create main schema with filter
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "toolsets": [{"name": "my_toolset", "filter": "only", "filterValue": "tool1"}],
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Should validate successfully in validating mode
        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        assert client is not None


class TestValidatingModeExecutionBlocked:
    """Tests that tool execution is blocked in validating mode."""

    def test_execute_blocked_in_validating_mode(self, tmp_path):
        """Test that execute() raises error in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "test_tool", "execution": {"type": "text", "text": "Hello World"}}
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        # Should raise error
        with pytest.raises(MCIClientError) as exc_info:
            client.execute("test_tool", {})

        assert "validating mode" in str(exc_info.value).lower()
        assert "disabled" in str(exc_info.value).lower()

    def test_execute_error_message_helpful(self, tmp_path):
        """Test that execution error message is helpful."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "test_tool", "execution": {"type": "text", "text": "Hello World"}}
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)

        with pytest.raises(MCIClientError) as exc_info:
            client.execute("test_tool", {})

        error_msg = str(exc_info.value)
        assert "validating=False" in error_msg


class TestValidatingModeNoSideEffects:
    """Tests that validating mode has no side effects."""

    def test_no_mcp_cache_directory_created(self, tmp_path):
        """Test that MCP cache directory is not created in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "test_server": {
                    "command": "npx",
                    "args": ["-y", "test-server"],
                    "config": {"expDays": 1},
                }
            },
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Load in validating mode
        MCIClient(schema_file_path=str(schema_file), validating=True)

        # MCP cache directory should not exist
        mcp_dir = tmp_path / "mci" / "mcp"
        assert not mcp_dir.exists()

    def test_no_files_written_validating_mode(self, tmp_path):
        """Test that no files are written in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "libraryDir": "./mci",
            "mcp_servers": {
                "test_server": {
                    "command": "npx",
                    "args": ["-y", "test-server"],
                    "config": {"expDays": 1},
                }
            },
            "tools": [],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        # Get initial file list
        initial_files = set(tmp_path.rglob("*"))

        # Load in validating mode
        MCIClient(schema_file_path=str(schema_file), validating=True)

        # Get final file list
        final_files = set(tmp_path.rglob("*"))

        # No new files should be created
        assert initial_files == final_files


class TestValidatingModeSchemaValidation:
    """Tests that schema validation still works in validating mode."""

    def test_invalid_schema_version_fails(self, tmp_path):
        """Test that invalid schema version fails in validating mode."""
        schema = {"schemaVersion": "999.0", "tools": []}

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)
        assert "Unsupported schema version" in str(exc_info.value)

    def test_missing_required_fields_fails(self, tmp_path):
        """Test that missing required fields fail in validating mode."""
        schema = {"tools": []}  # Missing schemaVersion

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)
        # Check for the field name in the error (case-insensitive)
        assert "schemaversion" in str(exc_info.value).lower()

    def test_invalid_tool_structure_fails(self, tmp_path):
        """Test that invalid tool structure fails in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [{"name": "test_tool"}],  # Missing execution
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)
        assert "execution" in str(exc_info.value).lower()

    def test_invalid_execution_type_fails(self, tmp_path):
        """Test that invalid execution type fails in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [{"name": "test_tool", "execution": {"type": "invalid_type"}}],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(schema_file), validating=True)
        assert "Invalid execution type" in str(exc_info.value)


class TestValidatingModeToolsetFile:
    """Tests for validating mode when loading a toolset file directly."""

    def test_validate_toolset_file_directly(self, tmp_path):
        """Test validating a toolset file directly."""
        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        toolset_file = tmp_path / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_schema))

        # Should load successfully in validating mode
        client = MCIClient(schema_file_path=str(toolset_file), validating=True)
        assert client is not None
        # Toolset file is loaded even in validating mode (it's the main schema)
        assert len(client.list_tools()) == 2

    def test_validate_toolset_file_with_invalid_structure(self, tmp_path):
        """Test that invalid toolset file fails validation."""
        toolset_schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1"}  # Missing execution
            ],
        }

        toolset_file = tmp_path / "my_toolset.mci.json"
        toolset_file.write_text(json.dumps(toolset_schema))

        with pytest.raises(MCIClientError) as exc_info:
            MCIClient(schema_file_path=str(toolset_file), validating=True)
        assert "execution" in str(exc_info.value).lower()


class TestValidatingModeReadOnlyOperations:
    """Tests that read-only operations work in validating mode."""

    def test_list_tools_works(self, tmp_path):
        """Test that list_tools() works in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        tools = client.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_tools_works(self, tmp_path):
        """Test that tools() works in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        tools = client.tools()
        assert len(tools) == 2

    def test_only_works(self, tmp_path):
        """Test that only() filtering works in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        tools = client.only(["tool1"])
        assert len(tools) == 1
        assert tools[0].name == "tool1"

    def test_without_works(self, tmp_path):
        """Test that without() filtering works in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {"name": "tool1", "execution": {"type": "text", "text": "Tool 1"}},
                {"name": "tool2", "execution": {"type": "text", "text": "Tool 2"}},
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        tools = client.without(["tool1"])
        assert len(tools) == 1
        assert tools[0].name == "tool2"

    def test_get_tool_schema_works(self, tmp_path):
        """Test that get_tool_schema() works in validating mode."""
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "tool1",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                    "execution": {"type": "text", "text": "Tool 1"},
                }
            ],
        }

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file), validating=True)
        schema_obj = client.get_tool_schema("tool1")
        assert "properties" in schema_obj
        assert "param" in schema_obj["properties"]
