"""
Manual test for toolsets feature.

This test demonstrates real-world usage of toolsets including:
- Loading tools from multiple toolsets
- Applying schema-level filters (only, except, tags, withoutTags)
- Filtering by toolset name at runtime
- Mixing direct tools with toolset tools
- Overlapping tool names and tag-based filtering

Run this test manually:
    uv run python testsManual/test_toolsets_manual.py
"""

import json
import tempfile
from pathlib import Path

from mcipy import MCIClient


def create_test_environment():
    """Create a temporary test environment with toolsets."""
    tmpdir = Path(tempfile.mkdtemp())
    
    # Create library directory
    lib_dir = tmpdir / "mci"
    lib_dir.mkdir()
    
    # Create GitHub toolset
    github_toolset = {
        "schemaVersion": "1.0",
        "metadata": {
            "name": "GitHub Tools",
            "description": "Tools for GitHub operations",
            "version": "1.0.0",
        },
        "tools": [
            {
                "name": "list_repos",
                "description": "List repositories",
                "tags": ["github", "read"],
                "execution": {"type": "text", "text": "Listing repositories"},
            },
            {
                "name": "create_repo",
                "description": "Create a new repository",
                "tags": ["github", "write"],
                "execution": {"type": "text", "text": "Creating repository"},
            },
            {
                "name": "delete_repo",
                "description": "Delete a repository",
                "tags": ["github", "write", "destructive"],
                "execution": {"type": "text", "text": "Deleting repository"},
            },
        ],
    }
    (lib_dir / "github.mci.json").write_text(json.dumps(github_toolset))
    
    # Create File toolset
    file_toolset = {
        "schemaVersion": "1.0",
        "metadata": {
            "name": "File Operations",
            "description": "Tools for file operations",
            "version": "1.0.0",
        },
        "tools": [
            {
                "name": "read_file",
                "description": "Read a file",
                "tags": ["file", "read"],
                "execution": {"type": "text", "text": "Reading file"},
            },
            {
                "name": "write_file",
                "description": "Write to a file",
                "tags": ["file", "write"],
                "execution": {"type": "text", "text": "Writing file"},
            },
            {
                "name": "delete_file",
                "description": "Delete a file",
                "tags": ["file", "write", "destructive"],
                "execution": {"type": "text", "text": "Deleting file"},
            },
        ],
    }
    (lib_dir / "files.mci.json").write_text(json.dumps(file_toolset))
    
    # Create Database toolset
    db_toolset = {
        "schemaVersion": "1.0",
        "metadata": {
            "name": "Database Tools",
            "description": "Tools for database operations",
            "version": "1.0.0",
        },
        "tools": [
            {
                "name": "query_db",
                "description": "Query the database",
                "tags": ["database", "read"],
                "execution": {"type": "text", "text": "Querying database"},
            },
            {
                "name": "insert_record",
                "description": "Insert a record",
                "tags": ["database", "write"],
                "execution": {"type": "text", "text": "Inserting record"},
            },
            {
                "name": "drop_table",
                "description": "Drop a table",
                "tags": ["database", "write", "destructive"],
                "execution": {"type": "text", "text": "Dropping table"},
            },
        ],
    }
    (lib_dir / "database.mci.json").write_text(json.dumps(db_toolset))
    
    return tmpdir


