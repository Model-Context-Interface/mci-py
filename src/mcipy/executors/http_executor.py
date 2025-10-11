"""
HTTP executor for MCI tools.

This module provides the HTTPExecutor class that handles HTTP-based tool execution.
It supports various HTTP methods, authentication types (API Key, Bearer, Basic, OAuth2),
request body types (JSON, form, raw), and retry logic with exponential backoff.
"""

import base64
import time
from collections.abc import Callable
from typing import Any

import requests

from ..models import (
    ApiKeyAuth,
    AuthConfig,
    BasicAuth,
    BearerAuth,
    ExecutionConfig,
    ExecutionResult,
    HTTPBodyConfig,
    HTTPExecutionConfig,
    OAuth2Auth,
    RetryConfig,
)
from .base import BaseExecutor


class HTTPExecutor(BaseExecutor):
    """
    Executor for HTTP-based tools.

    Handles HTTP requests with various authentication methods, body types,
    and retry logic. Supports GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS methods.
    """

    def __init__(self):
        """Initialize the HTTP executor with a template engine."""
        super().__init__()

    def execute(self, config: ExecutionConfig, context: dict[str, Any]) -> ExecutionResult:
        """
        Execute an HTTP-based tool by making an HTTP request.

        Args:
            config: HTTP execution configuration with URL, method, headers, auth, etc.
            context: Context dictionary with 'props', 'env', and 'input' keys

        Returns:
            ExecutionResult with response content or error
        """
        # Type check to ensure we got the right config type
        if not isinstance(config, HTTPExecutionConfig):
            return self._format_error(
                TypeError(f"Expected HTTPExecutionConfig, got {type(config).__name__}")
            )

        try:
            # Apply basic templating to all config fields (URL, headers, params, etc.)
            # This also handles auth fields that contain templates
            self._apply_basic_templating_to_config(config, context)

            # Apply templating to auth fields (it's a nested Pydantic model)
            if config.auth:
                for field_name, field_value in config.auth.__dict__.items():
                    if isinstance(field_value, str):
                        setattr(
                            config.auth,
                            field_name,
                            self.template_engine.render_basic(field_value, context),
                        )

            # Apply templating to body content if present (it's a nested Pydantic model)
            if config.body:
                if isinstance(config.body.content, dict):
                    self._apply_basic_templating_to_dict(config.body.content, context)
                elif isinstance(config.body.content, str):  # pyright: ignore[reportUnnecessaryIsInstance]
                    config.body.content = self.template_engine.render_basic(
                        config.body.content, context
                    )

            # Build request kwargs
            request_kwargs: dict[str, Any] = {
                "method": config.method.upper(),
                "url": config.url,
                "timeout": self._handle_timeout(config.timeout_ms),
            }

            # Add headers if provided
            if config.headers:
                request_kwargs["headers"] = config.headers.copy()

            # Add query parameters if provided
            if config.params:
                request_kwargs["params"] = config.params

            # Apply authentication if configured
            if config.auth:
                self._apply_authentication(config.auth, request_kwargs)

            # Build and add body if provided
            if config.body:
                body_data, content_type = self._build_body(config.body, context)
                if body_data is not None:
                    if config.body.type == "json":
                        request_kwargs["json"] = body_data
                    elif config.body.type == "form":
                        request_kwargs["data"] = body_data
                    else:  # raw
                        request_kwargs["data"] = body_data

                    # Set Content-Type header if not already set and we have a content type
                    if content_type and "headers" in request_kwargs:
                        if "Content-Type" not in request_kwargs["headers"]:
                            request_kwargs["headers"]["Content-Type"] = content_type

            # Execute request with retry logic
            if config.retries:
                response = self._apply_retry_logic(
                    lambda: requests.request(**request_kwargs),
                    config.retries,
                )
            else:
                response = requests.request(**request_kwargs)

            # Check for HTTP errors
            response.raise_for_status()

            # Try to parse as JSON, otherwise return text
            try:
                content = response.json()
            except ValueError:
                content = response.text

            return ExecutionResult(
                isError=False,
                content=content,
                error=None,
                metadata={"status_code": response.status_code},
            )

        except Exception as e:
            return self._format_error(e)

    def _apply_authentication(self, auth: AuthConfig, request_kwargs: dict[str, Any]) -> None:
        """
        Apply authentication configuration to the request.

        Dispatches to the appropriate auth handler based on auth type.

        Args:
            auth: Authentication configuration
            request_kwargs: Request keyword arguments dictionary (modified in-place)
        """
        if isinstance(auth, ApiKeyAuth):
            self._handle_api_key_auth(auth, request_kwargs)
        elif isinstance(auth, BearerAuth):
            self._handle_bearer_auth(auth, request_kwargs)
        elif isinstance(auth, BasicAuth):
            self._handle_basic_auth(auth, request_kwargs)
        elif isinstance(auth, OAuth2Auth):  # pyright: ignore[reportUnnecessaryIsInstance]
            self._handle_oauth2_auth(auth, request_kwargs)

    def _handle_api_key_auth(self, auth: ApiKeyAuth, request_kwargs: dict[str, Any]) -> None:
        """
        Apply API Key authentication to the request.

        API keys can be placed in headers or query parameters.

        Args:
            auth: API Key authentication configuration
            request_kwargs: Request keyword arguments dictionary (modified in-place)
        """
        if auth.in_ == "header":
            # Add to headers
            if "headers" not in request_kwargs:
                request_kwargs["headers"] = {}
            request_kwargs["headers"][auth.name] = auth.value
        elif auth.in_ == "query":
            # Add to query parameters
            if "params" not in request_kwargs:
                request_kwargs["params"] = {}
            request_kwargs["params"][auth.name] = auth.value

    def _handle_bearer_auth(self, auth: BearerAuth, request_kwargs: dict[str, Any]) -> None:
        """
        Apply Bearer token authentication to the request.

        Bearer tokens are added to the Authorization header.

        Args:
            auth: Bearer authentication configuration
            request_kwargs: Request keyword arguments dictionary (modified in-place)
        """
        if "headers" not in request_kwargs:
            request_kwargs["headers"] = {}
        request_kwargs["headers"]["Authorization"] = f"Bearer {auth.token}"

    def _handle_basic_auth(self, auth: BasicAuth, request_kwargs: dict[str, Any]) -> None:
        """
        Apply Basic authentication to the request.

        Basic auth credentials are base64-encoded and added to the Authorization header.

        Args:
            auth: Basic authentication configuration
            request_kwargs: Request keyword arguments dictionary (modified in-place)
        """
        # Encode credentials as base64
        credentials = f"{auth.username}:{auth.password}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        if "headers" not in request_kwargs:
            request_kwargs["headers"] = {}
        request_kwargs["headers"]["Authorization"] = f"Basic {encoded}"

    def _handle_oauth2_auth(self, auth: OAuth2Auth, request_kwargs: dict[str, Any]) -> None:
        """
        Apply OAuth2 authentication to the request.

        Fetches an access token using client credentials flow and adds it
        to the Authorization header.

        Args:
            auth: OAuth2 authentication configuration
            request_kwargs: Request keyword arguments dictionary (modified in-place)

        Raises:
            RuntimeError: If token retrieval fails
        """
        # Currently only supporting client credentials flow
        if auth.flow != "clientCredentials":
            raise ValueError(f"Unsupported OAuth2 flow: {auth.flow}")

        # Request access token
        token_data = {
            "grant_type": "client_credentials",
            "client_id": auth.clientId,
            "client_secret": auth.clientSecret,
        }

        if auth.scopes:
            token_data["scope"] = " ".join(auth.scopes)

        token_response = requests.post(
            auth.tokenUrl,
            data=token_data,
            timeout=30,
        )
        token_response.raise_for_status()

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            raise RuntimeError("OAuth2 token response missing access_token")

        # Add bearer token to request
        if "headers" not in request_kwargs:
            request_kwargs["headers"] = {}
        request_kwargs["headers"]["Authorization"] = f"Bearer {access_token}"

    def _build_body(
        self,
        body_config: HTTPBodyConfig,
        _context: dict[str, Any],  # pyright: ignore[reportUnusedParameter]
    ) -> tuple[Any, str | None]:
        """
        Build the request body from the body configuration.

        Handles JSON, form, and raw body types. Note that basic templating has
        already been applied to the body_config.content by the time this is called.

        Args:
            body_config: HTTP body configuration
            context: Context dictionary (unused, kept for API consistency)

        Returns:
            Tuple of (body_data, content_type)

        Raises:
            ValueError: If body type is invalid
        """
        if body_config.type == "json":
            # Content is a dict that should be sent as JSON
            return (body_config.content, "application/json")
        elif body_config.type == "form":
            # Content is a dict that should be sent as form data
            return (body_config.content, "application/x-www-form-urlencoded")
        elif body_config.type == "raw":
            # Content is a string that should be sent as-is
            return (body_config.content, "text/plain")
        else:
            raise ValueError(f"Unsupported body type: {body_config.type}")

    def _apply_retry_logic(
        self, func: Callable[[], requests.Response], retries: RetryConfig
    ) -> requests.Response:
        """
        Apply retry logic with exponential backoff to a function.

        Retries on request exceptions and HTTP 5xx errors.

        Args:
            func: Function to call (should return a requests.Response)
            retries: Retry configuration with attempts and backoff

        Returns:
            Response from successful request

        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        backoff_ms = retries.backoff_ms

        for attempt in range(retries.attempts):
            try:
                response = func()
                # Only retry on server errors (5xx)
                if response.status_code < 500:
                    return response
                # Server error - will retry if attempts remain
                last_exception = requests.HTTPError(
                    f"Server error: {response.status_code}", response=response
                )
            except (
                requests.RequestException,
                requests.ConnectionError,
                requests.Timeout,
            ) as e:
                last_exception = e

            # If this wasn't the last attempt, sleep before retrying
            if attempt < retries.attempts - 1:
                time.sleep(backoff_ms / 1000.0)
                # Exponential backoff: double the backoff time for next attempt
                backoff_ms *= 2

        # All retries exhausted
        if last_exception:
            raise last_exception
        # Should not reach here, but just in case
        raise RuntimeError("All retry attempts failed")
