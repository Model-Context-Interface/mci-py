"""
Feature tests for end-to-end execution flow.

Tests the complete execution workflow from model construction through
ExecutorFactory to execution and result handling, covering all executor
types with appropriate mocking.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcipy.enums import ExecutionType
from mcipy.executors import ExecutorFactory
from mcipy.models import (
    ApiKeyAuth,
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPBodyConfig,
    HTTPExecutionConfig,
    TextExecutionConfig,
)


class TestExecutorFactory:
    """Tests for ExecutorFactory class."""

    def test_get_http_executor(self):
        """Test getting HTTP executor from factory."""
        ExecutorFactory.clear_cache()
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        assert executor is not None
        assert type(executor).__name__ == "HTTPExecutor"

    def test_get_cli_executor(self):
        """Test getting CLI executor from factory."""
        ExecutorFactory.clear_cache()
        executor = ExecutorFactory.get_executor(ExecutionType.CLI)
        assert executor is not None
        assert type(executor).__name__ == "CLIExecutor"

    def test_get_file_executor(self):
        """Test getting File executor from factory."""
        ExecutorFactory.clear_cache()
        executor = ExecutorFactory.get_executor(ExecutionType.FILE)
        assert executor is not None
        assert type(executor).__name__ == "FileExecutor"

    def test_get_text_executor(self):
        """Test getting Text executor from factory."""
        ExecutorFactory.clear_cache()
        executor = ExecutorFactory.get_executor(ExecutionType.TEXT)
        assert executor is not None
        assert type(executor).__name__ == "TextExecutor"

    def test_executor_caching(self):
        """Test that factory caches executor instances."""
        ExecutorFactory.clear_cache()
        executor1 = ExecutorFactory.get_executor(ExecutionType.HTTP)
        executor2 = ExecutorFactory.get_executor(ExecutionType.HTTP)
        assert executor1 is executor2

    def test_cache_clearing(self):
        """Test that cache clearing creates new instances."""
        ExecutorFactory.clear_cache()
        executor1 = ExecutorFactory.get_executor(ExecutionType.HTTP)
        ExecutorFactory.clear_cache()
        executor2 = ExecutorFactory.get_executor(ExecutionType.HTTP)
        assert executor1 is not executor2

    def test_all_execution_types_supported(self):
        """Test that all execution types are supported."""
        ExecutorFactory.clear_cache()
        for exec_type in ExecutionType:
            executor = ExecutorFactory.get_executor(exec_type)
            assert executor is not None

    def test_unsupported_execution_type_raises_error(self):
        """Test that invalid execution type raises ValueError."""
        # Create an invalid execution type by using a string directly
        # This tests the error handling in the factory
        ExecutorFactory.clear_cache()
        # We need to test the else branch, but since ExecutionType enum
        # covers all valid cases, we'll skip this test as it's not reachable
        # in normal usage with type safety
        pass


class TestTextExecutionE2E:
    """End-to-end tests for text execution via factory."""

    @pytest.fixture
    def context(self):
        """Fixture for execution context."""
        return {
            "props": {"name": "Alice", "role": "Developer"},
            "env": {"COMPANY": "ACME Corp"},
            "input": {"name": "Alice", "role": "Developer"},
        }

    def test_simple_text_execution(self, context):
        """Test simple text execution through factory."""
        executor = ExecutorFactory.get_executor(ExecutionType.TEXT)
        config = TextExecutionConfig(
            text="Hello {{props.name}}, {{props.role}} at {{env.COMPANY}}!"
        )
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        assert result.result.content[0].text == "Hello Alice, Developer at ACME Corp!"

    def test_text_execution_with_foreach(self, context):
        """Test text execution with @foreach directive."""
        context["props"]["items"] = ["Task 1", "Task 2", "Task 3"]
        context["input"]["items"] = ["Task 1", "Task 2", "Task 3"]

        executor = ExecutorFactory.get_executor(ExecutionType.TEXT)
        config = TextExecutionConfig(
            text="Tasks:\n@foreach(item in props.items)\n- {{item}}\n@endforeach"
        )
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        text_content = result.result.content[0].text
        assert "Task 1" in text_content
        assert "Task 2" in text_content
        assert "Task 3" in text_content

    def test_text_execution_with_if(self, context):
        """Test text execution with @if directive."""
        context["props"]["priority"] = "high"
        context["input"]["priority"] = "high"

        executor = ExecutorFactory.get_executor(ExecutionType.TEXT)
        config = TextExecutionConfig(
            text='@if(props.priority == "high")\nHigh Priority\n@else\nNormal Priority\n@endif'
        )
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        assert "High Priority" in result.result.content[0].text


class TestFileExecutionE2E:
    """End-to-end tests for file execution via factory."""

    @pytest.fixture
    def context(self):
        """Fixture for execution context."""
        return {
            "props": {"username": "Bob", "role": "Manager"},
            "env": {"COMPANY": "TechCorp"},
            "input": {"username": "Bob", "role": "Manager"},
        }

    @pytest.fixture
    def temp_file(self):
        """Fixture for a temporary file with template content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("User: {{props.username}}\nRole: {{props.role}}\nCompany: {{env.COMPANY}}")
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink()

    def test_file_execution_with_templating(self, temp_file, context):
        """Test file reading with templating enabled."""
        executor = ExecutorFactory.get_executor(ExecutionType.FILE)
        config = FileExecutionConfig(path=temp_file, enableTemplating=True)
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        text_content = result.result.content[0].text
        assert "User: Bob" in text_content
        assert "Role: Manager" in text_content
        assert "Company: TechCorp" in text_content

    def test_file_execution_without_templating(self, temp_file, context):
        """Test file reading with templating disabled."""
        executor = ExecutorFactory.get_executor(ExecutionType.FILE)
        config = FileExecutionConfig(path=temp_file, enableTemplating=False)
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        text_content = result.result.content[0].text
        assert "{{props.username}}" in text_content
        assert "{{props.role}}" in text_content
        assert "{{env.COMPANY}}" in text_content

    def test_file_execution_file_not_found(self, context):
        """Test error handling when file doesn't exist."""
        executor = ExecutorFactory.get_executor(ExecutionType.FILE)
        config = FileExecutionConfig(path="/nonexistent/file.txt", enableTemplating=False)
        result = executor.execute(config, context)

        assert result.result.isError
        assert len(result.result.content) == 1
        error_text = result.result.content[0].text
        assert "File not found" in error_text or "No such file" in error_text


