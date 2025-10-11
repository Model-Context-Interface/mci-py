"""
Text executor for MCI tools.

This module provides the TextExecutor class that handles simple text-based tool execution.
It applies templating to text strings and returns the result.
"""

from typing import Any

from ..models import ExecutionConfig, ExecutionResult, TextExecutionConfig
from .base import BaseExecutor


class TextExecutor(BaseExecutor):
    """
    Executor for text-based tools.

    Applies templating to text strings, supporting both basic placeholder
    substitution and advanced templating with @for, @foreach, and @if directives.
    """

    def __init__(self):
        """Initialize the text executor with a template engine."""
        super().__init__()

    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """
        Execute a text-based tool by applying templating to the text.

        Processes the text with advanced templating, supporting all directives
        (@for, @foreach, @if) along with basic placeholder substitution.

        Args:
            config: Text execution configuration with the text template
            context: Context dictionary with 'props', 'env', and 'input' keys

        Returns:
            ExecutionResult with templated text or error
        """
        # Type check to ensure we got the right config type
        if not isinstance(config, TextExecutionConfig):
            return self._format_error(
                TypeError(f"Expected TextExecutionConfig, got {type(config).__name__}")
            )

        try:
            # Apply advanced templating to the text
            result = self.template_engine.render_advanced(config.text, context)

            return ExecutionResult(
                isError=False,
                content=result,
                error=None,
            )

        except Exception as e:
            return self._format_error(e)
