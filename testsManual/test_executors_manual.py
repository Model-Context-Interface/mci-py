#!/usr/bin/env python3
"""
Manual test for executor implementations.

This test demonstrates the BaseExecutor, FileExecutor, and TextExecutor classes
working with various templating features including @for, @foreach, and @if directives.

Run with: uv run python testsManual/test_executors_manual.py
"""

import tempfile
from pathlib import Path

from mcipy.executors import FileExecutor, TextExecutor
from mcipy.models import FileExecutionConfig, TextExecutionConfig


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print(f"{'=' * 60}\n")


def test_text_executor():
    """Test TextExecutor with various templating features."""
    print_section("TEXT EXECUTOR TESTS")

    executor = TextExecutor()
    context = {
        "props": {
            "user": "Alice",
            "project": "MCI Adapter",
            "tasks": ["Design", "Implementation", "Testing"],
            "priority": "high",
        },
        "env": {
            "COMPANY": "ACME Corp",
            "VERSION": "1.0.0",
        },
        "input": {
            "user": "Alice",
            "project": "MCI Adapter",
            "tasks": ["Design", "Implementation", "Testing"],
            "priority": "high",
        },
    }

    # Test 1: Simple placeholder substitution
    print("1. Simple Placeholder Substitution:")
    config1 = TextExecutionConfig(text="Hello {{props.user}} from {{env.COMPANY}}!")
    result1 = executor.execute(config1, context)
    print(f"   Input:  'Hello {{{{props.user}}}} from {{{{env.COMPANY}}}}!'")
    print(f"   Output: '{result1.content}'")
    print(f"   Status: {'✓ Success' if not result1.isError else '✗ Error'}\n")

    # Test 2: @foreach loop
    print("2. @foreach Loop:")
    config2 = TextExecutionConfig(
        text="Tasks:\n@foreach(task in props.tasks)\n- {{task}}\n@endforeach"
    )
    result2 = executor.execute(config2, context)
    print("   Input:")
    print("     Tasks:")
    print("     @foreach(task in props.tasks)")
    print("     - {{task}}")
    print("     @endforeach")
    print(f"   Output:\n{result2.content}")
    print(f"   Status: {'✓ Success' if not result2.isError else '✗ Error'}\n")

    # Test 3: @for loop
    print("3. @for Loop:")
    config3 = TextExecutionConfig(text="@for(i in range(0, 3))\n{{i}}. Item {{i}}\n@endfor")
    result3 = executor.execute(config3, context)
    print("   Input:")
    print("     @for(i in range(0, 3))")
    print("     {{i}}. Item {{i}}")
    print("     @endfor")
    print(f"   Output:\n{result3.content}")
    print(f"   Status: {'✓ Success' if not result3.isError else '✗ Error'}\n")

    # Test 4: @if conditional
    print("4. @if Conditional:")
    config4 = TextExecutionConfig(
        text='@if(props.priority == "high")\n⚠️ High Priority!\n@else\n✓ Normal Priority\n@endif'
    )
    result4 = executor.execute(config4, context)
    print("   Input:")
    print('     @if(props.priority == "high")')
    print("     ⚠️ High Priority!")
    print("     @else")
    print("     ✓ Normal Priority")
    print("     @endif")
    print(f"   Output:\n{result4.content}")
    print(f"   Status: {'✓ Success' if not result4.isError else '✗ Error'}\n")

    # Test 5: Complex template with all features
    print("5. Complex Template (All Features):")
    complex_template = """{{env.COMPANY}} - {{props.project}} v{{env.VERSION}}
User: {{props.user}}

Task List:
@foreach(task in props.tasks)
- {{task}}
@endforeach

Progress:
@for(i in range(0, 3))
Step {{i}}: In Progress
@endfor

@if(props.priority == "high")
⚠️ This is a high priority project!
@endif"""

    config5 = TextExecutionConfig(text=complex_template)
    result5 = executor.execute(config5, context)
    print("   Output:")
    print(result5.content)
    print(f"   Status: {'✓ Success' if not result5.isError else '✗ Error'}\n")


