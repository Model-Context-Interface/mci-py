"""
Tool manager for MCI tools.

This module provides the ToolManager class that manages tool definitions
from an MCISchema, including retrieval, filtering, and execution.
"""

from pathlib import Path
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

    def __init__(self, schema: MCISchema, schema_file_path: str | None = None):
        """
        Initialize the ToolManager with an MCISchema.

        Args:
            schema: MCISchema containing tool definitions
            schema_file_path: Path to the schema file (for path validation context)
        """
        self.schema = schema
        # Create a mapping for fast tool lookup by name (excluding disabled tools)
        # Handle case where tools might be None (when only toolsets are used)
        tools_list = schema.tools if schema.tools is not None else []
        self._tool_map: dict[str, Tool] = {
            tool.name: tool for tool in tools_list if not tool.disabled
        }
        # Store schema file path for path validation
        self._schema_file_path = schema_file_path

    def get_tool(self, name: str) -> Tool | None:
        """
        Retrieve a tool by name (case-sensitive), excluding disabled tools.

        Args:
            name: Name of the tool to retrieve

        Returns:
            Tool object if found and enabled, None otherwise
        """
        return self._tool_map.get(name)

    def list_tools(self) -> list[Tool]:
        """
        List all available tools (excluding disabled tools).

        Returns:
            List of all enabled Tool objects in the schema
        """
        tools_list = self.schema.tools if self.schema.tools is not None else []
        return [tool for tool in tools_list if not tool.disabled]

    def filter_tools(
        self, only: list[str] | None = None, without: list[str] | None = None
    ) -> list[Tool]:
        """
        Filter tools by inclusion/exclusion lists (excluding disabled tools).

        If both 'only' and 'without' are provided, 'only' takes precedence
        (i.e., only tools in the 'only' list but not in 'without' are returned).
        Disabled tools are always excluded regardless of filters.

        Args:
            only: List of tool names to include (if None, all enabled tools are considered)
            without: List of tool names to exclude (if None, no tools are excluded)

        Returns:
            Filtered list of Tool objects
        """
        # Start with only enabled tools
        tools_list = self.schema.tools if self.schema.tools is not None else []
        tools = [tool for tool in tools_list if not tool.disabled]

        # If 'only' is specified, filter to only those tools
        if only is not None:
            only_set = set(only)
            tools = [tool for tool in tools if tool.name in only_set]

        # If 'without' is specified, exclude those tools
        if without is not None:
            without_set = set(without)
            tools = [tool for tool in tools if tool.name not in without_set]

        return tools

    def tags(self, tags: list[str]) -> list[Tool]:
        """
        Filter tools to include only those with at least one matching tag (excluding disabled tools).

        Returns tools that have at least one tag matching any tag in the provided list.
        Uses OR logic: a tool is included if it has any of the specified tags.
        Tags are matched case-sensitively and exactly as provided.

        Args:
            tags: List of tags to filter by

        Returns:
            Filtered list of Tool objects that have at least one matching tag
        """
        # Start with only enabled tools
        tools_list = self.schema.tools if self.schema.tools is not None else []
        tools = [tool for tool in tools_list if not tool.disabled]

        # Filter to tools that have at least one matching tag
        # Empty tag list should return no tools
        if not tags:
            return []

        tags_set = set(tags)
        tools = [tool for tool in tools if any(tag in tags_set for tag in tool.tags)]

        return tools

    def withoutTags(self, tags: list[str]) -> list[Tool]:
        """
        Filter tools to exclude those with any matching tag (excluding disabled tools).

        Returns tools that do NOT have any tags matching the provided list.
        Uses OR logic for exclusion: a tool is excluded if it has any of the specified tags.
        Tags are matched case-sensitively and exactly as provided.

        Args:
            tags: List of tags to exclude

        Returns:
            Filtered list of Tool objects that do not have any of the specified tags
        """
        # Start with only enabled tools
        tools_list = self.schema.tools if self.schema.tools is not None else []
        tools = [tool for tool in tools_list if not tool.disabled]

        # Filter to tools that don't have any matching tags
        # Empty tag list should return all tools
        if not tags:
            return tools

        tags_set = set(tags)
        tools = [tool for tool in tools if not any(tag in tags_set for tag in tool.tags)]

        return tools

    def toolsets(self, toolset_names: list[str]) -> list[Tool]:
        """
        Filter tools to include only those from specified toolsets (excluding disabled tools).

        Returns tools that were loaded from any of the specified toolsets.
        Uses OR logic: a tool is included if it came from any of the specified toolsets.
        Only tools that were registered by their toolset's schema-level filter are included.

        Args:
            toolset_names: List of toolset names to filter by

        Returns:
            Filtered list of Tool objects from the specified toolsets
        """
        # Start with only enabled tools
        tools_list = self.schema.tools if self.schema.tools is not None else []
        tools = [tool for tool in tools_list if not tool.disabled]

        # Filter to tools from specified toolsets
        # Empty toolset list should return no tools
        if not toolset_names:
            return []

        toolset_set = set(toolset_names)
        tools = [
            tool
            for tool in tools
            if tool.toolset_source is not None and tool.toolset_source in toolset_set
        ]

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
            # Resolve properties with defaults applied and optional properties skipped
            resolved_properties = self._resolve_properties_with_defaults(tool, properties)
        else:
            # No schema, use properties as-is
            resolved_properties = properties

        # Build context for execution
        context: dict[str, Any] = {
            "props": resolved_properties,
            "env": env_vars,
            "input": resolved_properties,  # Alias for backward compatibility
        }

        # Build path validation context
        path_context: dict[str, Any] | None = None
        if self._schema_file_path:
            from .path_validator import PathValidator

            # Get context directory from schema file path
            context_dir = Path(self._schema_file_path).parent

            # Merge schema and tool settings (tool takes precedence)
            enable_any_paths, directory_allow_list = PathValidator.merge_settings(
                schema_enable_any_paths=self.schema.enableAnyPaths,
                schema_directory_allow_list=self.schema.directoryAllowList,
                tool_enable_any_paths=tool.enableAnyPaths,
                tool_directory_allow_list=tool.directoryAllowList,
            )

            # Create path validator
            path_context = {
                "validator": PathValidator(
                    context_dir=context_dir,
                    enable_any_paths=enable_any_paths,
                    directory_allow_list=directory_allow_list,
                )
            }

        # Add path context to execution context
        context["path_validation"] = path_context

        # Get the appropriate executor based on execution type
        executor = ExecutorFactory.get_executor(
            tool.execution.type, mcp_servers=self.schema.mcp_servers
        )

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

    def _resolve_properties_with_defaults(
        self, tool: Tool, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Resolve properties with default values and skip optional properties.

        For each property in the input schema:
        - If provided in properties: use the provided value
        - Else if has default value in schema: use the default
        - Else if required: already validated, should not happen
        - Else (optional without default): skip, don't include in resolved properties

        This prevents template substitution errors for optional properties that
        are not provided and have no default value.

        Args:
            tool: Tool object with inputSchema
            properties: Properties provided by the caller

        Returns:
            Resolved properties dictionary with defaults applied and optional properties skipped
        """
        input_schema = tool.inputSchema
        if not input_schema:
            return properties

        # Get schema properties definition
        schema_properties = input_schema.get("properties", {})
        if not schema_properties:
            # No properties defined in schema, return as-is
            return properties

        # Get required properties list
        required = set(input_schema.get("required", []))

        # Build resolved properties
        resolved: dict[str, Any] = {}

        # Process each property in the schema
        for prop_name, prop_schema in schema_properties.items():
            if prop_name in properties:
                # Property was provided, use it
                resolved[prop_name] = properties[prop_name]
            elif "default" in prop_schema:
                # Property not provided but has default, use default
                resolved[prop_name] = prop_schema["default"]
            elif prop_name in required:
                # Required property not provided - this should have been caught by validation
                # but we'll include it anyway to maintain consistency
                # (validation should have raised an error before we get here)
                pass
            # else: optional property without default - skip it

        return resolved
