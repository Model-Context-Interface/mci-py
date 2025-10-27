"""
Schema parser for MCI JSON and YAML files.

This module provides the SchemaParser class for loading and validating
MCI schema files. It handles:
- Loading JSON and YAML files from disk
- Parsing dictionaries into MCISchema objects
- Validating schema versions
- Validating tool definitions
- Building appropriate execution configurations based on type
- Loading and filtering toolsets from library directories
"""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .enums import ExecutionType
from .models import (
    CLIExecutionConfig,
    ExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    MCISchema,
    TextExecutionConfig,
    Tool,
    ToolsetSchema,
)
from .schema_config import SUPPORTED_SCHEMA_VERSIONS


class SchemaParserError(Exception):
    """Exception raised for schema parsing errors."""

    pass


class SchemaParser:
    """
    Parser for MCI schema files.

    Loads and validates MCI JSON and YAML schema files, ensuring they conform to
    the expected structure and contain valid tool definitions. Uses Pydantic
    for strong validation and provides helpful error messages for invalid schemas.
    """

    @staticmethod
    def parse_file(file_path: str) -> MCISchema:
        """
        Load and validate an MCI schema file (JSON or YAML).

        Reads a JSON or YAML file from disk, validates its structure and content,
        and returns a parsed MCISchema object. The file type is determined by
        the file extension (.json, .yaml, or .yml).

        Args:
            file_path: Path to the MCI schema file (.json, .yaml, or .yml)

        Returns:
            Validated MCISchema object

        Raises:
            SchemaParserError: If the file doesn't exist, can't be read,
                             contains invalid JSON/YAML, has unsupported extension,
                             or fails validation
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            raise SchemaParserError(f"Schema file not found: {file_path}")

        if not path.is_file():
            raise SchemaParserError(f"Path is not a file: {file_path}")

        # Determine file type by extension
        file_extension = path.suffix.lower()

        # Read and parse file based on extension
        try:
            with path.open("r", encoding="utf-8") as f:
                if file_extension == ".json":
                    data = json.load(f)
                elif file_extension in (".yaml", ".yml"):
                    data = yaml.safe_load(f)
                else:
                    raise SchemaParserError(
                        f"Unsupported file extension '{file_extension}'. "
                        f"Supported extensions: .json, .yaml, .yml"
                    )
        except json.JSONDecodeError as e:
            raise SchemaParserError(f"Invalid JSON in file {file_path}: {e}") from e
        except yaml.YAMLError as e:
            raise SchemaParserError(f"Invalid YAML in file {file_path}: {e}") from e
        except OSError as e:
            raise SchemaParserError(f"Failed to read file {file_path}: {e}") from e

        # Parse the dictionary, passing the file path for toolset resolution
        return SchemaParser.parse_dict(data, schema_file_path=file_path)

    @staticmethod
    def parse_dict(data: dict[str, Any], schema_file_path: str | None = None) -> MCISchema:
        """
        Parse a dictionary into an MCISchema object.

        Validates the dictionary structure, schema version, and tool definitions,
        then returns a validated MCISchema object. If toolsets are defined,
        loads tools from toolset files and applies schema-level filtering.

        Args:
            data: Dictionary containing MCI schema data
            schema_file_path: Path to the schema file (for resolving relative paths in toolsets)

        Returns:
            Validated MCISchema object

        Raises:
            SchemaParserError: If the dictionary structure is invalid,
                             schema version is unsupported, or validation fails
        """
        if not isinstance(data, dict):
            raise SchemaParserError(f"Expected dictionary, got {type(data).__name__}")

        # Validate required fields exist
        if "schemaVersion" not in data:
            raise SchemaParserError("Missing required field 'schemaVersion'")

        # Either tools or toolsets must be provided (or both)
        has_tools = "tools" in data and data["tools"] is not None
        has_toolsets = "toolsets" in data and data["toolsets"] is not None

        if not has_tools and not has_toolsets:
            raise SchemaParserError("Either 'tools' or 'toolsets' field must be provided")

        # Validate schema version
        SchemaParser._validate_schema_version(data["schemaVersion"])

        # Validate tools if present
        if has_tools:
            if not isinstance(data["tools"], list):
                raise SchemaParserError(
                    f"Field 'tools' must be a list, got {type(data['tools']).__name__}"
                )
            SchemaParser._validate_tools(data["tools"])

        # Use Pydantic to validate and build the schema
        try:
            schema = MCISchema(**data)
        except ValidationError as e:
            raise SchemaParserError(f"Schema validation failed: {e}") from e

        # Load toolsets if present
        if schema.toolsets:
            toolset_tools = SchemaParser._load_toolsets(
                schema.toolsets, schema.libraryDir, schema_file_path
            )
            # Merge toolset tools with existing tools
            if schema.tools is None:
                schema.tools = toolset_tools
            else:
                schema.tools.extend(toolset_tools)

        return schema

    @staticmethod
    def _validate_schema_version(version: str) -> None:
        """
        Validate schema version compatibility.

        Ensures the schema version is supported by this parser implementation.

        Args:
            version: Schema version string

        Raises:
            SchemaParserError: If the version is not supported
        """
        if not isinstance(version, str):
            raise SchemaParserError(
                f"Schema version must be a string, got {type(version).__name__}"
            )

        if version not in SUPPORTED_SCHEMA_VERSIONS:
            raise SchemaParserError(
                f"Unsupported schema version '{version}'. "
                f"Supported versions: {', '.join(SUPPORTED_SCHEMA_VERSIONS)}"
            )

    @staticmethod
    def _validate_tools(tools: list[Any]) -> None:
        """
        Validate tool definitions.

        Ensures each tool has the required structure and valid execution configuration.

        Args:
            tools: List of tool definitions

        Raises:
            SchemaParserError: If any tool definition is invalid
        """
        for idx, tool in enumerate(tools):
            if not isinstance(tool, dict):
                raise SchemaParserError(
                    f"Tool at index {idx} must be a dictionary, got {type(tool).__name__}"
                )

            # Check required fields
            if "name" not in tool:
                raise SchemaParserError(f"Tool at index {idx} missing required field 'name'")

            if "execution" not in tool:
                raise SchemaParserError(
                    f"Tool at index {idx} ('{tool.get('name', 'unknown')}') missing required field 'execution'"
                )

            # Validate execution config
            execution = tool["execution"]
            if not isinstance(execution, dict):
                raise SchemaParserError(
                    f"Tool '{tool['name']}' execution must be a dictionary, got {type(execution).__name__}"
                )

            # Build and validate execution config
            try:
                SchemaParser._build_execution_config(execution)
            except SchemaParserError as e:
                raise SchemaParserError(
                    f"Tool '{tool['name']}' has invalid execution config: {e}"
                ) from e

    @staticmethod
    def _build_execution_config(execution: dict[str, Any]) -> ExecutionConfig:
        """
        Build the appropriate execution config based on type.

        Determines the execution type and creates the corresponding
        ExecutionConfig subclass (HTTP, CLI, File, or Text).

        Args:
            execution: Dictionary containing execution configuration

        Returns:
            Appropriate ExecutionConfig subclass instance

        Raises:
            SchemaParserError: If the execution type is missing, invalid,
                             or the configuration is invalid for that type
        """
        if "type" not in execution:
            raise SchemaParserError("Missing required field 'type' in execution config")

        exec_type = execution["type"]

        # Validate type is a string
        if not isinstance(exec_type, str):
            raise SchemaParserError(
                f"Execution type must be a string, got {type(exec_type).__name__}"
            )

        # Map execution type to config class
        type_map = {
            ExecutionType.HTTP.value: HTTPExecutionConfig,
            ExecutionType.CLI.value: CLIExecutionConfig,
            ExecutionType.FILE.value: FileExecutionConfig,
            ExecutionType.TEXT.value: TextExecutionConfig,
        }

        # Check if type is valid
        if exec_type not in type_map:
            valid_types = ", ".join(type_map.keys())
            raise SchemaParserError(
                f"Invalid execution type '{exec_type}'. Valid types: {valid_types}"
            )

        # Build the config using Pydantic validation
        config_class = type_map[exec_type]
        try:
            config = config_class(**execution)
        except ValidationError as e:
            raise SchemaParserError(f"Invalid {exec_type} execution config: {e}") from e

        return config

    @staticmethod
    def _load_toolsets(
        toolsets: list[Any], library_dir: str, schema_file_path: str | None
    ) -> list[Tool]:
        """
        Load tools from toolset definitions.

        Discovers toolset files in the library directory, loads them,
        and applies schema-level filtering based on the toolset configuration.

        Args:
            toolsets: List of toolset definitions from main schema
            library_dir: Directory to search for toolset files (relative to schema file)
            schema_file_path: Path to the main schema file (for resolving relative paths)

        Returns:
            List of Tool objects loaded from all toolsets with filters applied

        Raises:
            SchemaParserError: If toolset files cannot be found or loaded
        """
        all_tools: list[Tool] = []

        # Resolve library directory path
        if schema_file_path:
            base_dir = Path(schema_file_path).parent
            lib_path = base_dir / library_dir
        else:
            lib_path = Path(library_dir)

        # Check if library directory exists
        if not lib_path.exists():
            raise SchemaParserError(f"Library directory not found: {lib_path}")

        if not lib_path.is_dir():
            raise SchemaParserError(f"Library path is not a directory: {lib_path}")

        # Process each toolset
        for toolset in toolsets:
            # Load toolset schema
            toolset_schema = SchemaParser._load_toolset_file(toolset.name, lib_path)

            # Apply schema-level filter
            filtered_tools = SchemaParser._apply_toolset_filter(
                toolset_schema.tools, toolset.filter, toolset.filterValue
            )

            # Tag each tool with its toolset source
            for tool in filtered_tools:
                tool.toolset_source = toolset.name

            # Add to all tools
            all_tools.extend(filtered_tools)

        return all_tools

    @staticmethod
    def _load_toolset_file(name: str, lib_path: Path) -> ToolsetSchema:
        """
        Load a toolset file from the library directory.

        Tries to find the toolset as:
        1. A directory containing .mci.json files
        2. A file with exact name (e.g., github_prs.mci.json)
        3. A file with .mci.json extension added (e.g., github_prs -> github_prs.mci.json)

        Args:
            name: Name of the toolset (directory, file, or bare prefix)
            lib_path: Path to the library directory

        Returns:
            Parsed ToolsetSchema

        Raises:
            SchemaParserError: If toolset file cannot be found or loaded
        """
        # Try as directory first
        dir_path = lib_path / name
        if dir_path.is_dir():
            # Load all .mci.json files in directory
            toolset_files = list(dir_path.glob("*.mci.json"))
            if not toolset_files:
                raise SchemaParserError(
                    f"No .mci.json files found in toolset directory: {dir_path}"
                )
            # Merge all tools from all files in the directory.
            # Metadata is not merged - it's only for demonstration purposes in toolset files.
            # Schema version is validated to ensure compatibility for future parser extensibility.
            all_tools: list[Tool] = []
            schema_version = None
            for toolset_file in toolset_files:
                schema = SchemaParser._parse_toolset_file(toolset_file)
                all_tools.extend(schema.tools)
                # Validate schema version consistency across all files in directory
                if schema_version is None:
                    schema_version = schema.schemaVersion
                elif schema.schemaVersion != schema_version:
                    raise SchemaParserError(
                        f"Schema version mismatch in toolset directory '{dir_path}': "
                        f"File '{toolset_file.name}' has schemaVersion '{schema.schemaVersion}', "
                        f"but expected '{schema_version}' (from first file in directory). "
                        f"All files in a toolset directory must use the same schema version."
                    )

            # Return combined schema with only tools (no metadata from toolset files)
            return ToolsetSchema(
                schemaVersion=schema_version or "1.0",
                metadata=None,  # Don't merge metadata from toolset files
                tools=all_tools,
            )

        # Try as direct file
        file_path = lib_path / name
        if file_path.is_file():
            return SchemaParser._parse_toolset_file(file_path)

        # Try with .mci.json extension
        file_with_ext = lib_path / f"{name}.mci.json"
        if file_with_ext.is_file():
            return SchemaParser._parse_toolset_file(file_with_ext)

        # Try with .mci.yaml extension
        file_with_yaml = lib_path / f"{name}.mci.yaml"
        if file_with_yaml.is_file():
            return SchemaParser._parse_toolset_file(file_with_yaml)

        # Try with .mci.yml extension
        file_with_yml = lib_path / f"{name}.mci.yml"
        if file_with_yml.is_file():
            return SchemaParser._parse_toolset_file(file_with_yml)

        raise SchemaParserError(
            f"Toolset not found: {name}. Looked for directory, file, or file with .mci.json/.mci.yaml/.mci.yml extension in {lib_path}"
        )

    @staticmethod
    def _parse_toolset_file(file_path: Path) -> ToolsetSchema:
        """
        Parse a toolset file.

        Args:
            file_path: Path to the toolset file

        Returns:
            Parsed ToolsetSchema

        Raises:
            SchemaParserError: If file cannot be parsed or is invalid
        """
        # Determine file type by extension
        file_extension = file_path.suffix.lower()

        # Read and parse file
        try:
            with file_path.open("r", encoding="utf-8") as f:
                if file_extension == ".json":
                    data = json.load(f)
                elif file_extension in (".yaml", ".yml"):
                    data = yaml.safe_load(f)
                else:
                    raise SchemaParserError(
                        f"Unsupported toolset file extension '{file_extension}'. "
                        f"Supported extensions: .json, .yaml, .yml"
                    )
        except json.JSONDecodeError as e:
            raise SchemaParserError(f"Invalid JSON in toolset file {file_path}: {e}") from e
        except yaml.YAMLError as e:
            raise SchemaParserError(f"Invalid YAML in toolset file {file_path}: {e}") from e
        except OSError as e:
            raise SchemaParserError(f"Failed to read toolset file {file_path}: {e}") from e

        # Validate required fields
        if not isinstance(data, dict):
            raise SchemaParserError(
                f"Toolset file {file_path} must contain a JSON/YAML object, got {type(data).__name__}"
            )

        if "schemaVersion" not in data:
            raise SchemaParserError(
                f"Toolset file {file_path} missing required field 'schemaVersion'"
            )

        if "tools" not in data:
            raise SchemaParserError(f"Toolset file {file_path} missing required field 'tools'")

        # Validate schema version
        SchemaParser._validate_schema_version(data["schemaVersion"])

        # Validate tools
        if not isinstance(data["tools"], list):
            raise SchemaParserError(
                f"Toolset file {file_path} field 'tools' must be a list, got {type(data['tools']).__name__}"
            )
        SchemaParser._validate_tools(data["tools"])

        # Parse with Pydantic
        try:
            schema = ToolsetSchema(**data)
        except ValidationError as e:
            raise SchemaParserError(f"Toolset file {file_path} validation failed: {e}") from e

        return schema

    @staticmethod
    def _apply_toolset_filter(
        tools: list[Tool], filter_type: str | None, filter_value: str | None
    ) -> list[Tool]:
        """
        Apply schema-level filtering to toolset tools.

        Args:
            tools: List of tools from the toolset
            filter_type: Type of filter ("only", "except", "tags", "withoutTags", or None)
            filter_value: Comma-separated list of tool names or tags

        Returns:
            Filtered list of Tool objects

        Raises:
            SchemaParserError: If filter configuration is invalid
        """
        # If no filter, return all tools
        if filter_type is None:
            return tools

        # Validate that filterValue is provided when filter is specified
        if filter_value is None:
            raise SchemaParserError(
                f"Filter type '{filter_type}' specified but filterValue is missing"
            )

        # Parse filter value (comma-separated, trim whitespace)
        filter_items = [item.strip() for item in filter_value.split(",") if item.strip()]

        if not filter_items:
            raise SchemaParserError(f"Filter value cannot be empty for filter type '{filter_type}'")

        # Apply filter based on type
        if filter_type == "only":
            # Include only tools with names in filter_items
            filter_set = set(filter_items)
            return [tool for tool in tools if tool.name in filter_set]

        elif filter_type == "except":
            # Exclude tools with names in filter_items
            filter_set = set(filter_items)
            return [tool for tool in tools if tool.name not in filter_set]

        elif filter_type == "tags":
            # Include only tools with at least one matching tag
            filter_set = set(filter_items)
            return [tool for tool in tools if any(tag in filter_set for tag in tool.tags)]

        elif filter_type == "withoutTags":
            # Exclude tools with any matching tag
            filter_set = set(filter_items)
            return [tool for tool in tools if not any(tag in filter_set for tag in tool.tags)]

        else:
            raise SchemaParserError(
                f"Invalid filter type '{filter_type}'. Valid types: only, except, tags, withoutTags"
            )
