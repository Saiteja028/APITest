"""JSON Schema validation helpers.

Wraps ``jsonschema`` to give clear, test-friendly failure messages and to
accept a schema as a dict, a path, or a bare schema name under ``schemas/``.
"""
from __future__ import annotations

from typing import Any, Union

from jsonschema import Draft202012Validator

from framework.utils.data_loader import load_schema


def validate_schema(instance: Any, schema: Union[dict, str]) -> None:
    """Validate ``instance`` against ``schema``.

    ``schema`` may be a schema dict or the name/path of a schema file under
    ``schemas/``. Raises ``AssertionError`` listing every violation on failure.
    """
    schema_dict = schema if isinstance(schema, dict) else load_schema(schema)

    validator = Draft202012Validator(schema_dict)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        lines = [
            f"  - {'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
            for err in errors
        ]
        raise AssertionError(
            "Schema validation failed with "
            f"{len(errors)} error(s):\n" + "\n".join(lines)
        )
