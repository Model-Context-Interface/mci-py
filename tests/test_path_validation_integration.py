"""Integration tests for path validation in tool execution."""

import tempfile
from pathlib import Path

import pytest

from mcipy import MCIClient


class TestFileExecutorPathValidation:
    """Integration tests for file executor path validation."""

    @pytest.fixture
    def temp_schema_dir(self):
        """Fixture for a temporary directory with schema file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def schema_with_file_tool(self, temp_schema_dir):
        """Fixture for a schema file with file execution tool."""
        # Create a test file in the schema directory
        test_file = temp_schema_dir / "test.txt"
        test_file.write_text("Hello {{props.name}}!")

        # Create schema - use absolute path since file paths are resolved from CWD
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "read_file",
                    "execution": {
                        "type": "file",
                        "path": str(test_file),  # Use absolute path
                        "enableTemplating": True,
                    },
                }
            ],
        }

        schema_file = temp_schema_dir / "schema.json"
        import json

        schema_file.write_text(json.dumps(schema))
        return schema_file

    @pytest.fixture
    def schema_with_file_tool_outside_context(self, temp_schema_dir):
        """Fixture for a schema file with file execution tool referencing outside path."""
        # Create a test file OUTSIDE the schema directory
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Outside content")
            outside_file = Path(f.name)

        # Create schema
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "read_outside_file",
                    "execution": {
                        "type": "file",
                        "path": str(outside_file),
                        "enableTemplating": False,
                    },
                }
            ],
        }

        schema_file = temp_schema_dir / "schema.json"
        import json

        schema_file.write_text(json.dumps(schema))

        yield schema_file, outside_file

        # Cleanup
        outside_file.unlink(missing_ok=True)

    def test_file_executor_allows_context_dir(self, schema_with_file_tool):
        """Test that file executor allows access to files in context directory."""
        client = MCIClient(schema_file_path=str(schema_with_file_tool))
        result = client.execute("read_file", {"name": "World"})

        assert result.result.isError is False
        assert result.result.content[0].text == "Hello World!"

    def test_file_executor_blocks_outside_context(self, schema_with_file_tool_outside_context):
        """Test that file executor blocks access to files outside context directory."""
        schema_file, _outside_file = schema_with_file_tool_outside_context
        client = MCIClient(schema_file_path=str(schema_file))

        result = client.execute("read_outside_file")

        assert result.result.isError is True
        assert (
            result.result.content[0].text is not None
            and "File path access outside context directory" in result.result.content[0].text
        )

    def test_file_executor_allows_with_enable_any_paths_tool_level(
        self, schema_with_file_tool_outside_context
    ):
        """Test that file executor allows any path when tool has enableAnyPaths=True."""
        schema_file, _outside_file = schema_with_file_tool_outside_context

        # Update schema to add enableAnyPaths at tool level
        import json

        schema = json.loads(schema_file.read_text())
        schema["tools"][0]["enableAnyPaths"] = True
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))
        result = client.execute("read_outside_file")

        assert result.result.isError is False
        assert result.result.content[0].text == "Outside content"

    def test_file_executor_allows_with_enable_any_paths_schema_level(
        self, schema_with_file_tool_outside_context
    ):
        """Test that file executor allows any path when schema has enableAnyPaths=True."""
        schema_file, _outside_file = schema_with_file_tool_outside_context

        # Update schema to add enableAnyPaths at schema level
        import json

        schema = json.loads(schema_file.read_text())
        schema["enableAnyPaths"] = True
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))
        result = client.execute("read_outside_file")

        assert result.result.isError is False
        assert result.result.content[0].text == "Outside content"

    def test_file_executor_allows_with_directory_allow_list(
        self, schema_with_file_tool_outside_context
    ):
        """Test that file executor allows paths in directoryAllowList."""
        schema_file, outside_file = schema_with_file_tool_outside_context

        # Update schema to add directory to allow list
        import json

        schema = json.loads(schema_file.read_text())
        schema["tools"][0]["directoryAllowList"] = [str(outside_file.parent)]
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))
        result = client.execute("read_outside_file")

        assert result.result.isError is False
        assert result.result.content[0].text == "Outside content"

    def test_file_executor_allows_subdirectories(self, temp_schema_dir):
        """Test that file executor allows access to subdirectories of context."""
        # Create a subdirectory with a file
        subdir = temp_schema_dir / "sub" / "deep"
        subdir.mkdir(parents=True)
        test_file = subdir / "test.txt"
        test_file.write_text("Deep content")

        # Create schema - use absolute path
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "read_deep_file",
                    "execution": {
                        "type": "file",
                        "path": str(test_file),  # Use absolute path
                        "enableTemplating": False,
                    },
                }
            ],
        }

        schema_file = temp_schema_dir / "schema.json"
        import json

        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))
        result = client.execute("read_deep_file")

        assert result.result.isError is False
        assert result.result.content[0].text == "Deep content"


class TestCLIExecutorPathValidation:
    """Integration tests for CLI executor path validation."""

    @pytest.fixture
    def temp_schema_dir(self):
        """Fixture for a temporary directory with schema file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_cli_executor_allows_context_dir_cwd(self, temp_schema_dir):
        """Test that CLI executor allows cwd in context directory."""
        # Create a test file in the schema directory
        test_file = temp_schema_dir / "test.txt"
        test_file.write_text("test content")

        # Create schema with CLI tool using absolute path for cwd
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "list_files",
                    "execution": {"type": "cli", "command": "ls", "cwd": str(temp_schema_dir)},
                }
            ],
        }

        schema_file = temp_schema_dir / "schema.json"
        import json

        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))
        result = client.execute("list_files")

        # Should succeed and list files
        assert result.result.isError is False
        assert result.result.content[0].text is not None and "test.txt" in result.result.content[0].text

    def test_cli_executor_blocks_outside_context_cwd(self, temp_schema_dir):
        """Test that CLI executor blocks cwd outside context directory."""
        # Create schema with CLI tool using outside directory as cwd
        with tempfile.TemporaryDirectory() as outside_dir:
            schema = {
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "list_outside",
                        "execution": {"type": "cli", "command": "ls", "cwd": str(outside_dir)},
                    }
                ],
            }

            schema_file = temp_schema_dir / "schema.json"
            import json

            schema_file.write_text(json.dumps(schema))

            client = MCIClient(schema_file_path=str(schema_file))
            result = client.execute("list_outside")

            assert result.result.isError is True
            assert (
                result.result.content[0].text is not None
                and "File path access outside context directory" in result.result.content[0].text
            )

    def test_cli_executor_allows_with_enable_any_paths(self, temp_schema_dir):
        """Test that CLI executor allows any cwd when enableAnyPaths=True."""
        with tempfile.TemporaryDirectory() as outside_dir:
            # Create a test file in outside directory
            test_file = Path(outside_dir) / "outside.txt"
            test_file.write_text("outside")

            # Create schema with enableAnyPaths at tool level
            schema = {
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "list_outside",
                        "execution": {"type": "cli", "command": "ls", "cwd": str(outside_dir)},
                        "enableAnyPaths": True,
                    }
                ],
            }

            schema_file = temp_schema_dir / "schema.json"
            import json

            schema_file.write_text(json.dumps(schema))

            client = MCIClient(schema_file_path=str(schema_file))
            result = client.execute("list_outside")

            assert result.result.isError is False
            assert result.result.content[0].text is not None and "outside.txt" in result.result.content[0].text

    def test_cli_executor_allows_with_directory_allow_list(self, temp_schema_dir):
        """Test that CLI executor allows cwd in directoryAllowList."""
        with tempfile.TemporaryDirectory() as allowed_dir:
            # Create a test file in allowed directory
            test_file = Path(allowed_dir) / "allowed.txt"
            test_file.write_text("allowed")

            # Create schema with allowed directory
            schema = {
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "list_allowed",
                        "execution": {"type": "cli", "command": "ls", "cwd": str(allowed_dir)},
                        "directoryAllowList": [str(allowed_dir)],
                    }
                ],
            }

            schema_file = temp_schema_dir / "schema.json"
            import json

            schema_file.write_text(json.dumps(schema))

            client = MCIClient(schema_file_path=str(schema_file))
            result = client.execute("list_allowed")

            assert result.result.isError is False
            assert result.result.content[0].text is not None and "allowed.txt" in result.result.content[0].text

    def test_cli_executor_no_cwd_specified(self, temp_schema_dir):
        """Test that CLI executor works when no cwd is specified."""
        # Create schema with CLI tool without cwd
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "echo_test",
                    "execution": {"type": "cli", "command": "echo", "args": ["hello"]},
                }
            ],
        }

        schema_file = temp_schema_dir / "schema.json"
        import json

        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))
        result = client.execute("echo_test")

        # Should succeed - no path validation needed
        assert result.result.isError is False
        assert result.result.content[0].text is not None and "hello" in result.result.content[0].text
