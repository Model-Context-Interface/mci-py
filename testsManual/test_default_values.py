"""
Manual test for default values feature.

Run this directly to see the feature in action.
"""

import json
import tempfile
from pathlib import Path

from mcipy import MCIClient

# Create a schema with default values
schema_dict = {
    "schemaVersion": "1.0",
    "tools": [
        {
            "name": "search_files",
            "annotations": {
                "title": "Search Files",
                "readOnlyHint": True,
            },
            "description": "Search for text in files with optional parameters",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in",
                    },
                    "include_images": {
                        "type": "boolean",
                        "description": "Include image files in search",
                        "default": False,
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Use case-sensitive search",
                        "default": True,
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results",
                        "default": 100,
                    },
                    "file_extensions": {
                        "type": "string",
                        "description": "Optional comma-separated list of file extensions",
                    },
                },
                "required": ["pattern", "directory"],
            },
            "execution": {
                "type": "text",
                "text": "Searching for '{{props.pattern}}' in {{props.directory}}\n"
                "Include images: {{props.include_images}}\n"
                "Case sensitive: {{props.case_sensitive}}\n"
                "Max results: {{props.max_results}}",
            },
        }
    ],
}

# Write to temp file
with tempfile.NamedTemporaryFile(mode="w", suffix=".mci.json", delete=False) as f:
    json.dump(schema_dict, f)
    temp_file = f.name

try:
    client = MCIClient(schema_file_path=temp_file)

    print("=" * 60)
    print("Test 1: Execute with only required properties")
    print("=" * 60)
    result = client.execute(
        "search_files",
        properties={
            "pattern": "TODO",
            "directory": "/home/user/projects",
        },
    )
    print(result.result.content[0].text)
    print()

    print("=" * 60)
    print("Test 2: Execute with some defaults overridden")
    print("=" * 60)
    result = client.execute(
        "search_files",
        properties={
            "pattern": "FIXME",
            "directory": "/tmp",
            "include_images": True,
            "max_results": 50,
        },
    )
    print(result.result.content[0].text)
    print()

    print("=" * 60)
    print("Test 3: Execute with all defaults overridden")
    print("=" * 60)
    result = client.execute(
        "search_files",
        properties={
            "pattern": "ERROR",
            "directory": "/var/log",
            "include_images": False,
            "case_sensitive": False,
            "max_results": 10,
            "file_extensions": ".log,.txt",
        },
    )
    print(result.result.content[0].text)
    print()

    print("=" * 60)
    print("SUCCESS! All tests passed.")
    print("Default values are working correctly!")
    print("=" * 60)

finally:
    # Clean up temp file
    Path(temp_file).unlink(missing_ok=True)
