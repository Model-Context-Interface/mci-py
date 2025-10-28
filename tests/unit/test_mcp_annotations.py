"""Unit tests for MCP annotation handling and conversion to tags."""

from unittest.mock import MagicMock

import pytest

from mcipy.mcp_integration import MCPIntegration
from mcipy.models import Annotations


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
