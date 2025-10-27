"""Unit tests for path validation module."""

import tempfile
from pathlib import Path

import pytest

from mcipy.path_validator import PathValidationError, PathValidator


class TestPathValidator:
    """Tests for PathValidator class."""

    @pytest.fixture
    def temp_context_dir(self):
        """Fixture for a temporary context directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def temp_file_in_context(self, temp_context_dir):
        """Fixture for a file inside the context directory."""
        test_file = temp_context_dir / "test.txt"
        test_file.write_text("test content")
        return test_file

    @pytest.fixture
    def temp_file_outside_context(self):
        """Fixture for a file outside the context directory."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("outside content")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink(missing_ok=True)

    def test_init_with_context_dir(self, temp_context_dir):
        """Test initializing validator with context directory."""
        validator = PathValidator(context_dir=temp_context_dir)
        assert validator.context_dir == temp_context_dir.resolve()
        assert validator.enable_any_paths is False
        assert len(validator.allowed_dirs) == 1
        assert validator.allowed_dirs[0] == temp_context_dir.resolve()

    def test_init_with_enable_any_paths(self, temp_context_dir):
        """Test initializing validator with enableAnyPaths=True."""
        validator = PathValidator(context_dir=temp_context_dir, enable_any_paths=True)
        assert validator.enable_any_paths is True

    def test_init_with_directory_allow_list_absolute(self, temp_context_dir):
        """Test initializing validator with absolute paths in allow list."""
        with tempfile.TemporaryDirectory() as allowed_dir:
            validator = PathValidator(
                context_dir=temp_context_dir, directory_allow_list=[allowed_dir]
            )
            assert len(validator.allowed_dirs) == 2
            assert temp_context_dir.resolve() in validator.allowed_dirs
            assert Path(allowed_dir).resolve() in validator.allowed_dirs

    def test_init_with_directory_allow_list_relative(self, temp_context_dir):
        """Test initializing validator with relative paths in allow list."""
        validator = PathValidator(
            context_dir=temp_context_dir, directory_allow_list=["subdir", "../sibling"]
        )
        assert len(validator.allowed_dirs) == 3
        assert temp_context_dir.resolve() in validator.allowed_dirs
        assert (temp_context_dir / "subdir").resolve() in validator.allowed_dirs
        assert (temp_context_dir / "../sibling").resolve() in validator.allowed_dirs

    def test_validate_path_in_context_dir(self, temp_context_dir, temp_file_in_context):
        """Test validating a path inside the context directory."""
        validator = PathValidator(context_dir=temp_context_dir)
        # Should not raise
        validator.validate_path(str(temp_file_in_context))

    def test_validate_path_outside_context_dir(self, temp_context_dir, temp_file_outside_context):
        """Test validating a path outside the context directory raises error."""
        validator = PathValidator(context_dir=temp_context_dir)
        with pytest.raises(PathValidationError, match="File path access outside context directory"):
            validator.validate_path(str(temp_file_outside_context))

    def test_validate_path_with_enable_any_paths(self, temp_context_dir, temp_file_outside_context):
        """Test validating any path when enableAnyPaths=True."""
        validator = PathValidator(context_dir=temp_context_dir, enable_any_paths=True)
        # Should not raise even for outside paths
        validator.validate_path(str(temp_file_outside_context))

    def test_validate_path_in_allowed_directory(self, temp_context_dir):
        """Test validating a path in an allowed directory."""
        with tempfile.TemporaryDirectory() as allowed_dir:
            allowed_path = Path(allowed_dir)
            test_file = allowed_path / "test.txt"
            test_file.write_text("allowed content")

            validator = PathValidator(
                context_dir=temp_context_dir, directory_allow_list=[str(allowed_path)]
            )

            # Should not raise
            validator.validate_path(str(test_file))

    def test_validate_path_in_subdirectory(self, temp_context_dir):
        """Test validating a path in a subdirectory of context."""
        subdir = temp_context_dir / "sub" / "deep"
        subdir.mkdir(parents=True)
        test_file = subdir / "test.txt"
        test_file.write_text("deep content")

        validator = PathValidator(context_dir=temp_context_dir)

        # Should not raise - subdirectories are allowed
        validator.validate_path(str(test_file))

    def test_validate_path_with_relative_path(self, temp_context_dir):
        """Test validating a relative path resolved from context directory."""
        test_file = temp_context_dir / "test.txt"
        test_file.write_text("content")

        validator = PathValidator(context_dir=temp_context_dir)

        # Use absolute path - relative paths get resolved relative to CWD
        # so they would only work if CWD is the context directory
        validator.validate_path(str(test_file))

    def test_merge_settings_tool_precedence_enable_any_paths(self):
        """Test that tool enableAnyPaths takes precedence over schema."""
        # Tool has enableAnyPaths=True, schema has False
        enable, allow_list = PathValidator.merge_settings(
            schema_enable_any_paths=False,
            schema_directory_allow_list=[],
            tool_enable_any_paths=True,
            tool_directory_allow_list=[],
        )
        assert enable is True
        assert allow_list == []

    def test_merge_settings_schema_enable_any_paths(self):
        """Test that schema enableAnyPaths is used when tool doesn't override."""
        # Schema has enableAnyPaths=True, tool has False
        enable, allow_list = PathValidator.merge_settings(
            schema_enable_any_paths=True,
            schema_directory_allow_list=[],
            tool_enable_any_paths=False,
            tool_directory_allow_list=[],
        )
        assert enable is True
        assert allow_list == []

    def test_merge_settings_tool_precedence_allow_list(self):
        """Test that tool directoryAllowList takes precedence over schema."""
        # Tool has non-empty list, schema has different list
        enable, allow_list = PathValidator.merge_settings(
            schema_enable_any_paths=False,
            schema_directory_allow_list=["/schema/dir"],
            tool_enable_any_paths=False,
            tool_directory_allow_list=["/tool/dir"],
        )
        assert enable is False
        assert allow_list == ["/tool/dir"]

    def test_merge_settings_schema_allow_list(self):
        """Test that schema directoryAllowList is used when tool has empty list."""
        # Tool has empty list, schema has list
        enable, allow_list = PathValidator.merge_settings(
            schema_enable_any_paths=False,
            schema_directory_allow_list=["/schema/dir"],
            tool_enable_any_paths=False,
            tool_directory_allow_list=[],
        )
        assert enable is False
        assert allow_list == ["/schema/dir"]

    def test_merge_settings_both_false(self):
        """Test merge when both schema and tool have default settings."""
        enable, allow_list = PathValidator.merge_settings(
            schema_enable_any_paths=False,
            schema_directory_allow_list=[],
            tool_enable_any_paths=False,
            tool_directory_allow_list=[],
        )
        assert enable is False
        assert allow_list == []

    def test_validate_nonexistent_path_allowed(self, temp_context_dir):
        """Test that validation allows nonexistent paths in context dir."""
        validator = PathValidator(context_dir=temp_context_dir)
        # Should not raise even if file doesn't exist
        validator.validate_path(str(temp_context_dir / "nonexistent.txt"))
