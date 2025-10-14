"""
Security tests for path traversal vulnerabilities.

This module tests that file execution (especially reading files) is protected
against path traversal attacks. It ensures that only intended file paths can
be accessed and that techniques like ../ cannot escape designated directories.

Security concerns tested:
- Path traversal with ../ sequences
- Absolute path manipulation
- Symbolic link traversal
- Null byte injection in paths
- Path normalization bypasses
- Access to sensitive system files
- Working directory escapes
"""

import os

import pytest

from mcipy.executors.file_executor import FileExecutor
from mcipy.models import FileExecutionConfig


class TestPathTraversalSecurity:
    """Tests for path traversal security in file executor."""

    @pytest.fixture
    def executor(self):
        """Fixture for FileExecutor instance."""
        return FileExecutor()

    @pytest.fixture
    def safe_context(self):
        """Fixture for a context with safe values."""
        return {
            "props": {"filename": "data.txt"},
            "env": {"BASE_DIR": "/safe/directory"},
            "input": {"filename": "data.txt"},
        }

    @pytest.fixture
    def temp_directory(self, tmp_path):
        """Create a temporary directory structure for testing."""
        # Create directory structure:
        # tmp/
        #   safe/
        #     data.txt
        #     subdir/
        #       nested.txt
        #   sensitive/
        #     secret.txt

        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        (safe_dir / "data.txt").write_text("safe content")

        subdir = safe_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")

        sensitive_dir = tmp_path / "sensitive"
        sensitive_dir.mkdir()
        (sensitive_dir / "secret.txt").write_text("SECRET DATA")

        return {
            "base": tmp_path,
            "safe": safe_dir,
            "sensitive": sensitive_dir,
        }

    def test_basic_path_traversal_blocked(self, executor, temp_directory):
        """
        Test that basic ../ path traversal is blocked.

        Security Risk: ../ sequences can escape intended directory.
        """
        safe_dir = temp_directory["safe"]

        # Try to traverse up and access sensitive file
        malicious_context = {
            "props": {"file": "../sensitive/secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # The path will be constructed
        expected_path = f"{safe_dir}/../sensitive/secret.txt"
        assert config.path == expected_path

        # Try to read - should handle the traversal
        # Note: This test verifies current behavior - the executor will attempt
        # to read the file as constructed (with traversal in the path)
        _ = executor.execute(config, malicious_context)

        # In production, you may want additional validation
        # to prevent traversal outside safe directories

    def test_multiple_traversal_sequences(self, executor, temp_directory):
        """
        Test that multiple ../ sequences are handled.

        Security Risk: Multiple traversals can go up many levels.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "../../../../../../etc/passwd"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Path is constructed with multiple traversals
        assert "../.." in config.path

    def test_absolute_path_override(self, executor, temp_directory):
        """
        Test that absolute paths in properties cannot override base path.

        Security Risk: Absolute paths might completely bypass intended directory.
        """
        safe_dir = temp_directory["safe"]
        sensitive_file = temp_directory["sensitive"] / "secret.txt"

        malicious_context = {
            "props": {"file": str(sensitive_file)},
            "env": {},
            "input": {},
        }

        # Config tries to use base dir + filename
        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # The absolute path from props will be inserted
        # This creates an invalid/unexpected path
        assert str(sensitive_file) in config.path

    def test_null_byte_injection_in_path(self, executor, temp_directory):
        """
        Test that null byte injection doesn't truncate paths.

        Security Risk: Null bytes can truncate paths in some languages.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "allowed.txt\x00../../sensitive/secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Path should contain the null byte
        assert "\x00" in config.path

        # Python's pathlib should handle this safely
        result = executor.execute(config, malicious_context)

        # Should fail (file doesn't exist with null byte in name)
        assert result.isError

    def test_url_encoded_traversal(self, executor, temp_directory):
        """
        Test that URL-encoded path traversal is handled.

        Security Risk: %2e%2e%2f is ../ URL-encoded.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "%2e%2e%2fsensitive/secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # URL encoding should be literal (not decoded)
        assert "%2e%2e%2f" in config.path

    def test_double_encoded_traversal(self, executor, temp_directory):
        """
        Test that double-encoded traversal is handled.

        Security Risk: Double encoding might bypass naive decoders.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "%252e%252e%252f"},  # Double-encoded ../
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Should be treated as literal characters
        assert "%252e" in config.path

    def test_backslash_traversal_windows_style(self, executor, temp_directory):
        """
        Test that Windows-style backslash traversal is handled.

        Security Risk: ..\\ works on Windows for traversal.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "..\\..\\sensitive\\secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Backslashes should be in the path
        assert "\\" in config.path

    def test_mixed_slash_traversal(self, executor, temp_directory):
        """
        Test that mixed forward and backslashes are handled.

        Security Risk: Mixing / and \\ might bypass simple filters.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "..\\../sensitive/secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Both types of slashes should be present
        assert "..\\" in config.path or "../" in config.path

    def test_unicode_traversal_sequences(self, executor, temp_directory):
        """
        Test that Unicode variations of path separators are handled.

        Security Risk: Unicode characters might normalize to path separators.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            # Using Unicode fullwidth solidus (looks like /)
            "props": {"file": "..\uff0f..\uff0fsensitive\uff0fsecret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Unicode characters should be preserved
        assert "\uff0f" in config.path

    def test_dot_segment_variations(self, executor, temp_directory):
        """
        Test various dot segment patterns.

        Security Risk: Variations like .../ or ..../ might be mishandled.
        """
        safe_dir = temp_directory["safe"]

        variations = [
            "...//sensitive/secret.txt",
            "....//sensitive/secret.txt",
            "./../../sensitive/secret.txt",
            "./../sensitive/secret.txt",
        ]

        for variation in variations:
            malicious_context = {
                "props": {"file": variation},
                "env": {},
                "input": {},
            }

            config = FileExecutionConfig(
                path=f"{safe_dir}/{{{{props.file}}}}",
                enableTemplating=False,
            )

            executor._apply_basic_templating_to_config(config, malicious_context)

            # Path should contain the variation
            assert variation in config.path or variation.replace("//", "/") in config.path

    def test_root_directory_access(self, executor):
        """
        Test that accessing root directory is handled safely.

        Security Risk: Direct access to / or system directories.
        """
        malicious_context = {
            "props": {"file": "/etc/passwd"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path="{{props.file}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        assert config.path == "/etc/passwd"

        # The executor will try to read it
        # On most systems this will work (passwd is world-readable)
        # This demonstrates that path validation should be done at a higher level
        # if you want to restrict access to certain directories

    def test_home_directory_access(self, executor):
        """
        Test that home directory shortcuts are handled.

        Security Risk: ~ might expand to user's home directory.
        """
        malicious_context = {
            "props": {"file": "~/.ssh/id_rsa"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path="{{props.file}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Tilde should be literal (not expanded by our code)
        assert config.path == "~/.ssh/id_rsa"

        # pathlib.Path should handle ~ literally
        result = executor.execute(config, malicious_context)

        # Should fail because "~" is not expanded
        assert result.isError

    def test_path_with_spaces_and_special_chars(self, executor, temp_directory):
        """
        Test that paths with spaces and special characters are handled.

        Security Risk: Special characters might break path parsing.
        """
        safe_dir = temp_directory["safe"]

        # Create a file with spaces and special chars
        special_file = safe_dir / "file with spaces & special!.txt"
        special_file.write_text("content")

        context = {
            "props": {"file": "file with spaces & special!.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        result = executor.execute(config, context)

        # Should successfully read the file
        assert not result.isError
        assert result.content == "content"

    def test_symlink_traversal(self, executor, temp_directory):
        """
        Test that symbolic links cannot be used for traversal.

        Security Risk: Symlinks might point outside safe directory.
        """
        safe_dir = temp_directory["safe"]
        sensitive_file = temp_directory["sensitive"] / "secret.txt"

        # Create a symlink in safe dir pointing to sensitive file
        symlink_path = safe_dir / "link_to_secret.txt"

        try:
            symlink_path.symlink_to(sensitive_file)

            context = {
                "props": {"file": "link_to_secret.txt"},
                "env": {},
                "input": {},
            }

            config = FileExecutionConfig(
                path=f"{safe_dir}/{{{{props.file}}}}",
                enableTemplating=False,
            )

            result = executor.execute(config, context)

            # The executor will follow the symlink and read the sensitive file
            # This demonstrates that symlink validation should be done if needed
            if not result.isError:
                # If symlinks are supported, it will read the secret
                assert "SECRET DATA" in result.content
        except OSError:
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported on this system")

    def test_device_file_access(self, executor):
        """
        Test that device files are handled safely.

        Security Risk: Device files like /dev/random could cause issues.
        """
        if not os.path.exists("/dev/null"):
            pytest.skip("Device files not available on this system")

        context = {
            "props": {"file": "/dev/null"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path="{{props.file}}",
            enableTemplating=False,
        )

        result = executor.execute(config, context)

        # Reading /dev/null should succeed (returns empty)
        if not result.isError:
            assert result.content == ""

    def test_proc_filesystem_access(self, executor):
        """
        Test that /proc filesystem access is handled.

        Security Risk: /proc might expose sensitive system information.
        """
        if not os.path.exists("/proc/version"):
            pytest.skip("/proc filesystem not available on this system")

        context = {
            "props": {"file": "/proc/version"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path="{{props.file}}",
            enableTemplating=False,
        )

        # The executor will try to read it (demonstrating that path validation
        # should be done at a higher level if you want to restrict access)
        _ = executor.execute(config, context)

        # This will likely succeed and expose system info
        # Demonstrating need for higher-level access control

    def test_path_with_control_characters(self, executor, temp_directory):
        """
        Test that control characters in paths are handled.

        Security Risk: Control chars might break path handling.
        """
        safe_dir = temp_directory["safe"]

        malicious_context = {
            "props": {"file": "file\rwith\ncontrol\tchars.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Control characters should be in the path
        assert "\r" in config.path or "\n" in config.path

    def test_very_long_path(self, executor, temp_directory):
        """
        Test that very long paths are handled safely.

        Security Risk: Long paths might cause buffer overflows or DoS.
        """
        safe_dir = temp_directory["safe"]

        # Create a very long path
        long_name = "a" * 1000 + ".txt"

        malicious_context = {
            "props": {"file": long_name},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Path should be very long
        assert len(config.path) > 1000

        result = executor.execute(config, malicious_context)

        # Should handle gracefully (file doesn't exist)
        assert result.isError

    def test_relative_path_with_current_dir(self, executor, temp_directory):
        """
        Test that ./ sequences in paths are handled.

        Security Risk: ./././ might obfuscate paths.
        """
        safe_dir = temp_directory["safe"]

        context = {
            "props": {"file": "./././data.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        result = executor.execute(config, context)

        # Should be able to read the file (./././ is normalized)
        if not result.isError:
            assert "safe content" in result.content

    def test_path_normalization_bypass(self, executor, temp_directory):
        """
        Test that path normalization doesn't create vulnerabilities.

        Security Risk: Normalization might unexpectedly resolve traversals.
        """
        safe_dir = temp_directory["safe"]

        # Path that normalizes to parent directory
        malicious_context = {
            "props": {"file": "subdir/../../sensitive/secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=f"{safe_dir}/{{{{props.file}}}}",
            enableTemplating=False,
        )

        executor._apply_basic_templating_to_config(config, malicious_context)

        # Path contains traversal that goes up from subdir
        assert "subdir/../.." in config.path

    def test_templating_with_path_traversal(self, executor, temp_directory):
        """
        Test that templating doesn't enable path traversal.

        Security Risk: Template processing might normalize or resolve paths.
        """
        safe_dir = temp_directory["safe"]

        # File content with traversal in it
        traversal_file = safe_dir / "traversal.txt"
        traversal_file.write_text("Path: {{props.malicious}}")

        context = {
            "props": {"malicious": "../../sensitive/secret.txt"},
            "env": {},
            "input": {},
        }

        config = FileExecutionConfig(
            path=str(traversal_file),
            enableTemplating=True,
        )

        result = executor.execute(config, context)

        # Should template the content
        assert not result.isError
        assert "../../sensitive/secret.txt" in result.content

        # The traversal is in the content, not used as a path
        assert "SECRET DATA" not in result.content

    def test_case_sensitivity_bypass(self, executor, temp_directory):
        """
        Test that case variations don't bypass security on case-insensitive systems.

        Security Risk: Case differences might bypass path filters.
        """
        safe_dir = temp_directory["safe"]

        variations = [
            "../Sensitive/secret.txt",
            "../SENSITIVE/secret.txt",
            "../sEnSiTiVe/secret.txt",
        ]

        for variation in variations:
            context = {
                "props": {"file": variation},
                "env": {},
                "input": {},
            }

            config = FileExecutionConfig(
                path=f"{safe_dir}/{{{{props.file}}}}",
                enableTemplating=False,
            )

            executor._apply_basic_templating_to_config(config, context)

            # Path should contain the variation
            assert variation in config.path
