"""
Manual test for LiteMcpClient class.

This test demonstrates realistic usage of the LiteMcpClient for connecting to
MCP servers via STDIO and HTTP transports. Run this file directly to see
the client in action with the @modelcontextprotocol/server-memory package.

Setup:
    1. Install npx or uvx if not already installed
    2. The test will use @modelcontextprotocol/server-memory via npx

Usage:
    uv run python testsManual/test_mcp_client_manual.py
"""

import asyncio
import os

from mcipy import ClientCfg, LiteMcpClient, SseCfg, StdioCfg


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"   ✓ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"   ✗ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"   → {message}")


async def test_stdio_connection():
    """Test STDIO connection to MCP server using npx."""
    print_section("STDIO CONNECTION TEST (NPX)")

    print_info("Using @modelcontextprotocol/server-memory via npx")
    print_info("This may take a moment on first run to download the package\n")

    cfg = ClientCfg(
        server=StdioCfg(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
            env={},  # No additional env vars needed for memory server
        )
    )

    try:
        async with LiteMcpClient(cfg) as client:
            print_success("Connected to MCP server via STDIO")

            # List available tools
            tools = await client.list_tools()
            print_success(f"Listed {len(tools)} tools")
            print_info(f"Available tools: {', '.join(tools)}\n")

            # Test tool call if tools are available
            if "store_memory" in tools:
                print_info("Testing 'store_memory' tool...")
                result = await client.call_tool(
                    "store_memory",
                    key="test_key",
                    value="Hello from LiteMcpClient!",
                )
                print_success(f"Tool executed successfully")
                print_info(f"Result: {result}\n")

            if "retrieve_memory" in tools:
                print_info("Testing 'retrieve_memory' tool...")
                result = await client.call_tool("retrieve_memory", key="test_key")
                print_success(f"Tool executed successfully")
                print_info(f"Result: {result}\n")

            if "list_memories" in tools:
                print_info("Testing 'list_memories' tool...")
                result = await client.call_tool("list_memories")
                print_success(f"Tool executed successfully")
                print_info(f"Result: {result}\n")

    except Exception as e:
        print_error(f"Failed to connect or execute: {e}")
        print_info("Make sure npx is installed and accessible in PATH")
        raise


async def test_uvx_connection():
    """Test STDIO connection to MCP server using uvx."""
    print_section("STDIO CONNECTION TEST (UVX)")

    print_info("Using mcp-server-memory via uvx")
    print_info("This requires uvx to be installed (part of uv toolkit)\n")

    cfg = ClientCfg(
        server=StdioCfg(
            command="uvx",
            args=[
                "mcp-python-interpreter",
                "--dir",
                "/mnt/c/Users/admin/Desktop/mci/mci-py/testUvxServer",
                "--python-path",
                "/mnt/c/Users/admin/Desktop/mci/mci-py/venv/bin/python"
            ],
            env={},
        )
    )

    try:
        async with LiteMcpClient(cfg) as client:
            print_success("Connected to MCP server via STDIO (uvx)")

            # List available tools
            tools = await client.list_tools()
            print_success(f"Listed {len(tools)} tools")
            print_info(f"Available tools: {', '.join(tools)}\n")

    except FileNotFoundError:
        print_error("uvx not found in PATH")
        print_info("Install uv toolkit: https://docs.astral.sh/uv/getting-started/installation/")
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        print_info("This is expected if mcp-server-memory is not available via uvx")


