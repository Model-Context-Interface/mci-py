"""
Pydantic data models for MCI schema validation.

This module defines the data structures used throughout the MCI adapter,
providing strong typing, validation, and schema enforcement for:
- Top-level MCI schema with metadata and tools
- Tool definitions with input schemas and execution configurations
- Execution configurations for different execution types (HTTP, CLI, File, Text)
- Authentication configurations
- Execution results
"""

from typing import Any

from pydantic import BaseModel, Field

from .enums import ExecutionType


class Metadata(BaseModel):
    """
    Optional metadata for an MCI schema.

    Contains descriptive information about the tool collection,
    such as name, version, description, license, and authors.
    """

    name: str | None = None
    description: str | None = None
    version: str | None = None
    license: str | None = None
    authors: list[str] | None = None


class ApiKeyAuth(BaseModel):
    """API Key authentication configuration."""

    type: str = Field(default="apiKey")
    in_: str = Field(alias="in")  # "header" or "query"
    name: str
    value: str


class BearerAuth(BaseModel):
    """Bearer token authentication configuration."""

    type: str = Field(default="bearer")
    token: str


class BasicAuth(BaseModel):
    """Basic authentication configuration."""

    type: str = Field(default="basic")
    username: str
    password: str


class OAuth2Auth(BaseModel):
    """OAuth2 authentication configuration."""

    type: str = Field(default="oauth2")
    flow: str  # "clientCredentials", etc.
    tokenUrl: str
    clientId: str
    clientSecret: str
    scopes: list[str] | None = None


AuthConfig = ApiKeyAuth | BearerAuth | BasicAuth | OAuth2Auth


class RetryConfig(BaseModel):
    """Retry configuration for HTTP requests."""

    attempts: int = Field(default=1, ge=1)
    backoff_ms: int = Field(default=500, ge=0)


class HTTPBodyConfig(BaseModel):
    """HTTP request body configuration."""

    type: str  # "json", "form", "raw"
    content: dict[str, Any] | str


class ExecutionConfig(BaseModel):
    """
    Base execution configuration.

    All execution types inherit from this base model,
    providing the type field to discriminate between different executors.
    """

    type: ExecutionType


class HTTPExecutionConfig(ExecutionConfig):
    """
    HTTP execution configuration.

    Defines how to make HTTP requests including method, URL, headers,
    authentication, query parameters, body, timeout, and retry logic.
    """

    type: ExecutionType = Field(default=ExecutionType.HTTP)
    method: str = Field(default="GET")
    url: str
    headers: dict[str, str] | None = None
    auth: AuthConfig | None = None
    params: dict[str, Any] | None = None
    body: HTTPBodyConfig | None = None
    timeout_ms: int = Field(default=30000, ge=0)
    retries: RetryConfig | None = None


class FlagConfig(BaseModel):
    """CLI flag configuration."""

    from_: str = Field(alias="from")
    type: str  # "boolean" or "value"


class CLIExecutionConfig(ExecutionConfig):
    """
    CLI execution configuration.

    Defines how to execute command-line tools including the command,
    arguments, flags, working directory, and timeout.
    """

    type: ExecutionType = Field(default=ExecutionType.CLI)
    command: str
    args: list[str] | None = None
    flags: dict[str, FlagConfig] | None = None
    cwd: str | None = None
    timeout_ms: int = Field(default=30000, ge=0)


class FileExecutionConfig(ExecutionConfig):
    """
    File execution configuration.

    Defines how to read and parse files, including the file path
    and whether to parse placeholders in the file content.
    """

    type: ExecutionType = Field(default=ExecutionType.FILE)
    path: str
    enableTemplating: bool = Field(default=True)


class TextExecutionConfig(ExecutionConfig):
    """
    Text execution configuration.

    Defines a simple text template that will be processed with
    placeholder substitution and returned as the result.
    """

    type: ExecutionType = Field(default=ExecutionType.TEXT)
    text: str


class Tool(BaseModel):
    """
    Individual tool definition.

    Represents a single tool with its name, title, description,
    input schema (JSON Schema), and execution configuration.
    The execution configuration determines how the tool is executed
    (HTTP, CLI, file, or text).
    """

    name: str
    title: str | None = None
    description: str | None = None
    inputSchema: dict[str, Any] | None = None
    execution: HTTPExecutionConfig | CLIExecutionConfig | FileExecutionConfig | TextExecutionConfig


class MCISchema(BaseModel):
    """
    Top-level MCI schema.

    Represents the complete MCI context file with schema version,
    optional metadata, and a list of tool definitions.
    This is the root model that validates the entire JSON schema.
    """

    schemaVersion: str
    metadata: Metadata | None = None
    tools: list[Tool]


class ExecutionResult(BaseModel):
    """
    Execution result format.

    Represents the result of executing a tool, including whether
    an error occurred and the content or error message.
    This provides a consistent format for all execution results.
    """

    isError: bool
    content: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None
