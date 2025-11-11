#!/usr/bin/env python3
"""
Manual test for JSON-native {!! ... !!} placeholder resolution.

This test demonstrates the difference between standard {{...}} placeholders
(which always resolve to strings) and JSON-native {!!...!!} placeholders
(which preserve native types like boolean, number, array, object).

Run this test manually:
    uv run python testsManual/test_json_native_feature.py

Expected output:
    ✓ All tests demonstrating JSON-native resolution passed!
"""

import json
from typing import Any
from unittest.mock import Mock, patch

from mcipy.enums import ExecutionType
from mcipy.executors import ExecutorFactory
from mcipy.models import HTTPBodyConfig, HTTPExecutionConfig


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_result(test_name: str, body_sent: dict[str, Any]) -> None:
    """Print test result showing the JSON body that was sent."""
    print(f"✓ {test_name}")
    print(f"  Body sent: {json.dumps(body_sent, indent=2)}")
    print()


def test_boolean_resolution():
    """Test that boolean values are preserved as native booleans."""
    print_section("Test 1: Boolean Resolution")

    context = {
        "props": {"include_images": True, "case_sensitive": False},
        "env": {},
        "input": {"include_images": True, "case_sensitive": False},
    }

    # Standard placeholders (converts to string)
    print("Using standard {{...}} placeholders:")
    body_standard = HTTPBodyConfig(
        type="json",
        content={
            "include_images": "{{props.include_images}}",  # Will be "True" (string)
            "case_sensitive": "{{props.case_sensitive}}",  # Will be "False" (string)
        },
    )
    config_standard = HTTPExecutionConfig(
        url="https://api.example.com/test", method="POST", body=body_standard
    )
    executor = ExecutorFactory.get_executor(ExecutionType.HTTP)

    with patch("requests.request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        executor.execute(config_standard, context)
        body_sent = mock_request.call_args[1]["json"]

        print(f"  include_images type: {type(body_sent['include_images']).__name__}")
        print(f"  include_images value: {repr(body_sent['include_images'])}")
        print(f"  case_sensitive type: {type(body_sent['case_sensitive']).__name__}")
        print(f"  case_sensitive value: {repr(body_sent['case_sensitive'])}")
        print()

        # Values are strings "True" and "False"
        assert body_sent["include_images"] == "True"
        assert body_sent["case_sensitive"] == "False"
        assert isinstance(body_sent["include_images"], str)
        assert isinstance(body_sent["case_sensitive"], str)

    # JSON-native placeholders (preserves native type)
    print("Using JSON-native {!!...!!} placeholders:")
    body_native = HTTPBodyConfig(
        type="json",
        content={
            "include_images": "{!!props.include_images!!}",  # Will be true (boolean)
            "case_sensitive": "{!!props.case_sensitive!!}",  # Will be false (boolean)
        },
    )
    config_native = HTTPExecutionConfig(
        url="https://api.example.com/test", method="POST", body=body_native
    )

    with patch("requests.request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        executor.execute(config_native, context)
        body_sent = mock_request.call_args[1]["json"]

        print(f"  include_images type: {type(body_sent['include_images']).__name__}")
        print(f"  include_images value: {repr(body_sent['include_images'])}")
        print(f"  case_sensitive type: {type(body_sent['case_sensitive']).__name__}")
        print(f"  case_sensitive value: {repr(body_sent['case_sensitive'])}")
        print()

        # Values are native booleans
        assert body_sent["include_images"] is True
        assert body_sent["case_sensitive"] is False
        assert isinstance(body_sent["include_images"], bool)
        assert isinstance(body_sent["case_sensitive"], bool)

    print_result("Boolean values preserved as native types", body_sent)


def test_array_and_object_resolution():
    """Test that arrays and objects are preserved as native types."""
    print_section("Test 2: Array and Object Resolution")

    context = {
        "props": {
            "urls": ["https://api1.com", "https://api2.com"],
            "config": {"debug": False, "retries": 3, "timeout": 5000},
        },
        "env": {},
        "input": {},
    }

    body = HTTPBodyConfig(
        type="json",
        content={
            "urls": "{!!props.urls!!}",  # Native array
            "config": "{!!props.config!!}",  # Native object
        },
    )
    config = HTTPExecutionConfig(
        url="https://api.example.com/test", method="POST", body=body
    )
    executor = ExecutorFactory.get_executor(ExecutionType.HTTP)

    with patch("requests.request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        executor.execute(config, context)
        body_sent = mock_request.call_args[1]["json"]

        print(f"  urls type: {type(body_sent['urls']).__name__}")
        print(f"  urls value: {body_sent['urls']}")
        print(f"  config type: {type(body_sent['config']).__name__}")
        print(f"  config value: {body_sent['config']}")
        print()

        # Verify arrays and objects are native
        assert isinstance(body_sent["urls"], list)
        assert body_sent["urls"] == ["https://api1.com", "https://api2.com"]
        assert isinstance(body_sent["config"], dict)
        assert body_sent["config"]["debug"] is False
        assert body_sent["config"]["retries"] == 3

    print_result("Arrays and objects preserved as native types", body_sent)


def test_number_resolution():
    """Test that numbers are preserved as native integers and floats."""
    print_section("Test 3: Number Resolution")

    context = {
        "props": {"max_results": 100, "quality": 0.95, "temperature": 72.5},
        "env": {},
        "input": {},
    }

    body = HTTPBodyConfig(
        type="json",
        content={
            "max_results": "{!!props.max_results!!}",  # Native integer
            "quality": "{!!props.quality!!}",  # Native float
            "temperature": "{!!props.temperature!!}",  # Native float
        },
    )
    config = HTTPExecutionConfig(
        url="https://api.example.com/test", method="POST", body=body
    )
    executor = ExecutorFactory.get_executor(ExecutionType.HTTP)

    with patch("requests.request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        executor.execute(config, context)
        body_sent = mock_request.call_args[1]["json"]

        print(f"  max_results type: {type(body_sent['max_results']).__name__}")
        print(f"  max_results value: {body_sent['max_results']}")
        print(f"  quality type: {type(body_sent['quality']).__name__}")
        print(f"  quality value: {body_sent['quality']}")
        print(f"  temperature type: {type(body_sent['temperature']).__name__}")
        print(f"  temperature value: {body_sent['temperature']}")
        print()

        # Verify numbers are native
        assert isinstance(body_sent["max_results"], int)
        assert body_sent["max_results"] == 100
        assert isinstance(body_sent["quality"], float)
        assert body_sent["quality"] == 0.95
        assert isinstance(body_sent["temperature"], float)
        assert body_sent["temperature"] == 72.5

    print_result("Numbers preserved as native types", body_sent)


def test_mixed_placeholders():
    """Test mixing JSON-native and standard placeholders."""
    print_section("Test 4: Mixed Placeholders")

    context = {
        "props": {
            "enabled": True,
            "count": 50,
            "urls": ["https://a.com", "https://b.com"],
            "name": "My Search",
            "query": "testing",
        },
        "env": {},
        "input": {},
    }

    body = HTTPBodyConfig(
        type="json",
        content={
            "enabled": "{!!props.enabled!!}",  # Native boolean
            "count": "{!!props.count!!}",  # Native number
            "urls": "{!!props.urls!!}",  # Native array
            "name": "{{props.name}}",  # String placeholder
            "description": "Search for {{props.query}}",  # String with placeholder
            "static": "fixed value",  # No placeholder
        },
    )
    config = HTTPExecutionConfig(
        url="https://api.example.com/test", method="POST", body=body
    )
    executor = ExecutorFactory.get_executor(ExecutionType.HTTP)

    with patch("requests.request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        executor.execute(config, context)
        body_sent = mock_request.call_args[1]["json"]

        print("  Mixed placeholder types in same JSON body:")
        print(f"    enabled: {body_sent['enabled']} (type: {type(body_sent['enabled']).__name__})")
        print(f"    count: {body_sent['count']} (type: {type(body_sent['count']).__name__})")
        print(f"    urls: {body_sent['urls']} (type: {type(body_sent['urls']).__name__})")
        print(f"    name: {body_sent['name']} (type: {type(body_sent['name']).__name__})")
        print(
            f"    description: {body_sent['description']} (type: {type(body_sent['description']).__name__})"
        )
        print(f"    static: {body_sent['static']} (type: {type(body_sent['static']).__name__})")
        print()

        # Verify mixed types
        assert body_sent["enabled"] is True
        assert isinstance(body_sent["enabled"], bool)
        assert body_sent["count"] == 50
        assert isinstance(body_sent["count"], int)
        assert isinstance(body_sent["urls"], list)
        assert body_sent["name"] == "My Search"
        assert isinstance(body_sent["name"], str)
        assert body_sent["description"] == "Search for testing"
        assert isinstance(body_sent["description"], str)

    print_result("Mixed native and string placeholders work together", body_sent)


def main():
    """Run all manual tests."""
    print("\n" + "=" * 70)
    print("  JSON-Native Placeholder Resolution - Manual Feature Test")
    print("=" * 70)
    print("\nThis test demonstrates the {!!...!!} syntax for JSON-native resolution.")
    print("Standard {{...}} placeholders always resolve to strings.")
    print("JSON-native {!!...!!} placeholders preserve native types.\n")

    try:
        test_boolean_resolution()
        test_array_and_object_resolution()
        test_number_resolution()
        test_mixed_placeholders()

        print("\n" + "=" * 70)
        print("  ✓ All tests demonstrating JSON-native resolution passed!")
        print("=" * 70 + "\n")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        raise


if __name__ == "__main__":
    main()
