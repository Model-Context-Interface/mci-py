"""
MCP Integration - Handles fetching and building toolsets from MCP servers.

This module provides the MCPIntegration class for interacting with MCP servers,
fetching their tool definitions, and building MCI-compatible toolset schemas.
"""

import asyncio
import concurrent.futures
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
    def _annotations_to_tags(mcp_annotations: Any) -> list[str]:
        """
        Convert MCP tool annotations to MCI tags.

        Converts boolean annotation hints (readOnlyHint, destructiveHint, etc.) to
        standardized tags. Also handles audience annotations if present.

        Args:
            mcp_annotations: MCP ToolAnnotations object

        Returns:
            List of tags derived from annotations
        """
        tags: list[str] = []

        if not mcp_annotations:
            return tags

        # Convert boolean annotations to tags
        # Use the exact names from the issue: IsReadOnly, IsDestructive, IsIdempotent, IsOpenWorld
        if mcp_annotations.readOnlyHint:
            tags.append("IsReadOnly")
        if mcp_annotations.destructiveHint:
            tags.append("IsDestructive")
        if mcp_annotations.idempotentHint:
            tags.append("IsIdempotent")
        if mcp_annotations.openWorldHint:
            tags.append("IsOpenWorld")

        # Handle audience annotations if present (for future compatibility)
        # MCP ToolAnnotations doesn't currently have an audience field,
        # but we check for it dynamically in case it's added
        if hasattr(mcp_annotations, "audience") and mcp_annotations.audience:
            for role in mcp_annotations.audience:
                tags.append(f"audience_{role}")

        return tags

    @staticmethod
    async def fetch_and_build_toolset_async(
        server_name: str,
        server_config: StdioMCPServer | HttpMCPServer,
        schema_version: str,
        env_context: dict[str, Any],
        template_engine: TemplateEngine,
    ) -> ToolsetSchema:
        return await MCPIntegration._async_fetch_and_build_toolset(
            server_name, server_config, schema_version, env_context, template_engine
        )

    @staticmethod
    def fetch_and_build_toolset(
        server_name: str,
        server_config: StdioMCPServer | HttpMCPServer,
        schema_version: str,
        env_context: dict[str, Any],
        template_engine: TemplateEngine,
    ) -> ToolsetSchema:
        """
        Sync convenience for callers.

        - If NO event loop is running, use asyncio.run(...) in this thread.
        - If a loop IS running (e.g., inside an async CLI), offload the async
          work to a separate thread that owns its own loop, and block until it finishes.
        """

        async def _coro():
            return await MCPIntegration.fetch_and_build_toolset_async(
                server_name, server_config, schema_version, env_context, template_engine
            )

        try:
            # detect running loop
            try:
                asyncio.get_running_loop()
                loop_running = True
            except RuntimeError:
                loop_running = False

            if not loop_running:
                return asyncio.run(_coro())

            # Run in separate thread if a loop is active
            def _run_in_thread():
                return asyncio.run(_coro())

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(_run_in_thread).result()

        except Exception as e:
            # <-- place your error handler HERE
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

                        # Capture annotations from MCP tool
                        annotations = Annotations()
                        if mcp_tool.annotations:
                            # Copy annotation fields from MCP to MCI
                            annotations.title = mcp_tool.annotations.title
                            annotations.readOnlyHint = mcp_tool.annotations.readOnlyHint
                            annotations.destructiveHint = mcp_tool.annotations.destructiveHint
                            annotations.idempotentHint = mcp_tool.annotations.idempotentHint
                            annotations.openWorldHint = mcp_tool.annotations.openWorldHint

                            # Check for audience field (for future compatibility)
                            # MCP ToolAnnotations doesn't currently have this field,
                            # but we check dynamically in case it's added
                            if hasattr(mcp_tool.annotations, "audience"):
                                audience_value = getattr(mcp_tool.annotations, "audience", None)
                                if audience_value:
                                    annotations.audience = audience_value

                        # Convert annotations to tags
                        tags = MCPIntegration._annotations_to_tags(mcp_tool.annotations)

                        mci_tool = Tool(
                            name=mcp_tool.name,
                            description=mcp_tool.description or "",
                            annotations=annotations,
                            inputSchema=input_schema,
                            tags=tags,
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
