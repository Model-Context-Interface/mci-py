"""Unit tests for HTTPExecutor class."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

from mcipy.executors.http_executor import HTTPExecutor
from mcipy.models import (
    ApiKeyAuth,
    BasicAuth,
    BearerAuth,
    HTTPBodyConfig,
    HTTPExecutionConfig,
    OAuth2Auth,
    RetryConfig,
)


class TestHTTPExecutor:
    """Tests for HTTPExecutor class."""

    @pytest.fixture
    def executor(self):
        """Fixture for HTTPExecutor instance."""
        return HTTPExecutor()

    @pytest.fixture
    def context(self):
        """Fixture for test context."""
        return {
            "props": {"location": "Seattle", "user": "Alice"},
            "env": {"API_KEY": "secret123", "TOKEN": "bearer-token", "USERNAME": "user1"},
            "input": {"location": "Seattle", "user": "Alice"},
        }

    def test_execute_simple_get_request(self, executor, context):
        """Test executing a simple GET request."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Success"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            assert result.content == "Success"
            assert result.error is None
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["method"] == "GET"
            assert mock_request.call_args[1]["url"] == "https://api.example.com/data"

    def test_execute_get_request_with_json_response(self, executor, context):
        """Test executing a GET request that returns JSON."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok", "data": [1, 2, 3]}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            assert result.content == {"status": "ok", "data": [1, 2, 3]}
            assert result.error is None

    def test_execute_post_request_with_json_body(self, executor, context):
        """Test executing a POST request with JSON body."""
        body = HTTPBodyConfig(type="json", content={"key": "value", "num": 42})
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="POST",
            body=body,
            headers={"Accept": "application/json"},
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"created": True}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            assert result.content == {"created": True}
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["json"] == {"key": "value", "num": 42}

    def test_execute_post_request_with_form_body(self, executor, context):
        """Test executing a POST request with form data."""
        body = HTTPBodyConfig(type="form", content={"username": "alice", "password": "secret"})
        config = HTTPExecutionConfig(
            url="https://api.example.com/login",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"token": "abc123"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["data"] == {"username": "alice", "password": "secret"}

    def test_execute_post_request_with_raw_body(self, executor, context):
        """Test executing a POST request with raw body."""
        body = HTTPBodyConfig(type="raw", content="plain text data")
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["data"] == "plain text data"

    def test_execute_with_query_parameters(self, executor, context):
        """Test executing a request with query parameters."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/search",
            method="GET",
            params={"q": "test", "limit": 10},
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["params"] == {"q": "test", "limit": 10}

    def test_execute_with_templated_url(self, executor, context):
        """Test executing a request with templated URL."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/users/{{props.user}}/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Data"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            # URL should have been templated
            assert mock_request.call_args[1]["url"] == "https://api.example.com/users/Alice/data"

    def test_execute_with_templated_headers(self, executor, context):
        """Test executing a request with templated headers."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            headers={"X-User": "{{props.user}}", "X-Location": "{{props.location}}"},
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            headers = mock_request.call_args[1]["headers"]
            assert headers["X-User"] == "Alice"
            assert headers["X-Location"] == "Seattle"

    def test_execute_with_templated_params(self, executor, context):
        """Test executing a request with templated query parameters."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            params={"location": "{{props.location}}", "user": "{{props.user}}"},
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            params = mock_request.call_args[1]["params"]
            assert params["location"] == "Seattle"
            assert params["user"] == "Alice"

    def test_execute_with_templated_json_body(self, executor, context):
        """Test executing a request with templated JSON body."""
        body = HTTPBodyConfig(
            type="json", content={"location": "{{props.location}}", "user": "{{props.user}}"}
        )
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="POST",
            body=body,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            json_data = mock_request.call_args[1]["json"]
            assert json_data["location"] == "Seattle"
            assert json_data["user"] == "Alice"

    def test_execute_with_timeout(self, executor, context):
        """Test that timeout is properly converted and applied."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            timeout_ms=5000,  # 5 seconds
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            # Timeout should be converted to seconds
            assert mock_request.call_args[1]["timeout"] == 5

    def test_execute_with_http_error(self, executor, context):
        """Test handling of HTTP error responses."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert result.isError
            assert "404 Not Found" in result.error

    def test_execute_with_connection_error(self, executor, context):
        """Test handling of connection errors."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_request.side_effect = requests.ConnectionError("Connection failed")

            result = executor.execute(config, context)

            assert result.isError
            assert "Connection failed" in result.error

    def test_execute_with_timeout_error(self, executor, context):
        """Test handling of timeout errors."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_request.side_effect = requests.Timeout("Request timed out")

            result = executor.execute(config, context)

            assert result.isError
            assert "Request timed out" in result.error

    def test_execute_with_wrong_config_type(self, executor, context):
        """Test that wrong config type is handled properly."""
        from mcipy.models import TextExecutionConfig

        config = TextExecutionConfig(text="test")
        result = executor.execute(config, context)

        assert result.isError
        assert "Expected HTTPExecutionConfig" in result.error

    def test_apply_api_key_auth_in_header(self, executor):
        """Test applying API key authentication in header."""
        auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "secret123"})
        request_kwargs: dict[str, Any] = {}

        executor._apply_authentication(auth, request_kwargs)

        assert "headers" in request_kwargs
        assert request_kwargs["headers"]["X-API-Key"] == "secret123"

    def test_apply_api_key_auth_in_query(self, executor):
        """Test applying API key authentication in query parameters."""
        auth = ApiKeyAuth(**{"in": "query", "name": "api_key", "value": "secret123"})
        request_kwargs: dict[str, Any] = {}

        executor._apply_authentication(auth, request_kwargs)

        assert "params" in request_kwargs
        assert request_kwargs["params"]["api_key"] == "secret123"

    def test_apply_bearer_auth(self, executor):
        """Test applying Bearer token authentication."""
        auth = BearerAuth(token="bearer-token-123")
        request_kwargs: dict[str, Any] = {}

        executor._apply_authentication(auth, request_kwargs)

        assert "headers" in request_kwargs
        assert request_kwargs["headers"]["Authorization"] == "Bearer bearer-token-123"

    def test_apply_basic_auth(self, executor):
        """Test applying Basic authentication."""
        auth = BasicAuth(username="user1", password="pass123")
        request_kwargs: dict[str, Any] = {}

        executor._apply_authentication(auth, request_kwargs)

        assert "headers" in request_kwargs
        # Check that Authorization header is set with Basic scheme
        assert request_kwargs["headers"]["Authorization"].startswith("Basic ")
        # Decode and verify (base64 of "user1:pass123")
        import base64

        encoded = request_kwargs["headers"]["Authorization"].split(" ")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == "user1:pass123"

    def test_apply_oauth2_auth_client_credentials(self, executor):
        """Test applying OAuth2 client credentials authentication."""
        auth = OAuth2Auth(
            flow="clientCredentials",
            tokenUrl="https://auth.example.com/token",
            clientId="client123",
            clientSecret="secret456",
            scopes=["read", "write"],
        )
        request_kwargs: dict[str, Any] = {}

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "oauth-token-xyz"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            executor._apply_authentication(auth, request_kwargs)

            # Verify token request
            mock_post.assert_called_once()
            assert mock_post.call_args[0][0] == "https://auth.example.com/token"
            token_data = mock_post.call_args[1]["data"]
            assert token_data["grant_type"] == "client_credentials"
            assert token_data["client_id"] == "client123"
            assert token_data["client_secret"] == "secret456"
            assert token_data["scope"] == "read write"

            # Verify token was added to request
            assert "headers" in request_kwargs
            assert request_kwargs["headers"]["Authorization"] == "Bearer oauth-token-xyz"

    def test_apply_oauth2_auth_without_scopes(self, executor):
        """Test OAuth2 authentication without scopes."""
        auth = OAuth2Auth(
            flow="clientCredentials",
            tokenUrl="https://auth.example.com/token",
            clientId="client123",
            clientSecret="secret456",
        )
        request_kwargs: dict[str, Any] = {}

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "oauth-token"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            executor._apply_authentication(auth, request_kwargs)

            # Verify no scope in token request
            token_data = mock_post.call_args[1]["data"]
            assert "scope" not in token_data

    def test_apply_oauth2_auth_missing_access_token(self, executor):
        """Test OAuth2 authentication when access_token is missing from response."""
        auth = OAuth2Auth(
            flow="clientCredentials",
            tokenUrl="https://auth.example.com/token",
            clientId="client123",
            clientSecret="secret456",
        )
        request_kwargs: dict[str, Any] = {}

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"token_type": "bearer"}  # Missing access_token
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            with pytest.raises(RuntimeError, match="missing access_token"):
                executor._apply_authentication(auth, request_kwargs)

    def test_apply_oauth2_auth_unsupported_flow(self, executor):
        """Test OAuth2 authentication with unsupported flow."""
        auth = OAuth2Auth(
            flow="authorizationCode",  # Not supported
            tokenUrl="https://auth.example.com/token",
            clientId="client123",
            clientSecret="secret456",
        )
        request_kwargs: dict[str, Any] = {}

        with pytest.raises(ValueError, match="Unsupported OAuth2 flow"):
            executor._apply_authentication(auth, request_kwargs)

    def test_execute_with_api_key_auth_templated(self, executor, context):
        """Test full execution with API key auth using templated values."""
        auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "{{env.API_KEY}}"})
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            auth=auth,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            headers = mock_request.call_args[1]["headers"]
            # Value should be templated
            assert headers["X-API-Key"] == "secret123"

    def test_execute_with_bearer_auth_templated(self, executor, context):
        """Test full execution with Bearer auth using templated token."""
        auth = BearerAuth(token="{{env.TOKEN}}")
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            auth=auth,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            headers = mock_request.call_args[1]["headers"]
            # Token should be templated
            assert headers["Authorization"] == "Bearer bearer-token"

    def test_execute_with_basic_auth_templated(self, executor, context):
        """Test full execution with Basic auth using templated credentials."""
        auth = BasicAuth(username="{{env.USERNAME}}", password="secret")
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            auth=auth,
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            headers = mock_request.call_args[1]["headers"]
            # Username should be templated
            import base64

            encoded = headers["Authorization"].split(" ")[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            assert decoded == "user1:secret"

    def test_build_body_json(self, executor, context):
        """Test building JSON body."""
        body_config = HTTPBodyConfig(type="json", content={"key": "value"})
        body_data, content_type = executor._build_body(body_config, context)

        assert body_data == {"key": "value"}
        assert content_type == "application/json"

    def test_build_body_form(self, executor, context):
        """Test building form body."""
        body_config = HTTPBodyConfig(type="form", content={"username": "alice"})
        body_data, content_type = executor._build_body(body_config, context)

        assert body_data == {"username": "alice"}
        assert content_type == "application/x-www-form-urlencoded"

    def test_build_body_raw(self, executor, context):
        """Test building raw body."""
        body_config = HTTPBodyConfig(type="raw", content="raw text data")
        body_data, content_type = executor._build_body(body_config, context)

        assert body_data == "raw text data"
        assert content_type == "text/plain"

    def test_build_body_invalid_type(self, executor, context):
        """Test building body with invalid type."""
        body_config = HTTPBodyConfig(type="xml", content="<data/>")

        with pytest.raises(ValueError, match="Unsupported body type"):
            executor._build_body(body_config, context)

    def test_apply_retry_logic_success_on_first_attempt(self, executor):
        """Test retry logic when request succeeds on first attempt."""
        retry_config = RetryConfig(attempts=3, backoff_ms=100)
        mock_func = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_func.return_value = mock_response

        result = executor._apply_retry_logic(mock_func, retry_config)

        assert result == mock_response
        mock_func.assert_called_once()

    def test_apply_retry_logic_success_after_retry(self, executor):
        """Test retry logic when request succeeds after retries."""
        retry_config = RetryConfig(attempts=3, backoff_ms=10)
        mock_func = Mock()

        # Fail first two times, succeed on third
        mock_func.side_effect = [
            requests.ConnectionError("Connection failed"),
            requests.Timeout("Timeout"),
            Mock(status_code=200),
        ]

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = executor._apply_retry_logic(mock_func, retry_config)

        assert result.status_code == 200
        assert mock_func.call_count == 3

    def test_apply_retry_logic_all_attempts_fail(self, executor):
        """Test retry logic when all attempts fail."""
        retry_config = RetryConfig(attempts=3, backoff_ms=10)
        mock_func = Mock()
        mock_func.side_effect = requests.ConnectionError("Connection failed")

        with patch("time.sleep"):  # Mock sleep to speed up test
            with pytest.raises(requests.ConnectionError, match="Connection failed"):
                executor._apply_retry_logic(mock_func, retry_config)

        assert mock_func.call_count == 3

    def test_apply_retry_logic_server_error_retries(self, executor):
        """Test retry logic retries on 5xx server errors."""
        retry_config = RetryConfig(attempts=3, backoff_ms=10)
        mock_func = Mock()

        # Server error on first attempt, success on second
        error_response = Mock()
        error_response.status_code = 503
        success_response = Mock()
        success_response.status_code = 200

        mock_func.side_effect = [error_response, success_response]

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = executor._apply_retry_logic(mock_func, retry_config)

        assert result.status_code == 200
        assert mock_func.call_count == 2

    def test_apply_retry_logic_client_error_no_retry(self, executor):
        """Test retry logic does not retry on 4xx client errors."""
        retry_config = RetryConfig(attempts=3, backoff_ms=10)
        mock_func = Mock()

        # Client error (4xx) should not be retried
        error_response = Mock()
        error_response.status_code = 404

        mock_func.return_value = error_response

        result = executor._apply_retry_logic(mock_func, retry_config)

        assert result.status_code == 404
        mock_func.assert_called_once()  # Should not retry

    def test_apply_retry_logic_exponential_backoff(self, executor):
        """Test that retry logic applies exponential backoff."""
        retry_config = RetryConfig(attempts=3, backoff_ms=100)
        mock_func = Mock()
        mock_func.side_effect = [
            requests.ConnectionError("Fail 1"),
            requests.ConnectionError("Fail 2"),
            Mock(status_code=200),
        ]

        with patch("time.sleep") as mock_sleep:
            result = executor._apply_retry_logic(mock_func, retry_config)

        assert result.status_code == 200
        # Should have slept twice (after first and second attempts)
        assert mock_sleep.call_count == 2
        # First sleep: 100ms / 1000 = 0.1s
        assert mock_sleep.call_args_list[0][0][0] == 0.1
        # Second sleep: 200ms / 1000 = 0.2s (exponential backoff)
        assert mock_sleep.call_args_list[1][0][0] == 0.2

    def test_execute_with_retry_success(self, executor, context):
        """Test full execution with retry configuration succeeding after retry."""
        retry_config = RetryConfig(attempts=2, backoff_ms=10)
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            retries=retry_config,
        )

        with patch("requests.request") as mock_request:
            # Fail first time, succeed second time
            error_response = Mock()
            error_response.status_code = 503
            success_response = Mock()
            success_response.status_code = 200
            success_response.text = "Success"
            success_response.json.side_effect = ValueError("Not JSON")
            success_response.raise_for_status = Mock()

            mock_request.side_effect = [error_response, success_response]

            with patch("time.sleep"):
                result = executor.execute(config, context)

            assert not result.isError
            assert result.content == "Success"
            assert mock_request.call_count == 2

    def test_execute_with_retry_all_fail(self, executor, context):
        """Test full execution with retry configuration when all attempts fail."""
        retry_config = RetryConfig(attempts=2, backoff_ms=10)
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
            retries=retry_config,
        )

        with patch("requests.request") as mock_request:
            mock_request.side_effect = requests.ConnectionError("Connection failed")

            with patch("time.sleep"):
                result = executor.execute(config, context)

            assert result.isError
            assert "Connection failed" in result.error
            assert mock_request.call_count == 2

    def test_execute_returns_metadata_with_status_code(self, executor, context):
        """Test that successful execution includes metadata with HTTP status code."""
        config = HTTPExecutionConfig(
            url="https://api.example.com/data",
            method="GET",
        )

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"created": True}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = executor.execute(config, context)

            assert not result.isError
            assert result.metadata is not None
            assert "status_code" in result.metadata
            assert result.metadata["status_code"] == 201
