"""Feature tests for templating engine.

These tests verify the templating engine works end-to-end with realistic scenarios
that mirror actual MCI use cases.
"""

import pytest

from mcipy.templating import TemplateEngine, TemplateError


@pytest.fixture
def engine():
    """Fixture for TemplateEngine instance."""
    return TemplateEngine()


class TestBasicTemplatingFeatures:
    """Test basic templating features in realistic scenarios."""

    def test_api_url_templating(self, engine):
        """Test templating API URLs with props and env."""
        context = {
            "props": {"location": "New York", "units": "metric"},
            "env": {"API_BASE": "https://api.weather.com"},
            "input": {"location": "New York", "units": "metric"},
        }
        url_template = "{{env.API_BASE}}/weather?location={{props.location}}&units={{props.units}}"
        result = engine.render_basic(url_template, context)
        assert result == "https://api.weather.com/weather?location=New York&units=metric"

    def test_auth_header_templating(self, engine):
        """Test templating authentication headers."""
        context = {
            "props": {},
            "env": {"API_KEY": "sk_live_123456789"},
            "input": {},
        }
        header_template = "Bearer {{env.API_KEY}}"
        result = engine.render_basic(header_template, context)
        assert result == "Bearer sk_live_123456789"

    def test_request_body_templating(self, engine):
        """Test templating request body with multiple placeholders."""
        context = {
            "props": {"username": "alice", "email": "alice@example.com", "age": 30},
            "env": {},
            "input": {"username": "alice", "email": "alice@example.com", "age": 30},
        }
        body_template = (
            '{"user": "{{props.username}}", "email": "{{props.email}}", "age": {{props.age}}}'
        )
        result = engine.render_basic(body_template, context)
        assert result == '{"user": "alice", "email": "alice@example.com", "age": 30}'

    def test_file_path_templating(self, engine):
        """Test templating file paths."""
        context = {
            "props": {"report_id": "2024-Q1", "format": "pdf"},
            "env": {"REPORTS_DIR": "/var/reports"},
            "input": {"report_id": "2024-Q1"},
        }
        path_template = "{{env.REPORTS_DIR}}/report-{{props.report_id}}.{{props.format}}"
        result = engine.render_basic(path_template, context)
        assert result == "/var/reports/report-2024-Q1.pdf"

    def test_cli_command_templating(self, engine):
        """Test templating CLI command with working directory."""
        context = {
            "props": {"project": "myapp", "branch": "main"},
            "env": {"HOME": "/home/user"},
            "input": {"project": "myapp"},
        }
        cwd_template = "{{env.HOME}}/projects/{{props.project}}"
        result = engine.render_basic(cwd_template, context)
        assert result == "/home/user/projects/myapp"

    def test_nested_object_templating(self, engine):
        """Test templating with nested object properties."""
        context = {
            "props": {
                "user": {
                    "profile": {"firstName": "John", "lastName": "Doe"},
                    "settings": {"theme": "dark"},
                }
            },
            "env": {},
            "input": {},
        }
        template = "{{props.user.profile.firstName}} {{props.user.profile.lastName}} prefers {{props.user.settings.theme}} mode"
        result = engine.render_basic(template, context)
        assert result == "John Doe prefers dark mode"


class TestAdvancedTemplatingFeatures:
    """Test advanced templating features in realistic scenarios."""

    def test_generate_list_items(self, engine):
        """Test generating list items with foreach."""
        context = {
            "props": {"items": ["Task 1", "Task 2", "Task 3"]},
            "env": {},
            "input": {},
        }
        template = """Todo List:
@foreach(task in props.items)
- {{task}}
@endforeach"""
        result = engine.render_advanced(template, context)
        assert "- Task 1" in result
        assert "- Task 2" in result
        assert "- Task 3" in result

    def test_generate_table_rows(self, engine):
        """Test generating table rows with foreach."""
        context = {
            "props": {
                "users": [
                    {"name": "Alice", "email": "alice@example.com"},
                    {"name": "Bob", "email": "bob@example.com"},
                ]
            },
            "env": {},
            "input": {},
        }
        template = """@foreach(user in props.users){{user.name}} <{{user.email}}>
@endforeach"""
        result = engine.render_advanced(template, context)
        assert "Alice <alice@example.com>" in result
        assert "Bob <bob@example.com>" in result

    def test_numbered_list_with_for(self, engine):
        """Test generating numbered list with for loop."""
        context = {"props": {}, "env": {}, "input": {}}
        template = "@for(i in range(1, 4))Step {{i}}: Do something\n@endfor"
        result = engine.render_advanced(template, context)
        assert "Step 1: Do something" in result
        assert "Step 2: Do something" in result
        assert "Step 3: Do something" in result

    def test_conditional_error_message(self, engine):
        """Test conditional error messages."""
        # Success case
        context_success = {
            "props": {"status": "success", "data": "Operation completed"},
            "env": {},
            "input": {},
        }
        template = '@if(props.status == "success")✓ {{props.data}}@else✗ Error occurred@endif'
        result = engine.render_advanced(template, context_success)
        assert "✓ Operation completed" in result

        # Error case
        context_error = {"props": {"status": "error"}, "env": {}, "input": {}}
        result = engine.render_advanced(template, context_error)
        assert "✗ Error occurred" in result

    def test_environment_specific_config(self, engine):
        """Test environment-specific configuration rendering."""
        # Production environment
        context_prod = {
            "props": {},
            "env": {"ENVIRONMENT": "production", "API_URL": "https://api.prod.com"},
            "input": {},
        }
        template = """@if(env.ENVIRONMENT == "production")Production Configuration:
API: {{env.API_URL}}
Mode: Production
@else Development Configuration:
API: {{env.API_URL}}
Mode: Development
@endif"""
        result = engine.render_advanced(template, context_prod)
        assert "Production Configuration" in result
        assert "https://api.prod.com" in result

    def test_report_generation(self, engine):
        """Test complete report generation with all features."""
        context = {
            "props": {
                "title": "Monthly Sales Report",
                "month": "January",
                "year": 2024,
                "sales": [
                    {"product": "Widget A", "amount": 1200},
                    {"product": "Widget B", "amount": 850},
                    {"product": "Widget C", "amount": 2100},
                ],
                "total": 4150,
            },
            "env": {"COMPANY": "ACME Corp", "GENERATED_BY": "ReportBot"},
            "input": {},
        }
        template = """{{env.COMPANY}} - {{props.title}}
{{props.month}} {{props.year}}

Sales Breakdown:
@foreach(sale in props.sales)
- {{sale.product}}: ${{sale.amount}}
@endforeach

Total: ${{props.total}}

@if(props.total > 4000)
Status: Excellent performance! Target exceeded.
@else Status: Keep up the good work.
@endif

Generated by {{env.GENERATED_BY}}"""

        result = engine.render_advanced(template, context)
        assert "ACME Corp - Monthly Sales Report" in result
        assert "January 2024" in result
        assert "Widget A: $1200" in result
        assert "Widget B: $850" in result
        assert "Widget C: $2100" in result
        assert "Total: $4150" in result
        assert "Excellent performance" in result
        assert "Generated by ReportBot" in result

    def test_dynamic_email_template(self, engine):
        """Test dynamic email generation."""
        context = {
            "props": {
                "recipient": "Alice",
                "items": [
                    {"name": "Product 1", "price": 29.99},
                    {"name": "Product 2", "price": 19.99},
                ],
                "hasDiscount": True,
                "discountPercent": 10,
            },
            "env": {},
            "input": {},
        }
        template = """Dear {{props.recipient}},

Your order contains:
@foreach(item in props.items)
- {{item.name}}: ${{item.price}}
@endforeach

@if(props.hasDiscount)
Special Discount: {{props.discountPercent}}% off!
@endif

Thank you for your order!"""

        result = engine.render_advanced(template, context)
        assert "Dear Alice" in result
        assert "Product 1: $29.99" in result
        assert "Product 2: $19.99" in result
        assert "Special Discount: 10% off!" in result


class TestTemplatingEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_template(self, engine):
        """Test empty template."""
        context = {"props": {}, "env": {}, "input": {}}
        result = engine.render_basic("", context)
        assert result == ""

    def test_template_with_only_text(self, engine):
        """Test template with no placeholders."""
        context = {"props": {}, "env": {}, "input": {}}
        result = engine.render_basic("Just plain text", context)
        assert result == "Just plain text"

    def test_placeholder_at_start(self, engine):
        """Test placeholder at the start of template."""
        context = {"props": {"value": "Start"}, "env": {}, "input": {}}
        result = engine.render_basic("{{props.value}} of text", context)
        assert result == "Start of text"

    def test_placeholder_at_end(self, engine):
        """Test placeholder at the end of template."""
        context = {"props": {"value": "End"}, "env": {}, "input": {}}
        result = engine.render_basic("Text at {{props.value}}", context)
        assert result == "Text at End"

    def test_adjacent_placeholders(self, engine):
        """Test adjacent placeholders without space."""
        context = {"props": {"first": "Hello", "second": "World"}, "env": {}, "input": {}}
        result = engine.render_basic("{{props.first}}{{props.second}}", context)
        assert result == "HelloWorld"

    def test_foreach_with_empty_array(self, engine):
        """Test foreach with empty array produces empty output."""
        context = {"props": {"items": []}, "env": {}, "input": {}}
        template = "@foreach(item in props.items){{item}}@endforeach"
        result = engine.render_advanced(template, context)
        assert result == ""

    def test_for_loop_with_zero_range(self, engine):
        """Test for loop with range that produces no iterations."""
        context = {"props": {}, "env": {}, "input": {}}
        template = "@for(i in range(5, 5)){{i}}@endfor"
        result = engine.render_advanced(template, context)
        assert result == ""

    def test_if_with_nonexistent_path(self, engine):
        """Test if block with path that doesn't exist evaluates to false."""
        context = {"props": {}, "env": {}, "input": {}}
        template = "@if(props.missing)Should not appear@endif"
        result = engine.render_advanced(template, context)
        assert result == ""

    def test_missing_placeholder_raises_error(self, engine):
        """Test that missing placeholder raises appropriate error."""
        context = {"props": {}, "env": {}, "input": {}}
        with pytest.raises(TemplateError) as exc_info:
            engine.render_basic("{{props.missing}}", context)
        assert "not found" in str(exc_info.value)


class TestInputAlias:
    """Test that input is an alias for props."""

    def test_input_and_props_are_same(self, engine):
        """Test that input and props reference the same data."""
        context = {
            "props": {"name": "Alice"},
            "env": {},
            "input": {"name": "Alice"},  # Same data
        }
        template1 = "{{props.name}}"
        template2 = "{{input.name}}"
        result1 = engine.render_basic(template1, context)
        result2 = engine.render_basic(template2, context)
        assert result1 == result2 == "Alice"

    def test_mixed_input_and_props_usage(self, engine):
        """Test using both input and props in same template."""
        context = {
            "props": {"first": "John", "last": "Doe"},
            "env": {},
            "input": {"first": "John", "last": "Doe"},
        }
        template = "{{input.first}} {{props.last}}"
        result = engine.render_basic(template, context)
        assert result == "John Doe"
