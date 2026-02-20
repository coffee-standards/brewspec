"""
`brewlog import` command.

Imports brews from a BrewSpec v0.2 YAML or JSON file.
Validates the file against the JSON Schema before any DB writes.
Uses yaml.safe_load() for all YAML parsing — yaml.load() is prohibited.
All inserts are performed in a single transaction (all-or-nothing).
"""

from __future__ import annotations

import json
import sys

import click
import yaml

from brewlog import db, schema, serialise


@click.command("import")
@click.argument("path", type=str)
def import_cmd(path: str) -> None:
    """Import brews from a BrewSpec v0.2 YAML or JSON file."""

    # -- Path validation (before opening the file) --
    in_path = serialise.validate_import_path(path)

    # -- Detect format from extension --
    suffix = in_path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        fmt = "yaml"
    elif suffix == ".json":
        fmt = "json"
    else:
        click.echo(
            f"Error: unrecognised file extension '{suffix}'. "
            "Supported formats: .yaml, .yml, .json",
            err=True,
        )
        sys.exit(1)

    # -- Parse file --
    raw_text = in_path.read_text(encoding="utf-8")
    if fmt == "yaml":
        try:
            doc = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            click.echo(f"Error parsing YAML: {exc}", err=True)
            sys.exit(1)
    else:
        try:
            doc = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            click.echo(f"Error parsing JSON: {exc}", err=True)
            sys.exit(1)

    if not isinstance(doc, dict):
        click.echo("Error: file content is not a valid BrewSpec document.", err=True)
        sys.exit(1)

    # -- Schema validation (before any DB writes) --
    errors = schema.validate_document(doc)
    if errors:
        click.echo("Validation failed:", err=True)
        for e in errors:
            click.echo(f"  - {e}", err=True)
        sys.exit(1)

    # -- Insert all brews in a single transaction --
    brews = doc.get("brews", [])
    conn = db.get_connection()
    try:
        conn.execute("BEGIN")
        try:
            for brew_dict in brews:
                db.insert_brew_dict(brew_dict, conn)
            conn.commit()
        except Exception:
            conn.rollback()
            click.echo("Error: failed to insert brews. No changes written.", err=True)
            sys.exit(1)
    finally:
        conn.close()

    click.echo(f"Imported {len(brews)} brews.")
