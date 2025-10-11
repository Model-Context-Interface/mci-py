"""Unit tests for FileExecutor class."""

import tempfile
from pathlib import Path

import pytest

from mcipy.executors.file_executor import FileExecutor
from mcipy.models import FileExecutionConfig


class TestFileExecutor:
    """Tests for FileExecutor class."""

    @pytest.fixture
    def executor(self):
        """Fixture for FileExecutor instance."""
        return FileExecutor()

    @pytest.fixture
    def temp_file(self):
        """Fixture for a temporary file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello World")
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def temp_template_file(self):
        """Fixture for a temporary file with template content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello {{props.name}}! Your key is {{env.API_KEY}}.")
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def context(self):
        """Fixture for test context."""
        return {
            "props": {"name": "Alice", "location": "Seattle"},
            "env": {"API_KEY": "secret123", "ENV": "production"},
            "input": {"name": "Alice", "location": "Seattle"},
        }

    def test_read_file_success(self, executor, temp_file):
        """Test reading a file successfully."""
        content = executor._read_file(temp_file)
        assert content == "Hello World"

    def test_read_file_not_found(self, executor):
        """Test reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            executor._read_file("/path/that/does/not/exist.txt")

    def test_read_file_is_directory(self, executor):
        """Test reading a directory raises OSError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(OSError, match="Path is not a file"):
                executor._read_file(temp_dir)

    def test_parse_content_no_templating(self, executor, context):
        """Test parsing content with templating disabled."""
        content = "Hello {{props.name}}!"
        result = executor._parse_content(content, context, parse_placeholders=False)
        assert result == "Hello {{props.name}}!"  # Unchanged

    def test_parse_content_with_templating(self, executor, context):
        """Test parsing content with templating enabled."""
        content = "Hello {{props.name}}!"
        result = executor._parse_content(content, context, parse_placeholders=True)
        assert result == "Hello Alice!"

    def test_parse_content_advanced_templating_for(self, executor, context):
        """Test parsing content with @for directive."""
        content = "@for(i in range(0, 3))Item {{i}}\n@endfor"
        result = executor._parse_content(content, context, parse_placeholders=True)
        assert "Item 0" in result
        assert "Item 1" in result
        assert "Item 2" in result

    def test_parse_content_advanced_templating_foreach(self, executor):
        """Test parsing content with @foreach directive."""
        context = {
            "props": {"items": ["apple", "banana", "cherry"]},
            "env": {},
            "input": {"items": ["apple", "banana", "cherry"]},
        }
        content = "@foreach(item in props.items)- {{item}}\n@endforeach"
        result = executor._parse_content(content, context, parse_placeholders=True)
        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_parse_content_advanced_templating_if(self, executor, context):
        """Test parsing content with @if directive."""
        content = '@if(env.ENV == "production")Production mode@endif'
        result = executor._parse_content(content, context, parse_placeholders=True)
        assert "Production mode" in result

    def test_execute_success_no_templating(self, executor, temp_file):
        """Test executing file read without templating."""
        config = FileExecutionConfig(path=temp_file, enableTemplating=False)
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "Hello World"
        assert result.error is None

    def test_execute_success_with_templating(self, executor, temp_template_file, context):
        """Test executing file read with templating."""
        config = FileExecutionConfig(path=temp_template_file, enableTemplating=True)

        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "Hello Alice! Your key is secret123."
        assert result.error is None

    def test_execute_file_not_found(self, executor):
        """Test executing with non-existent file returns error."""
        config = FileExecutionConfig(path="/nonexistent/file.txt", enableTemplating=False)
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is True
        assert "File not found" in result.error
        assert result.content is None

    def test_execute_templated_path(self, executor, temp_file):
        """Test executing with templated file path."""
        # Create a context where we template the path
        context = {
            "props": {"filename": Path(temp_file).name},
            "env": {"BASE_DIR": str(Path(temp_file).parent)},
            "input": {"filename": Path(temp_file).name},
        }

        # Use templated path
        config = FileExecutionConfig(
            path="{{env.BASE_DIR}}/{{props.filename}}", enableTemplating=False
        )

        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "Hello World"

    def test_execute_with_all_advanced_features(self, executor):
        """Test executing with file containing all advanced templating features."""
        context = {
            "props": {
                "title": "Test Report",
                "items": ["item1", "item2"],
            },
            "env": {"MODE": "test"},
            "input": {"title": "Test Report", "items": ["item1", "item2"]},
        }

        content = """{{props.title}}
@foreach(item in props.items)
- {{item}}
@endforeach
@for(i in range(0, 3))
Number: {{i}}
@endfor
@if(env.MODE == "test")
Test mode active
@endif"""

        # Create temp file with this content
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(content)
            temp_path = f.name

        try:
            config = FileExecutionConfig(path=temp_path, enableTemplating=True)
            result = executor.execute(config, context)

            assert result.isError is False
            assert "Test Report" in result.content
            assert "- item1" in result.content
            assert "- item2" in result.content
            assert "Number: 0" in result.content
            assert "Number: 1" in result.content
            assert "Number: 2" in result.content
            assert "Test mode active" in result.content
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_execute_wrong_config_type(self, executor):
        """Test executing with wrong config type returns error."""
        from mcipy.models import TextExecutionConfig

        config = TextExecutionConfig(text="test")
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is True
        assert "Expected FileExecutionConfig" in result.error
        assert result.content is None
