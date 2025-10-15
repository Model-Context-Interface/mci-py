"""Unit tests for templating engine."""

from typing import Any

import pytest

from mcipy.templating import TemplateEngine, TemplateError


@pytest.fixture
def engine():
    """Fixture for TemplateEngine instance."""
    return TemplateEngine()


@pytest.fixture
def context() -> dict[str, Any]:
    """Fixture for test context with props, env, and input."""
    return {
        "props": {"name": "Alice", "age": 30, "city": "NYC"},
        "env": {"API_KEY": "secret123", "USER": "testuser"},
        "input": {"name": "Alice", "age": 30, "city": "NYC"},
    }


class TestRenderBasic:
    """Tests for render_basic method."""

    def test_simple_placeholder_props(self, engine, context):
        """Test simple placeholder replacement from props."""
        template = "Hello {{props.name}}"
        result = engine.render_basic(template, context)
        assert result == "Hello Alice"

    def test_simple_placeholder_env(self, engine, context):
        """Test simple placeholder replacement from env."""
        template = "API Key: {{env.API_KEY}}"
        result = engine.render_basic(template, context)
        assert result == "API Key: secret123"

    def test_simple_placeholder_input(self, engine, context):
        """Test simple placeholder replacement from input (alias for props)."""
        template = "User: {{input.name}}"
        result = engine.render_basic(template, context)
        assert result == "User: Alice"

    def test_multiple_placeholders(self, engine, context):
        """Test multiple placeholders in one template."""
        template = "{{props.name}} lives in {{props.city}}, age {{props.age}}"
        result = engine.render_basic(template, context)
        assert result == "Alice lives in NYC, age 30"

    def test_mixed_props_and_env(self, engine, context):
        """Test mixing props and env placeholders."""
        template = "User {{env.USER}} has name {{props.name}}"
        result = engine.render_basic(template, context)
        assert result == "User testuser has name Alice"

    def test_placeholder_with_whitespace(self, engine, context):
        """Test placeholders with whitespace are handled."""
        template = "{{ props.name }} and {{ env.USER }}"
        result = engine.render_basic(template, context)
        assert result == "Alice and testuser"

    def test_no_placeholders(self, engine, context):
        """Test template with no placeholders."""
        template = "Just plain text"
        result = engine.render_basic(template, context)
        assert result == "Just plain text"

    def test_missing_placeholder(self, engine, context):
        """Test error when placeholder path doesn't exist."""
        template = "Hello {{props.missing}}"
        with pytest.raises(TemplateError) as exc_info:
            engine.render_basic(template, context)
        # Error message should include the placeholder path
        error_msg = str(exc_info.value)
        assert "props.missing" in error_msg
        assert "{{props.missing}}" in error_msg  # Should show the placeholder format
        assert "not found" in error_msg


class TestResolvePlaceholder:
    """Tests for _resolve_placeholder method."""

    def test_resolve_simple_path(self, engine, context):
        """Test resolving a simple path."""
        result = engine._resolve_placeholder("props.name", context)
        assert result == "Alice"

    def test_resolve_nested_path(self, engine):
        """Test resolving nested paths."""
        context = {"props": {"user": {"profile": {"name": "Bob", "email": "bob@example.com"}}}}
        result = engine._resolve_placeholder("props.user.profile.name", context)
        assert result == "Bob"

    def test_resolve_env_path(self, engine, context):
        """Test resolving environment variable path."""
        result = engine._resolve_placeholder("env.API_KEY", context)
        assert result == "secret123"

    def test_resolve_missing_key(self, engine, context):
        """Test error when key doesn't exist."""
        with pytest.raises(TemplateError) as exc_info:
            engine._resolve_placeholder("props.nonexistent", context)
        assert "not found" in str(exc_info.value)

    def test_resolve_missing_nested_key(self, engine):
        """Test error when nested key doesn't exist."""
        context = {"props": {"user": {"name": "Alice"}}}
        with pytest.raises(TemplateError) as exc_info:
            engine._resolve_placeholder("props.user.email", context)
        assert "not found" in str(exc_info.value)

    def test_resolve_non_dict_access(self, engine):
        """Test error when trying to access property on non-dict."""
        context = {"props": {"value": "string"}}
        with pytest.raises(TemplateError) as exc_info:
            engine._resolve_placeholder("props.value.invalid", context)
        assert "non-dict" in str(exc_info.value)


