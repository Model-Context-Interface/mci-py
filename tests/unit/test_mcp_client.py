"""
Unit tests for LiteMcpClient class.

Tests the MCP client integration including STDIO and HTTP connections,
tool listing, tool execution, and error handling.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcipy import ClientCfg, LiteMcpClient, SseCfg, StdioCfg


class TestStdioCfg:
    """Test STDIO configuration model."""

    def test_stdio_cfg_defaults(self):
        """Test StdioCfg with default values."""
        cfg = StdioCfg(command="uvx")
        assert cfg.type == "stdio"
        assert cfg.command == "uvx"
        assert cfg.args == []
        assert cfg.env == {}

    def test_stdio_cfg_with_args(self):
        """Test StdioCfg with arguments."""
        cfg = StdioCfg(command="npx", args=["-y", "mcp-server-memory"])
        assert cfg.command == "npx"
        assert cfg.args == ["-y", "mcp-server-memory"]

    def test_stdio_cfg_with_env(self):
        """Test StdioCfg with environment variables."""
        cfg = StdioCfg(command="uvx", args=["mcp-browser"], env={"API_KEY": "secret"})
        assert cfg.env == {"API_KEY": "secret"}

    def test_stdio_cfg_validation(self):
        """Test StdioCfg validation."""
        # Command is required
        with pytest.raises(Exception):  # Pydantic validation error
            StdioCfg()  # type: ignore


class TestSseCfg:
    """Test SSE/HTTP configuration model."""

    def test_sse_cfg_defaults(self):
        """Test SseCfg with default values."""
        cfg = SseCfg(url="http://localhost:8000/mcp")
        assert cfg.type == "http"
        assert str(cfg.url) == "http://localhost:8000/mcp"
        assert cfg.headers == {}

    def test_sse_cfg_with_headers(self):
        """Test SseCfg with custom headers."""
        cfg = SseCfg(
            url="https://api.example.com/mcp", headers={"Authorization": "Bearer token"}
        )
        assert cfg.headers == {"Authorization": "Bearer token"}

    def test_sse_cfg_url_validation(self):
        """Test SseCfg URL validation."""
        # Invalid URL should fail
        with pytest.raises(Exception):  # Pydantic validation error
            SseCfg(url="not-a-url")  # type: ignore


class TestClientCfg:
    """Test client configuration model."""

    def test_client_cfg_with_stdio(self):
        """Test ClientCfg with STDIO server."""
        server = StdioCfg(command="uvx", args=["mcp-browser"])
        cfg = ClientCfg(server=server)
        assert isinstance(cfg.server, StdioCfg)
        assert cfg.request_timeout == 60.0

    def test_client_cfg_with_http(self):
        """Test ClientCfg with HTTP server."""
        server = SseCfg(url="http://localhost:8000/mcp")
        cfg = ClientCfg(server=server)
        assert isinstance(cfg.server, SseCfg)
        assert cfg.request_timeout == 60.0

    def test_client_cfg_custom_timeout(self):
        """Test ClientCfg with custom timeout."""
        server = StdioCfg(command="uvx")
        cfg = ClientCfg(server=server, request_timeout=120.0)
        assert cfg.request_timeout == 120.0


class TestLiteMcpClient:
    """Test LiteMcpClient functionality."""

    def test_client_initialization(self):
        """Test client initialization."""
        cfg = ClientCfg(server=StdioCfg(command="uvx"))
        client = LiteMcpClient(cfg)
        assert client.cfg == cfg
        assert client.session is None

    @pytest.mark.anyio
    async def test_stdio_connection_setup(self):
        """Test STDIO connection setup in context manager."""
        cfg = ClientCfg(server=StdioCfg(command="uvx", args=["mcp-browser"]))

        # Mock the STDIO client and session
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_ctx.__aexit__ = AsyncMock()

        with patch("mcipy.mcp_client.stdio_client", return_value=mock_ctx), patch(
            "mcipy.mcp_client.ClientSession", return_value=mock_session
        ):
            client = LiteMcpClient(cfg)
            async with client:
                assert client.session is not None
                assert client._read == mock_read
                assert client._write == mock_write
                mock_session.initialize.assert_awaited_once()

    @pytest.mark.anyio
    async def test_http_connection_setup(self):
        """Test HTTP connection setup in context manager."""
        cfg = ClientCfg(
            server=SseCfg(url="http://localhost:8000/mcp", headers={"Auth": "Bearer xyz"})
        )

        # Mock the HTTP client and session
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_ctx.__aexit__ = AsyncMock()

        with patch("mcipy.mcp_client.streamablehttp_client", return_value=mock_ctx), patch(
            "mcipy.mcp_client.ClientSession", return_value=mock_session
        ):
            client = LiteMcpClient(cfg)
            async with client:
                assert client.session is not None
                assert client._read == mock_read
                assert client._write == mock_write
                mock_session.initialize.assert_awaited_once()

    @pytest.mark.anyio
    async def test_list_tools_success(self):
        """Test successful tool listing."""
        cfg = ClientCfg(server=StdioCfg(command="uvx"))

        # Mock tool response
        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"

        mock_response = MagicMock()
        mock_response.tools = [mock_tool1, mock_tool2]

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_response)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_ctx.__aexit__ = AsyncMock()

        with patch("mcipy.mcp_client.stdio_client", return_value=mock_ctx), patch(
            "mcipy.mcp_client.ClientSession", return_value=mock_session
        ):
            client = LiteMcpClient(cfg)
            async with client:
                tools = await client.list_tools()
                assert tools == ["tool1", "tool2"]
                mock_session.list_tools.assert_awaited_once()

    @pytest.mark.anyio
    async def test_list_tools_without_context_manager(self):
        """Test list_tools raises error when not used as context manager."""
        cfg = ClientCfg(server=StdioCfg(command="uvx"))
        client = LiteMcpClient(cfg)

        with pytest.raises(RuntimeError, match="Session not initialized"):
            await client.list_tools()

    @pytest.mark.anyio
    async def test_call_tool_success(self):
        """Test successful tool execution."""
        cfg = ClientCfg(server=StdioCfg(command="uvx"))

        # Mock tool result
        mock_result = MagicMock()
        mock_result.content = [{"type": "text", "text": "Success"}]

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_ctx.__aexit__ = AsyncMock()

        with patch("mcipy.mcp_client.stdio_client", return_value=mock_ctx), patch(
            "mcipy.mcp_client.ClientSession", return_value=mock_session
        ):
            client = LiteMcpClient(cfg)
            async with client:
                result = await client.call_tool("test_tool", param1="value1", param2="value2")
                assert result == mock_result
                mock_session.call_tool.assert_awaited_once_with(
                    "test_tool", arguments={"param1": "value1", "param2": "value2"}
                )

    @pytest.mark.anyio
    async def test_call_tool_without_context_manager(self):
        """Test call_tool raises error when not used as context manager."""
        cfg = ClientCfg(server=StdioCfg(command="uvx"))
        client = LiteMcpClient(cfg)

        with pytest.raises(RuntimeError, match="Session not initialized"):
            await client.call_tool("test_tool", param="value")

    @pytest.mark.anyio
    async def test_context_manager_cleanup(self):
        """Test proper cleanup on context manager exit."""
        cfg = ClientCfg(server=StdioCfg(command="uvx"))

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_ctx.__aexit__ = AsyncMock()

        with patch("mcipy.mcp_client.stdio_client", return_value=mock_ctx), patch(
            "mcipy.mcp_client.ClientSession", return_value=mock_session
        ):
            client = LiteMcpClient(cfg)
            async with client:
                pass

            # Verify cleanup was called
            mock_session.__aexit__.assert_awaited_once()
            mock_ctx.__aexit__.assert_awaited_once()

    @pytest.mark.anyio
    async def test_environment_variable_merging(self):
        """Test that environment variables are properly merged for STDIO."""
        import os

        cfg = ClientCfg(server=StdioCfg(command="uvx", env={"CUSTOM_VAR": "test_value"}))

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_ctx.__aexit__ = AsyncMock()

        with patch("mcipy.mcp_client.stdio_client", return_value=mock_ctx) as mock_stdio, patch(
            "mcipy.mcp_client.ClientSession", return_value=mock_session
        ):
            client = LiteMcpClient(cfg)
            async with client:
                pass

            # Verify stdio_client was called with merged environment
            call_args = mock_stdio.call_args
            params = call_args[0][0]
            assert params.env is not None
            assert "CUSTOM_VAR" in params.env
            assert params.env["CUSTOM_VAR"] == "test_value"
