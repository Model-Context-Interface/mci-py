"""
File executor for MCI tools.

This module provides the FileExecutor class that handles file-based tool execution.
It reads files from disk and optionally applies templating to the content.
"""

from pathlib import Path
from typing import Any

from ..models import ExecutionConfig, ExecutionResult, FileExecutionConfig
from .base import BaseExecutor


class FileExecutor(BaseExecutor):
    """
    Executor for file-based tools.

    Reads files from disk and optionally applies templating to the content.
    Supports both basic placeholder substitution and advanced templating
    with @for, @foreach, and @if directives when enableTemplating is true.
    """

    def __init__(self):
        """Initialize the file executor with a template engine."""
        super().__init__()

    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """
        Execute a file-based tool by reading and optionally templating file content.

        Args:
            config: File execution configuration with path and enableTemplating flag
            context: Context dictionary with 'props', 'env', and 'input' keys

        Returns:
            ExecutionResult with file content (possibly templated) or error
        """
        # Type check to ensure we got the right config type
        if not isinstance(config, FileExecutionConfig):
            return self._format_error(
                TypeError(f"Expected FileExecutionConfig, got {type(config).__name__}")
            )

        try:
            # Apply basic templating to all config fields (e.g., path)
            self._apply_basic_templating_to_config(config, context)

            # Read the file content
            content = self._read_file(config.path)

            # Parse content with templating if enabled
            parsed_content = self._parse_content(content, context, config.enableTemplating)

            return ExecutionResult(
                isError=False,
                content=parsed_content,
                error=None,
            )

        except Exception as e:
            return self._format_error(e)

    def _read_file(self, path: str) -> str:
        """
        Read the content of a file from disk.

        Args:
            path: Path to the file to read

        Returns:
            File content as a string

        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If the file cannot be read
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not file_path.is_file():
            raise OSError(f"Path is not a file: {path}")

        # Read file content
        return file_path.read_text(encoding="utf-8")

    def _parse_content(
        self, content: str, context: dict[str, Any], parse_placeholders: bool
    ) -> str:
        """
        Apply templating to file content if enabled.

        When parse_placeholders is True, applies advanced templating including
        @for, @foreach, and @if directives along with basic placeholder substitution.
        When False, returns content unchanged.

        Args:
            content: File content to parse
            context: Context dictionary for template resolution
            parse_placeholders: Whether to apply templating

        Returns:
            Parsed content (templated if enabled, otherwise unchanged)

        Raises:
            TemplateError: If template processing fails
        """
        if not parse_placeholders:
            return content

        # Use advanced templating to support all directives
        return self.template_engine.render_advanced(content, context)
