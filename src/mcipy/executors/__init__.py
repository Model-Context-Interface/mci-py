"""
Execution handlers for MCI tools.

This module provides the executor classes that handle different types of
tool execution (HTTP, CLI, file, text). Each executor inherits from BaseExecutor
and implements the execute() method according to its execution type.

The ExecutorFactory provides centralized instantiation of executors based on
execution type, with singleton caching for performance.
"""

from ..enums import ExecutionType
from .base import BaseExecutor
from .cli_executor import CLIExecutor
from .file_executor import FileExecutor
from .http_executor import HTTPExecutor
from .text_executor import TextExecutor


class ExecutorFactory:
    """
    Factory for creating and caching executor instances.

    Provides centralized instantiation of executors based on execution type.
    Uses singleton pattern to cache executor instances for better performance.
    """

    _executors: dict[ExecutionType, BaseExecutor] = {}

    @classmethod
    def get_executor(cls, execution_type: ExecutionType) -> BaseExecutor:
        """
        Get an executor instance for the given execution type.

        Returns a cached executor instance if available, otherwise creates
        a new one and caches it for future use.

        Args:
            execution_type: The type of execution (HTTP, CLI, FILE, TEXT)

        Returns:
            BaseExecutor instance for the specified type

        Raises:
            ValueError: If the execution type is not supported
        """
        # Return cached executor if available
        if execution_type in cls._executors:
            return cls._executors[execution_type]

        # Create new executor based on type
        if execution_type == ExecutionType.HTTP:
            executor = HTTPExecutor()
        elif execution_type == ExecutionType.CLI:
            executor = CLIExecutor()
        elif execution_type == ExecutionType.FILE:
            executor = FileExecutor()
        elif execution_type == ExecutionType.TEXT:
            executor = TextExecutor()
        else:
            raise ValueError(f"Unsupported execution type: {execution_type}")

        # Cache and return
        cls._executors[execution_type] = executor
        return executor

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the executor cache.

        Useful for testing or when you want to ensure fresh executor instances.
        """
        cls._executors.clear()


__all__ = [
    "BaseExecutor",
    "CLIExecutor",
    "ExecutorFactory",
    "FileExecutor",
    "HTTPExecutor",
    "TextExecutor",
]
