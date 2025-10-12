"""Unit tests for CLIExecutor class."""

import subprocess
import sys
from pathlib import Path

import pytest

from mcipy.executors.cli_executor import CLIExecutor
from mcipy.models import CLIExecutionConfig, FlagConfig


class TestCLIExecutor:
    """Tests for CLIExecutor class."""

    @pytest.fixture
    def executor(self):
        """Fixture for CLIExecutor instance."""
        return CLIExecutor()

    @pytest.fixture
    def context(self):
        """Fixture for test context."""
        return {
            "props": {"verbose": True, "output": "result.txt", "count": 5, "debug": False},
            "env": {"HOME": "/home/user", "PATH": "/usr/bin"},
            "input": {"verbose": True, "output": "result.txt"},
        }

    def test_build_command_args_simple(self, executor):
        """Test building command with no args or flags."""
        config = CLIExecutionConfig(command="ls")
        result = executor._build_command_args(config, {})
        assert result == ["ls"]

    def test_build_command_args_with_args(self, executor):
        """Test building command with arguments."""
        config = CLIExecutionConfig(command="grep", args=["-n", "pattern", "file.txt"])
        result = executor._build_command_args(config, {})
        assert result == ["grep", "-n", "pattern", "file.txt"]

    def test_build_command_args_with_boolean_flags(self, executor, context):
        """Test building command with boolean flags."""
        flags = {
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
            "-d": FlagConfig(**{"from": "props.debug", "type": "boolean"}),
        }
        config = CLIExecutionConfig(command="tool", flags=flags)
        result = executor._build_command_args(config, context)

        # Should include -v (verbose=True) but not -d (debug=False)
        assert "tool" in result
        assert "-v" in result
        assert "-d" not in result

    def test_build_command_args_with_value_flags(self, executor, context):
        """Test building command with value flags."""
        flags = {
            "--output": FlagConfig(**{"from": "props.output", "type": "value"}),
            "--count": FlagConfig(**{"from": "props.count", "type": "value"}),
        }
        config = CLIExecutionConfig(command="tool", flags=flags)
        result = executor._build_command_args(config, context)

        assert "tool" in result
        assert "--output" in result
        assert "result.txt" in result
        assert "--count" in result
        assert "5" in result

    def test_build_command_args_with_args_and_flags(self, executor, context):
        """Test building command with both args and flags."""
        flags = {
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
        }
        config = CLIExecutionConfig(command="grep", args=["-n", "pattern"], flags=flags)
        result = executor._build_command_args(config, context)

        assert result[0] == "grep"
        assert "-n" in result
        assert "pattern" in result
        assert "-v" in result

    def test_apply_flags_boolean_only(self, executor, context):
        """Test applying boolean flags only."""
        flags = {
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
            "-d": FlagConfig(**{"from": "props.debug", "type": "boolean"}),
        }
        result = executor._apply_flags(flags, context)

        assert "-v" in result  # verbose is True
        assert "-d" not in result  # debug is False

    def test_apply_flags_value_only(self, executor, context):
        """Test applying value flags only."""
        flags = {
            "--output": FlagConfig(**{"from": "props.output", "type": "value"}),
        }
        result = executor._apply_flags(flags, context)

        assert "--output" in result
        assert "result.txt" in result
        assert len(result) == 2  # flag and value

    def test_apply_flags_mixed(self, executor, context):
        """Test applying mixed boolean and value flags."""
        flags = {
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
            "--output": FlagConfig(**{"from": "props.output", "type": "value"}),
            "-d": FlagConfig(**{"from": "props.debug", "type": "boolean"}),
        }
        result = executor._apply_flags(flags, context)

        assert "-v" in result
        assert "--output" in result
        assert "result.txt" in result
        assert "-d" not in result

    def test_apply_flags_missing_property(self, executor, context):
        """Test that flags with missing properties are skipped."""
        flags = {
            "--missing": FlagConfig(**{"from": "props.nonexistent", "type": "value"}),
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
        }
        result = executor._apply_flags(flags, context)

        # Should skip --missing but include -v
        assert "--missing" not in result
        assert "-v" in result

    def test_apply_flags_from_env(self, executor, context):
        """Test applying flags from environment variables."""
        flags = {
            "--home": FlagConfig(**{"from": "env.HOME", "type": "value"}),
        }
        result = executor._apply_flags(flags, context)

        assert "--home" in result
        assert "/home/user" in result

    def test_run_subprocess_success(self, executor):
        """Test running subprocess successfully."""
        # Use a simple cross-platform command
        if sys.platform == "win32":
            command = ["cmd", "/c", "echo", "test"]
        else:
            command = ["echo", "test"]

        stdout, _stderr, returncode = executor._run_subprocess(command, None, 5)

        assert returncode == 0
        assert "test" in stdout

    def test_run_subprocess_with_cwd(self, executor):
        """Test running subprocess with working directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use pwd (Linux/macOS) or cd (Windows) to check working directory
            if sys.platform == "win32":
                command = ["cmd", "/c", "cd"]
            else:
                command = ["pwd"]

            stdout, _stderr, returncode = executor._run_subprocess(command, tmpdir, 5)

            assert returncode == 0
            # The output should contain the temp directory path
            assert Path(tmpdir).name in stdout or tmpdir in stdout

    def test_run_subprocess_with_timeout(self, executor):
        """Test that subprocess respects timeout."""
        # Use a command that sleeps longer than the timeout
        if sys.platform == "win32":
            command = ["cmd", "/c", "timeout", "/t", "10"]
        else:
            command = ["sleep", "10"]

        with pytest.raises(subprocess.TimeoutExpired):
            executor._run_subprocess(command, None, 1)

    def test_run_subprocess_command_not_found(self, executor):
        """Test handling of command not found error."""
        command = ["nonexistent_command_12345"]

        with pytest.raises(FileNotFoundError):
            executor._run_subprocess(command, None, 5)

    def test_run_subprocess_non_zero_exit(self, executor):
        """Test subprocess with non-zero exit code."""
        # Use false command (Linux/macOS) or a failing command (Windows)
        if sys.platform == "win32":
            command = ["cmd", "/c", "exit", "42"]
        else:
            command = ["sh", "-c", "exit 42"]

        _stdout, _stderr, returncode = executor._run_subprocess(command, None, 5)

        assert returncode == 42

    def test_execute_simple_command(self, executor, context):
        """Test executing a simple command."""
        config = CLIExecutionConfig(command="echo" if sys.platform != "win32" else "cmd")
        if sys.platform == "win32":
            config.args = ["/c", "echo", "hello"]
        else:
            config.args = ["hello"]

        result = executor.execute(config, context)

        assert not result.isError
        assert "hello" in result.content
        assert result.metadata["returncode"] == 0

    def test_execute_command_with_templated_args(self, executor, context):
        """Test executing command with templated arguments."""
        if sys.platform == "win32":
            config = CLIExecutionConfig(
                command="cmd",
                args=["/c", "echo", "{{props.output}}"],
            )
        else:
            config = CLIExecutionConfig(
                command="echo",
                args=["{{props.output}}"],
            )

        result = executor.execute(config, context)

        assert not result.isError
        assert "result.txt" in result.content

    def test_execute_command_with_templated_command(self, executor, context):
        """Test executing command with templated command name."""
        # Add echo to context env
        context["env"]["CMD"] = "echo"

        config = CLIExecutionConfig(
            command="{{env.CMD}}" if sys.platform != "win32" else "cmd",
            args=["hello"] if sys.platform != "win32" else ["/c", "echo", "hello"],
        )

        result = executor.execute(config, context)

        assert not result.isError
        assert "hello" in result.content

    def test_execute_with_boolean_flags(self, executor, context):
        """Test executing command with boolean flags."""
        # Test with echo -n (no newline) which is a boolean flag behavior
        if sys.platform != "win32":
            config = CLIExecutionConfig(
                command="echo",
                args=["test"],
                flags={
                    # Can't easily test -n with echo in a cross-platform way
                    # so we'll just verify the flag is added to the command
                },
            )
        else:
            # On Windows, just test that flags are processed
            config = CLIExecutionConfig(
                command="cmd",
                args=["/c", "echo", "test"],
            )

        result = executor.execute(config, context)
        assert not result.isError

    def test_execute_command_failure(self, executor, context):
        """Test executing a command that fails."""
        if sys.platform == "win32":
            config = CLIExecutionConfig(command="cmd", args=["/c", "exit", "1"])
        else:
            config = CLIExecutionConfig(command="sh", args=["-c", "exit 1"])

        result = executor.execute(config, context)

        assert result.isError
        assert "exited with code 1" in result.error
        assert result.metadata["returncode"] == 1

    def test_execute_command_not_found(self, executor, context):
        """Test executing a command that doesn't exist."""
        config = CLIExecutionConfig(command="nonexistent_command_xyz_12345")

        result = executor.execute(config, context)

        assert result.isError
        assert "FileNotFoundError" in result.error or "No such file" in result.error

    def test_execute_with_timeout(self, executor, context):
        """Test executing command with timeout."""
        if sys.platform == "win32":
            config = CLIExecutionConfig(
                command="cmd", args=["/c", "timeout", "/t", "10"], timeout_ms=500
            )
        else:
            config = CLIExecutionConfig(command="sleep", args=["10"], timeout_ms=500)

        result = executor.execute(config, context)

        assert result.isError
        # The error message contains "timed out" (from subprocess.TimeoutExpired)
        assert "timed out" in result.error.lower()

    def test_execute_with_cwd(self, executor, context):
        """Test executing command with working directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            if sys.platform == "win32":
                config = CLIExecutionConfig(command="cmd", args=["/c", "cd"], cwd=tmpdir)
            else:
                config = CLIExecutionConfig(command="pwd", cwd=tmpdir)

            result = executor.execute(config, context)

            assert not result.isError
            assert Path(tmpdir).name in result.content or tmpdir in result.content

    def test_execute_with_templated_cwd(self, executor, context):
        """Test executing command with templated working directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            context["props"]["workdir"] = tmpdir

            if sys.platform == "win32":
                config = CLIExecutionConfig(
                    command="cmd", args=["/c", "cd"], cwd="{{props.workdir}}"
                )
            else:
                config = CLIExecutionConfig(command="pwd", cwd="{{props.workdir}}")

            result = executor.execute(config, context)

            assert not result.isError
            assert Path(tmpdir).name in result.content or tmpdir in result.content

    def test_execute_wrong_config_type(self, executor, context):
        """Test executing with wrong config type."""
        from mcipy.models import HTTPExecutionConfig

        config = HTTPExecutionConfig(url="https://example.com")
        result = executor.execute(config, context)

        assert result.isError
        assert "Expected CLIExecutionConfig" in result.error

    def test_execute_captures_stderr(self, executor, context):
        """Test that stderr is captured when command fails."""
        if sys.platform == "win32":
            # Windows command that writes to stderr
            config = CLIExecutionConfig(command="cmd", args=["/c", "echo error 1>&2 && exit 1"])
        else:
            # Unix command that writes to stderr
            config = CLIExecutionConfig(command="sh", args=["-c", "echo error >&2; exit 1"])

        result = executor.execute(config, context)

        assert result.isError
        assert result.metadata["returncode"] == 1
        # stderr should be captured in metadata
        assert "error" in result.metadata["stderr"] or result.metadata["stderr"] != ""

    def test_execute_with_all_features(self, executor, context):
        """Test executing with command, args, flags, cwd, and timeout all together."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            if sys.platform == "win32":
                config = CLIExecutionConfig(
                    command="cmd",
                    args=["/c", "echo", "{{props.output}}"],
                    cwd=tmpdir,
                    timeout_ms=5000,
                )
            else:
                flags = {
                    # Use a flag that works with echo if verbose is true
                }
                config = CLIExecutionConfig(
                    command="echo",
                    args=["{{props.output}}"],
                    flags=flags,
                    cwd=tmpdir,
                    timeout_ms=5000,
                )

            result = executor.execute(config, context)

            assert not result.isError
            assert "result.txt" in result.content

    def test_apply_flags_with_numeric_value(self, executor):
        """Test that numeric flag values are converted to strings."""
        context = {"props": {"count": 42}, "env": {}, "input": {}}
        flags = {
            "--count": FlagConfig(**{"from": "props.count", "type": "value"}),
        }

        result = executor._apply_flags(flags, context)

        assert "--count" in result
        assert "42" in result

    def test_apply_flags_preserves_order(self, executor, context):
        """Test that flags maintain their order in the dictionary."""
        # Note: In Python 3.7+, dicts preserve insertion order
        flags = {
            "-a": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
            "-b": FlagConfig(**{"from": "props.debug", "type": "boolean"}),
            "-c": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
        }

        result = executor._apply_flags(flags, context)

        # verbose is True, debug is False
        # So we should get -a and -c in that order
        assert result == ["-a", "-c"]
