"""Unit tests for Pydantic data models."""

import pytest
from pydantic import ValidationError

from mcipy.enums import ExecutionType
from mcipy.models import (
    ApiKeyAuth,
    BasicAuth,
    BearerAuth,
    CLIExecutionConfig,
    ExecutionResult,
    FileExecutionConfig,
    FlagConfig,
    HTTPBodyConfig,
    HTTPExecutionConfig,
    MCISchema,
    Metadata,
    OAuth2Auth,
    RetryConfig,
    TextExecutionConfig,
    Tool,
)


class TestMetadata:
    """Tests for Metadata model."""

    def test_metadata_all_fields(self):
        """Test creating Metadata with all fields."""
        metadata = Metadata(
            name="Test Tools",
            description="A collection of test tools",
            version="1.0.0",
            license="MIT",
            authors=["Alice", "Bob"],
        )
        assert metadata.name == "Test Tools"
        assert metadata.description == "A collection of test tools"
        assert metadata.version == "1.0.0"
        assert metadata.license == "MIT"
        assert metadata.authors == ["Alice", "Bob"]

    def test_metadata_optional_fields(self):
        """Test that all Metadata fields are optional."""
        metadata = Metadata()
        assert metadata.name is None
        assert metadata.description is None
        assert metadata.version is None
        assert metadata.license is None
        assert metadata.authors is None

    def test_metadata_partial_fields(self):
        """Test creating Metadata with partial fields."""
        metadata = Metadata(name="Test", version="1.0.0")
        assert metadata.name == "Test"
        assert metadata.version == "1.0.0"
        assert metadata.description is None


class TestAuthConfigs:
    """Tests for authentication configuration models."""

    def test_api_key_auth_header(self):
        """Test API key authentication in header."""
        auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "secret123"})
        assert auth.type == "apiKey"
        assert auth.in_ == "header"
        assert auth.name == "X-API-Key"
        assert auth.value == "secret123"

    def test_api_key_auth_query(self):
        """Test API key authentication in query."""
        auth = ApiKeyAuth(**{"in": "query", "name": "api_key", "value": "secret123"})
        assert auth.in_ == "query"
        assert auth.name == "api_key"

    def test_bearer_auth(self):
        """Test bearer token authentication."""
        auth = BearerAuth(token="bearer_token_123")
        assert auth.type == "bearer"
        assert auth.token == "bearer_token_123"

    def test_basic_auth(self):
        """Test basic authentication."""
        auth = BasicAuth(username="user", password="pass")
        assert auth.type == "basic"
        assert auth.username == "user"
        assert auth.password == "pass"

    def test_oauth2_auth_minimal(self):
        """Test OAuth2 authentication with minimal fields."""
        auth = OAuth2Auth(
            flow="clientCredentials",
            tokenUrl="https://auth.example.com/token",
            clientId="client123",
            clientSecret="secret456",
        )
        assert auth.type == "oauth2"
        assert auth.flow == "clientCredentials"
        assert auth.tokenUrl == "https://auth.example.com/token"
        assert auth.scopes is None

    def test_oauth2_auth_with_scopes(self):
        """Test OAuth2 authentication with scopes."""
        auth = OAuth2Auth(
            flow="clientCredentials",
            tokenUrl="https://auth.example.com/token",
            clientId="client123",
            clientSecret="secret456",
            scopes=["read:data", "write:data"],
        )
        assert auth.scopes == ["read:data", "write:data"]


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_retry_config_defaults(self):
        """Test retry config with default values."""
        retry = RetryConfig()
        assert retry.attempts == 1
        assert retry.backoff_ms == 500

    def test_retry_config_custom(self):
        """Test retry config with custom values."""
        retry = RetryConfig(attempts=3, backoff_ms=1000)
        assert retry.attempts == 3
        assert retry.backoff_ms == 1000

    def test_retry_config_validation(self):
        """Test retry config validation."""
        with pytest.raises(ValidationError):
            RetryConfig(attempts=0)  # Must be >= 1
        with pytest.raises(ValidationError):
            RetryConfig(backoff_ms=-1)  # Must be >= 0


class TestHTTPBodyConfig:
    """Tests for HTTP body configuration."""

    def test_http_body_json(self):
        """Test HTTP body with JSON type."""
        body = HTTPBodyConfig(type="json", content={"key": "value"})
        assert body.type == "json"
        assert body.content == {"key": "value"}

    def test_http_body_form(self):
        """Test HTTP body with form type."""
        body = HTTPBodyConfig(type="form", content={"field1": "value1"})
        assert body.type == "form"

    def test_http_body_raw(self):
        """Test HTTP body with raw type."""
        body = HTTPBodyConfig(type="raw", content="raw string data")
        assert body.type == "raw"
        assert body.content == "raw string data"