class TestParseForLoop:
    """Tests for _parse_for_loop method."""

    def test_simple_for_loop(self, engine, context):
        """Test simple for loop."""
        template = "@for(i in range(0, 3))Item {{i}} @endfor"
        result = engine._parse_for_loop(template, context)
        assert result == "Item 0 Item 1 Item 2 "

    def test_for_loop_with_text(self, engine, context):
        """Test for loop with surrounding text."""
        template = "Start @for(i in range(1, 4)){{i}}, @endfor End"
        result = engine._parse_for_loop(template, context)
        assert result == "Start 1, 2, 3,  End"

    def test_for_loop_single_iteration(self, engine, context):
        """Test for loop with single iteration."""
        template = "@for(i in range(0, 1))Single {{i}}@endfor"
        result = engine._parse_for_loop(template, context)
        assert result == "Single 0"

    def test_for_loop_zero_iterations(self, engine, context):
        """Test for loop with zero iterations."""
        template = "@for(i in range(0, 0))Should not appear@endfor"
        result = engine._parse_for_loop(template, context)
        assert result == ""

    def test_multiple_for_loops(self, engine, context):
        """Test multiple for loops in same template."""
        template = "@for(i in range(0, 2))A{{i}}@endfor-@for(j in range(0, 2))B{{j}}@endfor"
        result = engine._parse_for_loop(template, context)
        assert result == "A0A1-B0B1"


class TestParseForeachLoop:
    """Tests for _parse_foreach_loop method."""

    def test_foreach_simple_array(self, engine):
        """Test foreach loop with simple array."""
        context = {"props": {"items": ["apple", "banana", "cherry"]}, "env": {}, "input": {}}
        template = "@foreach(item in props.items){{item}}, @endforeach"
        result = engine._parse_foreach_loop(template, context)
        assert result == "apple, banana, cherry, "

    def test_foreach_array_of_objects(self, engine):
        """Test foreach loop with array of objects."""
        context = {
            "props": {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]},
            "env": {},
            "input": {},
        }
        template = "@foreach(user in props.users){{user.name}} is {{user.age}}, @endforeach"
        result = engine._parse_foreach_loop(template, context)
        assert result == "Alice is 30, Bob is 25, "

    def test_foreach_object(self, engine):
        """Test foreach loop with object/dict."""
        context = {"props": {"config": {"host": "localhost", "port": 8080}}, "env": {}, "input": {}}
        template = "@foreach(value in props.config){{value}}, @endforeach"
        result = engine._parse_foreach_loop(template, context)
        # Note: dict iteration order is preserved in Python 3.7+
        assert "localhost" in result and "8080" in result

    def test_foreach_empty_array(self, engine):
        """Test foreach loop with empty array."""
        context = {"props": {"items": []}, "env": {}, "input": {}}
        template = "@foreach(item in props.items){{item}}@endforeach"
        result = engine._parse_foreach_loop(template, context)
        assert result == ""

    def test_foreach_missing_path(self, engine, context):
        """Test error when foreach path doesn't exist."""
        template = "@foreach(item in props.missing){{item}}@endforeach"
        with pytest.raises(TemplateError) as exc_info:
            engine._parse_foreach_loop(template, context)
        assert "props.missing" in str(exc_info.value)

    def test_foreach_non_iterable(self, engine):
        """Test error when foreach path is not array or object."""
        context = {"props": {"value": "string"}, "env": {}, "input": {}}
        template = "@foreach(item in props.value){{item}}@endforeach"
        with pytest.raises(TemplateError) as exc_info:
            engine._parse_foreach_loop(template, context)
        assert "array or object" in str(exc_info.value)