def test_basic_toolset_loading():
    """Test 1: Basic toolset loading without filters."""
    print("\n=== Test 1: Basic Toolset Loading ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {"name": "github"},
            {"name": "files"},
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    tools = client.tools()
    
    print(f"Loaded {len(tools)} tools from 2 toolsets")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    assert len(tools) == 6, f"Expected 6 tools, got {len(tools)}"
    print("✅ Test passed!")


def test_toolset_with_only_filter():
    """Test 2: Toolset with 'only' filter."""
    print("\n=== Test 2: Toolset with 'only' Filter ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {
                "name": "github",
                "filter": "only",
                "filterValue": "list_repos, create_repo",  # Only these two
            }
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    tools = client.tools()
    
    print(f"Loaded {len(tools)} tools with 'only' filter")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    assert len(tools) == 2, f"Expected 2 tools, got {len(tools)}"
    tool_names = [t.name for t in tools]
    assert "list_repos" in tool_names
    assert "create_repo" in tool_names
    assert "delete_repo" not in tool_names
    print("✅ Test passed!")


def test_toolset_with_except_filter():
    """Test 3: Toolset with 'except' filter."""
    print("\n=== Test 3: Toolset with 'except' Filter ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {
                "name": "github",
                "filter": "except",
                "filterValue": "delete_repo",  # Exclude destructive tool
            }
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    tools = client.tools()
    
    print(f"Loaded {len(tools)} tools with 'except' filter")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    assert len(tools) == 2, f"Expected 2 tools, got {len(tools)}"
    tool_names = [t.name for t in tools]
    assert "list_repos" in tool_names
    assert "create_repo" in tool_names
    assert "delete_repo" not in tool_names
    print("✅ Test passed!")


def test_toolset_with_tags_filter():
    """Test 4: Toolset with 'tags' filter."""
    print("\n=== Test 4: Toolset with 'tags' Filter ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {"name": "github", "filter": "tags", "filterValue": "read"},
            {"name": "files", "filter": "tags", "filterValue": "read"},
            {"name": "database", "filter": "tags", "filterValue": "read"},
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    tools = client.tools()
    
    print(f"Loaded {len(tools)} read-only tools")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description} (tags: {tool.tags})")
    
    assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"
    for tool in tools:
        assert "read" in tool.tags
    print("✅ Test passed!")


def test_toolset_with_without_tags_filter():
    """Test 5: Toolset with 'withoutTags' filter."""
    print("\n=== Test 5: Toolset with 'withoutTags' Filter ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {"name": "github", "filter": "withoutTags", "filterValue": "destructive"},
            {"name": "files", "filter": "withoutTags", "filterValue": "destructive"},
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    tools = client.tools()
    
    print(f"Loaded {len(tools)} non-destructive tools")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description} (tags: {tool.tags})")
    
    assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
    for tool in tools:
        assert "destructive" not in tool.tags
    print("✅ Test passed!")


def test_runtime_toolset_filtering():
    """Test 6: Runtime filtering by toolset name."""
    print("\n=== Test 6: Runtime Toolset Filtering ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {"name": "github"},
            {"name": "files"},
            {"name": "database"},
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    
    # Get all tools
    all_tools = client.tools()
    print(f"Total tools loaded: {len(all_tools)}")
    
    # Filter by github toolset
    github_tools = client.toolsets(["github"])
    print(f"\nGitHub toolset tools: {len(github_tools)}")
    for tool in github_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Filter by files toolset
    file_tools = client.toolsets(["files"])
    print(f"\nFiles toolset tools: {len(file_tools)}")
    for tool in file_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Filter by multiple toolsets
    multi_tools = client.toolsets(["github", "database"])
    print(f"\nGitHub + Database toolset tools: {len(multi_tools)}")
    for tool in multi_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    assert len(github_tools) == 3
    assert len(file_tools) == 3
    assert len(multi_tools) == 6
    print("✅ Test passed!")


def test_mixed_tools_and_toolsets():
    """Test 7: Schema with both direct tools and toolsets."""
    print("\n=== Test 7: Mixed Tools and Toolsets ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "tools": [
            {
                "name": "local_tool_1",
                "description": "A local tool",
                "tags": ["local"],
                "execution": {"type": "text", "text": "Local tool 1"},
            },
            {
                "name": "local_tool_2",
                "description": "Another local tool",
                "tags": ["local"],
                "execution": {"type": "text", "text": "Local tool 2"},
            },
        ],
        "toolsets": [
            {"name": "github", "filter": "tags", "filterValue": "read"},
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    
    all_tools = client.tools()
    print(f"Total tools: {len(all_tools)}")
    for tool in all_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Filter by tags (should include local tools and github read tools)
    local_tools = client.tags(["local"])
    print(f"\nLocal tools: {len(local_tools)}")
    for tool in local_tools:
        print(f"  - {tool.name}")
    
    # Filter by toolset (should only include github tools, not local)
    github_tools = client.toolsets(["github"])
    print(f"\nGitHub toolset tools: {len(github_tools)}")
    for tool in github_tools:
        print(f"  - {tool.name}")
    
    assert len(all_tools) == 3  # 2 local + 1 github read
    assert len(local_tools) == 2
    assert len(github_tools) == 1
    print("✅ Test passed!")


def test_adapter_level_filtering_on_toolsets():
    """Test 8: Adapter-level filtering works on toolset tools."""
    print("\n=== Test 8: Adapter-Level Filtering on Toolset Tools ===")
    
    tmpdir = create_test_environment()
    
    schema_data = {
        "schemaVersion": "1.0",
        "toolsets": [
            {"name": "github"},
            {"name": "files"},
        ],
    }
    schema_path = tmpdir / "schema.mci.json"
    schema_path.write_text(json.dumps(schema_data))
    
    client = MCIClient(schema_file_path=str(schema_path))
    
    # Filter by tags (cross-toolset)
    read_tools = client.tags(["read"])
    print(f"Read-only tools across all toolsets: {len(read_tools)}")
    for tool in read_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Filter by without tags
    safe_tools = client.withoutTags(["destructive"])
    print(f"\nNon-destructive tools: {len(safe_tools)}")
    for tool in safe_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Filter by only specific tools
    specific_tools = client.only(["list_repos", "read_file"])
    print(f"\nSpecific tools: {len(specific_tools)}")
    for tool in specific_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    assert len(read_tools) == 2  # list_repos, read_file
    assert len(safe_tools) == 4  # All except delete_* tools
    assert len(specific_tools) == 2
    print("✅ Test passed!")


def main():
    """Run all manual tests."""
    print("=" * 70)
    print("TOOLSETS FEATURE MANUAL TESTS")
    print("=" * 70)
    
    try:
        test_basic_toolset_loading()
        test_toolset_with_only_filter()
        test_toolset_with_except_filter()
        test_toolset_with_tags_filter()
        test_toolset_with_without_tags_filter()
        test_runtime_toolset_filtering()
        test_mixed_tools_and_toolsets()
        test_adapter_level_filtering_on_toolsets()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
