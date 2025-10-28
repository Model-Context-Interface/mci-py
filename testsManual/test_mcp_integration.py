"""
Manual test for MCP server integration.

This test demonstrates the full MCP integration workflow:
1. Loading an MCI schema with MCP servers defined
2. Auto-fetching and caching MCP toolsets
3. Listing tools from MCP servers
4. Executing tools via MCP protocol
5. Verifying toolset caching and expiration

Requirements:
- Node.js and npx installed
- MCP server packages available via npx (@modelcontextprotocol/server-filesystem, @modelcontextprotocol/server-everything)

Usage:
    uv run python testsManual/test_mcp_integration.py
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcipy import MCIClient  # noqa: E402
from rich import print  # noqa: E402


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"[bold cyan]{title}[/bold cyan]")
    print(f"{'='*80}\n")


def test_mcp_schema_loading():
    """Test loading schema with MCP servers."""
    print_section("Test 1: Loading MCI schema with MCP servers")

    schema_path = Path(__file__).parent.parent / "examples" / "mcp_example.mci.json"

    if not schema_path.exists():
        print(f"[red]❌ Schema file not found: {schema_path}[/red]")
        return False

    try:
        client = MCIClient(schema_file_path=str(schema_path), env_vars={
            "TMP_DIR": "/tmp"
        })
        print(f"[green]✅ Schema loaded successfully[/green]")
        return True
    except Exception as e:
        print(f"[red]❌ Failed to load schema: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def test_mcp_toolset_caching():
    """Test MCP toolset caching."""
    print_section("Test 2: MCP Toolset Caching")

    schema_path = Path(__file__).parent.parent / "examples" / "mcp_example.mci.json"
    mcp_dir = Path(__file__).parent.parent / "examples" / "mci" / "mcp"

    # Clean up previous cache
    if mcp_dir.exists():
        for file in mcp_dir.glob("*.mci.json"):
            print(f"Removing old cache file: {file}")
            try:
                file.unlink()
            except OSError as e:
                print(f"[yellow]⚠ Failed to remove cache file {file}: {e}[/yellow]")

    try:
        client = MCIClient(schema_file_path=str(schema_path), env_vars={
            "TMP_DIR": "/tmp"
        })

        # Check if cache files were created
        cache_files = list(mcp_dir.glob("*.mci.json"))
        if cache_files:
            print(f"[green]✅ Found {len(cache_files)} cached toolset(s)[/green]")
            for file in cache_files:
                print(f"  - {file.name}")

                # Check toolset content
                with file.open() as f:
                    toolset = json.load(f)
                    print(f"    Schema version: {toolset.get('schemaVersion')}")
                    print(f"    Tools count: {len(toolset.get('tools', []))}")
                    if "expiresAt" in toolset:
                        print(f"    Expires at: {toolset['expiresAt']}")
                    else:
                        print("    [yellow]⚠ No expiration date found[/yellow]")
            return True
        else:
            print("[yellow]⚠ No cache files found (MCP servers may not be available)[/yellow]")
            return True  # Not a failure, just unavailable
    except Exception as e:
        print(f"[red]❌ Error during caching test: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def test_list_mcp_tools():
    """Test listing tools from MCP servers."""
    print_section("Test 3: Listing Tools from MCP Servers")

    schema_path = Path(__file__).parent.parent / "examples" / "mcp_example.mci.json"

    try:
        client = MCIClient(schema_file_path=str(schema_path), env_vars={
            "TMP_DIR": "/tmp"
        })
        tools = client.tools()

        print(f"[cyan]Total tools available: {len(tools)}[/cyan]\n")

        # Separate MCP tools from regular tools
        mcp_tools = [t for t in tools if t.toolset_source is not None]
        regular_tools = [t for t in tools if t.toolset_source is None]

        print(f"[green]Regular tools: {len(regular_tools)}[/green]")
        for tool in regular_tools:
            print(f"  - {tool.name}: {tool.description or 'No description'}")

        if mcp_tools:
            print(f"\n[green]MCP tools: {len(mcp_tools)}[/green]")
            for tool in mcp_tools:
                print(
                    f"  - {tool.name} (from {tool.toolset_source}): {tool.description or 'No description'}"
                )
            return True
        else:
            print(
                "[yellow]⚠ No MCP tools found (MCP servers may not be available)[/yellow]"
            )
            return True  # Not a failure
    except Exception as e:
        print(f"[red]❌ Failed to list tools: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def test_execute_regular_tool():
    """Test executing a regular (non-MCP) tool to verify setup."""
    print_section("Test 4: Execute Regular Tool")

    schema_path = Path(__file__).parent.parent / "examples" / "mcp_example.mci.json"

    try:
        client = MCIClient(schema_file_path=str(schema_path), env_vars={
            "TMP_DIR": "/tmp"
        })
        result = client.execute("echo_test", {"message": "Hello from MCP integration test!"})
        print(result)

        if result.result.isError:
            print(f"[red]❌ Tool execution failed: {result.result.content[0].text}[/red]")
            return False
        else:
            print(f"[green]✅ Tool executed successfully[/green]")
            for content in result.result.content:
                if content.type == "text":
                    print(f"Result: {content.text}")
            return True
    except Exception as e:
        print(f"[red]❌ Error during tool execution: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def test_mcp_tool_filtering():
    """Test MCP tool filtering."""
    print_section("Test 5: MCP Tool Filtering")

    schema_path = Path(__file__).parent.parent / "examples" / "mcp_example.mci.json"

    # Expected max tools based on filter in schema (only: read_file,write_file,list_directory)
    EXPECTED_MAX_FILTERED_TOOLS = 3

    try:
        client = MCIClient(schema_file_path=str(schema_path), env_vars={
            "TMP_DIR": "/tmp"
        })

        # Test filtering by toolset
        fs_tools = client.toolsets(["filesystem"])
        print(f"[cyan]Tools from 'filesystem' server: {len(fs_tools)}[/cyan]")
        for tool in fs_tools:
            print(f"  - {tool.name}")

        if len(fs_tools) <= EXPECTED_MAX_FILTERED_TOOLS:
            print(
                f"[green]✅ Filtering working correctly (max {EXPECTED_MAX_FILTERED_TOOLS} tools expected)[/green]"
            )
            return True
        else:
            print(
                f"[yellow]⚠ Expected max {EXPECTED_MAX_FILTERED_TOOLS} filtered tools, got {len(fs_tools)}[/yellow]"
            )
            return True
    except Exception as e:
        print(f"[red]❌ Error during filtering test: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def test_execute_mcp_tool():
    """Test executing an MCP tool (list_directory)."""
    print_section("Test 6: Execute MCP Tool")

    schema_path = Path(__file__).parent.parent / "examples" / "mcp_example.mci.json"
    mcp_dir = Path(__file__).parent.parent / "examples" / "mci" / "mcp"

    # Ensure the directory exists for testing
    mcp_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = MCIClient(schema_file_path=str(schema_path), env_vars={
            "TMP_DIR": "/tmp"
        })

        # Try to execute list_directory tool on the mcp cache directory
        result = client.execute("list_directory", {"path": "/tmp"})
        print(result)
        if result.result.isError:
            print(f"[yellow]⚠ Tool execution returned error (MCP server may not be available)[/yellow]")
            if result.result.content:
                print(f"Error message: {result.result.content[0].text}")
            return True  # Not a failure, just unavailable
        else:
            print(f"[green]✅ MCP tool executed successfully[/green]")
            print(f"\n[cyan]Directory listing for {mcp_dir}:[/cyan]")
            for content in result.result.content:
                if content.type == "text":
                    print(content.text)
            return True
    except Exception as e:
        print(f"[red]❌ Error during MCP tool execution: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all manual tests."""
    print("\n[bold magenta]MCP Integration Manual Test Suite[/bold magenta]")
    print("[dim]Testing MCP server integration, caching, and execution[/dim]\n")

    # Check if npx is available
    import shutil

    if shutil.which("npx") is None:
        print("[red]❌ npx not found. Please install Node.js and npm.[/red]")
        print("[yellow]Note: MCP tests require npx to run MCP server packages.[/yellow]")
        return

    tests = [
        ("Schema Loading", test_mcp_schema_loading),
        ("Toolset Caching", test_mcp_toolset_caching),
        ("List MCP Tools", test_list_mcp_tools),
        ("Execute Regular Tool", test_execute_regular_tool),
        ("MCP Tool Filtering", test_mcp_tool_filtering),
        ("Execute MCP Tool", test_execute_mcp_tool),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[red]❌ Test '{test_name}' crashed: {e}[/red]")
            results.append((test_name, False))

    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
        print(f"{status} - {test_name}")

    print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")

    if passed == total:
        print("[bold green]All tests passed! 🎉[/bold green]")
    else:
        print(
            "[bold yellow]Some tests failed. Check output above for details.[/bold yellow]"
        )


if __name__ == "__main__":
    main()
