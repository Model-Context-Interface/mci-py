"""
Manual test for MCI data models.

This test file demonstrates the usage of MCI data models with realistic examples.
Run this file directly to see the models in action.

Usage:
    uv run python testsManual/test_models_manual.py
"""


from mcipy.models import (
    Annotations,
    ApiKeyAuth,
    BasicAuth,
    BearerAuth,
    CLIExecutionConfig,
    ExecutionResult,
    ExecutionResultContent,
    FileExecutionConfig,
    FlagConfig,
    HTTPBodyConfig,
    HTTPExecutionConfig,
    MCISchema,
    Metadata,
    OAuth2Auth,
    RetryConfig,
    TextContent,
    TextExecutionConfig,
    Tool,
)
from mcipy.tool_manager import ToolManager


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_http_tool_with_api_key():
    """Demonstrate HTTP tool with API key authentication."""
    print_section("HTTP Tool with API Key Authentication")

    auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "{{env.API_KEY}}"})

    body = HTTPBodyConfig(
        type="json", content={"location": "{{input.location}}", "units": "metric"}
    )

    execution = HTTPExecutionConfig(
        url="https://api.weatherapi.com/v1/current.json",
        method="POST",
        headers={"Accept": "application/json", "User-Agent": "MCI-Adapter/1.0"},
        auth=auth,
        params={"lang": "en"},
        body=body,
        timeout_ms=5000,
        retries=RetryConfig(attempts=3, backoff_ms=1000),
    )


    tool = Tool(
        name="get_weather",
        annotations=Annotations(title="Weather Information Provider"),
        description="Get current weather information for a location",
        inputSchema={
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City name or zip code"}},
            "required": ["location"],
        },
        execution=execution,
    )

    print(f"Tool Name: {tool.name}")
    print(f"Title: {tool.annotations.title if tool.annotations else 'None'}")
    print(f"Execution Type: {tool.execution.type}")
    print(f"Method: {tool.execution.method}")
    print(f"URL: {tool.execution.url}")
    print(f"Auth Type: {tool.execution.auth.type if tool.execution.auth else 'None'}")
    print(f"Timeout: {tool.execution.timeout_ms}ms")
    print(f"Retries: {tool.execution.retries.attempts if tool.execution.retries else 'None'}")


def test_cli_tool():
    """Demonstrate CLI tool configuration."""
    print_section("CLI Tool Configuration")


    flags = {
        "-i": FlagConfig(**{"from": "props.ignore_case", "type": "boolean"}),
        "--file": FlagConfig(**{"from": "props.file", "type": "value"}),
    }

    execution = CLIExecutionConfig(
        command="grep",
        args=["-n", "pattern"],
        flags=flags,
        cwd="{{props.directory}}",
        timeout_ms=8000,
    )

    tool = Tool(
        name="search_files",
        annotations=Annotations(title="File Search Tool"),
        description="Search for patterns in files using grep",
        execution=execution,
    )

    print(f"Tool Name: {tool.name}")
    print(f"Command: {tool.execution.command}")
    print(f"Args: {tool.execution.args}")
    print(f"Flags: {list(tool.execution.flags.keys()) if tool.execution.flags else 'None'}")
    print(f"Working Directory: {tool.execution.cwd}")
    print(f"Timeout: {tool.execution.timeout_ms}ms")


def test_file_tool():
    """Demonstrate file reading tool."""
    print_section("File Reading Tool")


    execution = FileExecutionConfig(
        path="./templates/report-{{props.report_id}}.txt", enableTemplating=True
    )

    tool = Tool(
        name="read_report",
        annotations=Annotations(title="Report Reader"),
        description="Read report templates with placeholder substitution",
        execution=execution,
    )

    print(f"Tool Name: {tool.name}")
    print(f"File Path: {tool.execution.path}")
    print(f"Parse Placeholders: {tool.execution.enableTemplating}")


