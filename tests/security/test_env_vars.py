"""
Security tests for environment variable handling.

This module tests that secrets and credentials are only obtained from environment
variables and cannot be injected or exposed through other means such as properties,
input data, or template manipulation.

Security concerns tested:
- Environment variables cannot be overridden by properties
- Secrets are only accessible through the 'env' context
- Template injection cannot access unintended environment variables
- Environment variable values are not exposed in error messages
"""

import pytest

from mcipy.client import MCIClient
from mcipy.executors.cli_executor import CLIExecutor
from mcipy.executors.file_executor import FileExecutor
from mcipy.executors.http_executor import HTTPExecutor
from mcipy.models import (
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
)
from mcipy.templating import TemplateEngine, TemplateError


class TestEnvironmentVariableSecurity:
    """Tests for environment variable security."""

    @pytest.fixture
    def template_engine(self):
        """Fixture for TemplateEngine instance."""
        return TemplateEngine()

    @pytest.fixture
    def secure_context(self):
        """Fixture for a secure context with sensitive env vars."""
        return {
            "props": {"api_key": "user_provided_key", "password": "user_password"},
            "env": {"API_KEY": "secret_api_key_123", "DB_PASSWORD": "super_secret_pass"},
            "input": {"api_key": "user_provided_key", "password": "user_password"},
        }

    def test_env_vars_cannot_be_overridden_by_props(self, template_engine, secure_context):
        """
        Test that environment variables cannot be overridden by properties.

        Security Risk: If props could override env vars, an attacker could
        inject malicious values to replace secrets or credentials.
        """
        # Try to use a property with the same name as an env var
        template = "API Key: {{env.API_KEY}}"
        result = template_engine.render_basic(template, secure_context)

        # Should use the env var, not the prop with a similar name
        assert result == "API Key: secret_api_key_123"
        assert "user_provided_key" not in result

    def test_env_vars_not_accessible_via_props(self, template_engine, secure_context):
        """
        Test that env vars are not accessible through the props namespace.

        Security Risk: If env vars were accessible via props, it could lead
        to unintended secret exposure.
        """
        # Trying to access env var through props should fail
        template = "{{props.API_KEY}}"

        with pytest.raises(TemplateError):
            template_engine.render_basic(template, secure_context)

    def test_env_vars_not_accessible_via_input(self, template_engine, secure_context):
        """
        Test that env vars are not accessible through the input namespace.

        Security Risk: Similar to props, input should not expose env vars.
        """
        template = "{{input.DB_PASSWORD}}"

        with pytest.raises(TemplateError):
            template_engine.render_basic(template, secure_context)

    def test_secrets_only_from_env_context(self, template_engine):
        """
        Test that secrets can only be accessed from the env context.

        Security Risk: Ensures that the only way to access environment
        variables is through the designated 'env' namespace.
        """
        context = {
            "props": {},
            "env": {"SECRET_TOKEN": "abc123xyz"},
            "input": {},
        }

        # This should work - accessing env var correctly
        template = "Token: {{env.SECRET_TOKEN}}"
        result = template_engine.render_basic(template, context)
        assert result == "Token: abc123xyz"

        # Try to access it any other way should fail
        invalid_templates = [
            "{{SECRET_TOKEN}}",  # Direct access without namespace
            "{{props.SECRET_TOKEN}}",  # Through props
            "{{input.SECRET_TOKEN}}",  # Through input
        ]

        for invalid_template in invalid_templates:
            with pytest.raises(TemplateError):
                template_engine.render_basic(invalid_template, context)

    def test_template_injection_cannot_access_env_vars(self, template_engine):
        """
        Test that template injection attempts cannot access env vars.

        Security Risk: An attacker might try to inject template syntax
        through properties to access environment variables.
        """
        context = {
            "props": {
                # Attacker tries to inject template to access env var
                "user_input": "{{env.API_KEY}}",
            },
            "env": {"API_KEY": "secret_key_should_not_appear"},
            "input": {"user_input": "{{env.API_KEY}}"},
        }

        # When we render props.user_input, it should not re-evaluate the template
        template = "User said: {{props.user_input}}"
        result = template_engine.render_basic(template, context)

        # The injected template should be treated as literal text
        assert result == "User said: {{env.API_KEY}}"
        # The secret should NOT appear in the result
        assert "secret_key_should_not_appear" not in result

    def test_nested_template_injection_blocked(self, template_engine):
        """
        Test that nested/double template injection is blocked.

        Security Risk: Attacker might try nested templates to bypass security.
        """
        context = {
            "props": {
                "malicious": "env.API_KEY}}",
                "prefix": "{{",
            },
            "env": {"API_KEY": "super_secret_key"},
            "input": {},
        }

        # Try to construct a template from parts
        template = "Value: {{props.prefix}}{{props.malicious}}"
        result = template_engine.render_basic(template, context)

        # Should render the literal values, not re-evaluate
        assert result == "Value: {{env.API_KEY}}"
        assert "super_secret_key" not in result

    def test_http_executor_env_var_isolation(self):
        """
        Test that HTTP executor properly isolates env vars from props.

        Security Risk: Ensure HTTP auth configurations use env vars securely.
        """
        executor = HTTPExecutor()

        config = HTTPExecutionConfig(
            method="GET",
            url="https://api.example.com/{{props.endpoint}}",
        )

        context = {
            "props": {"endpoint": "data", "API_KEY": "malicious_key"},
            "env": {"API_KEY": "correct_secret_key"},
            "input": {"endpoint": "data"},
        }

        # Apply templating to config
        executor._apply_basic_templating_to_config(config, context)

        # URL should use props.endpoint correctly
        assert config.url == "https://api.example.com/data"

        # If config had auth with {{env.API_KEY}}, it should use env not props
        config_with_auth = HTTPExecutionConfig(
            method="GET",
            url="https://api.example.com/data",
            headers={"Authorization": "Bearer {{env.API_KEY}}"},
        )

        executor._apply_basic_templating_to_config(config_with_auth, context)
        assert config_with_auth.headers["Authorization"] == "Bearer correct_secret_key"

    def test_cli_executor_env_var_isolation(self):
        """
        Test that CLI executor properly isolates env vars from props.

        Security Risk: Ensure CLI commands use env vars securely.
        """
        executor = CLIExecutor()

        config = CLIExecutionConfig(
            command="echo",
            args=["{{env.SECRET}}", "{{props.public}}"],
        )

        context = {
            "props": {"public": "public_value", "SECRET": "not_the_secret"},
            "env": {"SECRET": "actual_secret"},
            "input": {"public": "public_value"},
        }

        executor._apply_basic_templating_to_config(config, context)

        # Should use env.SECRET and props.public correctly
        assert config.args[0] == "actual_secret"
        assert config.args[1] == "public_value"

    def test_file_executor_env_var_isolation(self):
        """
        Test that file executor properly isolates env vars from props.

        Security Risk: Ensure file paths use env vars securely.
        """
        executor = FileExecutor()

        config = FileExecutionConfig(
            path="/home/{{env.USER}}/files/{{props.filename}}",
            enableTemplating=False,
        )

        context = {
            "props": {"filename": "data.txt", "USER": "attacker"},
            "env": {"USER": "legitimate_user"},
            "input": {"filename": "data.txt"},
        }

        executor._apply_basic_templating_to_config(config, context)

        # Should use env.USER, not props.USER
        assert config.path == "/home/legitimate_user/files/data.txt"

    def test_env_vars_not_in_error_messages(self):
        """
        Test that environment variables don't leak in error messages.

        Security Risk: Error messages might inadvertently expose secrets.
        """
        template_engine = TemplateEngine()

        context = {
            "props": {},
            "env": {"SECRET_KEY": "very_secret_value_12345"},
            "input": {},
        }

        # Try to access a non-existent env var
        template = "{{env.NONEXISTENT_VAR}}"

        with pytest.raises(Exception) as exc_info:
            template_engine.render_basic(template, context)

        error_message = str(exc_info.value)

        # Error message should not contain other env var values
        assert "very_secret_value_12345" not in error_message

    def test_mci_client_env_isolation(self, tmp_path):
        """
        Test that MCIClient properly isolates environment variables.

        Security Risk: Ensure client-level env var handling is secure.
        """
        # Create a test schema file
        schema_file = tmp_path / "test.mci.json"
        schema_file.write_text(
            """{
            "schemaVersion": "1.0",
            "tools": [{
                "name": "test_tool",
                "title": "Test Tool",
                "description": "Test",
                "inputSchema": {
                    "type": "object",
                    "properties": {"endpoint": {"type": "string"}}
                },
                "execution": {
                    "type": "text",
                    "text": "API: {{env.API_KEY}}, Endpoint: {{props.endpoint}}"
                }
            }]
        }"""
        )

        # Create client with env vars
        client = MCIClient(
            json_file_path=str(schema_file),
            env_vars={"API_KEY": "secret_from_env"},
        )

        # Execute with props that try to override env
        result = client.execute(
            tool_name="test_tool",
            properties={"endpoint": "/data", "API_KEY": "malicious_override"},
        )

        # Should use env.API_KEY, not props.API_KEY
        assert not result.isError
        assert "secret_from_env" in result.content
        assert "malicious_override" not in result.content

    def test_advanced_templating_env_isolation(self, template_engine):
        """
        Test that advanced templating (loops, conditionals) maintains env isolation.

        Security Risk: Complex templates might have vulnerabilities.
        """
        context = {
            "props": {"items": ["a", "b", "c"], "SECRET": "not_secret"},
            "env": {"SECRET": "actual_secret"},
            "input": {"items": ["a", "b", "c"]},
        }

        # Test with foreach loop
        template = """
@foreach(item in props.items)
Item: {{item}}, Secret: {{env.SECRET}}
@endforeach
"""
        result = template_engine.render_advanced(template, context)

        # Should use env.SECRET in all iterations
        assert result.count("actual_secret") == 3
        assert "not_secret" not in result

    def test_conditional_env_isolation(self, template_engine):
        """
        Test that conditional blocks maintain env var isolation.

        Security Risk: Conditionals might expose env vars incorrectly.
        """
        context = {
            "props": {"debug": True},
            "env": {"DEBUG_KEY": "secret_debug_key"},
            "input": {"debug": True},
        }

        template = """
@if(props.debug)
Debug Mode: {{env.DEBUG_KEY}}
@else
Production Mode
@endif
"""
        result = template_engine.render_advanced(template, context)

        # Should show the debug key from env
        assert "secret_debug_key" in result
        assert "Debug Mode" in result