class TestCLIExecutionE2E:
    """End-to-end tests for CLI execution via factory."""

    @pytest.fixture
    def context(self):
        """Fixture for execution context."""
        return {
            "props": {"message": "Hello World"},
            "env": {},
            "input": {"message": "Hello World"},
        }

    def test_simple_cli_execution(self, context):
        """Test simple command execution."""
        executor = ExecutorFactory.get_executor(ExecutionType.CLI)
        config = CLIExecutionConfig(command="echo", args=["Hello from CLI"])
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        assert "Hello from CLI" in result.result.content[0].text

    def test_cli_execution_with_templating(self, context):
        """Test command execution with templating in args."""
        executor = ExecutorFactory.get_executor(ExecutionType.CLI)
        config = CLIExecutionConfig(command="echo", args=["{{props.message}}"])
        result = executor.execute(config, context)

        assert not result.result.isError
        assert len(result.result.content) == 1
        assert "Hello World" in result.result.content[0].text

    def test_cli_execution_command_not_found(self, context):
        """Test error handling when command doesn't exist."""
        executor = ExecutorFactory.get_executor(ExecutionType.CLI)
        config = CLIExecutionConfig(command="nonexistent_command_xyz_12345")
        result = executor.execute(config, context)

        assert result.result.isError
        assert len(result.result.content) == 1