class TestHTTPExecutionConfig:
    """Tests for HTTP execution configuration."""

    def test_http_config_minimal(self):
        """Test HTTP config with minimal required fields."""
        config = HTTPExecutionConfig(url="https://api.example.com/data")
        assert config.type == ExecutionType.HTTP
        assert config.method == "GET"
        assert config.url == "https://api.example.com/data"
        assert config.timeout_ms == 30000

    def test_http_config_full(self):
        """Test HTTP config with all fields."""
        auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "secret"})
        body = HTTPBodyConfig(type="json", content={"data": "test"})
        retry = RetryConfig(attempts=3, backoff_ms=1000)

        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="POST",
            headers={"Content-Type": "application/json"},
            auth=auth,
            params={"query": "value"},
            body=body,
            timeout_ms=5000,
            retries=retry,
        )

        assert config.method == "POST"
        assert config.headers == {"Content-Type": "application/json"}
        assert config.auth == auth
        assert config.params == {"query": "value"}
        assert config.body == body
        assert config.timeout_ms == 5000
        assert config.retries == retry

    def test_http_config_various_methods(self):
        """Test HTTP config with various HTTP methods."""
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
            config = HTTPExecutionConfig(url="https://api.example.com", method=method)
            assert config.method == method


class TestFlagConfig:
    """Tests for CLI flag configuration."""

    def test_flag_config_boolean(self):
        """Test flag config for boolean type."""
        flag = FlagConfig(**{"from": "props.verbose", "type": "boolean"})
        assert flag.from_ == "props.verbose"
        assert flag.type == "boolean"

    def test_flag_config_value(self):
        """Test flag config for value type."""
        flag = FlagConfig(**{"from": "props.output", "type": "value"})
        assert flag.from_ == "props.output"
        assert flag.type == "value"


class TestCLIExecutionConfig:
    """Tests for CLI execution configuration."""

    def test_cli_config_minimal(self):
        """Test CLI config with minimal required fields."""
        config = CLIExecutionConfig(command="ls")
        assert config.type == ExecutionType.CLI
        assert config.command == "ls"
        assert config.args is None
        assert config.flags is None
        assert config.cwd is None
        assert config.timeout_ms == 30000

    def test_cli_config_with_args(self):
        """Test CLI config with arguments."""
        config = CLIExecutionConfig(command="grep", args=["-n", "pattern"])
        assert config.command == "grep"
        assert config.args == ["-n", "pattern"]

    def test_cli_config_with_flags(self):
        """Test CLI config with flags."""
        flags = {
            "-v": FlagConfig(**{"from": "props.verbose", "type": "boolean"}),
            "--output": FlagConfig(**{"from": "props.output", "type": "value"}),
        }
        config = CLIExecutionConfig(command="tool", flags=flags)
        assert config.flags == flags

    def test_cli_config_full(self):
        """Test CLI config with all fields."""
        config = CLIExecutionConfig(
            command="docker",
            args=["run"],
            flags={"-it": FlagConfig(**{"from": "props.interactive", "type": "boolean"})},
            cwd="/home/user/project",
            timeout_ms=60000,
        )
        assert config.command == "docker"
        assert config.args == ["run"]
        assert config.cwd == "/home/user/project"
        assert config.timeout_ms == 60000


class TestFileExecutionConfig:
    """Tests for file execution configuration."""

    def test_file_config_minimal(self):
        """Test file config with minimal required fields."""
        config = FileExecutionConfig(path="/path/to/file.txt")
        assert config.type == ExecutionType.FILE
        assert config.path == "/path/to/file.txt"
        assert config.enableTemplating is True

    def test_file_config_no_parse(self):
        """Test file config with placeholders disabled."""
        config = FileExecutionConfig(path="/path/to/file.txt", enableTemplating=False)
        assert config.enableTemplating is False


class TestTextExecutionConfig:
    """Tests for text execution configuration."""

    def test_text_config(self):
        """Test text config."""
        config = TextExecutionConfig(text="Hello {{env.USER}}")
        assert config.type == ExecutionType.TEXT
        assert config.text == "Hello {{env.USER}}"


