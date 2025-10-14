"""
MCI Client - Main API for MCI adapter.

This module provides the MCIClient class, the main entry point for
programmatic use of MCI tool contexts. It handles loading tool schemas,
managing environment variables, filtering tools, and executing tools.
"""

from typing import Any

from .models import ExecutionResult, Tool
from .parser import SchemaParser
from .tool_manager import ToolManager, ToolManagerError


class MCIClientError(Exception):
    """Exception raised for MCI client errors."""

    pass


class MCIClient:
    """
    Main client for MCI adapter.

    Provides the primary API for loading, filtering, and executing MCI tools.
    Handles schema parsing, environment variable management, and tool execution
    orchestration through the ToolManager.

    Example:
        ```python
        from mcipy import MCIClient

        client = MCIClient(
            json_file_path="example.mci.json",
            env_vars={"API_KEY": "your-secret-key"}
        )

        # List all tools
        tool_names = client.list_tools()

        # Filter tools
        weather_tools = client.only(["get_weather", "get_forecast"])
        safe_tools = client.without(["delete_data", "admin_tools"])

        # Execute a tool
        result = client.execute(
            tool_name="get_weather",
            properties={"location": "New York"}
        )
        ```
    """

    def __init__(self, json_file_path: str, env_vars: dict[str, Any] | None = None):
        """
        Initialize the MCI client with a schema file and environment variables.

        Loads the MCI JSON schema, stores environment variables for templating,
        and initializes the ToolManager for tool execution.

        Args:
            json_file_path: Path to the MCI JSON schema file
            env_vars: Environment variables for template substitution (default: empty dict)

        Raises:
            MCIClientError: If the schema file cannot be loaded or parsed
        """
        # Load schema using SchemaParser
        try:
            self._schema = SchemaParser.parse_file(json_file_path)
        except Exception as e:
            raise MCIClientError(f"Failed to load schema from {json_file_path}: {e}") from e

        # Store environment variables
        self._env_vars = env_vars if env_vars is not None else {}

        # Initialize ToolManager
        self._tool_manager = ToolManager(self._schema)

    def tools(self) -> list[Tool]:
        """
        Get all available tools.

        Returns:
            List of all Tool objects in the schema
        """
        return self._tool_manager.list_tools()

    def only(self, tool_names: list[str]) -> list[Tool]:
        """
        Filter to include only specified tools.

        Returns only the tools whose names are in the provided list.
        Tools not in the list are excluded.

        Args:
            tool_names: List of tool names to include

        Returns:
            Filtered list of Tool objects
        """
        return self._tool_manager.filter_tools(only=tool_names)

    def without(self, tool_names: list[str]) -> list[Tool]:
        """
        Filter to exclude specified tools.

        Returns all tools except those whose names are in the provided list.

        Args:
            tool_names: List of tool names to exclude

        Returns:
            Filtered list of Tool objects
        """
        return self._tool_manager.filter_tools(without=tool_names)

    def execute(self, tool_name: str, properties: dict[str, Any] | None = None) -> ExecutionResult:
        """
        Execute a tool by name with the provided properties.

        Validates that the tool exists, builds the execution context from
        properties and environment variables, and executes the tool using
        the appropriate executor.

        Args:
            tool_name: Name of the tool to execute
            properties: Properties/parameters to pass to the tool (default: empty dict)

        Returns:
            ExecutionResult with success/error status and content

        Raises:
            MCIClientError: If tool not found or execution fails with validation error
        """
        try:
            return self._tool_manager.execute(
                tool_name=tool_name,
                properties=properties,
                env_vars=self._env_vars,
            )
        except ToolManagerError as e:
            # Convert ToolManagerError to MCIClientError for consistent API
            raise MCIClientError(str(e)) from e

    def list_tools(self) -> list[str]:
        """
        List available tool names.

        Returns:
            List of tool names (strings)
        """
        return [tool.name for tool in self._tool_manager.list_tools()]

    def get_tool_schema(self, tool_name: str) -> dict[str, Any]:
        """
        Get a tool's input schema.

        Returns the JSON schema that defines the expected input properties
        for the specified tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool's input schema as a dictionary (or empty dict if no schema)

        Raises:
            MCIClientError: If tool not found
        """
        tool = self._tool_manager.get_tool(tool_name)
        if tool is None:
            raise MCIClientError(f"Tool not found: {tool_name}")

        # Return the input schema, or empty dict if None
        return tool.inputSchema if tool.inputSchema is not None else {}
