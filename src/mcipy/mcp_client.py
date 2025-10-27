"""
LiteMcpClient - Lightweight MCP client integration using official mcp package.

This module provides a minimal, robust client for connecting to MCP tool servers
via STDIO (e.g., uvx/npx) and HTTP/SSE endpoints. It leverages the official `mcp`
package to handle server communication and tool management.

The LiteMcpClient allows seamless access to MCP tool servers for listing and
calling tools with full support for both local STDIO-based servers and web-based
HTTP/streamable endpoints.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel, Field, HttpUrl


class StdioCfg(BaseModel):
    """
    Configuration for STDIO-based MCP servers.

    Used for local servers started via command-line tools like uvx or npx.
    Supports environment variable injection for credentials and configuration.
    """

    type: Literal["stdio"] = "stdio"
    command: str = Field(..., description="Command to run (e.g., 'uvx', 'npx', or direct path)")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the command")
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables for the server process"
    )


class SseCfg(BaseModel):
    """
    Configuration for HTTP/SSE-based MCP servers.

    Used for web-based MCP servers using HTTP with Server-Sent Events (SSE)
    or modern Streamable HTTP transport. Supports custom headers for authentication.
    """

    type: Literal["http"] = "http"
    url: HttpUrl = Field(..., description="Server URL (e.g., 'http://localhost:8000/mcp')")
    headers: dict[str, str] = Field(
        default_factory=dict, description="HTTP headers for authentication"
    )


ServerCfg = StdioCfg | SseCfg


class ClientCfg(BaseModel):
    """
    Complete configuration for the LiteMcpClient.

    Wraps the server configuration with optional request timeout settings.
    """

    server: ServerCfg = Field(..., description="Server connection configuration")
    request_timeout: float | None = Field(default=60.0, description="Request timeout in seconds")


class LiteMcpClient:
    """
    Lightweight MCP client for connecting to MCP tool servers.

    Provides async context manager interface for managing connections to both
    STDIO-based and HTTP/SSE-based MCP servers. Supports listing and calling
    tools with full error handling.

    Example:
        ```python
        import asyncio
        from mcipy.mcp_client import LiteMcpClient, ClientCfg, StdioCfg

        async def main():
            cfg = ClientCfg(server=StdioCfg(
                command="uvx",
                args=["mcp-browser"]
            ))

            async with LiteMcpClient(cfg) as client:
                tools = await client.list_tools()
                print(f"Available tools: {tools}")

                if tools:
                    result = await client.call_tool(tools[0], param1="value")
                    print(f"Result: {result}")

        asyncio.run(main())
        ```
    """

    def __init__(self, cfg: ClientCfg):
        """
        Initialize the LiteMcpClient with configuration.

        Args:
            cfg: Client configuration specifying server type and connection details
        """
        self.cfg = cfg
        self._ctx = None
        self._read = None
        self._write = None
        self.session: ClientSession | None = None

    async def __aenter__(self) -> LiteMcpClient:
        """
        Async context manager entry - establish connection to MCP server.

        Returns:
            The initialized client instance with active session
        """
        try:
            srv = self.cfg.server

            if isinstance(srv, StdioCfg):
                # STDIO transport for local servers (uvx, npx, etc.)
                # Merge server env vars with current environment
                merged_env = os.environ.copy()
                merged_env.update(srv.env)

                params = StdioServerParameters(command=srv.command, args=srv.args, env=merged_env)
                self._ctx = stdio_client(params)
            else:
                # Streamable HTTP transport for web servers
                # This is the modern replacement for SSE transport
                self._ctx = streamablehttp_client(str(srv.url), headers=srv.headers or None)

            # Enter the transport context and get read/write streams
            context_result = await self._ctx.__aenter__()
            self._read, self._write = context_result[0], context_result[1]

            # Create and initialize the client session
            self.session = ClientSession(self._read, self._write)
            await self.session.__aenter__()
            await self.session.initialize()

            return self

        except Exception:
            # If initialization fails, clean up any partially initialized resources
            await self.__aexit__(None, None, None)
            raise

    async def __aexit__(self, *exc) -> None:
        """
        Async context manager exit - clean up connection.

        Args:
            exc: Exception information if an error occurred
        """
        # Clean up session first, then transport context
        # Handle each cleanup separately to avoid cascading failures
        if self.session:
            try:
                await self.session.__aexit__(*exc)
            except Exception:
                # Suppress cleanup errors - the original exception is more important
                pass
            finally:
                self.session = None

        if self._ctx:
            try:
                await self._ctx.__aexit__(*exc)
            except Exception:
                # Suppress cleanup errors - the original exception is more important
                pass
            finally:
                self._ctx = None

    async def list_tools(self) -> list[str]:
        """
        List all available tools from the MCP server.

        Returns:
            List of tool names available on the server

        Raises:
            RuntimeError: If session is not initialized (client not used as context manager)
        """
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use LiteMcpClient as an async context manager."
            )

        resp = await self.session.list_tools()
        return [t.name for t in resp.tools]

    async def call_tool(self, name: str, **arguments: Any) -> Any:
        """
        Call a tool on the MCP server with the provided arguments.

        Args:
            name: Name of the tool to call
            **arguments: Keyword arguments to pass to the tool

        Returns:
            The tool execution result from the server

        Raises:
            RuntimeError: If session is not initialized (client not used as context manager)
        """
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use LiteMcpClient as an async context manager."
            )

        result = await self.session.call_tool(name, arguments=arguments)
        return result
