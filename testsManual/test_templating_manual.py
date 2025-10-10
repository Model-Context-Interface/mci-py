"""
Manual test for templating engine.

This file demonstrates the templating engine capabilities with clear output.
Run this file directly to see the templating engine in action.

Usage:
    uv run python testsManual/test_templating_manual.py
"""

from mcipy.templating import TemplateEngine, TemplateError


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_basic_placeholders():
    """Test basic placeholder substitution."""
    print_section("Basic Placeholder Substitution")

    engine = TemplateEngine()
    context = {
        "props": {"name": "Alice", "city": "New York", "age": 30},
        "env": {"API_KEY": "secret_key_123", "USER": "admin"},
        "input": {"name": "Alice", "city": "New York", "age": 30},
    }

    templates = [
        ("Simple props", "Hello {{props.name}}!"),
        ("Multiple props", "{{props.name}} lives in {{ props.city }} and is {{props.age}} years old"),
        ("Environment vars", "API Key: {{env.API_KEY}}, User: {{env.USER}}"),
        ("Input alias", "Using input: {{input.name}} from {{input.city}}"),
        ("Mixed", "User {{env.USER}} is processing {{props.name}}'s request"),
    ]

    for name, template in templates:
        print(f"\n{name}:")
        print(f"  Template: {template}")
        result = engine.render_basic(template, context)
        print(f"  Result:   {result}")


def test_nested_paths():
    """Test nested object path resolution."""
    print_section("Nested Path Resolution")

    engine = TemplateEngine()
    context = {
        "props": {
            "user": {
                "profile": {"firstName": "John", "lastName": "Doe"},
                "contact": {"email": "john@example.com", "phone": "555-0123"},
            }
        },
        "env": {},
        "input": {},
    }

    template = "Name: {{props.user.profile.firstName}} {{props.user.profile.lastName}}, Email: {{props.user.contact.email}}"
    print(f"\nTemplate: {template}")
    result = engine.render_basic(template, context)
    print(f"Result:   {result}")


def test_for_loops():
    """Test for loops."""
    print_section("For Loops")

    engine = TemplateEngine()
    context = {"props": {}, "env": {}, "input": {}}

    templates = [
        ("Simple loop", "@for(i in range(0, 5)){{i}} @endfor"),
        ("Numbered list", "@for(i in range(1, 4))Step {{i}}: Execute command\n@endfor"),
        ("Repeated pattern", "Items: @for(i in range(0, 3))[Item {{i}}] @endfor"),
    ]

    for name, template in templates:
        print(f"\n{name}:")
        print(f"  Template: {template}")
        result = engine.render_advanced(template, context)
        print(f"  Result:   {result}")


def test_foreach_loops():
    """Test foreach loops."""
    print_section("Foreach Loops")

    engine = TemplateEngine()

    # Test 1: Simple array
    print("\nTest 1: Simple Array")
    context1 = {
        "props": {"fruits": ["apple", "banana", "cherry"]},
        "env": {},
        "input": {},
    }
    template1 = "@foreach(fruit in props.fruits)- {{fruit}}\n@endforeach"
    print(f"  Template: {template1}")
    result1 = engine.render_advanced(template1, context1)
    print(f"  Result:\n{result1}")

    # Test 2: Array of objects
    print("\nTest 2: Array of Objects")
    context2 = {
        "props": {
            "users": [
                {"name": "Alice", "role": "Admin"},
                {"name": "Bob", "role": "User"},
                {"name": "Charlie", "role": "Moderator"},
            ]
        },
        "env": {},
        "input": {},
    }
    template2 = "@foreach(user in props.users)- {{user.name}} ({{user.role}})\n@endforeach"
    print(f"  Template: {template2}")
    result2 = engine.render_advanced(template2, context2)
    print(f"  Result:\n{result2}")


