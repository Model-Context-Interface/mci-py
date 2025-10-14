"""
Tool manager for MCI tools.

This module provides the ToolManager class that manages tool definitions
from an MCISchema, including retrieval, filtering, and execution.
"""

from typing import Any

from .executors import ExecutorFactory
from .models import ExecutionResult, MCISchema, Tool


class ToolManagerError(Exception):
    """Exception raised for tool manager errors."""

    pass


class ToolManager:
    """
    Manager for MCI tool definitions.

    Provides functionality to retrieve, filter, and execute tools from an
    MCISchema. Handles input validation and dispatches execution to the
    appropriate executor based on tool configuration.
    """

    def __init__(self, schema: MCISchema):
        """
        Initialize the ToolManager with an MCISchema.

        Args:
            schema: MCISchema containing tool definitions
        """
        self.schema = schema
        # Create a mapping for fast tool lookup by name
        self._tool_map: dict[str, Tool] = {tool.name: tool for tool in schema.tools}

    def get_tool(self, name: str) -> Tool | None:
        """
        Retrieve a tool by name (case-sensitive).

        Args:
            name: Name of the tool to retrieve

        Returns:
            Tool object if found, None otherwise
        """
        return self._tool_map.get(name)

    def list_tools(self) -> list[Tool]:
        """
        List all available tools.

        Returns:
            List of all Tool objects in the schema
        """
        return self.schema.tools

    def filter_tools(
        self, only: list[str] | None = None, without: list[str] | None = None
    ) -> list[Tool]:
        """
        Filter tools by inclusion/exclusion lists.

        If both 'only' and 'without' are provided, 'only' takes precedence
        (i.e., only tools in the 'only' list but not in 'without' are returned).

        Args:
            only: List of tool names to include (if None, all tools are considered)
            without: List of tool names to exclude (if None, no tools are excluded)

        Returns:
            Filtered list of Tool objects
        """
        tools = self.schema.tools

        # If 'only' is specified, filter to only those tools
        if only is not None:
            only_set = set(only)
            tools = [tool for tool in tools if tool.name in only_set]

        # If 'without' is specified, exclude those tools
        if without is not None:
            without_set = set(without)
            tools = [tool for tool in tools if tool.name not in without_set]

        return tools

    def execute(
        self,
        tool_name: str,
        properties: dict[str, Any] | None = None,
        env_vars: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        Execute a tool by name with the provided properties.

        Validates the tool exists, validates input properties against the tool's
        input schema, and executes the tool using the appropriate executor.

        Args:
            tool_name: Name of the tool to execute
            properties: Properties/parameters to pass to the tool (default: empty dict)
            env_vars: Environment variables for template context (default: empty dict)

        Returns:
            ExecutionResult with success/error status and content

        Raises:
            ToolManagerError: If tool not found or properties validation fails
        """
        # Default to empty dicts if None
        if properties is None:
            properties = {}
        if env_vars is None:
            env_vars = {}

        # Check if tool exists
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ToolManagerError(f"Tool not found: {tool_name}")

        # Validate input schema if present
        # Check both: not None (schema exists) and not empty dict (schema has content)
        # This handles three cases: None (no schema), {} (empty schema), and {...} (schema with properties)
        if tool.inputSchema is not None and tool.inputSchema:
            self._validate_input_properties(tool, properties)

        # Build context for execution
        context = {
            "props": properties,
            "env": env_vars,
            "input": properties,  # Alias for backward compatibility
        }

        # Get the appropriate executor based on execution type
        executor = ExecutorFactory.get_executor(tool.execution.type)

        # Execute the tool
        result = executor.execute(tool.execution, context)

        return result

    def _validate_input_properties(self, tool: Tool, properties: dict[str, Any]) -> None:
        """
        Validate properties against the tool's input schema.

        Checks that all required properties are provided.

        Args:
            tool: Tool object with inputSchema
            properties: Properties to validate

        Raises:
            ToolManagerError: If required properties are missing
        """
        input_schema = tool.inputSchema
        if not input_schema:
            return

        # Check for required properties
        required = input_schema.get("required", [])
        if required:
            missing_props = [prop for prop in required if prop not in properties]
            if missing_props:
                raise ToolManagerError(
                    f"Tool '{tool.name}' requires properties: {', '.join(required)}. "
                    f"Missing: {', '.join(missing_props)}"
                )
