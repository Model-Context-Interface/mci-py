"""Unit tests for TextExecutor class."""

import pytest

from mcipy.executors.text_executor import TextExecutor
from mcipy.models import TextExecutionConfig


class TestTextExecutor:
    """Tests for TextExecutor class."""

    @pytest.fixture
    def executor(self):
        """Fixture for TextExecutor instance."""
        return TextExecutor()

    @pytest.fixture
    def context(self):
        """Fixture for test context."""
        return {
            "props": {"name": "Alice", "age": 30, "city": "Seattle"},
            "env": {"API_KEY": "secret123", "ENV": "production"},
            "input": {"name": "Alice", "age": 30, "city": "Seattle"},
        }

    def test_execute_simple_text(self, executor):
        """Test executing with simple text (no placeholders)."""
        config = TextExecutionConfig(text="Hello, World!")
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "Hello, World!"
        assert result.error is None

    def test_execute_with_props_placeholder(self, executor, context):
        """Test executing with props placeholders."""
        config = TextExecutionConfig(text="Hello {{props.name}}!")
        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "Hello Alice!"
        assert result.error is None

    def test_execute_with_env_placeholder(self, executor, context):
        """Test executing with environment variable placeholders."""
        config = TextExecutionConfig(text="API Key: {{env.API_KEY}}")
        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "API Key: secret123"
        assert result.error is None

    def test_execute_with_input_placeholder(self, executor, context):
        """Test executing with input placeholders (alias for props)."""
        config = TextExecutionConfig(text="User: {{input.name}}, Age: {{input.age}}")
        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "User: Alice, Age: 30"
        assert result.error is None

    def test_execute_with_multiple_placeholders(self, executor, context):
        """Test executing with multiple placeholders."""
        config = TextExecutionConfig(text="{{props.name}} lives in {{props.city}} ({{env.ENV}})")
        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "Alice lives in Seattle (production)"
        assert result.error is None

    def test_execute_with_for_loop(self, executor):
        """Test executing with @for loop."""
        config = TextExecutionConfig(text="@for(i in range(0, 3))Item {{i}}\n@endfor")
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is False
        assert "Item 0" in result.content
        assert "Item 1" in result.content
        assert "Item 2" in result.content

    def test_execute_with_foreach_loop(self, executor):
        """Test executing with @foreach loop."""
        context = {
            "props": {"fruits": ["apple", "banana", "cherry"]},
            "env": {},
            "input": {"fruits": ["apple", "banana", "cherry"]},
        }
        config = TextExecutionConfig(text="@foreach(fruit in props.fruits)- {{fruit}}\n@endforeach")

        result = executor.execute(config, context)

        assert result.isError is False
        assert "- apple" in result.content
        assert "- banana" in result.content
        assert "- cherry" in result.content

    def test_execute_with_if_directive(self, executor, context):
        """Test executing with @if directive."""
        config = TextExecutionConfig(
            text='@if(env.ENV == "production")Production Environment@endif'
        )

        result = executor.execute(config, context)

        assert result.isError is False
        assert "Production Environment" in result.content

    def test_execute_with_if_else_directive(self, executor):
        """Test executing with @if/@else directive."""
        context = {
            "props": {"debug": False},
            "env": {},
            "input": {"debug": False},
        }
        config = TextExecutionConfig(text="@if(props.debug)Debug Mode @else Production Mode @endif")

        result = executor.execute(config, context)

        assert result.isError is False
        assert "Production Mode" in result.content
        assert "Debug Mode" not in result.content

    def test_execute_complex_template(self, executor):
        """Test executing with complex template combining all features."""
        context = {
            "props": {
                "user": "Bob",
                "items": ["task1", "task2"],
                "priority": "high",
            },
            "env": {"SYSTEM": "TaskManager"},
            "input": {
                "user": "Bob",
                "items": ["task1", "task2"],
                "priority": "high",
            },
        }

        text = """Welcome to {{env.SYSTEM}}, {{props.user}}!

Your tasks:
@foreach(task in props.items)
- {{task}}
@endforeach

@if(props.priority == "high")
⚠️ High priority tasks require immediate attention!
@endif

Summary: {{props.user}} has completed @for(i in range(0, 2)){{i}} @endfor tasks."""

        config = TextExecutionConfig(text=text)
        result = executor.execute(config, context)

        assert result.isError is False
        assert "Welcome to TaskManager, Bob!" in result.content
        assert "- task1" in result.content
        assert "- task2" in result.content
        assert "High priority tasks require immediate attention!" in result.content

    def test_execute_missing_placeholder_error(self, executor):
        """Test executing with missing placeholder returns error."""
        config = TextExecutionConfig(text="Hello {{props.missing}}!")
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is True
        assert "missing" in result.error.lower()
        assert result.content is None

    def test_execute_nested_placeholders(self, executor):
        """Test executing with nested object placeholders."""
        context = {
            "props": {"user": {"name": "Charlie", "profile": {"role": "admin"}}},
            "env": {},
            "input": {"user": {"name": "Charlie", "profile": {"role": "admin"}}},
        }
        config = TextExecutionConfig(
            text="User: {{props.user.name}}, Role: {{props.user.profile.role}}"
        )

        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == "User: Charlie, Role: admin"

    def test_execute_empty_text(self, executor):
        """Test executing with empty text."""
        config = TextExecutionConfig(text="")
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is False
        assert result.content == ""
        assert result.error is None

    def test_execute_whitespace_preservation(self, executor, context):
        """Test that whitespace is preserved in output."""
        config = TextExecutionConfig(text="Line 1\n  Line 2 with indent\n\nLine 4 after blank")

        result = executor.execute(config, context)

        assert result.isError is False
        assert "Line 1\n  Line 2 with indent\n\nLine 4 after blank" == result.content

    def test_execute_all_templating_directives(self, executor):
        """Test executing with all templating directives working together."""
        context = {
            "props": {
                "title": "Sales Report",
                "quarters": ["Q1", "Q2", "Q3"],
                "status": "complete",
            },
            "env": {"YEAR": "2024", "COMPANY": "ACME Corp"},
            "input": {
                "title": "Sales Report",
                "quarters": ["Q1", "Q2", "Q3"],
                "status": "complete",
            },
        }

        text = """{{env.COMPANY}} - {{props.title}} {{env.YEAR}}

Quarterly Performance:
@foreach(quarter in props.quarters)
- {{quarter}}: Analysis
@endforeach

Numbered Summary:
@for(i in range(0, 4))
{{i}}. Quarter {{i}} data
@endfor

@if(props.status == "complete")
✓ Report is complete and verified
@elseif(props.status == "draft")
⚠ Report is in draft status
@else
❌ Report status unknown
@endif"""

        config = TextExecutionConfig(text=text)
        result = executor.execute(config, context)

        assert result.isError is False
        # Check all features work
        assert "ACME Corp - Sales Report 2024" in result.content
        assert "- Q1: Analysis" in result.content
        assert "- Q2: Analysis" in result.content
        assert "- Q3: Analysis" in result.content
        assert "0. Quarter 0 data" in result.content
        assert "3. Quarter 3 data" in result.content
        assert "✓ Report is complete and verified" in result.content

    def test_execute_wrong_config_type(self, executor):
        """Test executing with wrong config type returns error."""
        from mcipy.models import FileExecutionConfig

        config = FileExecutionConfig(path="/test/path.txt")
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert result.isError is True
        assert "Expected TextExecutionConfig" in result.error
        assert result.content is None