def test_file_executor():
    """Test FileExecutor with various templating features."""
    print_section("FILE EXECUTOR TESTS")

    executor = FileExecutor()
    context = {
        "props": {"name": "Bob", "items": ["apple", "banana", "cherry"]},
        "env": {"MODE": "production", "API_URL": "https://api.example.com"},
        "input": {"name": "Bob", "items": ["apple", "banana", "cherry"]},
    }

    # Test 1: File without templating
    print("1. Read File Without Templating:")
    content1 = "This is plain text with {{props.name}} placeholder that won't be replaced."
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write(content1)
        temp_path1 = f.name

    try:
        config1 = FileExecutionConfig(path=temp_path1, enableTemplating=False)
        result1 = executor.execute(config1, context)
        print(f"   File content: '{content1}'")
        print(f"   Output:       '{result1.content}'")
        print(f"   Status: {'✓ Success' if not result1.isError else '✗ Error'}\n")
    finally:
        Path(temp_path1).unlink(missing_ok=True)

    # Test 2: File with templating
    print("2. Read File With Templating:")
    content2 = """Hello {{props.name}}!

Your items:
@foreach(item in props.items)
- {{item}}
@endforeach

API URL: {{env.API_URL}}

@if(env.MODE == "production")
✓ Running in production mode
@else
⚠ Running in development mode
@endif"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write(content2)
        temp_path2 = f.name

    try:
        config2 = FileExecutionConfig(path=temp_path2, enableTemplating=True)
        result2 = executor.execute(config2, context)
        print("   File content:")
        print(content2)
        print("\n   Output after templating:")
        print(result2.content)
        print(f"   Status: {'✓ Success' if not result2.isError else '✗ Error'}\n")
    finally:
        Path(temp_path2).unlink(missing_ok=True)

    # Test 3: Templated file path
    print("3. Templated File Path:")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file with a specific name
        file_name = "config.txt"
        file_path = Path(temp_dir) / file_name
        file_path.write_text("Configuration loaded successfully!")

        # Use templated path
        context_with_path = {
            "props": {"filename": file_name},
            "env": {"CONFIG_DIR": temp_dir},
            "input": {"filename": file_name},
        }

        config3 = FileExecutionConfig(
            path="{{env.CONFIG_DIR}}/{{props.filename}}", enableTemplating=False
        )
        result3 = executor.execute(config3, context_with_path)
        print(f"   Path template: '{{{{env.CONFIG_DIR}}}}/{{{{props.filename}}}}'")
        print(f"   Resolved path: '{temp_dir}/{file_name}'")
        print(f"   Content:       '{result3.content}'")
        print(f"   Status: {'✓ Success' if not result3.isError else '✗ Error'}\n")

    # Test 4: Config-level templating demonstration
    print("4. Config-Level Templating (New Feature):")
    print("   Testing that ALL execution config fields are templated automatically")

    # Create a context with username
    context_demo = {
        "props": {"username": "john"},
        "env": {"BASE_PATH": "/var/data"},
        "input": {"username": "john"},
    }

    # The path will be automatically templated by the executor
    config_demo = FileExecutionConfig(
        path="{{env.BASE_PATH}}/users/{{props.username}}/data.txt", enableTemplating=False
    )

    # Create a temporary file to match the templated path
    import os

    templated_dir = f"/tmp/users/john"
    os.makedirs(templated_dir, exist_ok=True)
    templated_file = f"{templated_dir}/data.txt"
    Path(templated_file).write_text("User data for john")

    try:
        # Note: We use a modified context to point to /tmp instead
        context_demo["env"]["BASE_PATH"] = "/tmp"
        result_demo = executor.execute(config_demo, context_demo)

        print(f"   Original path: '{{{{env.BASE_PATH}}}}/users/{{{{props.username}}}}/data.txt'")
        print(f"   Templated to:  '/tmp/users/john/data.txt'")
        print(f"   Content:       '{result_demo.content}'")
        print(f"   Status: {'✓ Success' if not result_demo.isError else '✗ Error'}")
        print("   Note: Path templating happens automatically in the executor!\n")
    finally:
        # Cleanup
        if Path(templated_file).exists():
            Path(templated_file).unlink()
        if Path(templated_dir).exists():
            Path(templated_dir).rmdir()

    # Test 5: Error handling - file not found
    print("5. Error Handling (File Not Found):")
    config4 = FileExecutionConfig(path="/nonexistent/file.txt", enableTemplating=False)
    result4 = executor.execute(config4, context)
    print(f"   Path: '/nonexistent/file.txt'")
    print(f"   Status: {'✗ Error (as expected)' if result4.isError else '✓ Success (unexpected!)'}")
    print(f"   Error message: '{result4.error}'")


def test_context_building():
    """Test that context building works correctly."""
    print_section("CONTEXT BUILDING TEST")

    executor = TextExecutor()

    # Build context using the base executor method
    props = {"user": "Charlie", "age": 25}
    env_vars = {"API_KEY": "secret123"}

    context = executor._build_context(props, env_vars)

    print("Test: Context building with _build_context()")
    print(f"   Props:   {props}")
    print(f"   Env:     {env_vars}")
    print(f"   Context: {context}")
    print(
        f"   Status: {'✓ Success' if context['input'] is context['props'] else '✗ Error'}"
    )
    print(f"   Note: 'input' is an alias for 'props' (same object reference)\n")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 60)
    print("MCI EXECUTOR MANUAL TESTS".center(60))
    print("=" * 60)

    try:
        test_context_building()
        test_text_executor()
        test_file_executor()

        print_section("ALL TESTS COMPLETED")
        print("✓ All manual tests completed successfully!\n")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
