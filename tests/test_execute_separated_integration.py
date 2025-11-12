"""
Integration test for executeSeparated method with existing MCIClient features.

This test verifies that executeSeparated works well alongside existing
MCIClient methods and doesn't interfere with normal operation.
"""

import tempfile
from pathlib import Path

import pytest

from mcipy import MCIClient
from mcipy.models import TextExecutionConfig, Tool


class TestExecuteSeparatedIntegration:
    """Integration tests for executeSeparated with existing features."""

    @pytest.fixture
    def test_schema(self):
        """Create a test schema file with some tools."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(
                """{
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "registered_tool_1",
                        "description": "First registered tool",
                        "execution": {
                            "type": "text",
                            "text": "Output from registered_tool_1: {{props.value}}"
                        }
                    },
                    {
                        "name": "registered_tool_2",
                        "description": "Second registered tool",
                        "execution": {
                            "type": "text",
                            "text": "Output from registered_tool_2: {{env.KEY}}"
                        }
                    }
                ]
            }"""
            )
            schema_path = f.name

        # File is now closed and flushed
        yield schema_path

        # Cleanup after tests
        Path(schema_path).unlink()

    def test_execute_and_execute_separated_work_together(self, test_schema):
        """Test that execute and executeSeparated can be used together."""
        client = MCIClient(
            schema_file_path=test_schema, env_vars={"KEY": "client-value"}
        )

        # Execute a registered tool
        result1 = client.execute(
            "registered_tool_1", properties={"value": "from execute"}
        )
        assert "Output from registered_tool_1: from execute" in result1.result.content[0].text

        # Execute a dynamic tool
        dynamic_tool = Tool(
            name="dynamic_tool",
            execution=TextExecutionConfig(
                type="text", text="Dynamic: {{props.msg}}"
            ),
        )
        result2 = client.executeSeparated(
            tool=dynamic_tool, properties={"msg": "from executeSeparated"}
        )
        assert "Dynamic: from executeSeparated" in result2.result.content[0].text

        # Execute another registered tool to verify nothing broke
        result3 = client.execute("registered_tool_2")
        assert "Output from registered_tool_2: client-value" in result3.result.content[0].text

    def test_filtering_not_affected_by_execute_separated(self, test_schema):
        """Test that executeSeparated doesn't affect filtering methods."""
        client = MCIClient(schema_file_path=test_schema)

        # Get initial filtered list
        filtered_before = client.only(["registered_tool_1"])
        assert len(filtered_before) == 1
        assert filtered_before[0].name == "registered_tool_1"

        # Execute a dynamic tool
        dynamic_tool = Tool(
            name="dynamic_tool",
            execution=TextExecutionConfig(type="text", text="test"),
        )
        client.executeSeparated(tool=dynamic_tool)

        # Verify filtering still works the same
        filtered_after = client.only(["registered_tool_1"])
        assert len(filtered_after) == 1
        assert filtered_after[0].name == "registered_tool_1"

        # Verify without() also works
        without_result = client.without(["registered_tool_1"])
        assert len(without_result) == 1
        assert without_result[0].name == "registered_tool_2"

    def test_list_tools_not_affected_by_execute_separated(self, test_schema):
        """Test that list_tools() is not affected by executeSeparated."""
        client = MCIClient(schema_file_path=test_schema)

        # Get initial tool list
        tools_before = client.list_tools()
        assert set(tools_before) == {"registered_tool_1", "registered_tool_2"}

        # Execute multiple dynamic tools
        for i in range(5):
            tool = Tool(
                name=f"dynamic_tool_{i}",
                execution=TextExecutionConfig(type="text", text=f"Tool {i}"),
            )
            client.executeSeparated(tool=tool)

        # Verify tool list unchanged
        tools_after = client.list_tools()
        assert set(tools_after) == {"registered_tool_1", "registered_tool_2"}
        assert tools_before == tools_after

    def test_execute_separated_respects_client_env_vars(self, test_schema):
        """Test that executeSeparated properly uses client env_vars when None."""
        client = MCIClient(
            schema_file_path=test_schema,
            env_vars={"KEY1": "value1", "KEY2": "value2"},
        )

        tool = Tool(
            name="env_tool",
            execution=TextExecutionConfig(
                type="text", text="{{env.KEY1}} - {{env.KEY2}}"
            ),
        )

        # Should use client's env_vars
        result = client.executeSeparated(tool=tool, env_vars=None)
        assert result.result.content[0].text == "value1 - value2"

    def test_execute_separated_with_same_name_as_registered(self, test_schema):
        """Test executeSeparated with tool name same as registered tool."""
        client = MCIClient(schema_file_path=test_schema)

        # Create tool with same name but different behavior
        override_tool = Tool(
            name="registered_tool_1",
            execution=TextExecutionConfig(
                type="text", text="Override: {{props.data}}"
            ),
        )

        # Execute override tool
        result1 = client.executeSeparated(
            tool=override_tool, properties={"data": "custom"}
        )
        assert result1.result.content[0].text == "Override: custom"

        # Verify registered tool still works normally
        result2 = client.execute(
            "registered_tool_1", properties={"value": "normal"}
        )
        assert "Output from registered_tool_1: normal" in result2.result.content[0].text

    def test_multiple_clients_independent_execute_separated(self):
        """Test that executeSeparated on different clients is independent."""
        # Create two separate schema files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f1:
            f1.write('{"schemaVersion": "1.0", "tools": []}')
            schema1 = f1.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f2:
            f2.write('{"schemaVersion": "1.0", "tools": []}')
            schema2 = f2.name

        try:
            # Create two clients with different env vars
            client1 = MCIClient(
                schema_file_path=schema1, env_vars={"CLIENT": "one"}
            )
            client2 = MCIClient(
                schema_file_path=schema2, env_vars={"CLIENT": "two"}
            )

            tool = Tool(
                name="test_tool",
                execution=TextExecutionConfig(
                    type="text", text="Client: {{env.CLIENT}}"
                ),
            )

            # Execute on both clients
            result1 = client1.executeSeparated(tool=tool)
            result2 = client2.executeSeparated(tool=tool)

            # Verify they use their own env vars
            assert result1.result.content[0].text == "Client: one"
            assert result2.result.content[0].text == "Client: two"

        finally:
            Path(schema1).unlink()
            Path(schema2).unlink()
