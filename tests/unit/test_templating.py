"""Unit tests for templating engine."""

from typing import Any

import pytest

from mcipy.templating import TemplateEngine, TemplateError


class TestTemplateEngine:
    """Tests for TemplateEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TemplateEngine()  # pyright: ignore[reportUninitializedInstanceVariable]
        self.context: dict[str, Any] = {  # pyright: ignore[reportUninitializedInstanceVariable]
            "props": {"name": "Alice", "age": 30, "city": "NYC"},
            "env": {"API_KEY": "secret123", "USER": "testuser"},
            "input": {"name": "Alice", "age": 30, "city": "NYC"},
        }


class TestRenderBasic(TestTemplateEngine):
    """Tests for render_basic method."""

    def test_simple_placeholder_props(self):
        """Test simple placeholder replacement from props."""
        template = "Hello {{props.name}}"
        result = self.engine.render_basic(template, self.context)
        assert result == "Hello Alice"

    def test_simple_placeholder_env(self):
        """Test simple placeholder replacement from env."""
        template = "API Key: {{env.API_KEY}}"
        result = self.engine.render_basic(template, self.context)
        assert result == "API Key: secret123"

    def test_simple_placeholder_input(self):
        """Test simple placeholder replacement from input (alias for props)."""
        template = "User: {{input.name}}"
        result = self.engine.render_basic(template, self.context)
        assert result == "User: Alice"

    def test_multiple_placeholders(self):
        """Test multiple placeholders in one template."""
        template = "{{props.name}} lives in {{props.city}}, age {{props.age}}"
        result = self.engine.render_basic(template, self.context)
        assert result == "Alice lives in NYC, age 30"

    def test_mixed_props_and_env(self):
        """Test mixing props and env placeholders."""
        template = "User {{env.USER}} has name {{props.name}}"
        result = self.engine.render_basic(template, self.context)
        assert result == "User testuser has name Alice"

    def test_placeholder_with_whitespace(self):
        """Test placeholders with whitespace are handled."""
        template = "{{ props.name }} and {{ env.USER }}"
        result = self.engine.render_basic(template, self.context)
        assert result == "Alice and testuser"

    def test_no_placeholders(self):
        """Test template with no placeholders."""
        template = "Just plain text"
        result = self.engine.render_basic(template, self.context)
        assert result == "Just plain text"

    def test_missing_placeholder(self):
        """Test error when placeholder path doesn't exist."""
        template = "Hello {{props.missing}}"
        with pytest.raises(TemplateError) as exc_info:
            self.engine.render_basic(template, self.context)
        assert "props.missing" in str(exc_info.value)


class TestResolvePlaceholder(TestTemplateEngine):
    """Tests for _resolve_placeholder method."""

    def test_resolve_simple_path(self):
        """Test resolving a simple path."""
        result = self.engine._resolve_placeholder("props.name", self.context)
        assert result == "Alice"

    def test_resolve_nested_path(self):
        """Test resolving nested paths."""
        context = {"props": {"user": {"profile": {"name": "Bob", "email": "bob@example.com"}}}}
        result = self.engine._resolve_placeholder("props.user.profile.name", context)
        assert result == "Bob"

    def test_resolve_env_path(self):
        """Test resolving environment variable path."""
        result = self.engine._resolve_placeholder("env.API_KEY", self.context)
        assert result == "secret123"

    def test_resolve_missing_key(self):
        """Test error when key doesn't exist."""
        with pytest.raises(TemplateError) as exc_info:
            self.engine._resolve_placeholder("props.nonexistent", self.context)
        assert "not found" in str(exc_info.value)

    def test_resolve_missing_nested_key(self):
        """Test error when nested key doesn't exist."""
        context = {"props": {"user": {"name": "Alice"}}}
        with pytest.raises(TemplateError) as exc_info:
            self.engine._resolve_placeholder("props.user.email", context)
        assert "not found" in str(exc_info.value)

    def test_resolve_non_dict_access(self):
        """Test error when trying to access property on non-dict."""
        context = {"props": {"value": "string"}}
        with pytest.raises(TemplateError) as exc_info:
            self.engine._resolve_placeholder("props.value.invalid", context)
        assert "non-dict" in str(exc_info.value)


