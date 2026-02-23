"""
Schema validation module for BrewLog.

Loads the bundled brewspec.schema.json using importlib.resources and exposes
a validate_document() function.

The $id URL in the schema is metadata only — Draft202012Validator does not
fetch it. No network calls are made.
"""

from __future__ import annotations

import importlib.resources
import json

from jsonschema import Draft202012Validator


# AC-15: configurable constant for the schema resource name.
SCHEMA_RESOURCE_NAME = "brewspec.schema.json"


def _load_schema() -> dict:
    """Load the bundled BrewSpec v0.4 schema using importlib.resources."""
    with importlib.resources.files("brewlog").joinpath(SCHEMA_RESOURCE_NAME).open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


_SCHEMA = _load_schema()
_VALIDATOR = Draft202012Validator(_SCHEMA)


def validate_document(doc: dict) -> list[str]:
    """
    Validate a parsed BrewSpec document dict against the v0.4 JSON Schema.
    Returns a list of error message strings. Empty list means valid.
    """
    errors = sorted(_VALIDATOR.iter_errors(doc), key=lambda e: list(e.path))
    return [e.message for e in errors]
