"""
Unit tests for MCIClient.executeSeparated method.

Tests the executeSeparated method which allows executing Tool models directly
without requiring them to be registered in the tool registry.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcipy import MCIClient, MCIClientError
from mcipy.models import (
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    TextExecutionConfig,
    Tool,
)


class TestExecuteSeparatedBasic:
    """Basic tests for executeSeparated method."""

    @pytest.fixture
    def minimal_schema_file(self):
        """Create a minimal schema file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"schemaVersion": "1.0", "tools": []}')
            return f.name

    def test_execute_separated_with_text_execution(self, minimal_schema_file):
        """Test executeSeparated with a simple text execution tool."""
        client = MCIClient(schema_file_path=minimal_schema_file)

        # Create a dynamic tool
        tool = Tool(
            name="test_greeting",
            description="Generate a greeting",
            execution=TextExecutionConfig(
                type="text", text="Hello {{props.name}}!"
            ),
        )

        # Execute the tool
        result = client.executeSeparated(
            tool=tool, properties={"name": "Alice"}, env_vars={}
        )

        # Verify result
        assert result is not None
        assert result.result.isError is False
        assert len(result.result.content) == 1
        assert result.result.content[0].text == "Hello Alice!"

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_with_env_vars(self, minimal_schema_file):
        """Test executeSeparated with environment variable substitution."""
        client = MCIClient(
            schema_file_path=minimal_schema_file,
            env_vars={"DEFAULT_LOCATION": "World"},
        )

        # Create a tool using both props and env
        tool = Tool(
            name="test_greeting",
            execution=TextExecutionConfig(
                type="text",
                text="Hello {{props.name}} from {{env.LOCATION}}!",
            ),
        )

        # Execute with custom env_vars
        result = client.executeSeparated(
            tool=tool,
            properties={"name": "Bob"},
            env_vars={"LOCATION": "NYC"},
        )

        assert result.result.content[0].text == "Hello Bob from NYC!"

        # Execute with client's env_vars (env_vars=None)
        result = client.executeSeparated(
            tool=tool,
            properties={"name": "Charlie"},
            env_vars={"LOCATION": "World"},
        )

        assert result.result.content[0].text == "Hello Charlie from World!"

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_uses_client_env_vars_when_none(
        self, minimal_schema_file
    ):
        """Test that executeSeparated uses client's env_vars when env_vars param is None."""
        client = MCIClient(
            schema_file_path=minimal_schema_file,
            env_vars={"API_KEY": "client-key-123"},
        )

        tool = Tool(
            name="test_tool",
            execution=TextExecutionConfig(
                type="text", text="Key: {{env.API_KEY}}"
            ),
        )

        # Call with env_vars=None should use client's env_vars
        result = client.executeSeparated(tool=tool, properties={}, env_vars=None)

        assert result.result.content[0].text == "Key: client-key-123"

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_with_no_properties(self, minimal_schema_file):
        """Test executeSeparated with no properties required."""
        client = MCIClient(schema_file_path=minimal_schema_file)

        tool = Tool(
            name="simple_tool",
            execution=TextExecutionConfig(type="text", text="Static message"),
        )

        # Execute without properties
        result = client.executeSeparated(tool=tool)

        assert result.result.content[0].text == "Static message"

        # Execute with None properties
        result = client.executeSeparated(tool=tool, properties=None)

        assert result.result.content[0].text == "Static message"

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_with_input_schema_validation(
        self, minimal_schema_file
    ):
        """Test that executeSeparated validates input schema."""
        client = MCIClient(schema_file_path=minimal_schema_file)

        # Create a tool with required properties
        tool = Tool(
            name="test_tool",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            execution=TextExecutionConfig(
                type="text", text="Hello {{props.name}}!"
            ),
        )

        # Test with missing required property
        with pytest.raises(MCIClientError) as exc_info:
            client.executeSeparated(tool=tool, properties={})

        assert "requires properties" in str(exc_info.value).lower()
        assert "name" in str(exc_info.value).lower()

        # Test with valid properties
        result = client.executeSeparated(tool=tool, properties={"name": "Alice"})
        assert result.result.content[0].text == "Hello Alice!"

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_with_default_values(self, minimal_schema_file):
        """Test that executeSeparated applies default values from input schema."""
        client = MCIClient(schema_file_path=minimal_schema_file)

        tool = Tool(
            name="test_tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "greeting": {"type": "string", "default": "Hi"},
                },
                "required": ["name"],
            },
            execution=TextExecutionConfig(
                type="text", text="{{props.greeting}} {{props.name}}!"
            ),
        )

        # Execute without optional property - should use default
        result = client.executeSeparated(tool=tool, properties={"name": "Alice"})
        assert result.result.content[0].text == "Hi Alice!"

        # Execute with optional property - should override default
        result = client.executeSeparated(
            tool=tool, properties={"name": "Bob", "greeting": "Hello"}
        )
        assert result.result.content[0].text == "Hello Bob!"

        # Cleanup
        Path(minimal_schema_file).unlink()