class TestParseForLoop(TestTemplateEngine):
    """Tests for _parse_for_loop method."""

    def test_simple_for_loop(self):
        """Test simple for loop."""
        template = "@for(i in range(0, 3))Item {{i}} @endfor"
        result = self.engine._parse_for_loop(template, self.context)
        assert result == "Item 0 Item 1 Item 2 "

    def test_for_loop_with_text(self):
        """Test for loop with surrounding text."""
        template = "Start @for(i in range(1, 4)){{i}}, @endfor End"
        result = self.engine._parse_for_loop(template, self.context)
        assert result == "Start 1, 2, 3,  End"

    def test_for_loop_single_iteration(self):
        """Test for loop with single iteration."""
        template = "@for(i in range(0, 1))Single {{i}}@endfor"
        result = self.engine._parse_for_loop(template, self.context)
        assert result == "Single 0"

    def test_for_loop_zero_iterations(self):
        """Test for loop with zero iterations."""
        template = "@for(i in range(0, 0))Should not appear@endfor"
        result = self.engine._parse_for_loop(template, self.context)
        assert result == ""

    def test_multiple_for_loops(self):
        """Test multiple for loops in same template."""
        template = "@for(i in range(0, 2))A{{i}}@endfor-@for(j in range(0, 2))B{{j}}@endfor"
        result = self.engine._parse_for_loop(template, self.context)
        assert result == "A0A1-B0B1"


class TestParseForeachLoop(TestTemplateEngine):
    """Tests for _parse_foreach_loop method."""

    def test_foreach_simple_array(self):
        """Test foreach loop with simple array."""
        context = {"props": {"items": ["apple", "banana", "cherry"]}, "env": {}, "input": {}}
        template = "@foreach(item in props.items){{item}}, @endforeach"
        result = self.engine._parse_foreach_loop(template, context)
        assert result == "apple, banana, cherry, "

    def test_foreach_array_of_objects(self):
        """Test foreach loop with array of objects."""
        context = {
            "props": {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]},
            "env": {},
            "input": {},
        }
        template = "@foreach(user in props.users){{user.name}} is {{user.age}}, @endforeach"
        result = self.engine._parse_foreach_loop(template, context)
        assert result == "Alice is 30, Bob is 25, "

    def test_foreach_object(self):
        """Test foreach loop with object/dict."""
        context = {"props": {"config": {"host": "localhost", "port": 8080}}, "env": {}, "input": {}}
        template = "@foreach(value in props.config){{value}}, @endforeach"
        result = self.engine._parse_foreach_loop(template, context)
        # Note: dict iteration order is preserved in Python 3.7+
        assert "localhost" in result and "8080" in result

    def test_foreach_empty_array(self):
        """Test foreach loop with empty array."""
        context = {"props": {"items": []}, "env": {}, "input": {}}
        template = "@foreach(item in props.items){{item}}@endforeach"
        result = self.engine._parse_foreach_loop(template, context)
        assert result == ""

    def test_foreach_missing_path(self):
        """Test error when foreach path doesn't exist."""
        template = "@foreach(item in props.missing){{item}}@endforeach"
        with pytest.raises(TemplateError) as exc_info:
            self.engine._parse_foreach_loop(template, self.context)
        assert "props.missing" in str(exc_info.value)

    def test_foreach_non_iterable(self):
        """Test error when foreach path is not array or object."""
        context = {"props": {"value": "string"}, "env": {}, "input": {}}
        template = "@foreach(item in props.value){{item}}@endforeach"
        with pytest.raises(TemplateError) as exc_info:
            self.engine._parse_foreach_loop(template, context)
        assert "array or object" in str(exc_info.value)


class TestParseControlBlocks(TestTemplateEngine):
    """Tests for _parse_control_blocks method."""

    def test_if_true_condition(self):
        """Test if block with true condition."""
        template = "@if(props.name)Name exists@endif"
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == "Name exists"

    def test_if_false_condition(self):
        """Test if block with false condition."""
        context = {"props": {"name": ""}, "env": {}, "input": {}}
        template = "@if(props.name)Name exists@endif"
        result = self.engine._parse_control_blocks(template, context)
        assert result == ""

    def test_if_else_true(self):
        """Test if/else block when condition is true."""
        template = "@if(props.name)Has name@else No name@endif"
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == "Has name"

    def test_if_else_false(self):
        """Test if/else block when condition is false."""
        context = {"props": {"name": ""}, "env": {}, "input": {}}
        template = "@if(props.name)Has name@else No name@endif"
        result = self.engine._parse_control_blocks(template, context)
        assert result == "No name"

    def test_equality_condition_true(self):
        """Test equality condition that is true."""
        template = '@if(props.name == "Alice")Correct name@endif'
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == "Correct name"

    def test_equality_condition_false(self):
        """Test equality condition that is false."""
        template = '@if(props.name == "Bob")Wrong name@endif'
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == ""

    def test_inequality_condition(self):
        """Test inequality condition."""
        template = '@if(props.name != "Bob")Not Bob@endif'
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == "Not Bob"

    def test_greater_than_condition(self):
        """Test greater than condition."""
        template = "@if(props.age > 25)Over 25@endif"
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == "Over 25"

    def test_less_than_condition(self):
        """Test less than condition."""
        template = "@if(props.age < 25)Under 25@endif"
        result = self.engine._parse_control_blocks(template, self.context)
        assert result == ""