class TestTool:
    """Tests for Tool model."""

    def test_tool_minimal(self):
        """Test tool with minimal required fields."""
        config = HTTPExecutionConfig(url="https://api.example.com")
        tool = Tool(name="test_tool", execution=config)
        assert tool.name == "test_tool"
        assert tool.title is None
        assert tool.description is None
        assert tool.inputSchema is None
        assert tool.execution == config

    def test_tool_full(self):
        """Test tool with all fields."""
        config = HTTPExecutionConfig(url="https://api.example.com")
        input_schema = {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City name"}},
            "required": ["location"],
        }

        tool = Tool(
            name="get_weather",
            title="Weather Information Provider",
            description="Get current weather information",
            inputSchema=input_schema,
            execution=config,
        )

        assert tool.name == "get_weather"
        assert tool.title == "Weather Information Provider"
        assert tool.description == "Get current weather information"
        assert tool.inputSchema == input_schema

    def test_tool_with_different_execution_types(self):
        """Test tool with different execution config types."""
        http_tool = Tool(name="http_tool", execution=HTTPExecutionConfig(url="https://test.com"))
        assert http_tool.execution.type == ExecutionType.HTTP

        cli_tool = Tool(name="cli_tool", execution=CLIExecutionConfig(command="ls"))
        assert cli_tool.execution.type == ExecutionType.CLI

        file_tool = Tool(name="file_tool", execution=FileExecutionConfig(path="/file.txt"))
        assert file_tool.execution.type == ExecutionType.FILE

        text_tool = Tool(name="text_tool", execution=TextExecutionConfig(text="Hello"))
        assert text_tool.execution.type == ExecutionType.TEXT


class TestMCISchema:
    """Tests for MCI schema model."""

    def test_mci_schema_minimal(self):
        """Test MCI schema with minimal required fields."""
        tool = Tool(name="test_tool", execution=HTTPExecutionConfig(url="https://api.example.com"))
        schema = MCISchema(schemaVersion="1.0", tools=[tool])
        assert schema.schemaVersion == "1.0"
        assert schema.metadata is None
        assert len(schema.tools) == 1
        assert schema.tools[0].name == "test_tool"

    def test_mci_schema_full(self):
        """Test MCI schema with all fields."""
        metadata = Metadata(
            name="Test Context",
            description="A test MCI context",
            version="1.0.0",
            license="MIT",
            authors=["Test Author"],
        )

        tools = [
            Tool(name="tool1", execution=HTTPExecutionConfig(url="https://api1.com")),
            Tool(name="tool2", execution=CLIExecutionConfig(command="ls")),
            Tool(name="tool3", execution=FileExecutionConfig(path="/file.txt")),
        ]

        schema = MCISchema(schemaVersion="1.0", metadata=metadata, tools=tools)

        assert schema.schemaVersion == "1.0"
        assert schema.metadata == metadata
        assert len(schema.tools) == 3

    def test_mci_schema_empty_tools_validation(self):
        """Test that empty tools list is allowed."""
        schema = MCISchema(schemaVersion="1.0", tools=[])
        assert len(schema.tools) == 0


class TestExecutionResult:
    """Tests for execution result model."""

    def test_execution_result_success(self):
        """Test successful execution result."""
        result = ExecutionResult(isError=False, content={"data": "value"})
        assert result.isError is False
        assert result.content == {"data": "value"}
        assert result.error is None

    def test_execution_result_error(self):
        """Test error execution result."""
        result = ExecutionResult(isError=True, error="Connection timeout")
        assert result.isError is True
        assert result.error == "Connection timeout"
        assert result.content is None

    def test_execution_result_various_content_types(self):
        """Test execution result with various content types."""
        # String content
        result1 = ExecutionResult(isError=False, content="text response")
        assert result1.content == "text response"

        # Dict content
        result2 = ExecutionResult(isError=False, content={"key": "value"})
        assert result2.content == {"key": "value"}

        # List content
        result3 = ExecutionResult(isError=False, content=[1, 2, 3])
        assert result3.content == [1, 2, 3]

        # None content
        result4 = ExecutionResult(isError=False, content=None)
        assert result4.content is None

    def test_execution_result_with_metadata(self):
        """Test execution result with metadata field."""
        result = ExecutionResult(
            isError=False,
            content={"data": "value"},
            metadata={"status_code": 200, "execution_time_ms": 150},
        )
        assert result.isError is False
        assert result.content == {"data": "value"}
        assert result.metadata == {"status_code": 200, "execution_time_ms": 150}

    def test_execution_result_without_metadata(self):
        """Test execution result without metadata (backward compatibility)."""
        result = ExecutionResult(isError=False, content="test")
        assert result.isError is False
        assert result.content == "test"
        assert result.metadata is None
