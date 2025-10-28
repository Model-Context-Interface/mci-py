"""
MCP Integration - Handles fetching and building toolsets from MCP servers.

This module provides the MCPIntegration class for interacting with MCP servers,
fetching their tool definitions, and building MCI-compatible toolset schemas.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from .enums import ExecutionType
from .models import (
    Annotations,
    HttpMCPServer,
    MCPExecutionConfig,
    Metadata,
    StdioMCPServer,
    Tool,
    ToolsetSchema,
)
from .templating import TemplateEngine


class MCPIntegrationError(Exception):
    """Exception raised for MCP integration errors."""

    pass


class MCPIntegration:
    """
    Handles MCP server integration and toolset generation.

    Provides methods to fetch tools from MCP servers (STDIO and HTTP),
    build MCI-compatible toolsets, and manage toolset metadata.
    """

    @staticmethod
    def fetch_and_build_toolset(
        server_name: str,
        server_config: StdioMCPServer | HttpMCPServer,
        schema_version: str,
        env_context: dict[str, Any],
        template_engine: TemplateEngine,
    ) -> ToolsetSchema:
        """
        Fetch tools from an MCP server and build a toolset schema.

        Args:
            server_name: Name of the MCP server
            server_config: MCP server configuration (STDIO or HTTP)
            schema_version: Schema version to use for the toolset
            env_context: Environment context for templating
            template_engine: Template engine for processing placeholders

        Returns:
            ToolsetSchema with tools from the MCP server and expiration date

        Raises:
            MCPIntegrationError: If MCP server connection or tool fetching fails
        """
        # Run async operation in sync context
        try:
            return asyncio.run(
                MCPIntegration._async_fetch_and_build_toolset(
                    server_name, server_config, schema_version, env_context, template_engine
                )
            )
        except Exception as e:
            raise MCPIntegrationError(
                f"Failed to fetch from MCP server '{server_name}': {e}"
            ) from e

    @staticmethod
    async def _async_fetch_and_build_toolset(
        server_name: str,
        server_config: StdioMCPServer | HttpMCPServer,
        schema_version: str,
        env_context: dict[str, Any],
        template_engine: TemplateEngine,
    ) -> ToolsetSchema:
        """
        Async implementation of fetch_and_build_toolset.

        Connects to MCP server, fetches tools, and builds toolset schema.
        """
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp.client.streamable_http import streamablehttp_client

        # Apply templating to server config
        templated_config = MCPIntegration._apply_templating_to_config(
            server_config, env_context, template_engine
        )

        # Connect to MCP server based on type
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

        # Connect and fetch tools
        try:
            async with transport_ctx as context_result:
                read, write = context_result[0], context_result[1]

                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # List tools
                    tools_response = await session.list_tools()

                    # Build MCI tools from MCP tools
                    mci_tools = []
                    for mcp_tool in tools_response.tools:
                        # Convert MCP tool to MCI tool format
                        input_schema = None
                        if mcp_tool.inputSchema:
                            # Convert to dict - inputSchema is already a dict
                            input_schema = mcp_tool.inputSchema

                        mci_tool = Tool(
                            name=mcp_tool.name,
                            description=mcp_tool.description or "",
                            annotations=Annotations(),
                            inputSchema=input_schema,
                            execution=MCPExecutionConfig(
                                type=ExecutionType.MCP,
                                serverName=server_name,
                                toolName=mcp_tool.name,
                            ),
                        )
                        mci_tools.append(mci_tool)

                    # Calculate expiration date (date only, not datetime)
                    exp_days = templated_config.config.expDays
                    expires_date = (datetime.now(UTC) + timedelta(days=exp_days)).date()

                    # Build toolset schema with proper metadata
                    metadata = Metadata(name=server_name, description=f"MCP server: {server_name}")

                    toolset = ToolsetSchema(
                        schemaVersion=schema_version,
                        metadata=metadata,
                        tools=mci_tools,
                        expiresAt=expires_date.isoformat(),  # YYYY-MM-DD format
                    )

                    return toolset

        except Exception as e:
            raise MCPIntegrationError(
                f"Failed to connect to MCP server '{server_name}': {e}"
            ) from e

    @staticmethod
    def _apply_templating_to_config(
        server_config: StdioMCPServer | HttpMCPServer,
        env_context: dict[str, Any],
        template_engine: TemplateEngine,
    ) -> StdioMCPServer | HttpMCPServer:
        """
        Apply templating to MCP server configuration.

        Processes environment variable placeholders in server config fields.

        Args:
            server_config: MCP server configuration
            env_context: Environment context for templating
            template_engine: Template engine for processing placeholders

        Returns:
            Server configuration with templated values
        """
        if isinstance(server_config, StdioMCPServer):
            # Template command and args
            templated_command = template_engine.render_basic(server_config.command, env_context)
            templated_args = [
                template_engine.render_basic(arg, env_context) for arg in server_config.args
            ]

            # Template env vars
            templated_env = {
                key: template_engine.render_basic(value, env_context)
                for key, value in server_config.env.items()
            }

            return StdioMCPServer(
                command=templated_command,
                args=templated_args,
                env=templated_env,
                config=server_config.config,
            )
        else:
            # HTTP server
            templated_url = template_engine.render_basic(server_config.url, env_context)
            templated_headers = {
                key: template_engine.render_basic(value, env_context)
                for key, value in server_config.headers.items()
            }

            return HttpMCPServer(
                url=templated_url, headers=templated_headers, config=server_config.config
            )
