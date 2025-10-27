"""Unit tests for MCP-related models."""

import pytest

from mcipy.enums import ExecutionType
from mcipy.models import (
    HttpMCPServer,
    MCPExecutionConfig,
    MCPServerConfig,
    StdioMCPServer,
    Tool,
)


class TestMCPExecutionConfig:
    """Tests for MCPExecutionConfig model."""

    def test_mcp_config_minimal(self):
        """Test MCP execution config with minimal fields."""
        config = MCPExecutionConfig(
            type=ExecutionType.MCP, serverName="test-server", toolName="test-tool"
        )
        assert config.type == ExecutionType.MCP
        assert config.serverName == "test-server"
        assert config.toolName == "test-tool"

    def test_mcp_config_from_dict(self):
        """Test creating MCP execution config from dictionary."""
        data = {"type": "mcp", "serverName": "github", "toolName": "list_repos"}
        config = MCPExecutionConfig(**data)
        assert config.type == ExecutionType.MCP
        assert config.serverName == "github"
        assert config.toolName == "list_repos"

    def test_mcp_config_validation_missing_server_name(self):
        """Test validation fails when serverName is missing."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            MCPExecutionConfig(type=ExecutionType.MCP, toolName="test-tool")

    def test_mcp_config_validation_missing_tool_name(self):
        """Test validation fails when toolName is missing."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            MCPExecutionConfig(type=ExecutionType.MCP, serverName="test-server")


class TestMCPServerConfig:
    """Tests for MCPServerConfig model."""

    def test_mcp_server_config_defaults(self):
        """Test MCP server config with default values."""
        config = MCPServerConfig()
        assert config.expDays == 30
        assert config.filter is None
        assert config.filterValue is None

    def test_mcp_server_config_custom_exp_days(self):
        """Test MCP server config with custom expDays."""
        config = MCPServerConfig(expDays=7)
        assert config.expDays == 7

    def test_mcp_server_config_with_filter(self):
        """Test MCP server config with filter settings."""
        config = MCPServerConfig(
            expDays=14, filter="only", filterValue="tool1,tool2,tool3"
        )
        assert config.expDays == 14
        assert config.filter == "only"
        assert config.filterValue == "tool1,tool2,tool3"

    def test_mcp_server_config_validation_min_exp_days(self):
        """Test validation fails when expDays is less than 1."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            MCPServerConfig(expDays=0)


class TestStdioMCPServer:
    """Tests for StdioMCPServer model."""

    def test_stdio_server_minimal(self):
        """Test STDIO MCP server with minimal configuration."""
        server = StdioMCPServer(command="npx")
        assert server.command == "npx"
        assert server.args == []
        assert server.env == {}
        assert server.config.expDays == 30

    def test_stdio_server_with_args(self):
        """Test STDIO MCP server with arguments."""
        server = StdioMCPServer(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
        )
        assert server.command == "npx"
        assert len(server.args) == 3
        assert server.args[0] == "-y"
        assert server.args[2] == "/path/to/dir"

    def test_stdio_server_with_env(self):
        """Test STDIO MCP server with environment variables."""
        server = StdioMCPServer(
            command="uvx",
            args=["mcp-server"],
            env={"API_KEY": "{{env.MY_API_KEY}}", "DEBUG": "1"},
        )
        assert server.command == "uvx"
        assert server.env["API_KEY"] == "{{env.MY_API_KEY}}"
        assert server.env["DEBUG"] == "1"

    def test_stdio_server_with_config(self):
        """Test STDIO MCP server with custom configuration."""
        config = MCPServerConfig(expDays=7, filter="tags", filterValue="read")
        server = StdioMCPServer(command="npx", config=config)
        assert server.config.expDays == 7
        assert server.config.filter == "tags"
        assert server.config.filterValue == "read"

    def test_stdio_server_from_dict(self):
        """Test creating STDIO MCP server from dictionary."""
        data = {
            "command": "npx",
            "args": ["-y", "mcp-server"],
            "env": {"KEY": "value"},
            "config": {"expDays": 10},
        }
        server = StdioMCPServer(**data)
        assert server.command == "npx"
        assert server.args == ["-y", "mcp-server"]
        assert server.env == {"KEY": "value"}
        assert server.config.expDays == 10


class TestHttpMCPServer:
    """Tests for HttpMCPServer model."""

    def test_http_server_minimal(self):
        """Test HTTP MCP server with minimal configuration."""
        server = HttpMCPServer(url="https://api.example.com/mcp")
        assert server.type == "http"
        assert server.url == "https://api.example.com/mcp"
        assert server.headers == {}
        assert server.config.expDays == 30

    def test_http_server_with_headers(self):
        """Test HTTP MCP server with headers."""
        server = HttpMCPServer(
            url="https://api.githubcopilot.com/mcp/",
            headers={"Authorization": "Bearer {{env.GITHUB_MCP_PAT}}"},
        )
        assert server.url == "https://api.githubcopilot.com/mcp/"
        assert server.headers["Authorization"] == "Bearer {{env.GITHUB_MCP_PAT}}"

    def test_http_server_with_config(self):
        """Test HTTP MCP server with custom configuration."""
        config = MCPServerConfig(expDays=5, filter="except", filterValue="admin_tools")
        server = HttpMCPServer(url="https://api.example.com/mcp", config=config)
        assert server.config.expDays == 5
        assert server.config.filter == "except"
        assert server.config.filterValue == "admin_tools"

    def test_http_server_from_dict(self):
        """Test creating HTTP MCP server from dictionary."""
        data = {
            "type": "http",
            "url": "https://api.example.com/mcp",
            "headers": {"X-API-Key": "secret"},
            "config": {"expDays": 15},
        }
        server = HttpMCPServer(**data)
        assert server.url == "https://api.example.com/mcp"
        assert server.headers == {"X-API-Key": "secret"}
        assert server.config.expDays == 15


class TestToolWithMCPExecution:
    """Tests for Tool model with MCP execution."""

    def test_tool_with_mcp_execution(self):
        """Test Tool with MCP execution configuration."""
        tool = Tool(
            name="github_list_repos",
            description="List GitHub repositories",
            execution=MCPExecutionConfig(
                type=ExecutionType.MCP, serverName="github", toolName="list_repos"
            ),
        )
        assert tool.name == "github_list_repos"
        assert tool.execution.type == ExecutionType.MCP
        assert tool.execution.serverName == "github"
        assert tool.execution.toolName == "list_repos"

    def test_tool_with_mcp_execution_from_dict(self):
        """Test creating Tool with MCP execution from dictionary."""
        data = {
            "name": "filesystem_read",
            "description": "Read file from filesystem",
            "execution": {
                "type": "mcp",
                "serverName": "filesystem",
                "toolName": "read_file",
            },
        }
        tool = Tool(**data)
        assert tool.execution.type == ExecutionType.MCP
        assert tool.execution.serverName == "filesystem"
        assert tool.execution.toolName == "read_file"
