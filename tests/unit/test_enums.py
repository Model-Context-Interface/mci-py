"""Unit tests for execution type enums."""

from mcipy.enums import ExecutionType


def test_execution_type_values():
    """Test that ExecutionType enum has correct string values."""
    assert ExecutionType.HTTP == "http"
    assert ExecutionType.CLI == "cli"
    assert ExecutionType.FILE == "file"
    assert ExecutionType.TEXT == "text"


def test_execution_type_is_string():
    """Test that ExecutionType values are strings."""
    assert isinstance(ExecutionType.HTTP.value, str)
    assert isinstance(ExecutionType.CLI.value, str)
    assert isinstance(ExecutionType.FILE.value, str)
    assert isinstance(ExecutionType.TEXT.value, str)


def test_execution_type_all_values():
    """Test that all expected execution types are present."""
    types = [e.value for e in ExecutionType]
    assert "http" in types
    assert "cli" in types
    assert "file" in types
    assert "text" in types
    assert len(types) == 4


def test_execution_type_from_string():
    """Test creating ExecutionType from string."""
    assert ExecutionType("http") == ExecutionType.HTTP
    assert ExecutionType("cli") == ExecutionType.CLI
    assert ExecutionType("file") == ExecutionType.FILE
    assert ExecutionType("text") == ExecutionType.TEXT


def test_execution_type_comparison():
    """Test that ExecutionType can be compared with strings."""
    assert ExecutionType.HTTP == "http"
    assert ExecutionType.CLI == "cli"
    assert ExecutionType.FILE == "file"
    assert ExecutionType.TEXT == "text"