class TestExecuteSeparatedValidation:
    """Tests for validation and error handling in executeSeparated."""

    @pytest.fixture
    def minimal_schema_file(self):
        """Create a minimal schema file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"schemaVersion": "1.0", "tools": []}')
            return f.name

    def test_execute_separated_blocked_in_client_validating_mode(
        self, minimal_schema_file
    ):
        """Test that executeSeparated is blocked when client is in validating mode."""
        client = MCIClient(schema_file_path=minimal_schema_file, validating=True)

        tool = Tool(
            name="test_tool",
            execution=TextExecutionConfig(type="text", text="Hello"),
        )

        with pytest.raises(MCIClientError) as exc_info:
            client.executeSeparated(tool=tool)

        assert "validating mode" in str(exc_info.value).lower()

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_blocked_with_method_validating_flag(
        self, minimal_schema_file
    ):
        """Test that executeSeparated is blocked when validating=True parameter is passed."""
        client = MCIClient(
            schema_file_path=minimal_schema_file, validating=False
        )

        tool = Tool(
            name="test_tool",
            execution=TextExecutionConfig(type="text", text="Hello"),
        )

        with pytest.raises(MCIClientError) as exc_info:
            client.executeSeparated(tool=tool, validating=True)

        assert "validating mode" in str(exc_info.value).lower()

        # Cleanup
        Path(minimal_schema_file).unlink()


class TestExecuteSeparatedWithDifferentExecutors:
    """Tests for executeSeparated with different executor types."""

    @pytest.fixture
    def minimal_schema_file(self):
        """Create a minimal schema file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"schemaVersion": "1.0", "tools": []}')
            return f.name

    def test_execute_separated_with_cli_executor(self, minimal_schema_file):
        """Test executeSeparated with CLI executor."""
        client = MCIClient(schema_file_path=minimal_schema_file)

        tool = Tool(
            name="echo_tool",
            execution=CLIExecutionConfig(
                type="cli", command="echo", args=["{{props.message}}"]
            ),
        )

        result = client.executeSeparated(
            tool=tool, properties={"message": "Hello CLI"}
        )

        assert result is not None
        assert result.result.isError is False
        assert "Hello CLI" in result.result.content[0].text

        # Cleanup
        Path(minimal_schema_file).unlink()

    def test_execute_separated_with_file_executor(self, minimal_schema_file):
        """Test executeSeparated with File executor."""
        # Create a test file with content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as test_file:
            test_file.write("File content: {{props.value}}")
            test_file_path = test_file.name

        client = MCIClient(schema_file_path=minimal_schema_file)

        tool = Tool(
            name="read_file_tool",
            execution=FileExecutionConfig(
                type="file", path=test_file_path, enableTemplating=True
            ),
        )

        result = client.executeSeparated(
            tool=tool, properties={"value": "test123"}
        )

        assert result is not None
        assert result.result.isError is False
        assert "File content: test123" in result.result.content[0].text

        # Cleanup
        Path(test_file_path).unlink()
        Path(minimal_schema_file).unlink()

    @patch("mcipy.executors.http_executor.requests.request")
    def test_execute_separated_with_http_executor(
        self, mock_request, minimal_schema_file
    ):
        """Test executeSeparated with HTTP executor."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {"content-type": "application/json"}
        mock_request.return_value = mock_response

        client = MCIClient(schema_file_path=minimal_schema_file)

        tool = Tool(
            name="http_tool",
            execution=HTTPExecutionConfig(
                type="http",
                method="GET",
                url="https://api.example.com/data",
                params={"id": "{{props.item_id}}"},
            ),
        )

        result = client.executeSeparated(
            tool=tool, properties={"item_id": "123"}
        )

        assert result is not None
        assert result.result.isError is False

        # Verify the request was made with correct params
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["params"]["id"] == "123"

        # Cleanup
        Path(minimal_schema_file).unlink()


class TestExecuteSeparatedIsolation:
    """Tests to verify that executeSeparated doesn't affect the tool registry."""

    @pytest.fixture
    def schema_with_tools(self):
        """Create a schema file with some tools."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(
                """{
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "registered_tool",
                        "execution": {
                            "type": "text",
                            "text": "Registered tool output"
                        }
                    }
                ]
            }"""
            )
            return f.name

    def test_execute_separated_does_not_register_tool(self, schema_with_tools):
        """Test that executeSeparated doesn't add tool to registry."""
        client = MCIClient(schema_file_path=schema_with_tools)

        # Verify initial tool list
        initial_tools = client.list_tools()
        assert initial_tools == ["registered_tool"]

        # Execute a dynamic tool
        dynamic_tool = Tool(
            name="dynamic_tool",
            execution=TextExecutionConfig(type="text", text="Dynamic output"),
        )

        result = client.executeSeparated(tool=dynamic_tool)
        assert result.result.content[0].text == "Dynamic output"

        # Verify tool list hasn't changed
        final_tools = client.list_tools()
        assert final_tools == ["registered_tool"]
        assert "dynamic_tool" not in final_tools

        # Cleanup
        Path(schema_with_tools).unlink()

    def test_execute_separated_with_same_name_as_registered_tool(
        self, schema_with_tools
    ):
        """Test that executeSeparated can execute a tool with same name as registered tool."""
        client = MCIClient(schema_file_path=schema_with_tools)

        # Create a tool with same name but different config
        override_tool = Tool(
            name="registered_tool",
            execution=TextExecutionConfig(
                type="text", text="Override tool output"
            ),
        )

        # Execute the override tool
        result = client.executeSeparated(tool=override_tool)
        assert result.result.content[0].text == "Override tool output"

        # Verify the registered tool is unaffected
        result = client.execute("registered_tool")
        assert result.result.content[0].text == "Registered tool output"

        # Cleanup
        Path(schema_with_tools).unlink()

    def test_execute_separated_independent_env_vars(self, schema_with_tools):
        """Test that executeSeparated env_vars don't affect client env_vars."""
        client = MCIClient(
            schema_file_path=schema_with_tools,
            env_vars={"KEY": "client_value"},
        )

        tool = Tool(
            name="test_tool",
            execution=TextExecutionConfig(type="text", text="{{env.KEY}}"),
        )

        # Execute with different env_vars
        result = client.executeSeparated(
            tool=tool, env_vars={"KEY": "separated_value"}
        )
        assert result.result.content[0].text == "separated_value"

        # Verify client's env_vars are unchanged
        # Execute using client's env_vars
        result = client.executeSeparated(tool=tool, env_vars=None)
        assert result.result.content[0].text == "client_value"

        # Cleanup
        Path(schema_with_tools).unlink()