def test_text_tool():
    """Demonstrate text template tool."""
    print_section("Text Template Tool")


    execution = TextExecutionConfig(
        text="Report generated for {{input.username}} on {{env.CURRENT_DATE}}"
    )

    tool = Tool(
        name="generate_message",
        annotations=Annotations(title="Message Generator"),
        description="Generate formatted messages",
        execution=execution,
    )

    print(f"Tool Name: {tool.name}")
    print(f"Text Template: {tool.execution.text}")


def test_full_mci_schema():
    """Demonstrate a complete MCI schema with multiple tools."""
    print_section("Complete MCI Schema")


    metadata = Metadata(
        name="Development Tools Context",
        description="A collection of development and utility tools",
        version="1.0.0",
        license="MIT",
        authors=["MCI Team"],
    )

    # HTTP tool with Bearer auth
    bearer_auth = BearerAuth(token="{{env.GITHUB_TOKEN}}")
    http_tool = Tool(
        name="github_api",
        annotations=Annotations(title="GitHub API Client"),
        description="Query GitHub API",
        execution=HTTPExecutionConfig(
            url="https://api.github.com/repos/{{input.owner}}/{{input.repo}}",
            method="GET",
            auth=bearer_auth,
            headers={"Accept": "application/vnd.github.v3+json"},
        ),
    )

    # CLI tool
    cli_tool = Tool(
        name="list_files",
        annotations=Annotations(title="File Lister"),
        description="List files in directory",
        execution=CLIExecutionConfig(command="ls", args=["-la"]),
    )

    # File tool
    file_tool = Tool(
        name="read_config",
        annotations=Annotations(title="Config Reader"),
        description="Read configuration file",
        execution=FileExecutionConfig(path="{{props.config_path}}", enableTemplating=False),
    )

    # Text tool
    text_tool = Tool(
        name="status_message",
        annotations=Annotations(title="Status Message"),
        description="Generate status message",
        execution=TextExecutionConfig(text="Status: {{input.status}} at {{env.TIMESTAMP}}"),
    )

    schema = MCISchema(
        schemaVersion="1.0", metadata=metadata, tools=[http_tool, cli_tool, file_tool, text_tool]
    )

    print(f"Schema Version: {schema.schemaVersion}")
    print(f"Context Name: {schema.metadata.name}")
    print(f"Version: {schema.metadata.version}")
    print(f"Number of Tools: {len(schema.tools)}\n")

    for i, tool in enumerate(schema.tools, 1):
        print(f"{i}. {tool.name} ({tool.execution.type})")
        print(f"   Title: {tool.annotations.title if tool.annotations else 'None'}")
        print(f"   Description: {tool.description}")

    # Serialize to JSON
    print("\n" + "-" * 70)
    print("JSON Serialization (first 500 chars):")
    print("-" * 70)
    json_str = schema.model_dump_json(indent=2, exclude_none=True)
    print(json_str[:500] + "...")


def test_execution_results():
    """Demonstrate execution result models."""
    print_section("Execution Results")


    success_result = ExecutionResult(
        result=ExecutionResultContent(
            isError=False,
            content=[
                TextContent(
                    text='{"temperature": 72, "condition": "sunny", "humidity": 45}'
                )
            ],
        )
    )

    error_result = ExecutionResult(
        result=ExecutionResultContent(
            isError=True,
            content=[TextContent(text="Connection timeout after 5000ms")],
        )
    )

    print("Success Result:")
    print(f"  Is Error: {success_result.result.isError}")
    print(f"  Content: {success_result.result.content[0].text}")
    print()
    print("Error Result:")
    print(f"  Is Error: {error_result.result.isError}")
    print(f"  Error Message: {error_result.result.content[0].text}")


