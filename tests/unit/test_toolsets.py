"""Unit tests for toolset functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from mcipy import MCIClient, SchemaParser, ToolManager, Toolset, ToolsetFile
from mcipy.parser import SchemaParserError
from mcipy.tool_manager import ToolManagerError


class TestToolsetModel:
    """Tests for Toolset model."""

    def test_toolset_minimal(self):
        """Test creating Toolset with minimal fields."""
        toolset = Toolset(name="github_prs")
        assert toolset.name == "github_prs"
        assert toolset.filter is None
        assert toolset.filterValue is None

    def test_toolset_with_filter(self):
        """Test creating Toolset with filter."""
        toolset = Toolset(name="github_prs", filter="only", filterValue="list_prs,create_pr")
        assert toolset.name == "github_prs"
        assert toolset.filter == "only"
        assert toolset.filterValue == "list_prs,create_pr"

    def test_toolset_with_tags_filter(self):
        """Test creating Toolset with tags filter."""
        toolset = Toolset(name="github_prs", filter="tags", filterValue="read")
        assert toolset.name == "github_prs"
        assert toolset.filter == "tags"
        assert toolset.filterValue == "read"


class TestToolsetFileModel:
    """Tests for ToolsetFile model."""

    def test_toolset_file_valid(self):
        """Test creating ToolsetFile with valid data."""
        data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "execution": {"type": "text", "text": "Hello"},
                }
            ],
        }
        toolset_file = ToolsetFile(**data)
        assert toolset_file.schemaVersion == "1.0"
        assert len(toolset_file.tools) == 1
        assert toolset_file.tools[0].name == "test_tool"

    def test_toolset_file_with_metadata(self):
        """Test ToolsetFile with metadata."""
        data = {
            "schemaVersion": "1.0",
            "metadata": {"name": "Test Toolset", "version": "1.0.0"},
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "execution": {"type": "text", "text": "Hello"},
                }
            ],
        }
        toolset_file = ToolsetFile(**data)
        assert toolset_file.metadata is not None
        assert toolset_file.metadata.name == "Test Toolset"
        assert toolset_file.metadata.version == "1.0.0"


class TestSchemaParserToolsets:
    """Tests for parsing toolset files."""

    def test_parse_toolset_file_valid(self):
        """Test parsing a valid toolset file."""
        # Get the fixture file path
        fixture_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
        
        toolset_file = SchemaParser.parse_toolset_file(str(fixture_path))
        
        assert toolset_file.schemaVersion == "1.0"
        assert len(toolset_file.tools) == 3
        assert toolset_file.tools[0].name == "list_prs"
        assert toolset_file.tools[1].name == "create_pr"
        assert toolset_file.tools[2].name == "merge_pr"

    def test_parse_toolset_dict_valid(self):
        """Test parsing a valid toolset dictionary."""
        data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "execution": {"type": "text", "text": "Hello"},
                }
            ],
        }
        
        toolset_file = SchemaParser.parse_toolset_dict(data)
        
        assert toolset_file.schemaVersion == "1.0"
        assert len(toolset_file.tools) == 1
        assert toolset_file.tools[0].name == "test_tool"

    def test_parse_toolset_dict_missing_schema_version(self):
        """Test parsing toolset without schemaVersion."""
        data = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "execution": {"type": "text", "text": "Hello"},
                }
            ]
        }
        
        with pytest.raises(SchemaParserError, match="Toolset missing required field 'schemaVersion'"):
            SchemaParser.parse_toolset_dict(data)

    def test_parse_toolset_dict_missing_tools(self):
        """Test parsing toolset without tools."""
        data = {"schemaVersion": "1.0"}
        
        with pytest.raises(SchemaParserError, match="Toolset missing required field 'tools'"):
            SchemaParser.parse_toolset_dict(data)

    def test_parse_toolset_dict_disallowed_fields(self):
        """Test parsing toolset with disallowed fields."""
        data = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "execution": {"type": "text", "text": "Hello"},
                }
            ],
            "toolsets": [],  # Not allowed in toolset files
            "enableAnyPaths": True,  # Not allowed
        }
        
        with pytest.raises(
            SchemaParserError,
            match="Toolset files cannot contain fields: enableAnyPaths, toolsets",
        ):
            SchemaParser.parse_toolset_dict(data)

    def test_parse_toolset_file_not_found(self):
        """Test parsing a non-existent toolset file."""
        with pytest.raises(SchemaParserError, match="Toolset file not found"):
            SchemaParser.parse_toolset_file("/nonexistent/file.mci.json")


class TestToolsetLoading:
    """Tests for loading toolsets via ToolManager."""

    def test_load_toolset_without_filter(self):
        """Test loading a toolset without any filter."""
        # Create a main schema with toolsets
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            fixture_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            import shutil
            shutil.copy(fixture_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [{"name": "github_prs"}],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have all 3 tools from the toolset
            assert len(tools) == 3
            tool_names = [t.name for t in tools]
            assert "list_prs" in tool_names
            assert "create_pr" in tool_names
            assert "merge_pr" in tool_names

    def test_load_toolset_with_only_filter(self):
        """Test loading a toolset with 'only' filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            fixture_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            import shutil
            shutil.copy(fixture_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema with filter
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [
                    {
                        "name": "github_prs",
                        "filter": "only",
                        "filterValue": "list_prs, create_pr",  # With spaces
                    }
                ],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have only 2 tools (merge_pr excluded)
            assert len(tools) == 2
            tool_names = [t.name for t in tools]
            assert "list_prs" in tool_names
            assert "create_pr" in tool_names
            assert "merge_pr" not in tool_names

    def test_load_toolset_with_except_filter(self):
        """Test loading a toolset with 'except' filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            fixture_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            import shutil
            shutil.copy(fixture_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema with filter
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [
                    {"name": "github_prs", "filter": "except", "filterValue": "merge_pr"}
                ],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have 2 tools (merge_pr excluded)
            assert len(tools) == 2
            tool_names = [t.name for t in tools]
            assert "list_prs" in tool_names
            assert "create_pr" in tool_names
            assert "merge_pr" not in tool_names

    def test_load_toolset_with_tags_filter(self):
        """Test loading a toolset with 'tags' filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            fixture_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            import shutil
            shutil.copy(fixture_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema with filter
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [{"name": "github_prs", "filter": "tags", "filterValue": "read"}],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have only 1 tool with 'read' tag
            assert len(tools) == 1
            assert tools[0].name == "list_prs"

    def test_load_toolset_with_without_tags_filter(self):
        """Test loading a toolset with 'withoutTags' filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            fixture_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            import shutil
            shutil.copy(fixture_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema with filter
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [
                    {"name": "github_prs", "filter": "withoutTags", "filterValue": "admin"}
                ],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have 2 tools (merge_pr has 'admin' tag)
            assert len(tools) == 2
            tool_names = [t.name for t in tools]
            assert "list_prs" in tool_names
            assert "create_pr" in tool_names
            assert "merge_pr" not in tool_names

    def test_load_multiple_toolsets(self):
        """Test loading multiple toolsets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture files
            import shutil
            github_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            file_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "file_ops.mci.json"
            shutil.copy(github_path, lib_dir / "github_prs.mci.json")
            shutil.copy(file_path, lib_dir / "file_ops.mci.json")
            
            # Create main schema with multiple toolsets
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [
                    {"name": "github_prs", "filter": "tags", "filterValue": "read"},
                    {"name": "file_ops", "filter": "tags", "filterValue": "read"},
                ],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have 2 tools: list_prs and read_file (both have 'read' tag)
            assert len(tools) == 2
            tool_names = [t.name for t in tools]
            assert "list_prs" in tool_names
            assert "read_file" in tool_names

    def test_toolset_not_found(self):
        """Test loading a non-existent toolset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Create main schema with non-existent toolset
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [{"name": "nonexistent"}],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Should raise error when loading
            with pytest.raises(Exception, match="Toolset 'nonexistent' not found"):
                MCIClient(schema_file_path=str(schema_path))


class TestToolsetsFilterMethod:
    """Tests for the toolsets() filter method."""

    def test_filter_by_single_toolset(self):
        """Test filtering tools by a single toolset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture files
            import shutil
            github_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            file_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "file_ops.mci.json"
            shutil.copy(github_path, lib_dir / "github_prs.mci.json")
            shutil.copy(file_path, lib_dir / "file_ops.mci.json")
            
            # Create main schema with multiple toolsets
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [
                    {"name": "github_prs"},
                    {"name": "file_ops"},
                ],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            
            # Filter by github_prs toolset
            github_tools = client.toolsets(["github_prs"])
            assert len(github_tools) == 3
            tool_names = [t.name for t in github_tools]
            assert all(name in ["list_prs", "create_pr", "merge_pr"] for name in tool_names)

    def test_filter_by_multiple_toolsets(self):
        """Test filtering tools by multiple toolsets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture files
            import shutil
            github_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            file_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "file_ops.mci.json"
            shutil.copy(github_path, lib_dir / "github_prs.mci.json")
            shutil.copy(file_path, lib_dir / "file_ops.mci.json")
            
            # Create main schema with multiple toolsets, with filters
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [
                    {"name": "github_prs", "filter": "tags", "filterValue": "read"},
                    {"name": "file_ops", "filter": "tags", "filterValue": "read"},
                ],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            
            # Filter by both toolsets
            all_read_tools = client.toolsets(["github_prs", "file_ops"])
            assert len(all_read_tools) == 2
            tool_names = [t.name for t in all_read_tools]
            assert "list_prs" in tool_names
            assert "read_file" in tool_names

    def test_filter_by_nonexistent_toolset(self):
        """Test filtering by a toolset that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            import shutil
            github_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            shutil.copy(github_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [{"name": "github_prs"}],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            
            # Filter by non-existent toolset should return empty
            tools = client.toolsets(["nonexistent"])
            assert len(tools) == 0


class TestMixedToolsAndToolsets:
    """Tests for schemas with both tools and toolsets."""

    def test_schema_with_tools_and_toolsets(self):
        """Test schema with both direct tools and toolsets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            import shutil
            github_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            shutil.copy(github_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema with both tools and toolsets
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "local_tool",
                        "description": "A local tool",
                        "execution": {"type": "text", "text": "Local tool"},
                    }
                ],
                "toolsets": [{"name": "github_prs", "filter": "tags", "filterValue": "read"}],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have local_tool plus list_prs from toolset
            assert len(tools) == 2
            tool_names = [t.name for t in tools]
            assert "local_tool" in tool_names
            assert "list_prs" in tool_names

    def test_schema_with_only_toolsets(self):
        """Test schema with only toolsets (no direct tools)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create library directory
            lib_dir = tmpdir / "mci"
            lib_dir.mkdir()
            
            # Copy fixture file
            import shutil
            github_path = Path(__file__).parent.parent / "fixtures" / "toolsets" / "github_prs.mci.json"
            shutil.copy(github_path, lib_dir / "github_prs.mci.json")
            
            # Create main schema with only toolsets
            schema_path = tmpdir / "main.mci.json"
            schema_data = {
                "schemaVersion": "1.0",
                "toolsets": [{"name": "github_prs"}],
            }
            schema_path.write_text(json.dumps(schema_data))
            
            # Load via client
            client = MCIClient(schema_file_path=str(schema_path))
            tools = client.tools()
            
            # Should have all 3 tools from toolset
            assert len(tools) == 3