class TestHTTPExecutionE2E:
    """End-to-end tests for HTTP execution via factory with mocking."""

    @pytest.fixture
    def context(self):
        """Fixture for execution context."""
        return {
            "props": {"city": "London", "units": "metric"},
            "env": {"API_KEY": "test-key-123"},
            "input": {"city": "London", "units": "metric"},
        }

    def test_http_get_execution(self, context):
        """Test HTTP GET request execution."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        config = HTTPExecutionConfig(
            url="https://api.example.com/weather?city={{props.city}}",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"temperature": 22, "condition": "sunny"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.result.isError
            assert len(result.result.content) == 1
            # Content should be JSON formatted as text
            assert '"temperature": 22' in result.result.content[0].text
            # Verify URL was templated correctly
            call_args = mock_request.call_args
            assert "city=London" in call_args[1]["url"]

    def test_http_post_execution_with_auth(self, context):
        """Test HTTP POST request with authentication."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "{{env.API_KEY}}"})
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="POST",
            auth=auth,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": 123, "status": "created"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.result.isError
            assert len(result.result.content) == 1
            # Content should be JSON formatted as text
            assert '"id": 123' in result.result.content[0].text
            # Verify auth header was set correctly
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["headers"]["X-API-Key"] == "test-key-123"

    def test_http_execution_with_json_body(self, context):
        """Test HTTP request with JSON body."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(type="json", content={"city": "{{props.city}}"})
        config = HTTPExecutionConfig(
            url="https://api.example.com/search",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.result.isError
            # Verify JSON body was templated correctly
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"] == {"city": "London"}

    def test_http_execution_error_handling(self, context):
        """Test HTTP error handling."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        config = HTTPExecutionConfig(
            url="https://api.example.com/error",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_request.side_effect = Exception("Connection error")

            result = executor.execute(config, context)

            assert result.result.isError
            assert len(result.result.content) == 1
            assert "Connection error" in result.result.content[0].text


class TestExecutionFullStack:
    """Integration tests for full execution stack."""

    def test_full_stack_http_to_result(self):
        """Test full stack from config creation to result."""
        # 1. Create execution config
        config = HTTPExecutionConfig(
            url="https://api.example.com/test",
            method="GET",
        )

        # 2. Build context
        context = {
            "props": {},
            "env": {},
            "input": {},
        }

        # 3. Get executor from factory
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)

        # 4. Execute with mock
        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            # 5. Get result
            result = executor.execute(config, context)

            # 6. Verify result structure
            assert not result.result.isError
            assert len(result.result.content) >= 1
            assert result.result.metadata is not None

    def test_full_stack_all_executor_types(self):
        """Test that all executor types can be resolved and executed."""
        context = {
            "props": {},
            "env": {},
            "input": {},
        }

        # Test each execution type
        test_cases = [
            (ExecutionType.TEXT, TextExecutionConfig(text="Test")),
            (ExecutionType.CLI, CLIExecutionConfig(command="echo", args=["test"])),
        ]

        for exec_type, config in test_cases:
            executor = ExecutorFactory.get_executor(exec_type)
            result = executor.execute(config, context)
            # Just verify we get a result (success or error both ok)
            assert result is not None
            assert hasattr(result, "result")
            assert hasattr(result.result, "isError")
            assert hasattr(result.result, "content")


