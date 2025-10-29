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

        # Load from JSON file
        client = MCIClient(
            schema_file_path="example.mci.json",
            env_vars={"API_KEY": "your-secret-key"}
        )

        # Or load from YAML file
        client = MCIClient(
            schema_file_path="example.mci.yaml",
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

    def __init__(
        self,
        schema_file_path: str | None = None,
        env_vars: dict[str, Any] | None = None,
        json_file_path: str | None = None,
        validating: bool = False,
    ):
        """
        Initialize the MCI client with a schema file and environment variables.

        Loads the MCI schema (JSON or YAML), stores environment variables for templating,
        and initializes the ToolManager for tool execution.

        Args:
            schema_file_path: Path to the MCI schema file (.json, .yaml, or .yml)
            env_vars: Environment variables for template substitution (default: empty dict)
            json_file_path: DEPRECATED. Use schema_file_path instead. Kept for backward compatibility.
            validating: If True, perform pure schema validation without loading MCP servers,
                       toolsets, or resolving templates. No network/file actions are performed.
                       Tool execution is disabled in this mode. (default: False)

        Raises:
            MCIClientError: If the schema file cannot be loaded or parsed
        """
        # Handle backward compatibility: json_file_path is deprecated in favor of schema_file_path
        if json_file_path is not None and schema_file_path is None:
            schema_file_path = json_file_path
        elif schema_file_path is None:
            raise MCIClientError("Either 'schema_file_path' or 'json_file_path' must be provided")

        # Store schema file path for path validation
        self._schema_file_path = schema_file_path

        # Store validating mode flag
        self._validating = validating

        # Store environment variables first (needed for schema parsing)
        self._env_vars = env_vars if env_vars is not None else {}

        # Load schema using SchemaParser with env_vars for MCP server templating
        try:
            self._schema = SchemaParser.parse_file(
                schema_file_path, env_vars=self._env_vars, validating=validating
            )
        except Exception as e:
            raise MCIClientError(f"Failed to load schema from {schema_file_path}: {e}") from e

        # Initialize ToolManager with schema file path for path validation
        self._tool_manager = ToolManager(self._schema, schema_file_path)

    def tools(self) -> list[Tool]:
        """
        Get all available tools (excluding disabled tools).

        Returns:
            List of all enabled Tool objects in the schema
        """
        return self._tool_manager.list_tools()

    def only(self, tool_names: list[str]) -> list[Tool]:
        """
        Filter to include only specified tools (excluding disabled tools).

        Returns only the tools whose names are in the provided list and
        are not disabled. Tools not in the list or that are disabled are excluded.

        Args:
            tool_names: List of tool names to include

        Returns:
            Filtered list of enabled Tool objects
        """
        return self._tool_manager.filter_tools(only=tool_names)

    def without(self, tool_names: list[str]) -> list[Tool]:
        """
        Filter to exclude specified tools (disabled tools are also excluded).

        Returns all enabled tools except those whose names are in the provided list.

        Args:
            tool_names: List of tool names to exclude

        Returns:
            Filtered list of enabled Tool objects
        """
        return self._tool_manager.filter_tools(without=tool_names)

    def tags(self, tags: list[str]) -> list[Tool]:
        """
        Filter tools to include only those with at least one matching tag (excluding disabled tools).

        Returns tools that have at least one tag matching any tag in the provided list.
        Uses OR logic: a tool is included if it has any of the specified tags.
        Tags are matched case-sensitively and exactly as provided.

        Args:
            tags: List of tags to filter by

        Returns:
            Filtered list of enabled Tool objects that have at least one matching tag
        """
        return self._tool_manager.tags(tags)

    def withoutTags(self, tags: list[str]) -> list[Tool]:
        """
        Filter tools to exclude those with any matching tag (excluding disabled tools).

        Returns tools that do NOT have any tags matching the provided list.
        Uses OR logic for exclusion: a tool is excluded if it has any of the specified tags.
        Tags are matched case-sensitively and exactly as provided.

        Args:
            tags: List of tags to exclude

        Returns:
            Filtered list of enabled Tool objects that do not have any of the specified tags
        """
        return self._tool_manager.withoutTags(tags)

    def toolsets(self, toolset_names: list[str]) -> list[Tool]:
        """
        Filter tools to include only those from specified toolsets (excluding disabled tools).

        Returns tools that were loaded from any of the specified toolsets.
        Uses OR logic: a tool is included if it came from any of the specified toolsets.
        Only tools that were registered by their toolset's schema-level filter are included.

        Args:
            toolset_names: List of toolset names to filter by

        Returns:
            Filtered list of enabled Tool objects from the specified toolsets
        """
        return self._tool_manager.toolsets(toolset_names)

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
            MCIClientError: If tool not found or execution fails with validation error,
                          or if called in validating mode
        """
        # Prevent execution in validating mode
        if self._validating:
            raise MCIClientError(
                "Tool execution is disabled in validating mode. "
                "Initialize MCIClient with validating=False to execute tools."
            )

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
        List available tool names (excluding disabled tools).

        Returns:
            List of enabled tool names (strings)
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
