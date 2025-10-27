"""
Path validation utilities for MCI tool execution.

This module provides security functions to validate file paths used in tool execution.
It ensures that file/CLI paths are within allowed directories unless explicitly overridden
via enableAnyPaths configuration.
"""

from pathlib import Path


class PathValidationError(Exception):
    """Exception raised when path validation fails."""

    pass


class PathValidator:
    """
    Validates file paths against security restrictions.

    Ensures paths are within the context directory or allowed directories
    unless enableAnyPaths is enabled.
    """

    def __init__(
        self,
        context_dir: Path,
        enable_any_paths: bool = False,
        directory_allow_list: list[str] | None = None,
    ):
        """
        Initialize the path validator.

        Args:
            context_dir: Directory containing the MCI schema file (base directory)
            enable_any_paths: If True, skip all path validation
            directory_allow_list: Additional directories to allow (relative or absolute paths)
        """
        self.context_dir = context_dir.resolve()
        self.enable_any_paths = enable_any_paths
        self.allowed_dirs = self._build_allowed_dirs(directory_allow_list or [])

    def _build_allowed_dirs(self, directory_allow_list: list[str]) -> list[Path]:
        """
        Build list of allowed directories (absolute paths).

        Converts relative and absolute paths in the allow list to absolute paths.
        Relative paths are resolved relative to the context directory.

        Args:
            directory_allow_list: List of directory paths (relative or absolute)

        Returns:
            List of resolved absolute Path objects
        """
        allowed = [self.context_dir]  # Context directory is always allowed

        for dir_path in directory_allow_list:
            path = Path(dir_path)
            # If relative, resolve relative to context directory
            if not path.is_absolute():
                path = (self.context_dir / path).resolve()
            else:
                path = path.resolve()
            allowed.append(path)

        return allowed

    def validate_path(self, path: str) -> None:
        """
        Validate that a file path is allowed.

        Checks if the path is within the context directory or an allowed directory.
        Raises PathValidationError if the path is not allowed.

        Args:
            path: File or directory path to validate

        Raises:
            PathValidationError: If path is outside allowed directories and enableAnyPaths is False
        """
        # If enableAnyPaths is True, all paths are allowed
        if self.enable_any_paths:
            return

        # Resolve the path to absolute
        # If path is relative, resolve it relative to the context directory
        path_obj = Path(path)
        if not path_obj.is_absolute():
            file_path = (self.context_dir / path_obj).resolve()
        else:
            file_path = path_obj.resolve()

        # Check if the path is within any allowed directory
        for allowed_dir in self.allowed_dirs:
            try:
                # Check if file_path is relative to allowed_dir
                file_path.relative_to(allowed_dir)
                # If we get here, the path is within this allowed directory
                return
            except ValueError:
                # Path is not relative to this directory, try next
                continue

        # If we get here, path is not in any allowed directory
        raise PathValidationError(
            f"File path access outside context directory and allow-list is not allowed "
            f"unless enableAnyPaths is true. Path: {path}"
        )

    @staticmethod
    def merge_settings(
        schema_enable_any_paths: bool,
        schema_directory_allow_list: list[str],
        tool_enable_any_paths: bool,
        tool_directory_allow_list: list[str],
    ) -> tuple[bool, list[str]]:
        """
        Merge schema-level and tool-level settings with proper precedence.

        Tool-level settings take precedence over schema-level settings.
        If tool has explicit settings, use those; otherwise use schema settings.

        Args:
            schema_enable_any_paths: Schema-level enableAnyPaths
            schema_directory_allow_list: Schema-level directoryAllowList
            tool_enable_any_paths: Tool-level enableAnyPaths
            tool_directory_allow_list: Tool-level directoryAllowList

        Returns:
            Tuple of (effective_enable_any_paths, effective_directory_allow_list)
        """
        # Tool-level takes precedence
        # For enableAnyPaths: if tool has explicit True, use it; otherwise use schema setting
        # For directoryAllowList: if tool has non-empty list, use it; otherwise use schema list
        effective_enable_any_paths = tool_enable_any_paths or schema_enable_any_paths
        effective_directory_allow_list = (
            tool_directory_allow_list if tool_directory_allow_list else schema_directory_allow_list
        )

        return effective_enable_any_paths, effective_directory_allow_list
