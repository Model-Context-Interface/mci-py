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

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

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


class MCPExecutionConfig(ExecutionConfig):
    """
    MCP execution configuration.

    Defines how to execute tools via Model Context Protocol servers.
    The serverName must match a server registered in the main schema's
    mcp_servers field, and toolName identifies the specific tool to call.
    """

    type: ExecutionType = Field(default=ExecutionType.MCP)
    serverName: str
    toolName: str


class Annotations(BaseModel):
    """
    Optional annotations about tool behavior.

    Contains hints and metadata about how the tool behaves, including
    display information (title) and behavioral characteristics like
    whether it modifies state, is destructive, idempotent, or interacts
    with external entities. Also includes audience targeting for different roles.
    """

    title: str | None = None
    readOnlyHint: bool | None = None
    destructiveHint: bool | None = None
    idempotentHint: bool | None = None
    openWorldHint: bool | None = None
    audience: list[Literal["user", "assistant"]] | None = None


class Tool(BaseModel):
    """
    Individual tool definition.

    Represents a single tool with its name, description, disabled state,
    annotations, input schema (JSON Schema), and execution configuration.
    The execution configuration determines how the tool is executed
    (HTTP, CLI, file, or text).
    """

    name: str
    disabled: bool = Field(default=False)
    annotations: Annotations | None = None
    description: str | None = None
    inputSchema: dict[str, Any] | None = None
    execution: (
        HTTPExecutionConfig
        | CLIExecutionConfig
        | FileExecutionConfig
        | TextExecutionConfig
        | MCPExecutionConfig
    )
    enableAnyPaths: bool = Field(default=False)
    directoryAllowList: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    toolset_source: str | None = Field(default=None, exclude=True)  # Internal field, not serialized


class Toolset(BaseModel):
    """
    Toolset definition for loading tool collections from library files.

    Represents a reference to a toolset file (or directory) in the libraryDir,
    with optional filtering to control which tools from that toolset are loaded.
    """

    name: str
    filter: str | None = None  # One of: "only", "except", "tags", "withoutTags"
    filterValue: str | None = None  # Comma-separated list of tool names or tags


class MCPServerConfig(BaseModel):
    """
    Configuration for filtering and expiration of MCP toolsets.

    Applied when registering MCP servers to control which tools are loaded
    and how long the cached toolset remains valid.
    """

    expDays: int = Field(default=30, ge=1)  # Days until cached toolset expires
    filter: str | None = None  # One of: "only", "except", "tags", "withoutTags"
    filterValue: str | None = None  # Comma-separated list of tool names or tags


class StdioMCPServer(BaseModel):
    """
    STDIO-based MCP server configuration.

    Used for local MCP servers started via command-line tools like npx or uvx.
    Supports environment variable injection and templating.
    """

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    config: MCPServerConfig = Field(default_factory=MCPServerConfig)


class HttpMCPServer(BaseModel):
    """
    HTTP-based MCP server configuration.

    Used for web-based MCP servers using HTTP with SSE or Streamable HTTP transport.
    Supports custom headers for authentication and templating.
    """

    type: str = Field(default="http")
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    config: MCPServerConfig = Field(default_factory=MCPServerConfig)


MCPServer = StdioMCPServer | HttpMCPServer


class ToolsetSchema(BaseModel):
    """
    Schema for individual toolset files.

    Toolset files can only contain schemaVersion, optional metadata, required tools,
    and optional expiresAt field for MCP toolset caching.
    They cannot contain global configuration fields like toolsets, libraryDir, etc.
    """

    schemaVersion: str
    metadata: Metadata | None = None
    tools: list[Tool]
    expiresAt: str | None = None  # ISO 8601 timestamp for MCP toolset expiration


class MCISchema(BaseModel):
    """
    Top-level MCI schema.

    Represents the complete MCI context file with schema version,
    optional metadata, tool definitions, toolsets, and MCP server configurations.
    This is the root model that validates the entire JSON schema.
    """

    schemaVersion: str
    metadata: Metadata | None = None
    tools: list[Tool] | None = Field(default=None)
    toolsets: list[Toolset | str] | None = Field(default=None)
    mcp_servers: dict[str, MCPServer] | None = Field(default=None)
    libraryDir: str = Field(default="./mci")
    enableAnyPaths: bool = Field(default=False)
    directoryAllowList: list[str] = Field(default_factory=list)

    @field_validator("toolsets", mode="before")
    @classmethod
    def normalize_toolsets(cls, v: Any) -> Any:
        """
        Normalize toolsets to always be Toolset objects.

        Converts string toolset names to Toolset objects with just the name field.
        This allows users to specify simple toolset names without creating full objects
        when no filtering is needed.

        Examples:
            "github" -> {"name": "github"}
            {"name": "github", "filter": "tags", "filterValue": "read"} -> unchanged
        """
        if v is None:
            return v

        normalized = []
        for item in v:
            if isinstance(item, str):
                # Convert string to Toolset dict
                normalized.append({"name": item})
            else:
                # Keep object as is
                normalized.append(item)
        return normalized


class TextContent(BaseModel):
    """
    Text content object for execution results.

    Represents textual content in MCP-compatible format.
    """

    type: str = Field(default="text")
    text: str


class ImageContent(BaseModel):
    """
    Image content object for execution results.

    Represents base64-encoded image data in MCP-compatible format.
    """

    type: str = Field(default="image")
    data: str
    mimeType: str


class AudioContent(BaseModel):
    """
    Audio content object for execution results.

    Represents base64-encoded audio data in MCP-compatible format.
    """

    type: str = Field(default="audio")
    data: str
    mimeType: str


ContentObject = TextContent | ImageContent | AudioContent


class ExecutionResultContent(BaseModel):
    """
    Inner result object containing execution result data.

    Contains the structured content array, error status, and optional metadata.
    """

    content: list[ContentObject]
    isError: bool
    metadata: dict[str, Any] | None = None


class ExecutionResult(BaseModel):
    """
    Execution result format with MCP compatibility.

    Represents the result of executing a tool in MCP-compatible format
    with optional JSON-RPC wrapper fields and structured content array.
    The main result data is contained in the 'result' field.
    """

    result: ExecutionResultContent
    jsonrpc: str | None = Field(default=None)
    id: int | None = Field(default=None)
