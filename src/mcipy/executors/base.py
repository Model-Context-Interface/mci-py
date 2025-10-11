"""
Base executor class for MCI tool execution.

This module provides the abstract BaseExecutor class that all executors inherit from.
It provides common functionality for context building, timeout handling, and error formatting.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..models import ExecutionConfig, ExecutionResult
from ..templating import TemplateEngine


class BaseExecutor(ABC):
    """
    Abstract base class for all executors.

    Provides common execution logic including context building, timeout handling,
    and error formatting. All concrete executors (HTTP, CLI, File, Text) inherit
    from this base class and implement the execute() method.
    """

    def __init__(self):
        """Initialize the base executor with a template engine."""
        self.template_engine = TemplateEngine()

    @abstractmethod
    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """
        Execute a tool with the given configuration and context.

        This is an abstract method that must be implemented by all concrete executors.

        Args:
            config: Execution configuration specific to the executor type
            context: Context dictionary with 'props', 'env', and 'input' keys

        Returns:
            ExecutionResult with success/error status and content

        Raises:
            NotImplementedError: This is an abstract method
        """
        pass

    def _build_context(self, props: dict[str, Any], env_vars: dict[str, Any]) -> dict[str, Any]:
        """
        Build template context from properties and environment variables.

        Creates the context dictionary used for template rendering with 'props',
        'env', and 'input' keys. The 'input' key is an alias for 'props' for
        backward compatibility.

        Args:
            props: Properties/parameters passed to the tool execution
            env_vars: Environment variables

        Returns:
            Context dictionary with 'props', 'env', and 'input' keys
        """
        return {
            "props": props,
            "env": env_vars,
            "input": props,  # Alias for backward compatibility
        }

    def _handle_timeout(self, timeout_ms: int) -> int:
        """
        Convert timeout from milliseconds to seconds and apply defaults.

        If timeout_ms is 0 or negative, returns a default timeout of 30 seconds.
        Otherwise converts milliseconds to seconds (rounding up).

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            Timeout in seconds (minimum 1 second)
        """
        if timeout_ms <= 0:
            return 30  # Default timeout of 30 seconds

        # Convert milliseconds to seconds, rounding up to at least 1 second
        timeout_s = max(1, (timeout_ms + 999) // 1000)
        return timeout_s

    def _format_error(self, error: Exception) -> ExecutionResult:
        """
        Format an exception into a standardized ExecutionResult error response.

        Converts any exception into a consistent error format with isError=True
        and the error message as a string.

        Args:
            error: Exception that occurred during execution

        Returns:
            ExecutionResult with isError=True and error message
        """
        return ExecutionResult(
            isError=True,
            error=str(error),
            content=None,
        )

    def _apply_basic_templating_to_config(
        self, config: ExecutionConfig, context: dict[str, Any]
    ) -> None:
        """
        Apply basic templating to all string fields in the execution config.

        Recursively processes the config object and replaces placeholders like
        {{props.x}} and {{env.Y}} in all string fields. This is applied to
        the entire execution configuration (URLs, paths, headers, params, etc.)
        but NOT to large text content which uses advanced templating.

        Args:
            config: Execution configuration to process (modified in-place)
            context: Context dictionary for template resolution

        Note:
            This method modifies the config object in-place.
        """
        # Get all fields from the config model
        for field_name, field_value in config.__dict__.items():
            if field_value is None:
                continue

            # Apply templating based on field type
            if isinstance(field_value, str):
                # Apply basic templating to string fields
                templated_value = self.template_engine.render_basic(field_value, context)
                setattr(config, field_name, templated_value)
            elif isinstance(field_value, dict):
                # Recursively process dictionary fields
                self._apply_basic_templating_to_dict(field_value, context)
            elif isinstance(field_value, list):
                # Process list fields
                self._apply_basic_templating_to_list(field_value, context)
            # Note: We don't process Pydantic models recursively to avoid
            # modifying auth configs and other complex nested objects

    def _apply_basic_templating_to_dict(
        self, data: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """
        Apply basic templating to all string values in a dictionary.

        Args:
            data: Dictionary to process (modified in-place)
            context: Context dictionary for template resolution
        """
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.template_engine.render_basic(value, context)
            elif isinstance(value, dict):
                self._apply_basic_templating_to_dict(value, context)
            elif isinstance(value, list):
                self._apply_basic_templating_to_list(value, context)

    def _apply_basic_templating_to_list(self, data: list[Any], context: dict[str, Any]) -> None:
        """
        Apply basic templating to all string values in a list.

        Args:
            data: List to process (modified in-place)
            context: Context dictionary for template resolution
        """
        for i, value in enumerate(data):
            if isinstance(value, str):
                data[i] = self.template_engine.render_basic(value, context)
            elif isinstance(value, dict):
                self._apply_basic_templating_to_dict(value, context)
            elif isinstance(value, list):
                self._apply_basic_templating_to_list(value, context)
