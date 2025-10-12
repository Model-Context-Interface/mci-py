"""
Schema parser for MCI JSON files.

This module provides the SchemaParser class for loading and validating
MCI schema files. It handles:
- Loading JSON files from disk
- Parsing dictionaries into MCISchema objects
- Validating schema versions
- Validating tool definitions
- Building appropriate execution configurations based on type
"""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .enums import ExecutionType
from .models import (
    CLIExecutionConfig,
    ExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    MCISchema,
    TextExecutionConfig,
)
from .schema_config import SUPPORTED_SCHEMA_VERSIONS


class SchemaParserError(Exception):
    """Exception raised for schema parsing errors."""

    pass


class SchemaParser:
    """
    Parser for MCI schema files.

    Loads and validates MCI JSON schema files, ensuring they conform to
    the expected structure and contain valid tool definitions. Uses Pydantic
    for strong validation and provides helpful error messages for invalid schemas.
    """

    @staticmethod
    def parse_file(file_path: str) -> MCISchema:
        """
        Load and validate an MCI JSON file.

        Reads a JSON file from disk, validates its structure and content,
        and returns a parsed MCISchema object.

        Args:
            file_path: Path to the MCI JSON file

        Returns:
            Validated MCISchema object

        Raises:
            SchemaParserError: If the file doesn't exist, can't be read,
                             contains invalid JSON, or fails validation
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            raise SchemaParserError(f"Schema file not found: {file_path}")

        if not path.is_file():
            raise SchemaParserError(f"Path is not a file: {file_path}")

        # Read and parse JSON
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise SchemaParserError(f"Invalid JSON in file {file_path}: {e}") from e
        except OSError as e:
            raise SchemaParserError(f"Failed to read file {file_path}: {e}") from e

        # Parse the dictionary
        return SchemaParser.parse_dict(data)

    @staticmethod
    def parse_dict(data: dict[str, Any]) -> MCISchema:
        """
        Parse a dictionary into an MCISchema object.

        Validates the dictionary structure, schema version, and tool definitions,
        then returns a validated MCISchema object.

        Args:
            data: Dictionary containing MCI schema data

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

        if "tools" not in data:
            raise SchemaParserError("Missing required field 'tools'")

        # Validate schema version
        SchemaParser._validate_schema_version(data["schemaVersion"])

        # Validate tools is a list
        if not isinstance(data["tools"], list):
            raise SchemaParserError(
                f"Field 'tools' must be a list, got {type(data['tools']).__name__}"
            )

        # Validate tools
        SchemaParser._validate_tools(data["tools"])

        # Use Pydantic to validate and build the schema
        try:
            schema = MCISchema(**data)
        except ValidationError as e:
            raise SchemaParserError(f"Schema validation failed: {e}") from e

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
