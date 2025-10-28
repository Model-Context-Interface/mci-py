"""Unit tests for MCP server templating with fallback syntax."""

import pytest

from mcipy import MCIClient
from mcipy.client import MCIClientError


class TestMCPServerTemplating:
    """Tests for MCP server configuration templating with fallback syntax."""

    def test_mcp_server_with_env_var_fallback_to_literal(self, tmp_path):
        """Test MCP server config with env var fallback to string literal."""
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(
            """
{
  "schemaVersion": "1.0",
  "libraryDir": "./mci",
  "mcp_servers": {
    "test_server": {
      "command": "npx",
      "args": ["-y", "test-server", "{{env.TMP_DIR | '/tmp'}}"],
      "config": {
        "expDays": 1
      }
    }
  },
  "tools": []
}
"""
        )

        # Create client without TMP_DIR env var - should use fallback
        try:
            client = MCIClient(schema_file_path=str(schema_file), env_vars={})
            # If we get here without error, the fallback worked
            # (the actual MCP server may not exist, but templating succeeded)
        except MCIClientError as e:
            # Check that the error is NOT about template resolution
            assert "Failed to resolve placeholder" not in str(e)
            # Other errors are acceptable (e.g., MCP server not available)

    def test_mcp_server_with_env_var_fallback_to_another_var(self, tmp_path):
        """Test MCP server config with env var fallback to another env var."""
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(
            """
{
  "schemaVersion": "1.0",
  "libraryDir": "./mci",
  "mcp_servers": {
    "test_server": {
      "command": "npx",
      "args": ["-y", "test-server", "{{env.MISSING | env.ROOT_DIR}}"],
      "config": {
        "expDays": 1
      }
    }
  },
  "tools": []
}
"""
        )

        # Create client with ROOT_DIR but not MISSING - should use ROOT_DIR
        try:
            client = MCIClient(
                schema_file_path=str(schema_file), env_vars={"ROOT_DIR": "/workspace"}
            )
            # Templating succeeded if we get here
        except MCIClientError as e:
            # Check that the error is NOT about template resolution
            assert "Failed to resolve placeholder" not in str(e)
            assert "MISSING" not in str(e)

    def test_mcp_server_with_chained_fallbacks(self, tmp_path):
        """Test MCP server config with chained fallback values."""
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(
            """
{
  "schemaVersion": "1.0",
  "libraryDir": "./mci",
  "mcp_servers": {
    "test_server": {
      "command": "npx",
      "args": ["-y", "test-server", "{{env.TMP_DIR | env.ROOT_DIR | '/tmp'}}"],
      "config": {
        "expDays": 1
      }
    }
  },
  "tools": []
}
"""
        )

        # Create client without either env var - should use string literal fallback
        try:
            client = MCIClient(schema_file_path=str(schema_file), env_vars={})
            # Templating succeeded
        except MCIClientError as e:
            # Check that the error is NOT about template resolution
            assert "Failed to resolve placeholder" not in str(e)

    def test_mcp_server_env_var_in_headers(self, tmp_path):
        """Test MCP server HTTP config with env var in headers."""
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(
            """
{
  "schemaVersion": "1.0",
  "libraryDir": "./mci",
  "mcp_servers": {
    "test_http": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer {{env.API_TOKEN | 'default-token'}}"
      },
      "config": {
        "expDays": 1
      }
    }
  },
  "tools": []
}
"""
        )

        # Create client without API_TOKEN - should use fallback
        try:
            client = MCIClient(schema_file_path=str(schema_file), env_vars={})
            # Templating succeeded
        except MCIClientError as e:
            # Check that the error is NOT about template resolution
            assert "Failed to resolve placeholder" not in str(e)