class TestEvaluateCondition(TestTemplateEngine):
    """Tests for _evaluate_condition method."""

    def test_truthiness_check_true(self):
        """Test truthiness check with truthy value."""
        assert self.engine._evaluate_condition("props.name", self.context) is True

    def test_truthiness_check_false(self):
        """Test truthiness check with falsy value."""
        context = {"props": {"value": ""}, "env": {}, "input": {}}
        assert self.engine._evaluate_condition("props.value", context) is False

    def test_equality_string_true(self):
        """Test equality comparison with string (true)."""
        assert self.engine._evaluate_condition('props.name == "Alice"', self.context) is True

    def test_equality_string_false(self):
        """Test equality comparison with string (false)."""
        assert self.engine._evaluate_condition('props.name == "Bob"', self.context) is False

    def test_equality_number(self):
        """Test equality comparison with number."""
        assert self.engine._evaluate_condition("props.age == 30", self.context) is True

    def test_inequality(self):
        """Test inequality comparison."""
        assert self.engine._evaluate_condition('props.name != "Bob"', self.context) is True

    def test_greater_than(self):
        """Test greater than comparison."""
        assert self.engine._evaluate_condition("props.age > 25", self.context) is True
        assert self.engine._evaluate_condition("props.age > 35", self.context) is False

    def test_less_than(self):
        """Test less than comparison."""
        assert self.engine._evaluate_condition("props.age < 35", self.context) is True
        assert self.engine._evaluate_condition("props.age < 25", self.context) is False

    def test_greater_than_or_equal(self):
        """Test greater than or equal comparison."""
        assert self.engine._evaluate_condition("props.age >= 30", self.context) is True
        assert self.engine._evaluate_condition("props.age >= 31", self.context) is False

    def test_less_than_or_equal(self):
        """Test less than or equal comparison."""
        assert self.engine._evaluate_condition("props.age <= 30", self.context) is True
        assert self.engine._evaluate_condition("props.age <= 29", self.context) is False

    def test_missing_path_returns_false(self):
        """Test that missing path evaluates to False."""
        assert self.engine._evaluate_condition("props.missing", self.context) is False


class TestRenderAdvanced(TestTemplateEngine):
    """Tests for render_advanced method."""

    def test_advanced_with_for_loop_and_placeholders(self):
        """Test advanced rendering with for loop and basic placeholders."""
        template = "User {{props.name}}: @for(i in range(1, 4))Item {{i}}, @endfor"
        result = self.engine.render_advanced(template, self.context)
        assert result == "User Alice: Item 1, Item 2, Item 3, "

    def test_advanced_with_foreach_and_placeholders(self):
        """Test advanced rendering with foreach and basic placeholders."""
        context = {"props": {"name": "Alice", "items": ["a", "b"]}, "env": {}, "input": {}}
        template = "{{props.name}}: @foreach(item in props.items){{item}} @endforeach"
        result = self.engine.render_advanced(template, context)
        assert result == "Alice: a b "

    def test_advanced_with_if_and_placeholders(self):
        """Test advanced rendering with if block and placeholders."""
        template = "@if(props.name)Hello {{props.name}}!@endif"
        result = self.engine.render_advanced(template, self.context)
        assert result == "Hello Alice!"

    def test_advanced_complex_nested(self):
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
        result = self.engine.render_advanced(template, context)
        assert "Report:" in result
        assert "- apple" in result
        assert "- banana" in result
        assert "Production mode active" in result

    def test_advanced_with_all_features(self):
        """Test advanced rendering with all features combined."""
        context = {
            "props": {"count": 2, "items": [{"name": "Item1"}, {"name": "Item2"}]},
            "env": {"DEBUG": "true"},
            "input": {},
        }
        template = """@if(env.DEBUG == "true")Debug Mode
@endif@foreach(item in props.items){{item.name}} @endforeach"""
        result = self.engine.render_advanced(template, context)
        assert "Debug Mode" in result
        assert "Item1" in result
        assert "Item2" in result
