#!/usr/bin/env python3
"""
Manual verification test for path validation security features.

This test demonstrates the path validation security features in action,
showing both allowed and blocked file access scenarios.
"""

import json
import tempfile
from pathlib import Path

from mcipy import MCIClient


def test_basic_path_restriction():
    """Test that path validation blocks access outside schema directory."""
    print("=" * 80)
    print("TEST 1: Basic Path Restriction")
    print("=" * 80)

    # Create a temporary directory for the schema
    with tempfile.TemporaryDirectory() as schema_dir:
        schema_path = Path(schema_dir)

        # Create a file inside the schema directory
        allowed_file = schema_path / "allowed.txt"
        allowed_file.write_text("This file is in the schema directory")

        # Create a file outside the schema directory
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("This file is OUTSIDE the schema directory")
            blocked_file = Path(f.name)

        try:
            # Create schema with file tools
            schema = {
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "read_allowed",
                        "execution": {"type": "file", "path": str(allowed_file)},
                    },
                    {
                        "name": "read_blocked",
                        "execution": {"type": "file", "path": str(blocked_file)},
                    },
                ],
            }

            schema_file = schema_path / "test.mci.json"
            schema_file.write_text(json.dumps(schema))

            # Initialize client
            client = MCIClient(schema_file_path=str(schema_file))

            # Test allowed file access
            print("\n✓ Testing allowed file access (inside schema directory)...")
            result = client.execute("read_allowed")
            assert not result.result.isError, "Should allow access to file in schema directory"
            assert "schema directory" in result.result.content[0].text
            print("  SUCCESS: File read from schema directory")

            # Test blocked file access
            print("\n✗ Testing blocked file access (outside schema directory)...")
            result = client.execute("read_blocked")
            assert result.result.isError, "Should block access to file outside schema directory"
            assert "File path access outside context directory" in result.result.content[0].text
            print(f"  SUCCESS: Access blocked - {result.result.content[0].text[:80]}...")

        finally:
            blocked_file.unlink(missing_ok=True)


def test_enable_any_paths():
    """Test that enableAnyPaths allows unrestricted file access."""
    print("\n" + "=" * 80)
    print("TEST 2: enableAnyPaths Override")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as schema_dir:
        schema_path = Path(schema_dir)

        # Create a file outside the schema directory
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Outside file content")
            outside_file = Path(f.name)

        try:
            # Create schema with enableAnyPaths at tool level
            schema = {
                "schemaVersion": "1.0",
                "tools": [
                    {
                        "name": "read_anywhere",
                        "enableAnyPaths": True,
                        "execution": {"type": "file", "path": str(outside_file)},
                    }
                ],
            }

            schema_file = schema_path / "test.mci.json"
            schema_file.write_text(json.dumps(schema))

            client = MCIClient(schema_file_path=str(schema_file))

            print("\n✓ Testing file access with enableAnyPaths=True...")
            result = client.execute("read_anywhere")
            assert not result.result.isError, "Should allow access when enableAnyPaths=True"
            assert "Outside file content" in result.result.content[0].text
            print("  SUCCESS: Access allowed with enableAnyPaths override")

        finally:
            outside_file.unlink(missing_ok=True)


def test_directory_allow_list():
    """Test that directoryAllowList allows specific directories."""
    print("\n" + "=" * 80)
    print("TEST 3: directoryAllowList")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as schema_dir:
        schema_path = Path(schema_dir)

        # Create an allowed directory with a file
        with tempfile.TemporaryDirectory() as allowed_dir:
            allowed_path = Path(allowed_dir)
            test_file = allowed_path / "test.txt"
            test_file.write_text("File in allowed directory")

            # Create schema with directoryAllowList
            schema = {
                "schemaVersion": "1.0",
                "directoryAllowList": [str(allowed_path)],
                "tools": [
                    {
                        "name": "read_from_allowed",
                        "execution": {"type": "file", "path": str(test_file)},
                    }
                ],
            }

            schema_file = schema_path / "test.mci.json"
            schema_file.write_text(json.dumps(schema))

            client = MCIClient(schema_file_path=str(schema_file))

            print(f"\n✓ Testing file access from allowed directory: {allowed_path}")
            result = client.execute("read_from_allowed")
            assert not result.result.isError, "Should allow access to directoryAllowList directory"
            assert "allowed directory" in result.result.content[0].text
            print("  SUCCESS: Access allowed to directory in allow-list")


def test_cli_cwd_validation():
    """Test that CLI working directory is validated."""
    print("\n" + "=" * 80)
    print("TEST 4: CLI Working Directory Validation")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as schema_dir:
        schema_path = Path(schema_dir)

        # Create a test file in schema directory
        test_file = schema_path / "test.txt"
        test_file.write_text("test")

        # Create schema with CLI tool
        schema = {
            "schemaVersion": "1.0",
            "tools": [
                {
                    "name": "list_schema_dir",
                    "execution": {"type": "cli", "command": "ls", "cwd": str(schema_path)},
                },
                {
                    "name": "list_tmp",
                    "execution": {"type": "cli", "command": "ls", "cwd": "/tmp"},
                },
            ],
        }

        schema_file = schema_path / "test.mci.json"
        schema_file.write_text(json.dumps(schema))

        client = MCIClient(schema_file_path=str(schema_file))

        # Test allowed cwd (schema directory)
        print("\n✓ Testing CLI with cwd in schema directory...")
        result = client.execute("list_schema_dir")
        assert not result.result.isError, "Should allow cwd in schema directory"
        print("  SUCCESS: CLI allowed to use schema directory as cwd")

        # Test blocked cwd (outside schema directory)
        print("\n✗ Testing CLI with cwd outside schema directory...")
        result = client.execute("list_tmp")
        assert result.result.isError, "Should block cwd outside schema directory"
        assert "File path access outside context directory" in result.result.content[0].text
        print(f"  SUCCESS: CLI blocked from using outside cwd - {result.result.content[0].text[:80]}...")


def main():
    """Run all manual verification tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  MCI Path Validation Security Features - Manual Verification".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        test_basic_path_restriction()
        test_enable_any_paths()
        test_directory_allow_list()
        test_cli_cwd_validation()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print(
            "\nPath validation security features are working correctly!\n"
            "- File access is restricted to schema directory by default\n"
            "- enableAnyPaths override works as expected\n"
            "- directoryAllowList allows specific directories\n"
            "- CLI working directory validation is enforced\n"
        )

    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"\nAssertion Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