def test_auth_types():
    """Demonstrate all authentication types."""
    print_section("Authentication Types")

    # API Key in header
    api_key_header = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "secret123"})
    print("1. API Key (Header)")
    print(f"   Type: {api_key_header.type}")
    print(f"   Location: {api_key_header.in_}")
    print(f"   Name: {api_key_header.name}")

    # API Key in query
    api_key_query = ApiKeyAuth(**{"in": "query", "name": "api_key", "value": "secret123"})
    print("\n2. API Key (Query)")
    print(f"   Type: {api_key_query.type}")
    print(f"   Location: {api_key_query.in_}")

    # Bearer token
    bearer = BearerAuth(token="bearer_token_abc123")
    print("\n3. Bearer Token")
    print(f"   Type: {bearer.type}")
    print(f"   Token: {bearer.token[:20]}...")

    # Basic auth
    basic = BasicAuth(username="admin", password="password123")
    print("\n4. Basic Auth")
    print(f"   Type: {basic.type}")
    print(f"   Username: {basic.username}")

    # OAuth2
    oauth2 = OAuth2Auth(
        flow="clientCredentials",
        tokenUrl="https://auth.example.com/oauth/token",
        clientId="client_abc123",
        clientSecret="secret_xyz789",
        scopes=["read:data", "write:data"],
    )
    print("\n5. OAuth2")
    print(f"   Type: {oauth2.type}")
    print(f"   Flow: {oauth2.flow}")
    print(f"   Token URL: {oauth2.tokenUrl}")
    print(f"   Scopes: {', '.join(oauth2.scopes)}")


def test_tags_filtering():
    """Demonstrate tag filtering functionality."""
    print_section("Tag Filtering")

    # Create tools with different tags
    tool1 = Tool(
        name="github_api",
        description="GitHub API client",
        execution=HTTPExecutionConfig(url="https://api.github.com"),
        tags=["api", "external", "git"],
    )

    tool2 = Tool(
        name="database_query",
        description="Database query tool",
        execution=CLIExecutionConfig(command="psql"),
        tags=["database", "internal", "data"],
    )

    tool3 = Tool(
        name="data_processor",
        description="Process data files",
        execution=FileExecutionConfig(path="./data/input.csv"),
        tags=["data", "processing", "batch"],
    )

    tool4 = Tool(
        name="status_message",
        description="Generate status message",
        execution=TextExecutionConfig(text="Status: OK"),
        tags=["internal", "utility"],
    )

    tool5 = Tool(
        name="no_tags_tool",
        description="Tool without tags",
        execution=TextExecutionConfig(text="Hello"),
        tags=[],
    )

    schema = MCISchema(
        schemaVersion="1.0",
        tools=[tool1, tool2, tool3, tool4, tool5],
    )

    print("All Tools:")
    for tool in schema.tools:
        print(f"  - {tool.name}: {tool.tags if tool.tags else '(no tags)'}")

    # Demonstrate tag filtering with ToolManager
    manager = ToolManager(schema)

    print("\n" + "-" * 70)
    print("Filter by tags=['api']:")
    api_tools = manager.tags(["api"])
    for tool in api_tools:
        print(f"  - {tool.name}")

    print("\n" + "-" * 70)
    print("Filter by tags=['data', 'internal'] (OR logic):")
    data_or_internal = manager.tags(["data", "internal"])
    for tool in data_or_internal:
        print(f"  - {tool.name}")

    print("\n" + "-" * 70)
    print("Exclude tags=['internal'] using withoutTags:")
    without_internal = manager.withoutTags(["internal"])
    for tool in without_internal:
        print(f"  - {tool.name}")

    print("\n" + "-" * 70)
    print("Exclude tags=['api', 'database'] (OR logic):")
    without_api_db = manager.withoutTags(["api", "database"])
    for tool in without_api_db:
        print(f"  - {tool.name}")

    print("\n" + "-" * 70)
    print("Tags are case-sensitive:")
    print(f"  tags(['API']) = {len(manager.tags(['API']))} tools (uppercase 'API')")
    print(f"  tags(['api']) = {len(manager.tags(['api']))} tools (lowercase 'api')")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 70)
    print("  MCI Data Models - Manual Test Suite")
    print("=" * 70)

    test_http_tool_with_api_key()
    test_cli_tool()
    test_file_tool()
    test_text_tool()
    test_full_mci_schema()
    test_execution_results()
    test_auth_types()
    test_tags_filtering()

    print("\n" + "=" * 70)
    print("  All Manual Tests Completed Successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