async def test_http_connection():
    """Test HTTP connection to MCP server (if available)."""
    print_section("HTTP CONNECTION TEST")

    print_info("Testing connection to HTTP MCP server")
    print_info(f"Server URL: {os.getenv('MCP_SERVER_URL', 'https://api.githubcopilot.com/mcp')}")
    print_info(f"Auth token: {'Set' if os.getenv('MCP_AUTH_TOKEN') else 'Not set'}\n")

    # Check if a custom MCP server URL is provided via environment variable
    mcp_server_url = os.getenv('MCP_SERVER_URL', 'https://api.githubcopilot.com/mcp')
    mcp_auth_token = os.getenv('MCP_AUTH_TOKEN')

    headers = {}
    if mcp_auth_token:
        headers["Authorization"] = f"Bearer {mcp_auth_token}"

    cfg = ClientCfg(
        server=SseCfg(
            url=mcp_server_url,
            headers=headers,
        )
    )

    try:
        # Set a short timeout for the test
        async with asyncio.timeout(10):
            async with LiteMcpClient(cfg) as client:
                print_success("Connected to MCP server via HTTP")

                # List available tools
                tools = await client.list_tools()
                print_success(f"Listed {len(tools)} tools")
                print_info(f"Available tools: {', '.join(tools)}\n")

    except asyncio.TimeoutError:
        print_error(f"Connection timeout - server at {mcp_server_url} not responding")
        print_info("Set MCP_SERVER_URL environment variable to test a different server")
        print_info("Set MCP_AUTH_TOKEN environment variable if authentication is required")
    except asyncio.CancelledError:
        print_error("Connection cancelled - likely due to authentication failure")
        print_info("Set MCP_AUTH_TOKEN environment variable with a valid token")
    except ConnectionError as e:
        print_error(f"Connection failed: {e}")
        print_info("Check if the server is running and accessible")
    except Exception as e:
        error_msg = str(e).lower()
        if "401" in error_msg or "unauthorized" in error_msg:
            print_error("Authentication failed (401 Unauthorized)")
            print_info("Set MCP_AUTH_TOKEN environment variable with a valid token")
        elif "404" in error_msg or "not found" in error_msg:
            print_error("Server endpoint not found (404)")
            print_info("Check the MCP_SERVER_URL is correct")
        else:
            print_error(f"Connection failed: {type(e).__name__}: {e}")
        print_info("This is expected if authentication is not configured properly")


async def test_configuration_models():
    """Test configuration model creation and validation."""
    print_section("CONFIGURATION MODEL TESTS")

    # Test StdioCfg
    print_info("Testing StdioCfg model...")
    stdio_cfg = StdioCfg(command="uvx", args=["mcp-server"], env={"API_KEY": "secret"})
    print_success(f"StdioCfg created: command={stdio_cfg.command}, args={stdio_cfg.args}")

    # Test SseCfg
    print_info("Testing SseCfg model...")
    sse_cfg = SseCfg(url="http://localhost:8000/mcp", headers={"Authorization": "Bearer xyz"})
    print_success(f"SseCfg created: url={sse_cfg.url}, headers={sse_cfg.headers}")

    # Test ClientCfg with STDIO
    print_info("Testing ClientCfg with STDIO...")
    client_cfg = ClientCfg(server=stdio_cfg, request_timeout=120.0)
    print_success(f"ClientCfg created with STDIO server, timeout={client_cfg.request_timeout}")

    # Test ClientCfg with HTTP
    print_info("Testing ClientCfg with HTTP...")
    client_cfg = ClientCfg(server=sse_cfg)
    print_success(f"ClientCfg created with HTTP server, timeout={client_cfg.request_timeout}")


async def test_error_handling():
    """Test error handling scenarios."""
    print_section("ERROR HANDLING TESTS")

    # Test 1: Using client without context manager
    print_info("Test 1: Using client without context manager...")
    cfg = ClientCfg(server=StdioCfg(command="npx", args=["@modelcontextprotocol/server-memory"]))
    client = LiteMcpClient(cfg)

    try:
        await client.list_tools()
        print_error("Should have raised RuntimeError")
    except RuntimeError as e:
        print_success(f"Correctly raised RuntimeError: {e}")

    # Test 2: Invalid command
    print_info("\nTest 2: Invalid command...")
    cfg = ClientCfg(server=StdioCfg(command="nonexistent_command_12345"))

    try:
        async with asyncio.timeout(5):
            async with LiteMcpClient(cfg) as client:
                await client.list_tools()
        print_error("Should have raised an error")
    except (FileNotFoundError, Exception) as e:
        print_success(f"Correctly raised error: {type(e).__name__}")


async def main():
    """Run all manual tests."""
    print("\n" + "=" * 80)
    print("  LITEMCPCLIENT MANUAL TESTS")
    print("=" * 80)

    # Configuration tests (always run)
    await test_configuration_models()

    # Error handling tests (always run)
    await test_error_handling()

    # STDIO tests (may require npx/uvx)
    try:
        await test_stdio_connection()
    except Exception as e:
        print_info(f"\nSTDIO (npx) test skipped or failed: {e}")

    try:
        await test_uvx_connection()
    except Exception as e:
        print_info(f"\nSTDIO (uvx) test skipped or failed: {e}")

    # HTTP test (requires running server)
    try:
        await test_http_connection()
    except Exception as e:
        print_info(f"\nHTTP test failed: {type(e).__name__}: {e}")
        print_info("This is expected if no MCP server is running or configured")

    print_section("ALL TESTS COMPLETED")
    print("Note: Some tests may be skipped if dependencies are not available")


if __name__ == "__main__":
    asyncio.run(main())
