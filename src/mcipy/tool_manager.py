"""
Tool manager for MCI tools.

This module provides the ToolManager class that manages tool definitions
from an MCISchema, including retrieval, filtering, execution, and loading
tools from toolsets.
"""

from pathlib import Path
from typing import Any

from .executors import ExecutorFactory
from .models import ExecutionResult, MCISchema, Tool, Toolset
from .parser import SchemaParser


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

        Loads tools from the schema and any defined toolsets, applying
        schema-level filters to toolset tools during loading.

        Args:
            schema: MCISchema containing tool definitions
            schema_file_path: Path to the schema file (for path validation context and toolset loading)
        """
        self.schema = schema
        self._schema_file_path = schema_file_path

        # Start with tools from main schema (or empty list if None)
        all_tools: list[Tool] = list(schema.tools) if schema.tools else []

        # Track which toolset each tool came from
        self._tool_to_toolset: dict[str, str] = {}

        # Load tools from toolsets if defined
        if schema.toolsets and schema_file_path:
            schema_dir = Path(schema_file_path).parent
            library_dir = schema_dir / schema.libraryDir

            for toolset in schema.toolsets:
                toolset_tools = self._load_toolset(toolset, library_dir)
                # Track toolset origin for each tool
                for tool in toolset_tools:
                    self._tool_to_toolset[tool.name] = toolset.name
                all_tools.extend(toolset_tools)

        # Create a mapping for fast tool lookup by name (excluding disabled tools)
        self._tool_map: dict[str, Tool] = {
            tool.name: tool for tool in all_tools if not tool.disabled
        }
        # Store all tools (including disabled) for complete listing
        self._all_tools = all_tools

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
        return [tool for tool in self._all_tools if not tool.disabled]

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
        tools = [tool for tool in self._all_tools if not tool.disabled]

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
        tools = [tool for tool in self._all_tools if not tool.disabled]

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
        tools = [tool for tool in self._all_tools if not tool.disabled]

        # Filter to tools that don't have any matching tags
        # Empty tag list should return all tools
        if not tags:
            return tools

        tags_set = set(tags)
        tools = [tool for tool in tools if not any(tag in tags_set for tag in tool.tags)]

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
        context: dict[str, Any] = {
            "props": properties,
            "env": env_vars,
            "input": properties,  # Alias for backward compatibility
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

    def toolsets(self, toolset_names: list[str]) -> list[Tool]:
        """
        Filter tools to include only those from specified toolsets (excluding disabled tools).

        Returns tools that were loaded from any of the specified toolsets.
        Only tools that were registered by a toolset (via its filter) are included.

        Args:
            toolset_names: List of toolset names to filter by

        Returns:
            Filtered list of Tool objects from the specified toolsets
        """
        if not toolset_names:
            return []

        toolset_names_set = set(toolset_names)
        tools = [
            tool
            for tool in self._all_tools
            if not tool.disabled and self._tool_to_toolset.get(tool.name) in toolset_names_set
        ]

        return tools

    def _load_toolset(self, toolset: Toolset, library_dir: Path) -> list[Tool]:
        """
        Load tools from a toolset definition.

        Resolves the toolset name to a file path, loads the toolset file,
        and applies any schema-level filters defined in the toolset.

        Args:
            toolset: Toolset definition
            library_dir: Directory where toolset files are located

        Returns:
            List of Tool objects from the toolset (after applying filters)

        Raises:
            ToolManagerError: If toolset file cannot be found or loaded
        """
        # Resolve toolset name to file path
        toolset_path = self._resolve_toolset_path(toolset.name, library_dir)

        if not toolset_path:
            raise ToolManagerError(
                f"Toolset '{toolset.name}' not found in library directory: {library_dir}"
            )

        # Load the toolset file
        try:
            toolset_file = SchemaParser.parse_toolset_file(str(toolset_path))
        except Exception as e:
            raise ToolManagerError(f"Failed to load toolset '{toolset.name}': {e}") from e

        # Apply schema-level filter if defined
        tools = toolset_file.tools
        if toolset.filter and toolset.filterValue:
            tools = self._apply_toolset_filter(tools, toolset.filter, toolset.filterValue)

        return tools

    def _resolve_toolset_path(self, name: str, library_dir: Path) -> Path | None:
        """
        Resolve a toolset name to a file path.

        Checks for:
        1. Directory with name (looks for .mci.json files inside)
        2. File with exact name
        3. File with .mci.json extension added

        Args:
            name: Toolset name (can be directory, file, or bare prefix)
            library_dir: Directory where toolset files are located

        Returns:
            Path to the toolset file, or None if not found
        """
        # Check if it's a directory
        dir_path = library_dir / name
        if dir_path.is_dir():
            # Look for any .mci.json file in the directory
            json_files = list(dir_path.glob("*.mci.json"))
            if json_files:
                return json_files[0]  # Return first match

        # Check if it's an exact file match
        file_path = library_dir / name
        if file_path.is_file():
            return file_path

        # Try adding .mci.json extension
        json_path = library_dir / f"{name}.mci.json"
        if json_path.is_file():
            return json_path

        # Try adding .mci.yaml extension
        yaml_path = library_dir / f"{name}.mci.yaml"
        if yaml_path.is_file():
            return yaml_path

        # Try adding .mci.yml extension
        yml_path = library_dir / f"{name}.mci.yml"
        if yml_path.is_file():
            return yml_path

        return None

    def _apply_toolset_filter(
        self, tools: list[Tool], filter_type: str, filter_value: str
    ) -> list[Tool]:
        """
        Apply a schema-level filter to toolset tools.

        Args:
            tools: List of tools to filter
            filter_type: Type of filter ("only", "except", "tags", "withoutTags")
            filter_value: Comma-separated list of tool names or tags

        Returns:
            Filtered list of tools

        Raises:
            ToolManagerError: If filter type is invalid
        """
        # Parse filter value (comma-separated list, trim spaces)
        values = [v.strip() for v in filter_value.split(",") if v.strip()]

        if filter_type == "only":
            values_set = set(values)
            return [tool for tool in tools if tool.name in values_set]

        elif filter_type == "except":
            values_set = set(values)
            return [tool for tool in tools if tool.name not in values_set]

        elif filter_type == "tags":
            if not values:
                return []
            values_set = set(values)
            return [tool for tool in tools if any(tag in values_set for tag in tool.tags)]

        elif filter_type == "withoutTags":
            if not values:
                return tools
            values_set = set(values)
            return [tool for tool in tools if not any(tag in values_set for tag in tool.tags)]

        else:
            raise ToolManagerError(
                f"Invalid filter type '{filter_type}'. Valid types: only, except, tags, withoutTags"
            )
