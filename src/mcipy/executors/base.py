"""
Base executor class for MCI tool execution.

This module provides the abstract BaseExecutor class that all executors inherit from.
It provides common functionality for context building, timeout handling, and error formatting.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..models import ExecutionConfig, ExecutionResult


class BaseExecutor(ABC):
    """
    Abstract base class for all executors.

    Provides common execution logic including context building, timeout handling,
    and error formatting. All concrete executors (HTTP, CLI, File, Text) inherit
    from this base class and implement the execute() method.
    """

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
