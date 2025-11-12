"""
Templating engine for MCI.

This module provides the templating functionality for the MCI adapter,
enabling placeholder substitution, loops, and control blocks in templates.
It supports basic placeholder substitution ({{props.x}}, {{env.Y}}) and
advanced templating with @for, @foreach, and @if control structures.
"""

import re
from typing import Any


class TemplateError(Exception):
    """Exception raised when template processing fails."""

    pass


class TemplateEngine:
    """
    Template engine for processing MCI templates.

    Handles both basic placeholder substitution and advanced templating
    features like loops and conditional blocks. The engine supports:
    - Basic placeholders: {{props.propertyName}}, {{env.VAR_NAME}}
    - JSON-native placeholders: {!!props.propertyName!!}, {!!env.VAR_NAME!!}
    - For loops: @for(i in range(0, 5)) ... @endfor
    - Foreach loops: @foreach(item in items) ... @endforeach
    - Control blocks: @if(condition) ... @elseif(condition) ... @else ... @endif
    """

    # Pattern for JSON-native placeholders: {!!path!!} with optional whitespace
    _JSON_NATIVE_PATTERN = r"^\{!!\s*([^}]+?)\s*!!\}$"

    def is_json_native_placeholder(self, value: str) -> bool:
        """
        Check if a string is a JSON-native placeholder (and only that).

        A valid JSON-native placeholder must be exactly in the format:
        {!!path.to.value!!} with optional whitespace around the path.

        Args:
            value: String to check

        Returns:
            True if the string is exactly a JSON-native placeholder, False otherwise
        """
        if not isinstance(value, str):
            return False

        # Pattern: exactly {!! ... !!} with nothing before or after
        return bool(re.match(self._JSON_NATIVE_PATTERN, value))

    def resolve_json_native(self, placeholder: str, context: dict[str, Any]) -> Any:
        """
        Resolve a JSON-native placeholder to its native type.

        Extracts the path from {!!path!!} syntax and resolves it to the actual
        value without converting to string. This preserves booleans, numbers,
        arrays, objects, and null values.

        Args:
            placeholder: The placeholder string (e.g., "{!!props.include_images!!}")
            context: Context dictionary with 'props', 'env', and 'input' keys

        Returns:
            The resolved value in its native type

        Raises:
            TemplateError: If the placeholder is invalid or cannot be resolved
        """
        # Validate it's a JSON-native placeholder
        if not self.is_json_native_placeholder(placeholder):
            raise TemplateError(
                f"Invalid JSON-native placeholder format: '{placeholder}'. "
                "Must be exactly {!!path!!} with no surrounding content."
            )

        # Extract the path from {!! ... !!}
        match = re.match(self._JSON_NATIVE_PATTERN, placeholder)
        if not match:
            raise TemplateError(f"Failed to extract path from placeholder: '{placeholder}'")

        path = match.group(1).strip()

        # Resolve the path to its native value
        try:
            value = self._resolve_placeholder(path, context)
            return value
        except Exception as e:
            raise TemplateError(
                f"Failed to resolve JSON-native placeholder '{placeholder}': {e}"
            ) from e

    def render_basic(self, template: str, context: dict[str, Any]) -> str:
        """
        Perform basic placeholder substitution.

        Replaces placeholders like {{props.propertyName}} and {{env.VAR_NAME}}
        with their values from the context. Supports fallback syntax with | operator:
        - {{env.VAR | 'default'}} - Use string literal as fallback
        - {{env.VAR | env.OTHER}} - Use another variable as fallback
        - {{env.VAR | env.OTHER | '/tmp'}} - Chain multiple fallbacks

        Args:
            template: The template string containing placeholders
            context: Dictionary with 'props', 'env', and 'input' keys

        Returns:
            The template with all placeholders replaced

        Raises:
            TemplateError: If a placeholder cannot be resolved and no fallback is provided
        """
        # Pattern to match {{path.to.value}} or {{path.to.value | fallback | ...}}
        pattern = r"\{\{([^}]+)\}\}"

        def replace_placeholder(match: re.Match[str]) -> str:
            full_path = match.group(1).strip()
            try:
                value = self._resolve_placeholder_with_fallback(full_path, context)
                return str(value)
            except Exception as e:
                # Create placeholder string for error message
                placeholder_str = "{{" + full_path + "}}"
                raise TemplateError(
                    f"Failed to resolve placeholder '{placeholder_str}': {e}"
                ) from e

        return re.sub(pattern, replace_placeholder, template)

    def render_advanced(self, template: str, context: dict[str, Any]) -> str:
        """
        Perform advanced templating with loops and control blocks.

        Processes @for, @foreach, and @if/@elseif/@else/@endif blocks
        in addition to basic placeholder substitution.

        Args:
            template: The template string with advanced directives
            context: Dictionary with 'props', 'env', and 'input' keys

        Returns:
            The fully processed template

        Raises:
            TemplateError: If template processing fails
        """
        # Process control structures in order
        # 1. First process loops (they can contain conditionals)
        result = self._parse_for_loop(template, context)
        result = self._parse_foreach_loop(result, context)

        # 2. Then process conditionals
        result = self._parse_control_blocks(result, context)

        # 3. Finally, replace basic placeholders
        result = self.render_basic(result, context)

        return result

    def _resolve_placeholder_with_fallback(self, full_path: str, context: dict[str, Any]) -> Any:
        """
        Resolve a placeholder with optional fallback values using | operator.

        Supports:
        - env.VAR - Simple variable
        - env.VAR | 'default' - Fallback to string literal (single quotes or backticks)
        - env.VAR | env.OTHER - Fallback to another variable
        - env.VAR | env.OTHER | '/tmp' - Chain multiple fallbacks

        Args:
            full_path: Path with optional fallbacks (e.g., "env.VAR | 'default' | env.OTHER")
            context: Context dictionary

        Returns:
            The resolved value or fallback

        Raises:
            TemplateError: If no path can be resolved and no valid fallback provided
        """
        # Split by | to get alternatives
        alternatives = [alt.strip() for alt in full_path.split("|")]

        errors = []
        for alt in alternatives:
            # Check if it's a string literal (single quotes or backticks)
            if (alt.startswith("'") and alt.endswith("'")) or (
                alt.startswith("`") and alt.endswith("`")
            ):
                # Return the string literal without quotes
                return alt[1:-1]

            # Try to resolve as a variable path
            try:
                return self._resolve_placeholder(alt, context)
            except TemplateError as e:
                errors.append(f"{alt}: {e}")
                continue

        # If all alternatives failed, raise an error
        raise TemplateError(
            f"Could not resolve any alternative. Tried: {', '.join(alternatives)}. Errors: {'; '.join(errors)}"
        )

    def _resolve_placeholder(self, path: str, context: dict[str, Any]) -> Any:
        """
        Resolve a dot-notation path in the context.

        Supports paths like 'props.location', 'env.API_KEY', 'input.user.name'

        Args:
            path: Dot-notation path to resolve
            context: Context dictionary

        Returns:
            The value at the specified path

        Raises:
            TemplateError: If the path cannot be resolved
        """
        parts = path.split(".")
        current = context

        for i, part in enumerate(parts):
            if not isinstance(current, dict):
                raise TemplateError(
                    f"Cannot access '{part}' on non-dict value at '{'.'.join(parts[:i])}'"
                )

            if part not in current:
                raise TemplateError(f"Path '{path}' not found in context (missing '{part}')")

            current = current[part]

        return current

    def _replace_placeholders_with_whitespace_support(
        self, content: str, replacements: dict[str, str]
    ) -> str:
        """
        Replace placeholders in content, supporting optional whitespace around variable names.

        Args:
            content: The content containing placeholders
            replacements: Dictionary mapping variable paths to replacement values

        Returns:
            Content with placeholders replaced
        """
        result = content
        for var_path, replacement in replacements.items():
            # Pattern to match {{var_path}} with optional whitespace
            pattern = rf"\{{\{{\s*{re.escape(var_path)}\s*\}}\}}"
            result = re.sub(pattern, replacement, result)
        return result

    def _parse_for_loop(self, content: str, context: dict[str, Any]) -> str:
        """
        Parse and process @for loops.

        Supports syntax: @for(variable in range(start, end))...@endfor

        Args:
            content: Template content containing @for loops
            context: Context dictionary

        Returns:
            Content with @for loops expanded
        """
        # Pattern to match @for(var in range(start, end)) ... @endfor
        pattern = r"@for\s*\(\s*(\w+)\s+in\s+range\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*\)(.*?)@endfor"

        def replace_for_loop(match: re.Match[str]) -> str:
            var_name = match.group(1)
            start = int(match.group(2))
            end = int(match.group(3))
            body = match.group(4)

            result = []
            for i in range(start, end):
                # Create a new context with the loop variable
                loop_context = context.copy()
                loop_context[var_name] = i

                # Process the body with the loop variable available
                processed_body = body
                # Replace {{var_name}} with the current value, supporting whitespace
                replacements = {var_name: str(i)}
                processed_body = self._replace_placeholders_with_whitespace_support(
                    processed_body, replacements
                )

                result.append(processed_body)

            return "".join(result)

        return re.sub(pattern, replace_for_loop, content, flags=re.DOTALL)

    def _parse_foreach_loop(self, content: str, context: dict[str, Any]) -> str:
        """
        Parse and process @foreach loops.

        Supports syntax: @foreach(item in items)...@endforeach
        where 'items' is a path in the context (e.g., 'props.myArray')

        Args:
            content: Template content containing @foreach loops
            context: Context dictionary

        Returns:
            Content with @foreach loops expanded
        """
        # Pattern to match @foreach(var in path.to.array) ... @endforeach
        pattern = r"@foreach\s*\(\s*(\w+)\s+in\s+([\w.]+)\s*\)(.*?)@endforeach"

        def replace_foreach_loop(match: re.Match[str]) -> str:
            var_name = match.group(1)
            path = match.group(2)
            body = match.group(3)

            # Resolve the array/object from the context
            try:
                items = self._resolve_placeholder(path, context)
            except TemplateError as e:
                raise TemplateError(f"Failed to resolve foreach path '{path}': {e}") from e

            if not isinstance(items, (list, dict)):
                raise TemplateError(
                    f"@foreach requires an array or object, got {type(items).__name__}"
                )

            result = []
            if isinstance(items, list):
                for item in items:
                    # Create a new context with the loop variable
                    loop_context = context.copy()
                    loop_context[var_name] = item

                    # Process the body
                    processed_body = body
                    # Replace {{var_name}} with the current value, supporting whitespace
                    if isinstance(item, dict):
                        # For objects, allow {{var_name.property}} access
                        replacements = {}
                        for key, value in item.items():
                            replacements[f"{var_name}.{key}"] = str(value)
                        processed_body = self._replace_placeholders_with_whitespace_support(
                            processed_body, replacements
                        )
                    else:
                        replacements = {var_name: str(item)}
                        processed_body = self._replace_placeholders_with_whitespace_support(
                            processed_body, replacements
                        )

                    result.append(processed_body)
            else:  # dict
                for key, value in items.items():
                    # Create a new context with the loop variable
                    loop_context = context.copy()
                    loop_context[var_name] = value

                    # Process the body
                    processed_body = body
                    # Replace {{var_name}} with value and {{var_name.key}} with key, supporting whitespace
                    replacements = {var_name: str(value), f"{var_name}.key": str(key)}
                    processed_body = self._replace_placeholders_with_whitespace_support(
                        processed_body, replacements
                    )

                    result.append(processed_body)

            return "".join(result)

        return re.sub(pattern, replace_foreach_loop, content, flags=re.DOTALL)

    def _parse_control_blocks(self, content: str, context: dict[str, Any]) -> str:
        """
        Parse and process @if/@elseif/@else/@endif control blocks.

        Supports syntax:
        @if(condition)...@elseif(condition)...@else...@endif

        Conditions can be:
        - path.to.value (truthy check)
        - path.to.value == "value" (equality)
        - path.to.value != "value" (inequality)
        - path.to.value > number (greater than)
        - path.to.value < number (less than)

        Args:
            content: Template content containing control blocks
            context: Context dictionary

        Returns:
            Content with control blocks evaluated
        """
        # Pattern to match @if ... @endif with optional @elseif and @else
        pattern = r"@if\s*\((.*?)\)(.*?)(?:@elseif\s*\((.*?)\)(.*?))*(?:@else(.*?))?@endif"

        def replace_control_block(match: re.Match[str]) -> str:
            # This is a simplified version - for a full implementation,
            # we'd need to properly parse the full match with all elseifs
            # For now, we'll handle the basic if/else case
            full_match = match.group(0)

            # Split into parts to handle elseif and else properly
            parts = full_match.split("@elseif")
            if_part = parts[0]

            # Extract @if condition and body
            if_match = re.match(r"@if\s*\((.*?)\)(.*)", if_part, re.DOTALL)
            if not if_match:
                return full_match

            if_condition = if_match.group(1).strip()
            remaining = if_match.group(2)

            # Find where the if body ends
            if "@else" in remaining:
                if_body, else_part = remaining.split("@else", 1)
                else_body = else_part.replace("@endif", "").strip()
            else:
                if_body = remaining.replace("@endif", "").strip()
                else_body = ""

            # Evaluate the condition
            if self._evaluate_condition(if_condition, context):
                return if_body
            elif len(parts) > 1:
                # Handle elseif cases
                for elseif_part in parts[1:]:
                    elseif_match = re.match(r"\s*\((.*?)\)(.*)", elseif_part, re.DOTALL)
                    if elseif_match:
                        elseif_condition = elseif_match.group(1).strip()
                        elseif_remaining = elseif_match.group(2)

                        if "@else" in elseif_remaining:
                            elseif_body = elseif_remaining.split("@else")[0].strip()
                        elif "@endif" in elseif_remaining:
                            elseif_body = elseif_remaining.replace("@endif", "").strip()
                        else:
                            elseif_body = elseif_remaining.strip()

                        if self._evaluate_condition(elseif_condition, context):
                            return elseif_body

                return else_body
            else:
                return else_body

        return re.sub(pattern, replace_control_block, content, flags=re.DOTALL)

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.

        Supports:
        - path.to.value (truthy check)
        - path.to.value == "value" or path.to.value == number
        - path.to.value != "value" or path.to.value != number
        - path.to.value > number
        - path.to.value < number
        - path.to.value >= number
        - path.to.value <= number

        Args:
            condition: The condition expression to evaluate
            context: Context dictionary

        Returns:
            True if condition is met, False otherwise
        """
        condition = condition.strip()

        # Check for comparison operators
        for op in ["==", "!=", ">=", "<=", ">", "<"]:
            if op in condition:
                parts = condition.split(op, 1)
                left = parts[0].strip()
                right = parts[1].strip()

                # Resolve left side
                try:
                    left_value = self._resolve_placeholder(left, context)
                except TemplateError:
                    left_value = left

                # Resolve right side (could be a string, number, or path)
                if right.startswith('"') and right.endswith('"'):
                    right_value = right[1:-1]
                elif right.startswith("'") and right.endswith("'"):
                    right_value = right[1:-1]
                else:
                    try:
                        # Try to parse as number
                        if "." in right:
                            right_value = float(right)
                        else:
                            right_value = int(right)
                    except ValueError:
                        # Try to resolve as path
                        try:
                            right_value = self._resolve_placeholder(right, context)
                        except TemplateError:
                            right_value = right

                # Perform comparison
                if op == "==":
                    return left_value == right_value
                elif op == "!=":
                    return left_value != right_value
                elif op == ">":
                    if not (
                        isinstance(left_value, (int, float))
                        and isinstance(right_value, (int, float))
                    ):
                        raise TemplateError(
                            f"Cannot compare types '{type(left_value).__name__}' and '{type(right_value).__name__}' with '>'"
                        )
                    return left_value > right_value  # pyright: ignore[reportOperatorIssue]
                elif op == "<":
                    if not (
                        isinstance(left_value, (int, float))
                        and isinstance(right_value, (int, float))
                    ):
                        raise TemplateError(
                            f"Cannot compare types '{type(left_value).__name__}' and '{type(right_value).__name__}' with '<'"
                        )
                    return left_value < right_value  # pyright: ignore[reportOperatorIssue]
                elif op == ">=":
                    if not (
                        isinstance(left_value, (int, float))
                        and isinstance(right_value, (int, float))
                    ):
                        raise TemplateError(
                            f"Cannot compare types '{type(left_value).__name__}' and '{type(right_value).__name__}' with '>='"
                        )
                    return left_value >= right_value  # pyright: ignore[reportOperatorIssue]
                elif op == "<=":
                    if not (
                        isinstance(left_value, (int, float))
                        and isinstance(right_value, (int, float))
                    ):
                        raise TemplateError(
                            f"Cannot compare types '{type(left_value).__name__}' and '{type(right_value).__name__}' with '<='"
                        )
                    return left_value <= right_value  # pyright: ignore[reportOperatorIssue]

        # No operator found - just check truthiness
        try:
            value = self._resolve_placeholder(condition, context)
            return bool(value)
        except TemplateError:
            return False