class TestParseControlBlocks:
    """Tests for _parse_control_blocks method."""

    def test_if_true_condition(self, engine, context):
        """Test if block with true condition."""
        template = "@if(props.name)Name exists@endif"
        result = engine._parse_control_blocks(template, context)
        assert result == "Name exists"

    def test_if_false_condition(self, engine):
        """Test if block with false condition."""
        context = {"props": {"name": ""}, "env": {}, "input": {}}
        template = "@if(props.name)Name exists@endif"
        result = engine._parse_control_blocks(template, context)
        assert result == ""

    def test_if_else_true(self, engine, context):
        """Test if/else block when condition is true."""
        template = "@if(props.name)Has name@else No name@endif"
        result = engine._parse_control_blocks(template, context)
        assert result == "Has name"

    def test_if_else_false(self, engine):
        """Test if/else block when condition is false."""
        context = {"props": {"name": ""}, "env": {}, "input": {}}
        template = "@if(props.name)Has name@else No name@endif"
        result = engine._parse_control_blocks(template, context)
        assert result == "No name"

    def test_equality_condition_true(self, engine, context):
        """Test equality condition that is true."""
        template = '@if(props.name == "Alice")Correct name@endif'
        result = engine._parse_control_blocks(template, context)
        assert result == "Correct name"

    def test_equality_condition_false(self, engine, context):
        """Test equality condition that is false."""
        template = '@if(props.name == "Bob")Wrong name@endif'
        result = engine._parse_control_blocks(template, context)
        assert result == ""

    def test_inequality_condition(self, engine, context):
        """Test inequality condition."""
        template = '@if(props.name != "Bob")Not Bob@endif'
        result = engine._parse_control_blocks(template, context)
        assert result == "Not Bob"

    def test_greater_than_condition(self, engine, context):
        """Test greater than condition."""
        template = "@if(props.age > 25)Over 25@endif"
        result = engine._parse_control_blocks(template, context)
        assert result == "Over 25"

    def test_less_than_condition(self, engine, context):
        """Test less than condition."""
        template = "@if(props.age < 25)Under 25@endif"
        result = engine._parse_control_blocks(template, context)
        assert result == ""


class TestEvaluateCondition:
    """Tests for _evaluate_condition method."""

    def test_truthiness_check_true(self, engine, context):
        """Test truthiness check with truthy value."""
        assert engine._evaluate_condition("props.name", context) is True

    def test_truthiness_check_false(self, engine):
        """Test truthiness check with falsy value."""
        context = {"props": {"value": ""}, "env": {}, "input": {}}
        assert engine._evaluate_condition("props.value", context) is False

    def test_equality_string_true(self, engine, context):
        """Test equality comparison with string (true)."""
        assert engine._evaluate_condition('props.name == "Alice"', context) is True

    def test_equality_string_false(self, engine, context):
        """Test equality comparison with string (false)."""
        assert engine._evaluate_condition('props.name == "Bob"', context) is False

    def test_equality_number(self, engine, context):
        """Test equality comparison with number."""
        assert engine._evaluate_condition("props.age == 30", context) is True

    def test_inequality(self, engine, context):
        """Test inequality comparison."""
        assert engine._evaluate_condition('props.name != "Bob"', context) is True

    def test_greater_than(self, engine, context):
        """Test greater than comparison."""
        assert engine._evaluate_condition("props.age > 25", context) is True
        assert engine._evaluate_condition("props.age > 35", context) is False

    def test_less_than(self, engine, context):
        """Test less than comparison."""
        assert engine._evaluate_condition("props.age < 35", context) is True
        assert engine._evaluate_condition("props.age < 25", context) is False

    def test_greater_than_or_equal(self, engine, context):
        """Test greater than or equal comparison."""
        assert engine._evaluate_condition("props.age >= 30", context) is True
        assert engine._evaluate_condition("props.age >= 31", context) is False

    def test_less_than_or_equal(self, engine, context):
        """Test less than or equal comparison."""
        assert engine._evaluate_condition("props.age <= 30", context) is True
        assert engine._evaluate_condition("props.age <= 29", context) is False

    def test_missing_path_returns_false(self, engine, context):
        """Test that missing path evaluates to False."""
        assert engine._evaluate_condition("props.missing", context) is False


