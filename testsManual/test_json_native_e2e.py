#!/usr/bin/env python3
"""
End-to-end integration test for JSON-native resolution feature.

This test verifies that the feature works correctly when used through
the full MCIClient API, demonstrating a real-world use case.

Run this test manually:
    uv run python testsManual/test_json_native_e2e.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mcipy import MCIClient


def test_e2e_json_native_api_call():
    """Test JSON-native resolution through full MCIClient execution flow."""
    print("\n" + "=" * 70)
    print("  End-to-End Test: JSON-Native Resolution with MCIClient")
    print("=" * 70 + "\n")

    # Create a temporary MCI schema file with JSON-native placeholders
    schema = {
        "schemaVersion": "1.0",
        "metadata": {
            "name": "Search API Test",
            "version": "1.0.0",
        },
        "tools": [
            {
                "name": "search_files",
                "description": "Search files with various filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "include_images": {
                            "type": "boolean",
                            "description": "Include image files",
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Case-sensitive search",
                        },
                        "max_results": {
                            "type": "number",
                            "description": "Maximum results",
                        },
                        "quality": {
                            "type": "number",
                            "description": "Quality score (float)",
                        },
                        "file_types": {
                            "type": "array",
                            "description": "File type filters",
                            "items": {"type": "string"},
                        },
                        "advanced_options": {
                            "type": "object",
                            "description": "Advanced search options",
                        },
                        "tags": {
                            "type": "array",
                            "description": "Tags",
                            "items": {"type": "string"},
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Metadata",
                        },
                        "nothing": {
                            "type": "null",
                            "description": "Null value test",
                        },
                    },
                    "required": ["query"],
                },
                "execution": {
                    "type": "http",
                    "method": "POST",
                    "url": "https://api.example.com/search",
                    "body": {
                        "type": "json",
                        "content": {
                            # String placeholders
                            "query": "{{props.query}}",
                            "description": "Search for {{props.query}} items",
                            # JSON-native placeholders for all types
                            "include_images": "{!!props.include_images!!}",
                            "case_sensitive": "{!!props.case_sensitive!!}",
                            "max_results": "{!!props.max_results!!}",
                            "quality": "{!!props.quality!!}",
                            "file_types": "{!!props.file_types!!}",
                            "advanced_options": "{!!props.advanced_options!!}",
                            "tags": "{!!props.tags!!}",
                            "metadata": "{!!props.metadata!!}",
                            "nothing": "{!!props.nothing!!}",
                        },
                    },
                },
            }
        ],
    }

    # Write schema to temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mci.json", delete=False
    ) as f:
        json.dump(schema, f)
        schema_path = f.name

    try:
        # Initialize MCIClient
        client = MCIClient(json_file_path=schema_path, env_vars={})

        # Execution with all property types
        print("Executing tool with all JSON-native type examples")
        print("-" * 70)

        properties = {
            "query": "test search",
            # Booleans
            "include_images": True,
            "case_sensitive": False,
            # Numbers
            "max_results": 50,
            "quality": 0.95,
            # Arrays
            "file_types": [".py", ".js", ".md"],
            "tags": ["urgent", "review", "testing"],
            # Objects
            "advanced_options": {"fuzzy": True, "language": "en", "limit": 100},
            "metadata": {"version": "1.0", "priority": 5, "active": True},
            # Null
            "nothing": None,
        }

        print(f"Input properties:\n{json.dumps(properties, indent=2)}\n")

        with patch("requests.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": ["file1.py", "file2.js"],
                "count": 2,
            }
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response

            result = client.execute("search_files", properties=properties)

            # Verify execution succeeded
            assert not result.result.isError, f"Execution failed: {result.result}"

            # Get the actual JSON body that was sent
            call_kwargs = mock_request.call_args[1]
            body_sent = call_kwargs["json"]

            print("JSON body sent to API:")
            print(json.dumps(body_sent, indent=2))
            print()

            print("=" * 70)
            print("Type Verification Results:")
            print("=" * 70)

            # Verify String types (from {{...}})
            print("\n📝 String Placeholders ({{...}}):")
            assert isinstance(body_sent["query"], str)
            assert body_sent["query"] == "test search"
            print(f"  ✓ query: str = '{body_sent['query']}'")

            assert isinstance(body_sent["description"], str)
            assert "Search for test search items" in body_sent["description"]
            print(f"  ✓ description: str = '{body_sent['description']}'")

            # Verify Boolean types (from {!!...!!})
            print("\n✓ Boolean Placeholders ({!!...!!}):")
            assert isinstance(body_sent["include_images"], bool)
            assert body_sent["include_images"] is True
            print(f"  ✓ include_images: bool = {body_sent['include_images']}")

            assert isinstance(body_sent["case_sensitive"], bool)
            assert body_sent["case_sensitive"] is False
            print(f"  ✓ case_sensitive: bool = {body_sent['case_sensitive']}")

            # Verify Number types (from {!!...!!})
            print("\n🔢 Number Placeholders ({!!...!!}):")
            assert isinstance(body_sent["max_results"], int)
            assert body_sent["max_results"] == 50
            print(f"  ✓ max_results: int = {body_sent['max_results']}")

            assert isinstance(body_sent["quality"], float)
            assert body_sent["quality"] == 0.95
            print(f"  ✓ quality: float = {body_sent['quality']}")

            # Verify Array types (from {!!...!!})
            print("\n📋 Array Placeholders ({!!...!!}):")
            assert isinstance(body_sent["file_types"], list)
            assert body_sent["file_types"] == [".py", ".js", ".md"]
            print(f"  ✓ file_types: list = {body_sent['file_types']}")

            assert isinstance(body_sent["tags"], list)
            assert body_sent["tags"] == ["urgent", "review", "testing"]
            print(f"  ✓ tags: list = {body_sent['tags']}")

            # Verify Object types (from {!!...!!})
            print("\n🗂️  Object Placeholders ({!!...!!}):")
            assert isinstance(body_sent["advanced_options"], dict)
            assert body_sent["advanced_options"]["fuzzy"] is True
            assert body_sent["advanced_options"]["language"] == "en"
            print(f"  ✓ advanced_options: dict = {json.dumps(body_sent['advanced_options'])}")

            assert isinstance(body_sent["metadata"], dict)
            assert body_sent["metadata"]["version"] == "1.0"
            assert body_sent["metadata"]["priority"] == 5
            assert body_sent["metadata"]["active"] is True
            print(f"  ✓ metadata: dict = {json.dumps(body_sent['metadata'])}")

            # Verify Null type (from {!!...!!})
            print("\n∅ Null Placeholder ({!!...!!}):")
            assert body_sent["nothing"] is None
            print(f"  ✓ nothing: NoneType = {body_sent['nothing']}")

            print("\n" + "=" * 70)
            print("  ✓ All Type Checks Passed!")
            print("=" * 70)

        print("\n" + "=" * 70)
        print("  ✓ End-to-End Test Passed Successfully!")
        print("=" * 70)
        print(
            "\nConclusion: JSON-native resolution works correctly through the full"
        )
        print(
            "MCIClient execution flow, preserving all native JSON types:"
        )
        print("  • Booleans (true/false)")
        print("  • Numbers (integers and floats)")
        print("  • Arrays")
        print("  • Objects")
        print("  • Null values")
        print("  • Strings (via standard {{...}} syntax)\n")

    finally:
        # Clean up temporary file
        Path(schema_path).unlink()


if __name__ == "__main__":
    test_e2e_json_native_api_call()
