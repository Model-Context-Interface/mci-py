"""Unit tests for BaseExecutor class."""

from typing import Any

import pytest

from mcipy.enums import ExecutionType
from mcipy.executors.base import BaseExecutor
from mcipy.models import ExecutionConfig, ExecutionResult


class ConcreteExecutor(BaseExecutor):
    """Concrete implementation of BaseExecutor for testing."""

    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """Simple execute implementation that returns success."""
        return ExecutionResult(isError=False, content="test", error=None)


class TestBaseExecutor:
    """Tests for BaseExecutor abstract class."""

    @pytest.fixture
    def executor(self):
        """Fixture for a concrete executor instance."""
        return ConcreteExecutor()

    def test_cannot_instantiate_base_executor(self):
        """Test that BaseExecutor cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            BaseExecutor()  # pyright: ignore[reportAbstractUsage]

    def test_build_context_basic(self, executor):
        """Test building context with props and env_vars."""
        props = {"name": "Alice", "age": 30}
        env_vars = {"API_KEY": "secret123", "ENV": "production"}

        context = executor._build_context(props, env_vars)

        assert "props" in context
        assert "env" in context
        assert "input" in context
        assert context["props"] == props
        assert context["env"] == env_vars
        assert context["input"] == props  # input is an alias for props

    def test_build_context_empty(self, executor):
        """Test building context with empty dictionaries."""
        props = {}
        env_vars = {}

        context = executor._build_context(props, env_vars)

        assert context["props"] == {}
        assert context["env"] == {}
        assert context["input"] == {}

    def test_build_context_input_is_alias(self, executor):
        """Test that input is an alias for props, not a copy."""
        props = {"key": "value"}
        env_vars = {}

        context = executor._build_context(props, env_vars)

        assert context["input"] is context["props"]

    def test_handle_timeout_default(self, executor):
        """Test timeout handling with 0 or negative values."""
        assert executor._handle_timeout(0) == 30
        assert executor._handle_timeout(-100) == 30

    def test_handle_timeout_conversion(self, executor):
        """Test timeout conversion from milliseconds to seconds."""
        # 1000ms = 1s
        assert executor._handle_timeout(1000) == 1

        # 5000ms = 5s
        assert executor._handle_timeout(5000) == 5

        # 30000ms = 30s
        assert executor._handle_timeout(30000) == 30

    def test_handle_timeout_rounding(self, executor):
        """Test timeout rounding up."""
        # 1ms should round up to 1s
        assert executor._handle_timeout(1) == 1

        # 500ms should round up to 1s
        assert executor._handle_timeout(500) == 1

        # 999ms should round up to 1s
        assert executor._handle_timeout(999) == 1

        # 1001ms should round up to 2s
        assert executor._handle_timeout(1001) == 2

        # 1500ms should round up to 2s
        assert executor._handle_timeout(1500) == 2

    def test_format_error_basic(self, executor):
        """Test error formatting with a basic exception."""
        error = Exception("Something went wrong")
        result = executor._format_error(error)

        assert isinstance(result, ExecutionResult)
        assert result.isError is True
        assert result.error == "Something went wrong"
        assert result.content is None

    def test_format_error_different_types(self, executor):
        """Test error formatting with different exception types."""
        # ValueError
        error1 = ValueError("Invalid value")
        result1 = executor._format_error(error1)
        assert result1.isError is True
        assert result1.error == "Invalid value"

        # TypeError
        error2 = TypeError("Wrong type")
        result2 = executor._format_error(error2)
        assert result2.isError is True
        assert result2.error == "Wrong type"

        # RuntimeError
        error3 = RuntimeError("Runtime issue")
        result3 = executor._format_error(error3)
        assert result3.isError is True
        assert result3.error == "Runtime issue"

    def test_execute_returns_result(self, executor):
        """Test that execute method returns ExecutionResult."""
        config = ExecutionConfig(type=ExecutionType.TEXT)
        context = {"props": {}, "env": {}, "input": {}}

        result = executor.execute(config, context)

        assert isinstance(result, ExecutionResult)
        assert result.isError is False
        assert result.content == "test"

    def test_apply_basic_templating_to_config_string_fields(self, executor):
        """Test applying basic templating to string fields in config."""
        from mcipy.models import FileExecutionConfig

        config = FileExecutionConfig(path="/data/{{props.username}}/file.txt")
        context = {
            "props": {"username": "alice"},
            "env": {},
            "input": {"username": "alice"},
        }

        executor._apply_basic_templating_to_config(config, context)

        assert config.path == "/data/alice/file.txt"

    def test_apply_basic_templating_to_config_multiple_fields(self, executor):
        """Test applying basic templating to multiple fields."""
        from mcipy.models import FileExecutionConfig

        config = FileExecutionConfig(
            path="{{env.BASE_DIR}}/{{props.filename}}.txt", enableTemplating=True
        )
        context = {
            "props": {"filename": "config"},
            "env": {"BASE_DIR": "/home/user"},
            "input": {"filename": "config"},
        }

        executor._apply_basic_templating_to_config(config, context)

        assert config.path == "/home/user/config.txt"

    def test_apply_basic_templating_to_dict(self, executor):
        """Test applying basic templating to dictionary values."""
        data: dict[str, Any] = {
            "name": "{{props.username}}",
            "url": "https://api.example.com/{{env.API_VERSION}}",
            "nested": {"key": "value-{{props.id}}"},
        }
        context = {
            "props": {"username": "bob", "id": "123"},
            "env": {"API_VERSION": "v2"},
            "input": {"username": "bob", "id": "123"},
        }

        executor._apply_basic_templating_to_dict(data, context)

        assert data["name"] == "bob"
        assert data["url"] == "https://api.example.com/v2"
        nested = data["nested"]
        assert isinstance(nested, dict)
        assert nested["key"] == "value-123"

    def test_apply_basic_templating_to_list(self, executor):
        """Test applying basic templating to list values."""
        data = ["{{props.item1}}", "static", "{{env.ITEM2}}"]
        context = {
            "props": {"item1": "first"},
            "env": {"ITEM2": "second"},
            "input": {"item1": "first"},
        }

        executor._apply_basic_templating_to_list(data, context)

        assert data[0] == "first"
        assert data[1] == "static"
        assert data[2] == "second"

    def test_apply_basic_templating_no_placeholders(self, executor):
        """Test that templating works when there are no placeholders."""
        from mcipy.models import FileExecutionConfig

        config = FileExecutionConfig(path="/static/path/file.txt")
        context = {"props": {}, "env": {}, "input": {}}

        executor._apply_basic_templating_to_config(config, context)

        assert config.path == "/static/path/file.txt"
