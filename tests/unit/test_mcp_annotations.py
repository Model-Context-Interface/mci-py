"""Unit tests for MCP annotation handling and conversion to tags."""

from unittest.mock import MagicMock

import pytest

from mcipy.enums import ExecutionType
from mcipy.mcp_integration import MCPIntegration
from mcipy.models import Annotations, MCPExecutionConfig, Tool


class TestAnnotationsToTags:
    """Tests for converting MCP annotations to tags."""

    def test_annotations_to_tags_none(self):
        """Test that None annotations return empty tag list."""
        tags = MCPIntegration._annotations_to_tags(None)
        assert tags == []

    def test_annotations_to_tags_empty(self):
        """Test that empty annotations return empty tag list."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = None
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = None

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == []

    def test_annotations_to_tags_readonly(self):
        """Test that readOnlyHint=True creates IsReadOnly tag."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = True
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = None

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == ["IsReadOnly"]

    def test_annotations_to_tags_destructive(self):
        """Test that destructiveHint=True creates IsDestructive tag."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = None
        mock_annotations.destructiveHint = True
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = None

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == ["IsDestructive"]

    def test_annotations_to_tags_idempotent(self):
        """Test that idempotentHint=True creates IsIdempotent tag."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = None
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = True
        mock_annotations.openWorldHint = None

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == ["IsIdempotent"]

    def test_annotations_to_tags_openworld(self):
        """Test that openWorldHint=True creates IsOpenWorld tag."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = None
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = True

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == ["IsOpenWorld"]

    def test_annotations_to_tags_multiple(self):
        """Test that multiple boolean annotations create multiple tags."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = True
        mock_annotations.destructiveHint = False
        mock_annotations.idempotentHint = True
        mock_annotations.openWorldHint = True

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        # Should have tags for all True annotations
        assert "IsReadOnly" in tags
        assert "IsIdempotent" in tags
        assert "IsOpenWorld" in tags
        assert "IsDestructive" not in tags
        assert len(tags) == 3

    def test_annotations_to_tags_all_true(self):
        """Test that all boolean annotations create all tags."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = True
        mock_annotations.destructiveHint = True
        mock_annotations.idempotentHint = True
        mock_annotations.openWorldHint = True

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert "IsReadOnly" in tags
        assert "IsDestructive" in tags
        assert "IsIdempotent" in tags
        assert "IsOpenWorld" in tags
        assert len(tags) == 4

    def test_annotations_to_tags_false_values(self):
        """Test that False values don't create tags."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = False
        mock_annotations.destructiveHint = False
        mock_annotations.idempotentHint = False
        mock_annotations.openWorldHint = False

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == []

    def test_annotations_to_tags_with_audience(self):
        """Test that audience annotations are converted to tags with audience_ prefix."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = None
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = None
        mock_annotations.audience = ["user", "assistant"]

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert "audience_user" in tags
        assert "audience_assistant" in tags
        assert len(tags) == 2

    def test_annotations_to_tags_with_single_audience(self):
        """Test that single audience annotation is converted to tag."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = None
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = None
        mock_annotations.audience = ["user"]

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == ["audience_user"]

    def test_annotations_to_tags_combined_boolean_and_audience(self):
        """Test that boolean annotations and audience are both converted to tags."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = True
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = True
        mock_annotations.openWorldHint = None
        mock_annotations.audience = ["user"]

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert "IsReadOnly" in tags
        assert "IsIdempotent" in tags
        assert "audience_user" in tags
        assert len(tags) == 3

    def test_annotations_to_tags_no_audience_attribute(self):
        """Test that missing audience attribute doesn't cause errors."""
        mock_annotations = MagicMock()
        mock_annotations.readOnlyHint = True
        mock_annotations.destructiveHint = None
        mock_annotations.idempotentHint = None
        mock_annotations.openWorldHint = None
        # Don't set audience attribute
        del mock_annotations.audience

        tags = MCPIntegration._annotations_to_tags(mock_annotations)
        assert tags == ["IsReadOnly"]


class TestAnnotationsModel:
    """Tests for the Annotations model with audience field."""

    def test_annotations_with_audience(self):
        """Test that Annotations model accepts audience field."""
        annotations = Annotations(
            title="Test Tool",
            readOnlyHint=True,
            audience=["user", "assistant"],
        )
        assert annotations.audience == ["user", "assistant"]
        assert annotations.readOnlyHint is True
        assert annotations.title == "Test Tool"

    def test_annotations_without_audience(self):
        """Test that Annotations model works without audience field."""
        annotations = Annotations(
            title="Test Tool",
            readOnlyHint=True,
        )
        assert annotations.audience is None
        assert annotations.readOnlyHint is True

    def test_annotations_audience_validation(self):
        """Test that audience field validates role literals."""
        # Valid roles should work
        annotations = Annotations(audience=["user", "assistant"])
        assert annotations.audience == ["user", "assistant"]

        # Test with only user
        annotations = Annotations(audience=["user"])
        assert annotations.audience == ["user"]

        # Test with only assistant
        annotations = Annotations(audience=["assistant"])
        assert annotations.audience == ["assistant"]

    def test_annotations_empty_audience(self):
        """Test that empty audience list is accepted."""
        annotations = Annotations(audience=[])
        assert annotations.audience == []

    def test_annotations_all_fields(self):
        """Test that all annotation fields work together."""
        annotations = Annotations(
            title="Complete Tool",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
            audience=["user"],
        )
        assert annotations.title == "Complete Tool"
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is True
        assert annotations.openWorldHint is False
        assert annotations.audience == ["user"]


