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

    def test_apply_basic_templating_to_config_with_http_config(self, executor):
        """Test applying basic templating to HTTP execution config fields."""
        from mcipy.models import HTTPExecutionConfig

        config = HTTPExecutionConfig(
            url="https://{{env.API_HOST}}/api/{{props.endpoint}}",
            method="POST",
            headers={"Authorization": "Bearer {{env.API_TOKEN}}"},
            params={"user": "{{props.username}}", "limit": "10"},
        )
        context = {
            "props": {"endpoint": "users", "username": "alice"},
            "env": {"API_HOST": "api.example.com", "API_TOKEN": "secret123"},
            "input": {"endpoint": "users", "username": "alice"},
        }

        executor._apply_basic_templating_to_config(config, context)

        assert config.url == "https://api.example.com/api/users"
        assert config.headers == {"Authorization": "Bearer secret123"}
        assert config.params == {"user": "alice", "limit": "10"}

    def test_apply_basic_templating_to_dict_nested_deep(self, executor):
        """Test applying basic templating to deeply nested dictionaries."""
        data: dict[str, Any] = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "{{props.deep}}",
                    },
                    "another": "{{env.VAR}}",
                },
            },
        }
        context = {
            "props": {"deep": "nested_value"},
            "env": {"VAR": "env_value"},
            "input": {"deep": "nested_value"},
        }

        executor._apply_basic_templating_to_dict(data, context)

        assert data["level1"]["level2"]["level3"]["value"] == "nested_value"
        assert data["level1"]["level2"]["another"] == "env_value"

    def test_apply_basic_templating_to_list_nested(self, executor):
        """Test applying basic templating to nested lists and dicts."""
        data = [
            "{{props.item}}",
            {"key": "{{env.VALUE}}"},
            ["{{props.nested1}}", "{{env.nested2}}"],
        ]
        context = {
            "props": {"item": "first", "nested1": "n1"},
            "env": {"VALUE": "val", "nested2": "n2"},
            "input": {"item": "first", "nested1": "n1"},
        }

        executor._apply_basic_templating_to_list(data, context)

        assert data[0] == "first"
        assert isinstance(data[1], dict)
        assert data[1]["key"] == "val"
        assert isinstance(data[2], list)
        assert data[2][0] == "n1"
        assert data[2][1] == "n2"

    def test_apply_basic_templating_mixed_placeholders(self, executor):
        """Test applying templating with multiple placeholders in one string."""
        from mcipy.models import FileExecutionConfig

        config = FileExecutionConfig(path="{{env.BASE}}/{{props.dir}}/{{props.file}}.txt")
        context = {
            "props": {"dir": "data", "file": "output"},
            "env": {"BASE": "/home/user"},
            "input": {"dir": "data", "file": "output"},
        }

        executor._apply_basic_templating_to_config(config, context)

        assert config.path == "/home/user/data/output.txt"

    def test_apply_basic_templating_empty_values(self, executor):
        """Test applying templating with empty string values."""
        data: dict[str, Any] = {
            "name": "{{props.empty}}",
            "url": "https://api.example.com/{{props.path}}",
        }
        context = {
            "props": {"empty": "", "path": ""},
            "env": {},
            "input": {"empty": "", "path": ""},
        }

        executor._apply_basic_templating_to_dict(data, context)

        assert data["name"] == ""
        assert data["url"] == "https://api.example.com/"

    def test_apply_basic_templating_with_special_chars(self, executor):
        """Test templating with special characters in values."""
        data: dict[str, Any] = {
            "path": "/data/{{props.name}}/file.txt",
            "query": "?param={{props.value}}",
        }
        context = {
            "props": {"name": "user@example.com", "value": "a&b=c"},
            "env": {},
            "input": {"name": "user@example.com", "value": "a&b=c"},
        }

        executor._apply_basic_templating_to_dict(data, context)

        assert data["path"] == "/data/user@example.com/file.txt"
        assert data["query"] == "?param=a&b=c"

    def test_apply_basic_templating_preserves_non_string_types(self, executor):
        """Test that non-string types are preserved during templating."""
        data: dict[str, Any] = {
            "string": "{{props.name}}",
            "number": 42,
            "boolean": True,
            "none": None,
            "list_of_numbers": [1, 2, 3],
        }
        context = {
            "props": {"name": "alice"},
            "env": {},
            "input": {"name": "alice"},
        }

        executor._apply_basic_templating_to_dict(data, context)

        assert data["string"] == "alice"
        assert data["number"] == 42
        assert data["boolean"] is True
        assert data["none"] is None
        assert data["list_of_numbers"] == [1, 2, 3]

    def test_apply_basic_templating_handles_none_fields(self, executor):
        """Test that None fields in config are handled gracefully."""
        from mcipy.models import HTTPExecutionConfig

        config = HTTPExecutionConfig(
            url="https://api.example.com/{{props.endpoint}}",
            headers=None,  # None field
            params=None,  # None field
        )
        context = {
            "props": {"endpoint": "data"},
            "env": {},
            "input": {"endpoint": "data"},
        }

        # Should not raise an error
        executor._apply_basic_templating_to_config(config, context)

        assert config.url == "https://api.example.com/data"
        assert config.headers is None
        assert config.params is None

    def test_apply_basic_templating_input_alias(self, executor):
        """Test that input alias works correctly in templating."""
        data: dict[str, Any] = {
            "from_props": "{{props.value}}",
            "from_input": "{{input.value}}",
        }
        context = {
            "props": {"value": "test"},
            "env": {},
            "input": {"value": "test"},
        }

        executor._apply_basic_templating_to_dict(data, context)

        # Both should resolve to the same value
        assert data["from_props"] == "test"
        assert data["from_input"] == "test"

    def test_apply_basic_templating_error_handling(self, executor):
        """Test error handling when placeholder cannot be resolved."""
        from mcipy.templating import TemplateError

        data: dict[str, Any] = {"name": "{{props.missing}}"}
        context = {"props": {}, "env": {}, "input": {}}

        # Should raise TemplateError when trying to resolve missing placeholder
        with pytest.raises(TemplateError):
            executor._apply_basic_templating_to_dict(data, context)
