"""
Execution handlers for MCI tools.

This module provides the executor classes that handle different types of
tool execution (HTTP, CLI, file, text, MCP). Each executor inherits from BaseExecutor
and implements the execute() method according to its execution type.

The ExecutorFactory provides centralized instantiation of executors based on
execution type, with singleton caching for performance.
"""

from typing import Any

from ..enums import ExecutionType
from .base import BaseExecutor
from .cli_executor import CLIExecutor
from .file_executor import FileExecutor
from .http_executor import HTTPExecutor
from .mcp_executor import MCPExecutor
from .text_executor import TextExecutor


class ExecutorFactory:
    """
    Factory for creating and caching executor instances.

    Provides centralized instantiation of executors based on execution type.
    Uses singleton pattern to cache executor instances for better performance.
    MCP executors are not cached as they require server configuration.
    """

    _executors: dict[ExecutionType, BaseExecutor] = {}

    @classmethod
    def get_executor(
        cls, execution_type: ExecutionType, mcp_servers: dict[str, Any] | None = None
    ) -> BaseExecutor:
        """
        Get an executor instance for the given execution type.

        Returns a cached executor instance if available (except for MCP),
        otherwise creates a new one and caches it for future use.

        Args:
            execution_type: The type of execution (HTTP, CLI, FILE, TEXT, MCP)
            mcp_servers: Dictionary of MCP server configurations (required for MCP executor)

        Returns:
            BaseExecutor instance for the specified type

        Raises:
            ValueError: If the execution type is not supported
        """
        # MCP executors are not cached as they require server configuration
        if execution_type == ExecutionType.MCP:
            return MCPExecutor(mcp_servers=mcp_servers)

        # Return cached executor if available
        if execution_type in cls._executors:
            return cls._executors[execution_type]

        # Create new executor based on type
        if execution_type == ExecutionType.HTTP:
            executor = HTTPExecutor()
        elif execution_type == ExecutionType.CLI:
            executor = CLIExecutor()
        elif execution_type == ExecutionType.FILE:
            executor = FileExecutor()
        elif execution_type == ExecutionType.TEXT:
            executor = TextExecutor()
        else:
            raise ValueError(f"Unsupported execution type: {execution_type}")

        # Cache and return
        cls._executors[execution_type] = executor
        return executor

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the executor cache.

        Useful for testing or when you want to ensure fresh executor instances.
        """
        cls._executors.clear()


__all__ = [
    "BaseExecutor",
    "CLIExecutor",
    "ExecutorFactory",
    "FileExecutor",
    "HTTPExecutor",
    "MCPExecutor",
    "TextExecutor",
]