class TestRenderAdvanced:
    """Tests for render_advanced method."""

    def test_advanced_with_for_loop_and_placeholders(self, engine, context):
        """Test advanced rendering with for loop and basic placeholders."""
        template = "User {{props.name}}: @for(i in range(1, 4))Item {{i}}, @endfor"
        result = engine.render_advanced(template, context)
        assert result == "User Alice: Item 1, Item 2, Item 3, "

    def test_advanced_with_foreach_and_placeholders(self, engine):
        """Test advanced rendering with foreach and basic placeholders."""
        context = {"props": {"name": "Alice", "items": ["a", "b"]}, "env": {}, "input": {}}
        template = "{{props.name}}: @foreach(item in props.items){{item}} @endforeach"
        result = engine.render_advanced(template, context)
        assert result == "Alice: a b "

    def test_advanced_with_if_and_placeholders(self, engine, context):
        """Test advanced rendering with if block and placeholders."""
        template = "@if(props.name)Hello {{props.name}}!@endif"
        result = engine.render_advanced(template, context)
        assert result == "Hello Alice!"

    def test_advanced_complex_nested(self, engine):
        """Test complex nested advanced template."""
        context = {
            "props": {"title": "Report", "items": ["apple", "banana"]},
            "env": {"MODE": "production"},
            "input": {},
        }
        template = """{{props.title}}:
@foreach(item in props.items)
- {{item}}
@endforeach
@if(env.MODE == "production")
Production mode active
@endif"""
        result = engine.render_advanced(template, context)
        assert "Report:" in result
        assert "- apple" in result
        assert "- banana" in result
        assert "Production mode active" in result

    def test_advanced_with_all_features(self, engine):
        """Test advanced rendering with all features combined."""
        context = {
            "props": {"count": 2, "items": [{"name": "Item1"}, {"name": "Item2"}]},
            "env": {"DEBUG": "true"},
            "input": {},
        }
        template = """@if(env.DEBUG == "true")Debug Mode
@endif@foreach(item in props.items){{item.name}} @endforeach"""
        result = engine.render_advanced(template, context)
        assert "Debug Mode" in result
        assert "Item1" in result
        assert "Item2" in result

    def test_whitespace_support_in_loop_variables(self, engine):
        """Test that loop variables support whitespace in placeholders."""
        # Test @foreach with whitespace around variable names
        context = {
            "props": {"items": ["apple", "banana"]},
            "env": {},
            "input": {},
        }
        template = "@foreach(item in props.items){{ item }},{{item}};@endforeach"
        result = engine.render_advanced(template, context)
        
        # Should produce: "apple,apple;banana,banana;"
        assert result == "apple,apple;banana,banana;"

        # Test @for with whitespace around variable names  
        template2 = "@for(i in range(1, 3)){{ i }}-{{i}};@endfor"
        result2 = engine.render_advanced(template2, context)
        
        # Should produce: "1-1;2-2;"
        assert result2 == "1-1;2-2;"
        
        # Test with object properties and whitespace
        context_objects = {
            "props": {"users": [{"name": "Alice"}, {"name": "Bob"}]},
            "env": {},
            "input": {},
        }
        template3 = "@foreach(user in props.users){{ user.name }},{{user.name}};@endforeach"
        result3 = engine.render_advanced(template3, context_objects)
        
        # Should produce: "Alice,Alice;Bob,Bob;"
        assert result3 == "Alice,Alice;Bob,Bob;"