class TestMCPToolIntegration:
    """Integration tests for MCP tool annotation capture and tag conversion."""

    def test_mcp_tool_with_all_annotations(self):
        """Test that MCP tool annotations are properly captured and converted to tags."""
        # Create a mock MCP tool with all annotations
        mock_mcp_tool = MagicMock()
        mock_mcp_tool.name = "test_tool"
        mock_mcp_tool.description = "Test tool with all annotations"
        mock_mcp_tool.inputSchema = {"type": "object", "properties": {}}
        mock_mcp_tool.annotations = MagicMock()
        mock_mcp_tool.annotations.title = "Test Tool Title"
        mock_mcp_tool.annotations.readOnlyHint = True
        mock_mcp_tool.annotations.destructiveHint = False
        mock_mcp_tool.annotations.idempotentHint = True
        mock_mcp_tool.annotations.openWorldHint = True

        # Simulate annotation capture (what happens in mcp_integration.py)
        annotations = Annotations()
        annotations.title = mock_mcp_tool.annotations.title
        annotations.readOnlyHint = mock_mcp_tool.annotations.readOnlyHint
        annotations.destructiveHint = mock_mcp_tool.annotations.destructiveHint
        annotations.idempotentHint = mock_mcp_tool.annotations.idempotentHint
        annotations.openWorldHint = mock_mcp_tool.annotations.openWorldHint

        # Convert annotations to tags
        tags = MCPIntegration._annotations_to_tags(mock_mcp_tool.annotations)

        # Create MCI tool with annotations and tags
        mci_tool = Tool(
            name=mock_mcp_tool.name,
            description=mock_mcp_tool.description,
            annotations=annotations,
            inputSchema=mock_mcp_tool.inputSchema,
            tags=tags,
            execution=MCPExecutionConfig(
                type=ExecutionType.MCP,
                serverName="test-server",
                toolName=mock_mcp_tool.name,
            ),
        )

        # Verify annotations are captured
        assert mci_tool.annotations.title == "Test Tool Title"
        assert mci_tool.annotations.readOnlyHint is True
        assert mci_tool.annotations.destructiveHint is False
        assert mci_tool.annotations.idempotentHint is True
        assert mci_tool.annotations.openWorldHint is True

        # Verify tags are created from annotations
        assert "IsReadOnly" in mci_tool.tags
        assert "IsIdempotent" in mci_tool.tags
        assert "IsOpenWorld" in mci_tool.tags
        assert "IsDestructive" not in mci_tool.tags
        assert len(mci_tool.tags) == 3

    def test_mcp_tool_with_no_annotations(self):
        """Test that MCP tool without annotations creates empty annotations and no tags."""
        # Create a mock MCP tool without annotations
        mock_mcp_tool = MagicMock()
        mock_mcp_tool.name = "simple_tool"
        mock_mcp_tool.description = "Simple tool without annotations"
        mock_mcp_tool.inputSchema = {"type": "object", "properties": {}}
        mock_mcp_tool.annotations = None

        # Simulate annotation capture
        annotations = Annotations()

        # Convert annotations to tags
        tags = MCPIntegration._annotations_to_tags(mock_mcp_tool.annotations)

        # Create MCI tool
        mci_tool = Tool(
            name=mock_mcp_tool.name,
            description=mock_mcp_tool.description,
            annotations=annotations,
            inputSchema=mock_mcp_tool.inputSchema,
            tags=tags,
            execution=MCPExecutionConfig(
                type=ExecutionType.MCP,
                serverName="test-server",
                toolName=mock_mcp_tool.name,
            ),
        )

        # Verify empty annotations
        assert mci_tool.annotations.title is None
        assert mci_tool.annotations.readOnlyHint is None
        assert mci_tool.annotations.destructiveHint is None
        assert mci_tool.annotations.idempotentHint is None
        assert mci_tool.annotations.openWorldHint is None

        # Verify no tags created
        assert mci_tool.tags == []

    def test_mcp_tool_with_audience(self):
        """Test that MCP tool with audience annotation creates audience tags."""
        # Create a mock MCP tool with audience
        mock_mcp_tool = MagicMock()
        mock_mcp_tool.name = "audience_tool"
        mock_mcp_tool.description = "Tool with audience"
        mock_mcp_tool.inputSchema = {"type": "object", "properties": {}}
        mock_mcp_tool.annotations = MagicMock()
        mock_mcp_tool.annotations.title = None
        mock_mcp_tool.annotations.readOnlyHint = True
        mock_mcp_tool.annotations.destructiveHint = None
        mock_mcp_tool.annotations.idempotentHint = None
        mock_mcp_tool.annotations.openWorldHint = None
        mock_mcp_tool.annotations.audience = ["user", "assistant"]

        # Simulate annotation capture
        annotations = Annotations()
        annotations.readOnlyHint = mock_mcp_tool.annotations.readOnlyHint
        annotations.audience = mock_mcp_tool.annotations.audience

        # Convert annotations to tags
        tags = MCPIntegration._annotations_to_tags(mock_mcp_tool.annotations)

        # Create MCI tool
        mci_tool = Tool(
            name=mock_mcp_tool.name,
            description=mock_mcp_tool.description,
            annotations=annotations,
            inputSchema=mock_mcp_tool.inputSchema,
            tags=tags,
            execution=MCPExecutionConfig(
                type=ExecutionType.MCP,
                serverName="test-server",
                toolName=mock_mcp_tool.name,
            ),
        )

        # Verify annotations
        assert mci_tool.annotations.readOnlyHint is True
        assert mci_tool.annotations.audience == ["user", "assistant"]

        # Verify tags include both boolean and audience tags
        assert "IsReadOnly" in mci_tool.tags
        assert "audience_user" in mci_tool.tags
        assert "audience_assistant" in mci_tool.tags
        assert len(mci_tool.tags) == 3

