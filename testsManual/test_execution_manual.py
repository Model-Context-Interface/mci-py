#!/usr/bin/env python3
"""
Manual test for end-to-end execution flow with ExecutorFactory.

This test demonstrates the complete execution workflow for each execution type:
- ExecutorFactory resolution of executors
- Full execution from config to result
- Error handling scenarios

Run with: uv run python testsManual/test_execution_manual.py
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mcipy.enums import ExecutionType
from mcipy.executors import ExecutorFactory
from mcipy.models import (
    CLIExecutionConfig,
    FileExecutionConfig,
    HTTPExecutionConfig,
    TextExecutionConfig,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"{title:^70}")
    print(f"{'=' * 70}\n")


def test_executor_factory():
    """Test ExecutorFactory resolution and caching."""
    print_section("EXECUTOR FACTORY TESTS")

    # Test 1: Get HTTP executor
    print("1. Get HTTP Executor:")
    http_executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
    print(f"   Type: {type(http_executor).__name__}")
    print(f"   Expected: HTTPExecutor")
    print(f"   Status: {'✓ Success' if type(http_executor).__name__ == 'HTTPExecutor' else '✗ Failed'}\n")

    # Test 2: Get CLI executor
    print("2. Get CLI Executor:")
    cli_executor = ExecutorFactory.get_executor(ExecutionType.CLI)
    print(f"   Type: {type(cli_executor).__name__}")
    print(f"   Expected: CLIExecutor")
    print(f"   Status: {'✓ Success' if type(cli_executor).__name__ == 'CLIExecutor' else '✗ Failed'}\n")

    # Test 3: Get File executor
    print("3. Get File Executor:")
    file_executor = ExecutorFactory.get_executor(ExecutionType.FILE)
    print(f"   Type: {type(file_executor).__name__}")
    print(f"   Expected: FileExecutor")
    print(f"   Status: {'✓ Success' if type(file_executor).__name__ == 'FileExecutor' else '✗ Failed'}\n")

    # Test 4: Get Text executor
    print("4. Get Text Executor:")
    text_executor = ExecutorFactory.get_executor(ExecutionType.TEXT)
    print(f"   Type: {type(text_executor).__name__}")
    print(f"   Expected: TextExecutor")
    print(f"   Status: {'✓ Success' if type(text_executor).__name__ == 'TextExecutor' else '✗ Failed'}\n")

    # Test 5: Caching (same instance returned)
    print("5. Executor Caching:")
    http_executor2 = ExecutorFactory.get_executor(ExecutionType.HTTP)
    is_cached = http_executor is http_executor2
    print(f"   First call:  {id(http_executor)}")
    print(f"   Second call: {id(http_executor2)}")
    print(f"   Same instance: {is_cached}")
    print(f"   Status: {'✓ Success' if is_cached else '✗ Failed'}\n")

    # Test 6: Cache clearing
    print("6. Cache Clearing:")
    ExecutorFactory.clear_cache()
    http_executor3 = ExecutorFactory.get_executor(ExecutionType.HTTP)
    is_different = http_executor is not http_executor3
    print(f"   Original:     {id(http_executor)}")
    print(f"   After clear:  {id(http_executor3)}")
    print(f"   Different instance: {is_different}")
    print(f"   Status: {'✓ Success' if is_different else '✗ Failed'}\n")


def test_text_execution_e2e():
    """Test end-to-end text execution via factory."""
    print_section("TEXT EXECUTION END-TO-END")

    # Build context
    context = {
        "props": {"name": "Alice", "role": "Developer"},
        "env": {"COMPANY": "ACME Corp"},
        "input": {"name": "Alice", "role": "Developer"},
    }

    # Get executor via factory
    executor = ExecutorFactory.get_executor(ExecutionType.TEXT)

    # Test 1: Simple text execution
    print("1. Simple Text Execution:")
    config1 = TextExecutionConfig(text="Hello {{props.name}}, {{props.role}} at {{env.COMPANY}}!")
    result1 = executor.execute(config1, context)
    print(f"   Template: 'Hello {{{{props.name}}}}, {{{{props.role}}}} at {{{{env.COMPANY}}}}!'")
    print(f"   Result:   '{result1.content}'")
    print(f"   Expected: 'Hello Alice, Developer at ACME Corp!'")
    print(f"   Status: {'✓ Success' if not result1.isError else '✗ Error'}\n")

    # Test 2: Advanced templating with @foreach
    print("2. Advanced Templating (@foreach):")
    context["props"]["items"] = ["Task 1", "Task 2", "Task 3"]
    context["input"]["items"] = ["Task 1", "Task 2", "Task 3"]
    config2 = TextExecutionConfig(
        text="Tasks:\n@foreach(item in props.items)\n- {{item}}\n@endforeach"
    )
    result2 = executor.execute(config2, context)
    print(f"   Template: Tasks with @foreach loop")
    print(f"   Result:\n{result2.content}")
    print(f"   Status: {'✓ Success' if not result2.isError else '✗ Error'}\n")


def test_file_execution_e2e():
    """Test end-to-end file execution via factory."""
    print_section("FILE EXECUTION END-TO-END")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("User: {{props.username}}\nRole: {{props.role}}\nCompany: {{env.COMPANY}}")
        temp_file = f.name

    try:
        # Build context
        context = {
            "props": {"username": "Bob", "role": "Manager"},
            "env": {"COMPANY": "TechCorp"},
            "input": {"username": "Bob", "role": "Manager"},
        }

        # Get executor via factory
        executor = ExecutorFactory.get_executor(ExecutionType.FILE)

        # Test 1: File reading with templating
        print("1. File Reading with Templating:")
        config1 = FileExecutionConfig(path=temp_file, enableTemplating=True)
        result1 = executor.execute(config1, context)
        print(f"   Path: {temp_file}")
        print(f"   Templating: enabled")
        print(f"   Result:\n{result1.content}")
        print(f"   Status: {'✓ Success' if not result1.isError else '✗ Error'}\n")

        # Test 2: File reading without templating
        print("2. File Reading without Templating:")
        config2 = FileExecutionConfig(path=temp_file, enableTemplating=False)
        result2 = executor.execute(config2, context)
        print(f"   Path: {temp_file}")
        print(f"   Templating: disabled")
        print(f"   Result:\n{result2.content}")
        print(f"   Status: {'✓ Success' if not result2.isError else '✗ Error'}\n")

        # Test 3: Error handling - file not found
        print("3. Error Handling (File Not Found):")
        config3 = FileExecutionConfig(path="/nonexistent/file.txt", enableTemplating=False)
        result3 = executor.execute(config3, context)
        print(f"   Path: /nonexistent/file.txt")
        print(f"   Status: {'✗ Error (as expected)' if result3.isError else '✓ Success (unexpected!)'}")
        print(f"   Error: {result3.error}\n")

    finally:
        # Cleanup
        Path(temp_file).unlink()


def test_cli_execution_e2e():
    """Test end-to-end CLI execution via factory."""
    print_section("CLI EXECUTION END-TO-END")

    # Build context
    context = {
        "props": {"directory": "."},
        "env": {},
        "input": {"directory": "."},
    }

    # Get executor via factory
    executor = ExecutorFactory.get_executor(ExecutionType.CLI)

    # Test 1: Simple command execution
    print("1. Simple Command Execution (echo):")
    config1 = CLIExecutionConfig(command="echo", args=["Hello from CLI executor!"])
    result1 = executor.execute(config1, context)
    print(f"   Command: echo 'Hello from CLI executor!'")
    print(f"   Result: '{result1.content.strip() if result1.content else 'None'}'")
    print(f"   Status: {'✓ Success' if not result1.isError else '✗ Error'}\n")

    # Test 2: Command with templating in args
    print("2. Command with Templating:")
    config2 = CLIExecutionConfig(command="ls", args=["{{props.directory}}"])
    result2 = executor.execute(config2, context)
    print(f"   Command: ls {{{{props.directory}}}}")
    print(f"   Resolved: ls {context['props']['directory']}")
    print(f"   Status: {'✓ Success' if not result2.isError else '✗ Error'}")
    print(f"   Output (first 200 chars): {(result2.content or '')[:200]}\n")

    # Test 3: Error handling - command not found
    print("3. Error Handling (Command Not Found):")
    config3 = CLIExecutionConfig(command="nonexistent_command_12345")
    result3 = executor.execute(config3, context)
    print(f"   Command: nonexistent_command_12345")
    print(f"   Status: {'✗ Error (as expected)' if result3.isError else '✓ Success (unexpected!)'}")
    print(f"   Error: {result3.error[:100] if result3.error else 'None'}\n")


def test_http_execution_e2e():
    """Test end-to-end HTTP execution via factory (with mocks)."""
    print_section("HTTP EXECUTION END-TO-END")

    # Build context
    context = {
        "props": {"city": "London"},
        "env": {"API_KEY": "test-key-123"},
        "input": {"city": "London"},
    }

    # Get executor via factory
    executor = ExecutorFactory.get_executor(ExecutionType.HTTP)  # We'll patch it

    # Test 1: HTTP GET request with mocking
    print("1. HTTP GET Request (mocked):")
    config1 = HTTPExecutionConfig(
        url="https://api.example.com/weather?city={{props.city}}",
        method="GET",
    )

    with patch("requests.request") as mock_request:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"temperature": 22, "condition": "sunny"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        # Get HTTP executor
        http_executor = ExecutorFactory.get_executor(ExecutionType.HTTP)
        result1 = http_executor.execute(config1, context)

        print(f"   URL: https://api.example.com/weather?city={{{{props.city}}}}")
        print(f"   Resolved: https://api.example.com/weather?city=London")
        print(f"   Method: GET")
        print(f"   Response: {result1.content}")
        print(f"   Status: {'✓ Success' if not result1.isError else '✗ Error'}\n")

    # Test 2: HTTP POST with auth
    print("2. HTTP POST Request with Auth (mocked):")
    from mcipy.models import ApiKeyAuth

    auth = ApiKeyAuth(**{"in": "header", "name": "X-API-Key", "value": "{{env.API_KEY}}"})
    config2 = HTTPExecutionConfig(
        url="https://api.example.com/data",
        method="POST",
        auth=auth,
    )

    with patch("requests.request") as mock_request:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123, "status": "created"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result2 = http_executor.execute(config2, context)
        call_kwargs = mock_request.call_args[1]

        print(f"   URL: https://api.example.com/data")
        print(f"   Method: POST")
        print(f"   Auth header: {call_kwargs.get('headers', {}).get('X-API-Key', 'None')}")
        print(f"   Response: {result2.content}")
        print(f"   Status: {'✓ Success' if not result2.isError else '✗ Error'}\n")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 70)
    print("MCI END-TO-END EXECUTION MANUAL TESTS".center(70))
    print("=" * 70)

    try:
        test_executor_factory()
        test_text_execution_e2e()
        test_file_execution_e2e()
        test_cli_execution_e2e()
        test_http_execution_e2e()

        print_section("ALL TESTS COMPLETED")
        print("✓ All manual tests completed successfully!\n")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