def test_conditionals():
    """Test conditional blocks."""
    print_section("Conditional Blocks")

    engine = TemplateEngine()

    # Test 1: If with truthiness
    print("\nTest 1: Truthiness Check")
    context1 = {"props": {"username": "alice"}, "env": {}, "input": {}}
    template1 = "@if(props.username)User is logged in as {{props.username}}@endif"
    print(f"  Template: {template1}")
    result1 = engine.render_advanced(template1, context1)
    print(f"  Result:   {result1}")

    # Test 2: If/Else
    print("\nTest 2: If/Else Block")
    context2a = {"props": {"status": "active"}, "env": {}, "input": {}}
    context2b = {"props": {"status": ""}, "env": {}, "input": {}}
    template2 = "@if(props.status)Status: Active@else Status: Inactive@endif"
    print(f"  Template: {template2}")
    print(f"  Result (active):   {engine.render_advanced(template2, context2a)}")
    print(f"  Result (inactive): {engine.render_advanced(template2, context2b)}")

    # Test 3: Equality check
    print("\nTest 3: Equality Check")
    context3 = {"props": {"mode": "production"}, "env": {}, "input": {}}
    template3 = '@if(props.mode == "production")Running in PRODUCTION mode@else Running in development mode@endif'
    print(f"  Template: {template3}")
    result3 = engine.render_advanced(template3, context3)
    print(f"  Result:   {result3}")

    # Test 4: Numeric comparison
    print("\nTest 4: Numeric Comparison")
    context4 = {"props": {"score": 85}, "env": {}, "input": {}}
    template4 = "@if(props.score > 80)Excellent work!@else Keep trying@endif"
    print(f"  Template: {template4}")
    result4 = engine.render_advanced(template4, context4)
    print(f"  Result:   {result4}")


def test_complex_example():
    """Test complex real-world example."""
    print_section("Complex Real-World Example: Report Generation")

    engine = TemplateEngine()
    context = {
        "props": {
            "reportTitle": "Q4 2024 Sales Report",
            "quarter": "Q4",
            "year": 2024,
            "department": "Sales",
            "salesData": [
                {"product": "Widget A", "revenue": 125000, "units": 500},
                {"product": "Widget B", "revenue": 89000, "units": 350},
                {"product": "Widget C", "revenue": 203000, "units": 780},
            ],
            "totalRevenue": 417000,
            "target": 400000,
        },
        "env": {"COMPANY_NAME": "ACME Corporation", "REPORT_SYSTEM": "AutoReport v2.1"},
        "input": {},
    }

    template = """
╔════════════════════════════════════════════════════════════════╗
  {{env.COMPANY_NAME}}
  {{props.reportTitle}}
╚════════════════════════════════════════════════════════════════╝

Department: {{props.department}}
Period: {{props.quarter}} {{props.year}}

SALES BREAKDOWN:
@foreach(sale in props.salesData)
• {{sale.product}}
  Revenue: ${{sale.revenue}}
  Units Sold: {{sale.units}}
@endforeach

SUMMARY:
Total Revenue: ${{props.totalRevenue}}
Target: ${{props.target}}

@if(props.totalRevenue > props.target)
✓ TARGET EXCEEDED! Outstanding performance this quarter.
  Exceeded target by ${{props.totalRevenue - props.target}}
@else
○ Target not met. Review strategy for next quarter.
@endif

────────────────────────────────────────────────────────────────
Generated by {{env.REPORT_SYSTEM}}
"""

    print("Rendering complex report...")
    result = engine.render_advanced(template, context)
    print(result)


def test_error_handling():
    """Test error handling."""
    print_section("Error Handling")

    engine = TemplateEngine()
    context = {"props": {"name": "Alice"}, "env": {}, "input": {}}

    print("\nTest 1: Missing placeholder")
    template1 = "Hello {{props.missing}}"
    print(f"  Template: {template1}")
    try:
        result1 = engine.render_basic(template1, context)
        print(f"  Result:   {result1}")
    except TemplateError as e:
        print(f"  Error (expected): {e}")

    print("\nTest 2: Invalid path (accessing property on non-dict)")
    context2 = {"props": {"value": "string"}, "env": {}, "input": {}}
    template2 = "Value: {{props.value.invalid}}"
    print(f"  Template: {template2}")
    try:
        result2 = engine.render_basic(template2, context2)
        print(f"  Result:   {result2}")
    except TemplateError as e:
        print(f"  Error (expected): {e}")

    print("\nTest 3: Foreach on non-iterable")
    context3 = {"props": {"value": "not an array"}, "env": {}, "input": {}}
    template3 = "@foreach(item in props.value){{item}}@endforeach"
    print(f"  Template: {template3}")
    try:
        result3 = engine.render_advanced(template3, context3)
        print(f"  Result:   {result3}")
    except TemplateError as e:
        print(f"  Error (expected): {e}")


def main():
    """Run all manual tests."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "MCI TEMPLATING ENGINE MANUAL TEST" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        test_basic_placeholders()
        test_nested_paths()
        test_for_loops()
        test_foreach_loops()
        test_conditionals()
        test_complex_example()
        test_error_handling()

        print("\n" + "=" * 70)
        print("  ✓ All manual tests completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ Error during manual testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
