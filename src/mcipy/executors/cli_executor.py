"""
CLI executor for MCI tools.

This module provides the CLIExecutor class that handles CLI-based tool execution.
It supports command execution with arguments, boolean and value flags, working directory,
and timeout handling. The executor is platform-aware and handles Windows/Linux/macOS
differences in command execution.
"""

import subprocess
from typing import Any

from ..models import (
    CLIExecutionConfig,
    ExecutionConfig,
    ExecutionResult,
    ExecutionResultContent,
    FlagConfig,
    TextContent,
)
from .base import BaseExecutor


class CLIExecutor(BaseExecutor):
    """
    Executor for CLI-based tools.

    Handles command-line tool execution with support for arguments, flags,
    working directory, and timeouts. Applies templating to all command components
    and handles platform-specific differences.
    """

    def __init__(self):
        """Initialize the CLI executor with a template engine."""
        super().__init__()

    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """
        Execute a CLI-based tool by running a subprocess.

        Args:
            config: CLI execution configuration with command, args, flags, cwd, timeout
            context: Context dictionary with 'props', 'env', 'input', and 'path_validation' keys

        Returns:
            ExecutionResult with command output or error
        """
        # Type check to ensure we got the right config type
        if not isinstance(config, CLIExecutionConfig):
            return self._format_error(
                TypeError(f"Expected CLIExecutionConfig, got {type(config).__name__}")
            )

        try:
            # Apply basic templating to all config fields (command, args, cwd)
            self._apply_basic_templating_to_config(config, context)

            # Validate cwd path if path validation context is provided and cwd is specified
            if context.get("path_validation") and config.cwd:
                validator = context["path_validation"]["validator"]
                from ..path_validator import PathValidationError

                try:
                    validator.validate_path(config.cwd)
                except PathValidationError as e:
                    return self._format_error(e)

            # Build the complete command with arguments and flags
            command_list = self._build_command_args(config, context)

            # Get working directory (may be None)
            cwd = config.cwd if config.cwd else None

            # Get timeout in seconds
            timeout = self._handle_timeout(config.timeout_ms)

            # Execute the subprocess
            stdout, stderr, returncode = self._run_subprocess(command_list, cwd, timeout)

            # Calculate stdout and stderr sizes in bytes
            stdout_bytes = len(stdout.encode())
            stderr_bytes = len(stderr.encode())

            # Check if command succeeded
            if returncode != 0:
                # Command failed - return error with stderr
                error_msg = f"Command exited with code {returncode}"
                if stderr:
                    error_msg += f": {stderr}"
                return ExecutionResult(
                    result=ExecutionResultContent(
                        isError=True,
                        content=[TextContent(text=error_msg)],
                        metadata={
                            "exit_code": returncode,
                            "stdout_bytes": stdout_bytes,
                            "stderr_bytes": stderr_bytes,
                            "stderr": stderr,
                            "stdout": stdout,
                        },
                    )
                )

            # Command succeeded - return stdout
            return ExecutionResult(
                result=ExecutionResultContent(
                    isError=False,
                    content=[TextContent(text=stdout)],
                    metadata={
                        "exit_code": returncode,
                        "stdout_bytes": stdout_bytes,
                        "stderr_bytes": stderr_bytes,
                        "stderr": stderr,
                    },
                )
            )

        except Exception as e:
            return self._format_error(e)

    def _build_command_args(self, config: CLIExecutionConfig, context: dict[str, Any]) -> list[str]:
        """
        Build the full command list with arguments and flags.

        Combines the command, arguments, and flags into a single list suitable
        for subprocess execution. Handles both boolean and value flags.

        Args:
            config: CLI execution configuration
            context: Context dictionary for flag resolution

        Returns:
            List of command components (command, args, flags)
        """
        # Start with the command itself
        command_list = [config.command]

        # Add arguments if provided
        if config.args:
            command_list.extend(config.args)

        # Apply flags if provided
        if config.flags:
            flag_args = self._apply_flags(config.flags, context)
            command_list.extend(flag_args)

        return command_list

    def _apply_flags(self, flags: dict[str, FlagConfig], context: dict[str, Any]) -> list[str]:
        """
        Convert flags configuration to command-line arguments.

        Handles two types of flags:
        - Boolean flags: Included only if the referenced property is truthy
        - Value flags: Included with their value if the referenced property exists

        Args:
            flags: Dictionary of flag name to FlagConfig
            context: Context dictionary for resolving flag values

        Returns:
            List of flag arguments to add to the command
        """
        flag_args: list[str] = []

        for flag_name, flag_config in flags.items():
            # Resolve the flag value from context using the template engine
            try:
                # The flag_config.from_ is a path like "props.verbose" or "env.DEBUG"
                flag_value = self.template_engine._resolve_placeholder(flag_config.from_, context)
            except Exception:
                # If the property doesn't exist, skip this flag
                continue

            if flag_config.type == "boolean":
                # Boolean flag: only add if truthy
                if flag_value:
                    flag_args.append(flag_name)
            elif flag_config.type == "value":
                # Value flag: add flag name and value
                if flag_value is not None:
                    flag_args.append(flag_name)
                    flag_args.append(str(flag_value))

        return flag_args

    def _run_subprocess(
        self, command: list[str], cwd: str | None, timeout: int
    ) -> tuple[str, str, int]:
        """
        Execute a subprocess and capture output.

        Runs the command as a subprocess with the specified working directory
        and timeout. Captures both stdout and stderr.

        Args:
            command: List of command components (command and arguments)
            cwd: Working directory for the command (None for current directory)
            timeout: Timeout in seconds

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            subprocess.TimeoutExpired: If the command times out
            FileNotFoundError: If the command is not found
            OSError: If there's an error executing the command
        """
        # Run the subprocess
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            # Don't check returncode - we'll handle non-zero exits ourselves
            check=False,
        )

        return result.stdout, result.stderr, result.returncode
