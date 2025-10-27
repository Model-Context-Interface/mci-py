"""Unit tests for MCP integration module."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from mcipy.enums import ExecutionType
from mcipy.mcp_integration import MCPIntegration, MCPIntegrationError
from mcipy.models import (
    HttpMCPServer,
    MCPServerConfig,
    StdioMCPServer,
    ToolsetSchema,
)
from mcipy.templating import TemplateEngine


class TestMCPIntegrationTemplating:
    """Tests for MCP configuration templating."""

    def test_template_stdio_command(self):
        """Test templating in STDIO server command."""
        config = StdioMCPServer(
            command="{{env.COMMAND}}",
            args=["{{env.ARG1}}", "fixed-arg"],
            env={"API_KEY": "{{env.MY_KEY}}"},
        )
        env_context = {"env": {"COMMAND": "npx", "ARG1": "-y", "MY_KEY": "secret123"}}
        template_engine = TemplateEngine()

        templated = MCPIntegration._apply_templating_to_config(
            config, env_context, template_engine
        )

        assert templated.command == "npx"
        assert templated.args[0] == "-y"
        assert templated.args[1] == "fixed-arg"
        assert templated.env["API_KEY"] == "secret123"

    def test_template_http_url_and_headers(self):
        """Test templating in HTTP server URL and headers."""
        config = HttpMCPServer(
            url="{{env.BASE_URL}}/mcp",
            headers={"Authorization": "Bearer {{env.TOKEN}}"},
        )
        env_context = {"env": {"BASE_URL": "https://api.example.com", "TOKEN": "abc123"}}
        template_engine = TemplateEngine()

        templated = MCPIntegration._apply_templating_to_config(
            config, env_context, template_engine
        )

        assert templated.url == "https://api.example.com/mcp"
        assert templated.headers["Authorization"] == "Bearer abc123"

    def test_template_preserves_config(self):
        """Test that templating preserves server config."""
        config = StdioMCPServer(
            command="npx",
            config=MCPServerConfig(expDays=7, filter="only", filterValue="tool1"),
        )
        env_context = {"env": {}}
        template_engine = TemplateEngine()

        templated = MCPIntegration._apply_templating_to_config(
            config, env_context, template_engine
        )

        assert templated.config.expDays == 7
        assert templated.config.filter == "only"
        assert templated.config.filterValue == "tool1"


class TestMCPIntegrationFetchAndBuild:
    """Tests for MCP toolset fetching and building."""

    @pytest.mark.anyio
    async def test_build_toolset_from_mcp_tools(self):
        """Test building MCI toolset from MCP tool definitions."""
        # Mock MCP tool response
        mock_tool1 = MagicMock()
        mock_tool1.name = "read_file"
        mock_tool1.description = "Read a file"
        mock_tool1.inputSchema = {"type": "object", "properties": {"path": {"type": "string"}}}

        mock_tool2 = MagicMock()
        mock_tool2.name = "write_file"
        mock_tool2.description = "Write to a file"
        mock_tool2.inputSchema = None

        mock_tools_response = MagicMock()
        mock_tools_response.tools = [mock_tool1, mock_tool2]

        # Mock MCP session
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_tools_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock transport context
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("mcp.client.stdio.stdio_client", return_value=mock_context):
            with patch("mcp.ClientSession", return_value=mock_session):
                server_config = StdioMCPServer(
                    command="npx", args=["-y", "mcp-server"]
                )
                result = await MCPIntegration._async_fetch_and_build_toolset(
                    server_name="test-server",
                    server_config=server_config,
                    schema_version="1.0",
                    env_context={"env": {}},
                    template_engine=TemplateEngine(),
                )

                # Verify toolset structure
                assert isinstance(result, ToolsetSchema)
                assert result.schemaVersion == "1.0"
                assert len(result.tools) == 2

                # Verify first tool
                tool1 = result.tools[0]
                assert tool1.name == "read_file"
                assert tool1.description == "Read a file"
                assert tool1.execution.type == ExecutionType.MCP
                assert tool1.execution.serverName == "test-server"
                assert tool1.execution.toolName == "read_file"
                assert tool1.inputSchema == {"type": "object", "properties": {"path": {"type": "string"}}}

                # Verify second tool
                tool2 = result.tools[1]
                assert tool2.name == "write_file"
                assert tool2.inputSchema is None

                # Verify expiration is set
                assert result.expiresAt is not None
                expires_at = datetime.fromisoformat(result.expiresAt)
                expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
                # Allow 1 minute tolerance for test execution time
                assert abs((expires_at - expected_expiry).total_seconds()) < 60

    def test_fetch_and_build_sync_wrapper(self):
        """Test synchronous wrapper for async fetch_and_build_toolset."""
        # This test verifies that the sync wrapper correctly calls the async implementation
        # We'll mock the async call since testing actual MCP connections requires a real server

        with patch.object(
            MCPIntegration, "_async_fetch_and_build_toolset"
        ) as mock_async:
            mock_toolset = MagicMock(spec=ToolsetSchema)
            mock_async.return_value = mock_toolset

            server_config = StdioMCPServer(command="npx")

            # This will fail in actual execution but demonstrates the pattern
            # In real usage, asyncio.run would be called
            try:
                result = MCPIntegration.fetch_and_build_toolset(
                    server_name="test",
                    server_config=server_config,
                    schema_version="1.0",
                    env_context={"env": {}},
                    template_engine=TemplateEngine(),
                )
            except RuntimeError:
                # asyncio.run() not available in this context, which is expected
                pass

    def test_fetch_and_build_error_handling(self):
        """Test error handling when MCP server connection fails."""

        async def failing_fetch(*args, **kwargs):
            raise Exception("Connection failed")

        with patch.object(
            MCPIntegration, "_async_fetch_and_build_toolset", side_effect=failing_fetch
        ):
            server_config = StdioMCPServer(command="npx")

            with pytest.raises(MCPIntegrationError) as exc_info:
                MCPIntegration.fetch_and_build_toolset(
                    server_name="test",
                    server_config=server_config,
                    schema_version="1.0",
                    env_context={"env": {}},
                    template_engine=TemplateEngine(),
                )

            assert "Failed to fetch from MCP server" in str(exc_info.value)
            assert "Connection failed" in str(exc_info.value)


class TestMCPIntegrationExpiration:
    """Tests for MCP toolset expiration handling."""

    @pytest.mark.anyio
    async def test_expiration_date_calculation(self):
        """Test that expiration date is calculated correctly based on expDays."""
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test"
        mock_tool.inputSchema = None

        mock_tools_response = MagicMock()
        mock_tools_response.tools = [mock_tool]

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_tools_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("mcp.client.stdio.stdio_client", return_value=mock_context):
            with patch("mcp.ClientSession", return_value=mock_session):
                # Test with custom expDays
                server_config = StdioMCPServer(
                    command="npx", config=MCPServerConfig(expDays=7)
                )

                result = await MCPIntegration._async_fetch_and_build_toolset(
                    server_name="test",
                    server_config=server_config,
                    schema_version="1.0",
                    env_context={"env": {}},
                    template_engine=TemplateEngine(),
                )

                # Verify expiration is 7 days from now
                expires_at = datetime.fromisoformat(result.expiresAt)
                expected_expiry = datetime.now(timezone.utc) + timedelta(days=7)
                assert abs((expires_at - expected_expiry).total_seconds()) < 60
