"""Unit tests for MCP executor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcipy.enums import ExecutionType
from mcipy.executors.mcp_executor import MCPExecutor, MCPExecutorError
from mcipy.models import (
    ExecutionResult,
    HttpMCPServer,
    MCPExecutionConfig,
    StdioMCPServer,
)


class TestMCPExecutor:
    """Tests for MCPExecutor class."""

    def test_init_with_no_servers(self):
        """Test initialization with no MCP servers."""
        executor = MCPExecutor()
        assert executor.mcp_servers == {}

    def test_init_with_servers(self):
        """Test initialization with MCP servers."""
        servers = {
            "filesystem": StdioMCPServer(command="npx"),
            "github": HttpMCPServer(url="https://api.example.com/mcp"),
        }
        executor = MCPExecutor(mcp_servers=servers)
        assert "filesystem" in executor.mcp_servers
        assert "github" in executor.mcp_servers

    def test_execute_server_not_registered(self):
        """Test execution fails when server is not registered."""
        executor = MCPExecutor(mcp_servers={})
        config = MCPExecutionConfig(
            type=ExecutionType.MCP, serverName="unknown", toolName="test"
        )
        context = {"props": {}, "env": {}}

        result = executor.execute(config, context)

        assert result.result.isError is True
        assert "not registered" in str(result.result.content[0].text).lower()

    def test_execute_invalid_config_type(self):
        """Test execution fails with invalid config type."""
        from mcipy.models import TextExecutionConfig

        executor = MCPExecutor(mcp_servers={})
        config = TextExecutionConfig(type=ExecutionType.TEXT, text="test")
        context = {"props": {}, "env": {}}

        result = executor.execute(config, context)

        assert result.result.isError is True
        assert "Invalid config type" in result.result.content[0].text

    @pytest.mark.anyio
    async def test_async_execute_with_stdio_server(self):
        """Test async execution with STDIO MCP server."""
        # Mock MCP call result
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "File contents: Hello World"

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        mock_result.isError = False

        # Mock MCP session
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock transport context
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("mcipy.executors.mcp_executor.stdio_client", return_value=mock_context):
            with patch("mcipy.executors.mcp_executor.ClientSession", return_value=mock_session):
                server_config = StdioMCPServer(command="npx", args=["-y", "mcp-server"])
                executor = MCPExecutor(mcp_servers={"filesystem": server_config})

                config = MCPExecutionConfig(
                    type=ExecutionType.MCP, serverName="filesystem", toolName="read_file"
                )
                context = {"props": {"path": "/test/file.txt"}, "env": {}}

                result = await executor._async_execute(config, context, server_config)

                # Verify result
                assert isinstance(result, ExecutionResult)
                assert result.result.isError is False
                assert len(result.result.content) == 1
                assert result.result.content[0].text == "File contents: Hello World"
                assert result.result.metadata["mcp_server"] == "filesystem"
                assert result.result.metadata["mcp_tool"] == "read_file"

                # Verify tool was called with correct arguments
                mock_session.call_tool.assert_called_once_with(
                    "read_file", arguments={"path": "/test/file.txt"}
                )

    @pytest.mark.anyio
    async def test_async_execute_with_http_server(self):
        """Test async execution with HTTP MCP server."""
        # Mock MCP call result
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Repository list: repo1, repo2"

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        mock_result.isError = False

        # Mock MCP session
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock transport context
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "mcipy.executors.mcp_executor.streamablehttp_client", return_value=mock_context
        ):
            with patch("mcipy.executors.mcp_executor.ClientSession", return_value=mock_session):
                server_config = HttpMCPServer(
                    url="https://api.githubcopilot.com/mcp/",
                    headers={"Authorization": "Bearer token"},
                )
                executor = MCPExecutor(mcp_servers={"github": server_config})

                config = MCPExecutionConfig(
                    type=ExecutionType.MCP, serverName="github", toolName="list_repos"
                )
                context = {"props": {"org": "myorg"}, "env": {}}

                result = await executor._async_execute(config, context, server_config)

                # Verify result
                assert result.result.isError is False
                assert result.result.content[0].text == "Repository list: repo1, repo2"

                # Verify tool was called with correct arguments
                mock_session.call_tool.assert_called_once_with(
                    "list_repos", arguments={"org": "myorg"}
                )

    @pytest.mark.anyio
    async def test_async_execute_connection_failure(self):
        """Test async execution handles connection failures."""
        # Mock transport that fails
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("mcipy.executors.mcp_executor.stdio_client", return_value=mock_context):
            server_config = StdioMCPServer(command="npx")
            executor = MCPExecutor(mcp_servers={"test": server_config})

            config = MCPExecutionConfig(
                type=ExecutionType.MCP, serverName="test", toolName="test_tool"
            )
            context = {"props": {}, "env": {}}

            with pytest.raises(MCPExecutorError) as exc_info:
                await executor._async_execute(config, context, server_config)

            assert "Failed to execute MCP tool" in str(exc_info.value)
            assert "Connection refused" in str(exc_info.value)

    def test_execute_with_templating(self):
        """Test that execution applies templating to server configuration."""
        # This is tested implicitly through integration with MCPIntegration
        # The executor uses MCPIntegration._apply_templating_to_config
        pass

    @pytest.mark.anyio
    async def test_async_execute_with_empty_properties(self):
        """Test async execution with no tool properties."""
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Default result"

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        mock_result.isError = False

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("mcipy.executors.mcp_executor.stdio_client", return_value=mock_context):
            with patch("mcipy.executors.mcp_executor.ClientSession", return_value=mock_session):
                server_config = StdioMCPServer(command="npx")
                executor = MCPExecutor(mcp_servers={"test": server_config})

                config = MCPExecutionConfig(
                    type=ExecutionType.MCP, serverName="test", toolName="test_tool"
                )
                context = {"props": {}, "env": {}}  # Empty props

                result = await executor._async_execute(config, context, server_config)

                # Verify tool was called with empty arguments
                mock_session.call_tool.assert_called_once_with("test_tool", arguments={})
                assert result.result.isError is False
