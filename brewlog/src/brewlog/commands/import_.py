"""
`brewlog import` command.

Imports brews from a BrewSpec v0.9 YAML or JSON file.
Validates the file against the JSON Schema before any DB writes.
Uses yaml.safe_load() for all YAML parsing — yaml.load() is prohibited.
All inserts are performed in a single transaction (all-or-nothing).
Deduplicates based on date + type + dose_g + water_weight_g.
"""

from __future__ import annotations

import json
import sys

import click
import yaml

from brewlog import db, schema, serialise

# Verbatim error message for non-v0.9 BrewSpec files.
# The {version} placeholder is replaced with the version string found in the file.
_V09_REQUIRED_MSG = """\
Error: This file uses BrewSpec v{version}, which is not supported by BrewLog v0.8.
BrewLog v0.8 requires BrewSpec v0.9.

To migrate your file from v0.8 to v0.9, make the following changes:
  1. Bump brewspec_version from "0.8" to "0.9"

Full migration guide: https://github.com/coffee-standards/brewspec"""


def _brew_exists(brew_dict: dict, conn) -> bool:
    """
    Return True if a brew with the same date, type, dose_g, and water_weight_g exists.
    All four fields use exact equality (parameterised). AC-15.
    """
    row = conn.execute(
        "SELECT 1 FROM brews WHERE date = ? AND type = ? AND dose_g = ? AND water_weight_g = ? LIMIT 1",
        (
            brew_dict.get("date"),
            brew_dict.get("type"),
            brew_dict.get("dose_g"),
            brew_dict.get("water_weight_g"),
        )
    ).fetchone()
    return row is not None


@click.command("import")
@click.argument("path", type=str)
@click.pass_context
def import_cmd(ctx: click.Context, path: str) -> None:
    """Import brews from a BrewSpec v0.9 YAML or JSON file."""

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

    # -- Check for non-v0.9 BrewSpec version before schema validation --
    file_version = str(doc.get("brewspec_version", ""))
    if file_version != "0.9":
        version_label = file_version if file_version else "(unknown)"
        click.echo(_V09_REQUIRED_MSG.format(version=version_label), err=True)
        sys.exit(1)

    # -- Schema validation (before any DB writes or dedup checks) AC-19 --
    errors = schema.validate_document(doc)
    if errors:
        click.echo("Validation failed:", err=True)
        for e in errors:
            click.echo(f"  - {e}", err=True)
        sys.exit(1)

    # -- Insert brews with deduplication (AC-15 to AC-18) --
    brews = doc.get("brews", [])
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    conn = db.get_connection(db_path=db_path)
    inserted = 0
    skipped = 0
    try:
        conn.execute("BEGIN")
        try:
            for brew_dict in brews:
                if _brew_exists(brew_dict, conn):
                    skipped += 1
                else:
                    db.insert_brew_dict(brew_dict, conn)
                    inserted += 1
            conn.commit()
        except Exception:
            conn.rollback()
            click.echo("Error: failed to insert brews. No changes written.", err=True)
            sys.exit(1)
    finally:
        conn.close()

    click.echo(f"Import complete: {inserted} brews added, {skipped} skipped (already exist).")
