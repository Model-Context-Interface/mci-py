"""
MCP executor for executing tools via Model Context Protocol servers.

This module provides the MCPExecutor class for executing tools on MCP servers,
handling both STDIO and HTTP transports, and managing connections and tool calls.
"""

import asyncio
from typing import Any

from ..models import (
    ExecutionConfig,
    ExecutionResult,
    ExecutionResultContent,
    MCPExecutionConfig,
    TextContent,
)
from .base import BaseExecutor


class MCPExecutorError(Exception):
    """Exception raised for MCP executor errors."""

    pass


class MCPExecutor(BaseExecutor):
    """
    Executor for MCP (Model Context Protocol) tools.

    Connects to MCP servers via STDIO or HTTP transports and executes tools
    using the MCP protocol. Handles connection management, tool calls, and
    result formatting.
    """

    def __init__(self, mcp_servers: dict[str, Any] | None = None):
        """
        Initialize the MCP executor with MCP server configurations.

        Args:
            mcp_servers: Dictionary of MCP server configurations from main schema
        """
        super().__init__()
        self.mcp_servers = mcp_servers or {}

    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """
        Execute an MCP tool by connecting to the server and calling the tool.

        Args:
            config: MCP execution configuration with server and tool names
            context: Execution context with properties and environment variables

        Returns:
            ExecutionResult with tool execution results

        Raises:
            MCPExecutorError: If server is not registered or execution fails
        """
        # Type guard: ensure config is MCPExecutionConfig
        if not isinstance(config, MCPExecutionConfig):
            return self._format_error(
                MCPExecutorError(
                    f"Invalid config type: expected MCPExecutionConfig, got {type(config)}"
                )
            )

        # Get server configuration
        if config.serverName not in self.mcp_servers:
            return self._format_error(
                MCPExecutorError(f"MCP server '{config.serverName}' not registered in main schema")
            )

        server_config = self.mcp_servers[config.serverName]

        # Execute async operation in sync context
        try:
            result = asyncio.run(self._async_execute(config, context, server_config))
            return result
        except Exception as e:
            return self._format_error(e)

    async def _async_execute(
        self, config: MCPExecutionConfig, context: dict[str, Any], server_config: Any
    ) -> ExecutionResult:
        """
        Async implementation of MCP tool execution.

        Connects to MCP server, calls the tool, and returns formatted results.
        """
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp.client.streamable_http import streamablehttp_client

        from ..templating import TemplateEngine

        # Apply templating to server config
        template_engine = TemplateEngine()
        from ..mcp_integration import MCPIntegration

        templated_config = MCPIntegration._apply_templating_to_config(
            server_config, context, template_engine
        )

        # Connect to MCP server based on type
        from ..models import StdioMCPServer

        if isinstance(templated_config, StdioMCPServer):
            # STDIO server
            import os

            # Merge server env vars with current environment
            merged_env = os.environ.copy()
            merged_env.update(templated_config.env)

            params = StdioServerParameters(
                command=templated_config.command, args=templated_config.args, env=merged_env
            )
            transport_ctx = stdio_client(params)
        else:
            # HTTP server
            transport_ctx = streamablehttp_client(
                templated_config.url, headers=templated_config.headers or None
            )

        # Connect and call tool
        try:
            async with transport_ctx as context_result:
                read, write = context_result[0], context_result[1]

                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Extract properties for tool arguments
                    tool_args = context.get("props", {})

                    # Call the tool
                    result = await session.call_tool(config.toolName, arguments=tool_args)

                    # Convert MCP result to MCI ExecutionResult format
                    content_objects = []
                    for content_item in result.content:
                        if content_item.type == "text":
                            content_objects.append(TextContent(text=content_item.text))
                        elif content_item.type == "image":
                            from ..models import ImageContent

                            content_objects.append(
                                ImageContent(data=content_item.data, mimeType=content_item.mimeType)
                            )
                        elif content_item.type == "audio":
                            from ..models import AudioContent

                            content_objects.append(
                                AudioContent(data=content_item.data, mimeType=content_item.mimeType)
                            )
                        else:
                            # Default to text if type is unknown
                            content_objects.append(TextContent(text=str(content_item)))

                    # Extract jsonrpc and id if present
                    jsonrpc_value = getattr(result, "jsonrpc", None)
                    id_value = getattr(result, "id", None)

                    return ExecutionResult(
                        result=ExecutionResultContent(
                            content=content_objects,
                            isError=getattr(result, "isError", False),
                            metadata={"mcp_server": config.serverName, "mcp_tool": config.toolName},
                        ),
                        jsonrpc=jsonrpc_value,
                        id=id_value,
                    )

        except Exception as e:
            raise MCPExecutorError(f"Failed to execute MCP tool '{config.toolName}': {e}") from e