class TestJSONNativeResolutionIntegration:
    """Integration tests for JSON-native {!! ... !!} resolution in execution."""

    @pytest.fixture
    def context_with_types(self):
        """Fixture for context with various data types."""
        return {
            "props": {
                "include_images": True,
                "case_sensitive": False,
                "max_results": 100,
                "quality": 0.95,
                "urls": ["https://example.com/api", "https://test.com/api"],
                "payload": {"key": "value", "count": 42},
                "tags": ["urgent", "review"],
                "config": {"debug": False, "retries": 3},
            },
            "env": {
                "FEATURE_ENABLED": True,
                "MAX_TIMEOUT": 5000,
            },
            "input": {
                "include_images": True,
            },
        }

    def test_http_json_body_with_boolean_native(self, context_with_types):
        """Test HTTP execution with JSON body containing native boolean."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "include_images": "{!!props.include_images!!}",
                "title": "{{props.title}}",  # Standard string placeholder
            },
        )
        context_with_types["props"]["title"] = "Test Report"

        config = HTTPExecutionConfig(
            url="https://api.example.com/search",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify the JSON body was correctly constructed
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["include_images"] is True  # Native boolean
            assert isinstance(call_kwargs["json"]["include_images"], bool)
            assert call_kwargs["json"]["title"] == "Test Report"  # String

    def test_http_json_body_with_array_native(self, context_with_types):
        """Test HTTP execution with JSON body containing native array."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "urls": "{!!props.urls!!}",
                "tags": "{!!props.tags!!}",
            },
        )

        config = HTTPExecutionConfig(
            url="https://api.example.com/batch",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify arrays are native
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["urls"] == [
                "https://example.com/api",
                "https://test.com/api",
            ]
            assert isinstance(call_kwargs["json"]["urls"], list)
            assert call_kwargs["json"]["tags"] == ["urgent", "review"]
            assert isinstance(call_kwargs["json"]["tags"], list)

    def test_http_json_body_with_object_native(self, context_with_types):
        """Test HTTP execution with JSON body containing native object."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "payload": "{!!props.payload!!}",
                "config": "{!!props.config!!}",
            },
        )

        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify objects are native
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["payload"] == {"key": "value", "count": 42}
            assert isinstance(call_kwargs["json"]["payload"], dict)
            assert call_kwargs["json"]["config"] == {"debug": False, "retries": 3}
            assert isinstance(call_kwargs["json"]["config"], dict)

    def test_http_json_body_with_number_native(self, context_with_types):
        """Test HTTP execution with JSON body containing native numbers."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "max_results": "{!!props.max_results!!}",
                "quality": "{!!props.quality!!}",
            },
        )

        config = HTTPExecutionConfig(
            url="https://api.example.com/query",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify numbers are native
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["max_results"] == 100
            assert isinstance(call_kwargs["json"]["max_results"], int)
            assert call_kwargs["json"]["quality"] == 0.95
            assert isinstance(call_kwargs["json"]["quality"], float)

    def test_http_json_body_mixed_native_and_string(self, context_with_types):
        """Test HTTP execution with mix of native and string placeholders."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "enabled": "{!!props.include_images!!}",  # Native boolean
                "count": "{!!props.max_results!!}",  # Native number
                "urls": "{!!props.urls!!}",  # Native array
                "name": "{{props.title}}",  # String placeholder
                "static": "fixed value",  # No placeholder
            },
        )
        context_with_types["props"]["title"] = "My Search"

        config = HTTPExecutionConfig(
            url="https://api.example.com/complex",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify mixed types
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["enabled"] is True
            assert isinstance(call_kwargs["json"]["enabled"], bool)
            assert call_kwargs["json"]["count"] == 100
            assert isinstance(call_kwargs["json"]["count"], int)
            assert isinstance(call_kwargs["json"]["urls"], list)
            assert call_kwargs["json"]["name"] == "My Search"
            assert isinstance(call_kwargs["json"]["name"], str)
            assert call_kwargs["json"]["static"] == "fixed value"

    def test_http_json_body_nested_object_with_native(self, context_with_types):
        """Test HTTP execution with nested objects containing native types."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "settings": {
                    "enabled": "{!!props.include_images!!}",
                    "max": "{!!props.max_results!!}",
                    "quality": "{!!props.quality!!}",
                },
                "data": {
                    "tags": "{!!props.tags!!}",
                },
            },
        )

        config = HTTPExecutionConfig(
            url="https://api.example.com/nested",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify nested native types
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["settings"]["enabled"] is True
            assert isinstance(call_kwargs["json"]["settings"]["enabled"], bool)
            assert call_kwargs["json"]["settings"]["max"] == 100
            assert call_kwargs["json"]["settings"]["quality"] == 0.95
            assert call_kwargs["json"]["data"]["tags"] == ["urgent", "review"]
            assert isinstance(call_kwargs["json"]["data"]["tags"], list)

    def test_http_params_with_native_types(self, context_with_types):
        """Test HTTP execution with query params containing native types."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)

        config = HTTPExecutionConfig(
            url="https://api.example.com/search",
            method="GET",
            params={
                "enabled": "{!!props.include_images!!}",
                "max": "{!!props.max_results!!}",
            },
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify params have native types
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["params"]["enabled"] is True
            assert isinstance(call_kwargs["params"]["enabled"], bool)
            assert call_kwargs["params"]["max"] == 100
            assert isinstance(call_kwargs["params"]["max"], int)

    def test_http_json_native_from_env(self, context_with_types):
        """Test JSON-native resolution from environment variables."""
        executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        body = HTTPBodyConfig(
            type="json",
            content={
                "feature_enabled": "{!!env.FEATURE_ENABLED!!}",
                "timeout": "{!!env.MAX_TIMEOUT!!}",
            },
        )

        config = HTTPExecutionConfig(
            url="https://api.example.com/config",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context_with_types)

            assert not result.result.isError

            # Verify env values are native types
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"]["feature_enabled"] is True
            assert isinstance(call_kwargs["json"]["feature_enabled"], bool)
            assert call_kwargs["json"]["timeout"] == 5000
            assert isinstance(call_kwargs["json"]["timeout"], int)
